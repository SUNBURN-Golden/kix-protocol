/** Prepare the read profile, then bind the tuple to a committed producer source. */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { parseStrict } from "../src/jsonschema.ts";
import { canonicalBytes, gitBlobId, sha256Hex } from "../src/manifest.ts";

const ROOT = fileURLToPath(new URL("../..", import.meta.url));
const BOOTSTRAP = "sdk/compat/manifests/manifest.read-model-reference-1.json";
const HISTORICAL_PROFILE = "sdk/compat/profiles/read-model-reference-1.profile.json";
const REVISION = "commerce-resale-read-transport-1";
const PROFILE_PATH = `sdk/compat/profiles/${REVISION}.profile.json`;
const VECTORS = {
  "resale-read-transport": "reference/read_model/vectors/resale-read-transport.json",
  "qualified-market-setup": "sdk/conformance/vectors/commerce-fixture-tuple.vectors.json",
  "pagination-setup": "reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json",
};

function git(...args) {
  return execFileSync("git", args, { cwd: ROOT, maxBuffer: 8 * 1024 * 1024 });
}

function workingBytes(path) {
  return readFileSync(resolve(ROOT, path));
}

function makeProfile(readBytes) {
  const historical = parseStrict(readBytes(HISTORICAL_PROFILE));
  const vectors = Object.entries(VECTORS).map(([name, path]) => ({
    name, path, sha256: sha256Hex(readBytes(path)),
  }));
  return {
    ...historical,
    grants: "local fixture resale reads only",
    non_claims: ["no write qualification", "no N/N-1 qualification", "no production qualification", "not audit or approval evidence"],
    profile_kind: "SEMANTIC_CONFORMANCE",
    profile_revision: REVISION,
    vectors,
  };
}

function writeOutputs(outputs) {
  for (const [output, bytes] of outputs) {
    const target = resolve(ROOT, output);
    if (existsSync(target) && !readFileSync(target).equals(bytes)) {
      throw new Error(`immutable revision already exists with different bytes: ${output}`);
    }
  }
  for (const [output, bytes] of outputs) {
    const target = resolve(ROOT, output);
    if (!existsSync(target)) writeFileSync(target, bytes, { flag: "wx" });
  }
}

function main() {
  const [flag, source, ...extra] = process.argv.slice(2);
  if (flag === "--profile-only" && source === undefined) {
    const bytes = canonicalBytes(makeProfile(workingBytes));
    writeOutputs([[PROFILE_PATH, bytes]]);
    console.log(`${PROFILE_PATH} ${sha256Hex(bytes)}`);
    return;
  }
  if (flag !== "--source" || !/^[0-9a-f]{40}$/.test(source ?? "") || extra.length) {
    throw new Error("use --profile-only or --source with the full producer commit SHA");
  }
  const commit = git("rev-parse", "--verify", `${source}^{commit}`).toString().trim();
  if (commit !== source) throw new Error("producer source must be a commit");
  const sourceTree = git("rev-parse", `${commit}^{tree}`).toString().trim();
  function sourceBytes(path) {
    const committed = git("show", `${commit}:${path}`);
    if (!committed.equals(workingBytes(path))) {
      throw new Error(`working bytes differ from source commit: ${path}`);
    }
    return committed;
  }
  const bootstrap = parseStrict(sourceBytes(BOOTSTRAP));
  const generator = bootstrap.generator;
  const sdkOutput = bootstrap.sdk_output;
  const extension = bootstrap.source_references.extension_profile;
  for (const ref of [bootstrap.contract.contract_only, generator, sdkOutput, extension]) {
    if (sha256Hex(sourceBytes(ref.path)) !== ref.sha256) {
      throw new Error(`the unchanged write SDK tuple drifted: ${ref.path}`);
    }
  }
  const nodeMajor = JSON.parse(sourceBytes("toolchains.json")).nodeMajor;
  if (generator.toolchain !== `node-${nodeMajor}` || process.versions.node.split(".")[0] !== String(nodeMajor)) {
    throw new Error(`run with Node ${nodeMajor}`);
  }
  for (const path of [
    "integration_gate/constants.py", "integration_gate/fsm_host.py", "integration_gate/openapi_doc.py",
    "integration_gate/read_schema.py", "integration_gate/resale_reads.py", "integration_gate/server.py",
    "integration_gate/test_http_gate.py", "integration_gate/test_offline_limits.py",
    "reference/booking_resale_admission/resale_fsm.py", "reference/settlement_f01_f03/settlement_fsm.py",
  ]) sourceBytes(path);

  const path = bootstrap.contract.integration_gate.path;
  const gate = sourceBytes(path);
  const profile = makeProfile(sourceBytes);
  const profileBytes = canonicalBytes(profile);
  const manifest = canonicalBytes({
    ...bootstrap,
    contract: {
      contract_only: bootstrap.contract.contract_only,
      integration_gate: { path, gitBlob: gitBlobId(gate), sha256: sha256Hex(gate) },
    },
    producer: { ...bootstrap.producer, source_commit: commit, source_tree: sourceTree },
    profile_kind: profile.profile_kind,
    profile_revision: REVISION,
    profile_sha256: sha256Hex(profileBytes),
    vectors: profile.vectors,
  });
  const digest = sha256Hex(manifest);
  const manifestPath = `sdk/compat/manifests/manifest.${REVISION}.json`;
  writeOutputs([
    [PROFILE_PATH, profileBytes],
    [manifestPath, manifest],
    [`${manifestPath}.sha256`, Buffer.from(`${digest}\n`)],
  ]);
  console.log(`${manifestPath} ${digest}`);
}

try {
  main();
} catch (error) {
  console.error(`generate_resale_read_manifest: ${error.message}`);
  process.exitCode = 1;
}
