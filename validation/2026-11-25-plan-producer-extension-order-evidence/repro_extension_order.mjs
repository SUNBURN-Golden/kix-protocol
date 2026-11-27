import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  copyFileSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, rmSync, writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, isAbsolute, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { parseStrict } from "../../sdk/src/jsonschema.ts";
import { canonicalBytes, gitBlobId, sha256Hex } from "../../sdk/src/manifest.ts";

const checkout = realpathSync(fileURLToPath(new URL("../..", import.meta.url)));
const verifierPath = "sdk/compat/verify_compat.mjs";
const verifierSha256 = "8628518c41b4110f0adf9a5d841240ae06dc6c1fa5d5c4974f00d96a718c5de6";
const verifierBlob = "4d744a7e622f2678054b9f709a138252635309c6";
const pins = [
  {
    revision: "bootstrap-2",
    kind: "BOOTSTRAP",
    sha256: "eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0",
  },
  {
    revision: "commerce-fixture-8ba7f6c-1",
    kind: "SEMANTIC_CONFORMANCE",
    sha256: "76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f",
  },
];
const extensionDigest = "source_references.extension_profile.sha256";
const badDigest = "0".repeat(64);
const cases = [
  { name: "pristine", fields: [], errors: [] },
  {
    name: "extension-plus-profile",
    fields: [extensionDigest, "profile_sha256"],
    errors: ["extension_profile bytes drift", "profile bytes drift"],
  },
  {
    name: "extension-plus-sdk-output",
    fields: [extensionDigest, "sdk_output.sha256"],
    errors: ["extension_profile bytes drift", "sdk_output bytes drift"],
  },
];

function snapshot(root) {
  const entries = readdirSync(root, { recursive: true, withFileTypes: true });
  return new Map(entries.map((entry) => {
    const path = join(entry.parentPath, entry.name);
    assert.ok(entry.isDirectory() || entry.isFile(), `unexpected entry type: ${path}`);
    return [relative(root, path), entry.isDirectory() ? null : readFileSync(path)];
  }));
}

function fixtureFiles(manifestPath, revision, manifest) {
  return new Set([
    verifierPath,
    "sdk/src/jsonschema.ts",
    "sdk/src/manifest.ts",
    "sdk/package.json",
    "toolchains.json",
    manifestPath,
    `${manifestPath}.sha256`,
    `sdk/compat/profiles/${revision}.profile.json`,
    manifest.contract.contract_only.path,
    manifest.contract.integration_gate.path,
    manifest.generator.path,
    manifest.sdk_output.path,
    manifest.source_references.fixture_profile,
    manifest.source_references.extension_profile.path,
    ...manifest.vectors.map((vector) => vector.path),
  ]);
}

function digestField(manifest, field) {
  const path = field.split(".");
  const key = path.pop();
  return [path.reduce((parent, segment) => parent[segment], manifest), key];
}

function applyFaults(manifestFile, fields) {
  const pristine = readFileSync(manifestFile);
  const manifest = parseStrict(pristine);
  const originals = fields.map((field) => {
    const [target, key] = digestField(manifest, field);
    const original = target[key];
    assert.match(original, /^[0-9a-f]{64}$/u, field);
    assert.notEqual(original, badDigest, field);
    target[key] = badDigest;
    return original;
  });

  const mutated = canonicalBytes(manifest);
  writeFileSync(manifestFile, mutated);
  writeFileSync(`${manifestFile}.sha256`, `${sha256Hex(mutated)}\n`);

  // Restore the selected fields in memory and compare the full canonical bytes.
  const checked = parseStrict(readFileSync(manifestFile));
  fields.forEach((field, index) => {
    const [target, key] = digestField(checked, field);
    assert.equal(target[key], badDigest, field);
    target[key] = originals[index];
  });
  assert.deepEqual(Buffer.from(canonicalBytes(checked)), pristine);
}

function runCase(pin, testCase) {
  const { revision, kind, sha256 } = pin;
  const { name, fields, errors } = testCase;
  const context = `${revision} / ${name}`;
  const manifestPath = `sdk/compat/manifests/manifest.${revision}.json`;
  const root = mkdtempSync(join(realpathSync(tmpdir()), "kix-extension-order-"));
  try {
    const fromCheckout = relative(checkout, root);
    assert.ok(fromCheckout.startsWith(`..${sep}`) || isAbsolute(fromCheckout), root);
    const emptyPath = join(root, "empty-path");
    mkdirSync(emptyPath);
    const sourceManifest = readFileSync(join(checkout, manifestPath));
    for (const path of fixtureFiles(manifestPath, revision, parseStrict(sourceManifest))) {
      const target = join(root, path);
      mkdirSync(dirname(target), { recursive: true });
      copyFileSync(join(checkout, path), target);
    }

    const manifestFile = join(root, manifestPath);
    const sidecarFile = `${manifestFile}.sha256`;
    assert.equal(sha256Hex(readFileSync(manifestFile)), sha256, context);
    assert.equal(readFileSync(sidecarFile, "utf8"), `${sha256}\n`, context);
    if (fields.length > 0) {
      applyFaults(manifestFile, fields);
    }

    const manifestSha256 = sha256Hex(readFileSync(manifestFile));
    const sidecar = readFileSync(sidecarFile, "utf8");
    assert.equal(sidecar, `${manifestSha256}\n`, context);
    const verifierFile = join(root, verifierPath);
    const verifierBytes = readFileSync(verifierFile);
    assert.equal(sha256Hex(verifierBytes), verifierSha256, context);
    assert.equal(gitBlobId(verifierBytes), verifierBlob, context);

    const before = snapshot(root);
    const result = spawnSync(process.execPath, [
      "--permission", `--allow-fs-read=${root}`, `--allow-fs-write=${root}`,
      verifierFile, "--manifest", manifestFile, "--expect-kind", kind, "--expect-revision", revision,
    ], { cwd: root, encoding: "utf8", env: { PATH: emptyPath } });
    assert.deepEqual(snapshot(root), before, `${context}: fixture inventory and bytes`);
    assert.ifError(result.error);
    assert.equal(result.signal, null, context);
    assert.equal(result.stderr, "", context);
    assert.match(result.stdout, /^[^\r\n]+\n$/u, context);
    const verdict = JSON.parse(result.stdout);
    if (errors.length === 0) {
      assert.equal(result.status, 0, `${context}: ${result.stdout}`);
      assert.deepEqual(verdict, {
        ok: true, manifest_sha256: sha256, profile_kind: kind, profile_revision: revision,
      }, context);
    } else {
      assert.equal(result.status, 1, `${context}: ${result.stdout}`);
      assert.ok(Array.isArray(verdict.errors), context);
      // Compare membership and multiplicity, then record the emitted order.
      assert.deepEqual(
        { ...verdict, errors: verdict.errors.toSorted() },
        { ok: false, errors: errors.toSorted() },
        context,
      );
    }

    console.log(JSON.stringify({
      revision, case: name, changed_fields: fields, manifest_sha256: manifestSha256,
      sidecar, exit_status: result.status,
    }));
    process.stdout.write(result.stdout);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

assert.equal(process.versions.node.split(".")[0], "24", "run with Node 24");
console.log(JSON.stringify({ verifier: verifierPath, sha256: verifierSha256, git_blob: verifierBlob }));
for (const pin of pins) {
  for (const testCase of cases) {
    runCase(pin, testCase);
  }
}
