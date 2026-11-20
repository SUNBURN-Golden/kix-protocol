import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  cpSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, rmSync, writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { createLocalCallClient } from "../src/client.ts";
import {
  ACTION_BODY_MAP,
  COMMAND_SCHEMAS,
  COMMANDS,
  ENVELOPE_REQUIRED,
  FSM_COMMAND_MACHINES,
  OPENAPI_PIN,
} from "../generated/catalogue.ts";
import {
  CatalogueRejection,
  StrictJsonError,
  canonicalStringify,
  parseStrict,
} from "../src/jsonschema.ts";
import { gitBlobId, sha256Hex } from "../src/manifest.ts";

const ROOT = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const OPENAPI_PATH = "docs/contracts/openapi/kix-protocol.contract-only.openapi.json";
const SOURCE_PATH = "reference/v0.3-rc1/protocol_contract.json";
const DOMAIN = "kix:fixture:lifecycle:0.3";

const NEGATIVE_VECTOR_PATH = "sdk/conformance/vectors/manifest-verifier-negative.vectors.json";
const VERIFIER_PATH = "sdk/compat/verify_compat.mjs";
const MANIFEST_PATH = "sdk/compat/manifests/manifest.bootstrap-2.json";
const PROFILE_PATH = "sdk/compat/profiles/bootstrap-2.profile.json";
const COMMERCE_FIXTURES = "reference/booking_resale_admission/fixtures";
const COMMERCE_REVISION = "commerce-fixture-8ba7f6c-1";
const COMMERCE_MANIFEST = `sdk/compat/manifests/manifest.${COMMERCE_REVISION}.json`;
const COMMERCE_PROFILE = `sdk/compat/profiles/${COMMERCE_REVISION}.profile.json`;
const COMMERCE_TABLE = "docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json";
const COMMERCE_VECTORS = "sdk/conformance/vectors/commerce-fixture-tuple.vectors.json";
const SEMANTIC = "SEMANTIC_CONFORMANCE";

const VERIFIER_FIXTURES = [
  VERIFIER_PATH,
  "sdk/src/jsonschema.ts",
  "sdk/src/manifest.ts",
  "sdk/package.json",
  "toolchains.json",
];

// The copied verifier derives ROOT from its own location.
const NEGATIVE_FIXTURES = [
  ...VERIFIER_FIXTURES,
  "sdk/compat/profiles/bootstrap-1.profile.json",
  PROFILE_PATH,
  MANIFEST_PATH,
  `${MANIFEST_PATH}.sha256`,
  "sdk/generate/generate_client.mjs",
  "sdk/generate/generate_manifest.mjs",
  "sdk/generated/catalogue.ts",
  "sdk/conformance/vectors/canonical-encoding.vectors.json",
  "sdk/conformance/vectors/mixed-input.vectors.json",
  "docs/contracts/openapi/kix-protocol.contract-only.openapi.json",
  "docs/contracts/openapi/kix-protocol.integration-gate.openapi.json",
  "docs/contracts/openapi/fsm-command-contract.json",
];

// Positive artifacts the manifest binds directly or indirectly. The negative
// matrix must not change any of their bytes.
const POSITIVE_ARTIFACTS = [
  MANIFEST_PATH,
  `${MANIFEST_PATH}.sha256`,
  PROFILE_PATH,
  "sdk/conformance/vectors/canonical-encoding.vectors.json",
  "sdk/conformance/vectors/mixed-input.vectors.json",
  "sdk/generated/catalogue.ts",
  VERIFIER_PATH,
];

function read(path) {
  return readFileSync(resolve(ROOT, path));
}

function rejectionCode(run) {
  try {
    run();
  } catch (error) {
    if (error instanceof CatalogueRejection) {
      return error.code;
    }
    throw error;
  }
  return undefined;
}

function minimalValue(schema, key) {
  const types = Array.isArray(schema.type) ? schema.type : [schema.type];
  if (types.includes("string")) {
    return key === "domain" ? DOMAIN : "x";
  }
  if (types.includes("integer")) {
    return schema.minimum ?? 0;
  }
  if (types.includes("boolean")) {
    return false;
  }
  if (types.includes("array")) {
    return [];
  }
  if (types.includes("object")) {
    return {};
  }
  if (types.includes("null")) {
    return null;
  }
  throw new Error(`unsupported schema for ${key}`);
}

function wrongValue(schema) {
  const types = Array.isArray(schema.type) ? schema.type : [schema.type];
  if (types.includes("string") || types.includes("null")) {
    return 1;
  }
  if (types.includes("integer") || types.includes("boolean")) {
    return "x";
  }
  if (types.includes("array")) {
    return {};
  }
  if (types.includes("object")) {
    return [];
  }
  return 1;
}

function minimalBody(schema) {
  const body = {};
  for (const key of schema.required) {
    body[key] = minimalValue(schema.properties[key], key);
  }
  return body;
}

function independentCanonical(value) {
  if (value === null) {
    return "null";
  }
  if (value === true || value === false || typeof value === "string") {
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) {
      throw new Error("non-integer");
    }
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => independentCanonical(item)).join(",")}]`;
  }
  const keys = Object.keys(value).sort((left, right) => {
    const leftPoints = Array.from(left);
    const rightPoints = Array.from(right);
    const count = Math.min(leftPoints.length, rightPoints.length);
    for (let index = 0; index < count; index += 1) {
      const delta = leftPoints[index].codePointAt(0) - rightPoints[index].codePointAt(0);
      if (delta !== 0) {
        return delta;
      }
    }
    return leftPoints.length - rightPoints.length;
  });
  return `{${keys.map((key) => `${JSON.stringify(key)}:${independentCanonical(value[key])}`).join(",")}}`;
}

function runVerifier(manifestPath, kind = "BOOTSTRAP", revision = "bootstrap-2") {
  return spawnSync(
    process.execPath,
    [
      resolve(ROOT, "sdk/compat/verify_compat.mjs"),
      "--manifest",
      manifestPath,
      "--expect-kind",
      kind,
      "--expect-revision",
      revision,
    ],
    { cwd: ROOT, encoding: "utf8" },
  );
}

test("catalogue pin matches the contract-only OpenAPI and the source contract", () => {
  const openapiBytes = read(OPENAPI_PATH);
  const sourceBytes = read(SOURCE_PATH);
  const openapi = JSON.parse(openapiBytes.toString("utf8"));
  assert.equal(COMMANDS.length, 84);
  assert.equal(OPENAPI_PIN.commandCount, 84);
  assert.equal(OPENAPI_PIN.coreCommandCount, 40);
  assert.equal(OPENAPI_PIN.fsmCommandCount, 44);
  assert.equal(openapi["x-kix-source"].commandCount, 84);
  assert.equal(openapi["x-kix-source"].coreCommandCount, 40);
  assert.equal(COMMANDS.includes("capture"), true);
  assert.equal(COMMANDS.includes("settlement_capture"), true);
  assert.equal(COMMANDS.includes("admission_authorize_admission"), true);
  assert.equal(COMMANDS.includes("admission_consume"), true);
  assert.equal(COMMANDS.includes("consume_admission"), false);
  assert.equal(COMMANDS.includes("authorize_admission"), false);
  assert.equal(Object.keys(FSM_COMMAND_MACHINES).length, 44);
  assert.equal(FSM_COMMAND_MACHINES.settlement_capture, "settlement");
  assert.equal(FSM_COMMAND_MACHINES.admission_consume, "admission");
  assert.equal(FSM_COMMAND_MACHINES.credit_draw, "credit");
  assert.equal(OPENAPI_PIN.domain, DOMAIN);
  assert.equal(OPENAPI_PIN.sha256, sha256Hex(openapiBytes));
  assert.equal(OPENAPI_PIN.gitBlob, gitBlobId(openapiBytes));
  assert.equal(OPENAPI_PIN.sourceSha256, sha256Hex(sourceBytes));
  assert.equal(OPENAPI_PIN.sourceGitBlob, gitBlobId(sourceBytes));
  assert.equal(OPENAPI_PIN.sourceSha256, "ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e");
  assert.equal(OPENAPI_PIN.sourceGitBlob, "619ae21c82ca3df5661bd3831613f15fa65225ff");
  assert.equal(OPENAPI_PIN.liveHttpServer, false);
  assert.equal(OPENAPI_PIN.productionEndpoint, false);
  assert.equal(openapi.servers, undefined);
  assert.deepEqual([...ENVELOPE_REQUIRED], ["operationId", "actor", "action", "body"]);
  const names = Object.keys(openapi.components.schemas).filter((name) => name !== "LocalCallEnvelope");
  assert.deepEqual([...COMMANDS], names);
  for (const name of names) {
    assert.equal(ACTION_BODY_MAP[name], `#/components/schemas/${name}`);
    assert.equal(COMMAND_SCHEMAS[name].additionalProperties, false);
    assert.deepEqual(COMMAND_SCHEMAS[name], openapi.components.schemas[name]);
  }
});

test("every catalogue command accepts a minimal body and rejects schema violations", () => {
  for (const name of COMMANDS) {
    const schema = COMMAND_SCHEMAS[name];
    const body = minimalBody(schema);
    let calls = 0;
    const client = createLocalCallClient({
      transport(envelope) {
        calls += 1;
        assert.deepEqual(Object.keys(envelope).sort(), ["action", "actor", "body", "operationId"]);
        assert.equal(envelope.action, name);
        assert.equal(envelope.actor, "actor-1");
        assert.equal(envelope.operationId, "op-1");
        assert.deepEqual(envelope.body, body);
        return { opaque: true, delivered: false };
      },
    });
    const result = client.invoke({ operationId: "op-1", actor: "actor-1", action: name, body });
    assert.deepEqual(result, { opaque: true, delivered: false });
    assert.equal(calls, 1, name);

    const unknown = { ...body, unexpected: 1 };
    assert.equal(
      rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: name, body: unknown })),
      "UNKNOWN_FIELD",
      name,
    );
    assert.equal(calls, 1, name);

    const missing = { ...body };
    delete missing[schema.required[0]];
    assert.equal(
      rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: name, body: missing })),
      "MISSING_REQUIRED",
      name,
    );

    const wrong = { ...body, [schema.required[0]]: wrongValue(schema.properties[schema.required[0]]) };
    assert.equal(
      rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: name, body: wrong })),
      "WRONG_TYPE",
      name,
    );

    const mismatched = { ...body, domain: "other-domain" };
    const domainCode = (schema.required ?? []).includes("domain") ? "DOMAIN_MISMATCH" : "UNKNOWN_FIELD";
    assert.equal(
      rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: name, body: mismatched })),
      domainCode,
      name,
    );
    assert.equal(calls, 1, name);
  }
});

function commerceEnvelope(step, fixture) {
  return {
    operationId: fixture.operation_id_prefix + step.id,
    actor: fixture.actor,
    action: step.action,
    body: step.body,
  };
}

test("Commerce journey envelopes reach the transport once per step", () => {
  const journey = JSON.parse(read(`${COMMERCE_FIXTURES}/commerce_journey_conformance_v1.json`));
  const fixture = JSON.parse(read(`${COMMERCE_FIXTURES}/commerce_journey_envelope_cases_v1.json`));
  const calls = [];
  const client = createLocalCallClient({
    transport(envelope) {
      calls.push(structuredClone(envelope));
    },
  });
  assert.equal(journey.steps.length, 44);
  assert.equal(new Set(journey.steps.map((step) => step.action)).size, 27);
  // Schema acceptance includes steps whose expected FSM outcome is a refusal or replay.
  for (const step of journey.steps) {
    const envelope = commerceEnvelope(step, fixture);
    const expected = structuredClone(envelope);
    const before = calls.length;
    assert.doesNotThrow(() => client.invoke(envelope), step.id);
    assert.equal(calls.length, before + 1, step.id);
    assert.deepEqual(calls[before], expected, step.id);
  }
  assert.equal(calls.length, 44);
});

test("Commerce journey envelope faults are rejected before transport", () => {
  const journey = JSON.parse(read(`${COMMERCE_FIXTURES}/commerce_journey_conformance_v1.json`));
  const fixture = JSON.parse(read(`${COMMERCE_FIXTURES}/commerce_journey_envelope_cases_v1.json`));
  const baseStep = journey.steps.find((step) => step.id === fixture.base_step);
  assert.ok(baseStep, fixture.base_step);
  const baseline = commerceEnvelope(baseStep, fixture);
  const mutations = {
    "/body/idempotency_key": "delete",
    "/body/amount": "set",
    "/body/unexpected": "set",
    "/action": "set",
  };
  assert.equal(fixture.fixture_version, 1);
  assert.deepEqual(
    fixture.cases.map(({ mutation }) => mutation.path).sort(),
    Object.keys(mutations).sort(),
  );
  let calls = 0;
  const client = createLocalCallClient({ transport() { calls += 1; } });
  for (const { id, mutation, sdk_error: expectedCode } of fixture.cases) {
    assert.equal(mutation.op, mutations[mutation.path], id);
    if (mutation.path === "/action") {
      assert.ok(journey.final_expect.read_queries.includes(mutation.value), id);
    }
    const envelope = structuredClone(baseline);
    const [, field, child] = mutation.path.split("/");
    const target = child === undefined ? envelope : envelope[field];
    const key = child ?? field;
    if (mutation.op === "delete") {
      delete target[key];
    } else {
      target[key] = mutation.value;
    }
    assert.equal(rejectionCode(() => client.invoke(envelope)), expectedCode, id);
    assert.equal(calls, 0, id);
  }
});

test("Commerce semantic manifest binds the exact fixture scope and vector bytes", () => {
  const happy = runVerifier(COMMERCE_MANIFEST, SEMANTIC, COMMERCE_REVISION);
  assert.equal(happy.status, 0, happy.stderr || happy.stdout);
  assert.deepEqual(JSON.parse(happy.stdout), {
    ok: true, profile_kind: SEMANTIC, profile_revision: COMMERCE_REVISION,
    manifest_sha256: sha256Hex(read(COMMERCE_MANIFEST)),
  });

  const table = parseStrict(read(COMMERCE_TABLE));
  const manifest = parseStrict(read(COMMERCE_MANIFEST));
  const profile = parseStrict(read(COMMERCE_PROFILE));
  const bootstrap = parseStrict(read(MANIFEST_PATH));
  assert.deepEqual(manifest.producer, table.producer);
  for (const key of ["contract", "generator", "sdk_output", "source_references"]) {
    assert.deepEqual(manifest[key], bootstrap[key], key);
  }
  assert.deepEqual(profile.catalogue, parseStrict(read(PROFILE_PATH)).catalogue);
  assert.equal(profile.grants, "commerce-fixture-tuples-only: see commerce-fixture-qualification-table");
  assert.deepEqual(
    manifest.vectors.map(({ name, path }) => [name, path]),
    [
      ["commerce-fixture-qualification-table", COMMERCE_TABLE],
      ["commerce-fixture-request-to-receipt", COMMERCE_VECTORS],
      ["commerce-fixture-prior-inputs", `${COMMERCE_FIXTURES}/commerce_journey_conformance_v1.json`],
      ["commerce-fixture-prior-receipts", `${COMMERCE_FIXTURES}/commerce_journey_receipts_v1.json`],
    ],
  );

  const schemaOnly = runVerifier(MANIFEST_PATH, SEMANTIC, COMMERCE_REVISION);
  assert.equal(schemaOnly.status, 1);
  assert.deepEqual(JSON.parse(schemaOnly.stdout).errors, ["profile_kind mismatch", "profile_revision mismatch"]);
  const directory = mkdtempSync(join(tmpdir(), "kix-commerce-compat-"));
  try {
    const control = join(directory, "manifest.json");
    const mixedProfile = { ...manifest, profile_sha256: bootstrap.profile_sha256 };
    const mixedVectors = structuredClone(manifest);
    mixedVectors.vectors[1].sha256 = bootstrap.vectors[0].sha256;
    for (const [mutant, error] of [
      [mixedProfile, "profile bytes drift"],
      [mixedVectors, "vector bytes drift: commerce-fixture-request-to-receipt"],
    ]) {
      const encoded = canonicalStringify(mutant);
      writeFileSync(control, encoded);
      writeFileSync(`${control}.sha256`, `${sha256Hex(encoded)}\n`);
      const outcome = runVerifier(control, SEMANTIC, COMMERCE_REVISION);
      assert.equal(outcome.status, 1, outcome.stderr || outcome.stdout);
      assert.ok(JSON.parse(outcome.stdout).errors.includes(error), outcome.stdout);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("Commerce semantic envelopes preserve the request and stop schema refusals locally", () => {
  const { vectors } = parseStrict(read(COMMERCE_VECTORS));
  const calls = [];
  const client = createLocalCallClient({
    transport: (envelope) => calls.push(canonicalStringify(envelope)),
  });
  for (const { id, envelope, expected } of vectors) {
    const original = canonicalStringify(envelope);
    const before = calls.length;
    assert.notEqual(envelope.operationId, envelope.body.idempotency_key, id);
    if (expected.kind === "schema-reject") {
      assert.equal(rejectionCode(() => client.invoke(envelope)), expected.sdk_code, id);
      assert.equal(calls.length, before, id);
    } else {
      client.invoke(envelope);
      assert.equal(calls.length, before + 1, id);
      assert.equal(calls[before], original, id);
    }
  }
  assert.equal(calls.length, vectors.filter(({ expected }) => expected.kind !== "schema-reject").length);
});

test("envelope, identifier, and transport rules stay local to one call", async () => {
  let calls = 0;
  const client = createLocalCallClient({
    transport(envelope) {
      calls += 1;
      return envelope.actor;
    },
  });
  const body = minimalBody(COMMAND_SCHEMAS.create_event);
  assert.equal(client.invoke({ operationId: "op-1", actor: "not-a-credential", action: "create_event", body }), "not-a-credential");
  assert.equal(
    rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: "create_event", body, extra: true })),
    "ENVELOPE_EXTRA",
  );
  assert.equal(rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: "missing", body })), "UNKNOWN_ACTION");
  assert.equal(rejectionCode(() => client.invoke({ actor: "actor-1", action: "create_event", body })), "ENVELOPE");
  assert.equal(rejectionCode(() => client.invoke([])), "ENVELOPE");
  for (const bad of ["", " ", " x", "x ", "x".repeat(101), "가".repeat(101)]) {
    assert.equal(rejectionCode(() => client.invoke({ operationId: bad, actor: "actor-1", action: "create_event", body })), "INVALID_ID");
    assert.equal(rejectionCode(() => client.invoke({ operationId: "op-1", actor: bad, action: "create_event", body })), "INVALID_ID");
  }
  assert.equal(client.invoke({ operationId: "가".repeat(100), actor: "a b", action: "create_event", body }), "a b");
  const nullable = minimalBody(COMMAND_SCHEMAS.observe_recovery);
  nullable.allocationId = null;
  assert.equal(client.invoke({ operationId: "op-1", actor: "actor-1", action: "observe_recovery", body: nullable }), "actor-1");
  const bounded = minimalBody(COMMAND_SCHEMAS.create_event);
  bounded.invitationQuota = 1000000000001;
  assert.equal(
    rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: "create_event", body: bounded })),
    "CONSTRAINT",
  );
  bounded.invitationQuota = 1.5;
  assert.equal(
    rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: "create_event", body: bounded })),
    "WRONG_TYPE",
  );
  const empty = minimalBody(COMMAND_SCHEMAS.create_event);
  empty.eventId = "";
  assert.equal(
    rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: "create_event", body: empty })),
    "CONSTRAINT",
  );
  assert.equal(rejectionCode(() => createLocalCallClient({ transport() {}, baseUrl: "http://127.0.0.1" })), "UNKNOWN_FIELD");
  const beforeRepeat = calls;
  const throwing = createLocalCallClient({
    transport() {
      calls += 1;
      throw new Error("boom");
    },
  });
  assert.throws(() => throwing.invoke({ operationId: "op-1", actor: "actor-1", action: "create_event", body }), /boom/);
  assert.equal(calls, beforeRepeat + 1);
  const pending = createLocalCallClient({
    transport() {
      calls += 1;
      return Promise.reject(new Error("later"));
    },
  });
  const promise = pending.invoke({ operationId: "op-1", actor: "actor-1", action: "create_event", body });
  assert.equal(promise instanceof Promise, true);
  await assert.rejects(promise, /later/);
  assert.equal(calls, beforeRepeat + 2);
});

test("canonical encoding vectors", () => {
  const path = resolve(ROOT, "sdk/conformance/vectors/canonical-encoding.vectors.json");
  const bytes = readFileSync(path);
  const document = parseStrict(bytes);
  assert.equal(document.encoding_profile, "kix-canonical-json/1");
  assert.equal(canonicalStringify(document), new TextDecoder().decode(bytes));
  for (const item of document.cases) {
    if (item.expect === "accept") {
      const value = parseStrict(item.input);
      assert.equal(canonicalStringify(value), item.canonical, item.name);
      assert.equal(independentCanonical(value), item.canonical, item.name);
      assert.equal(item.input, item.canonical, item.name);
    } else {
      const input = item.input_hex === undefined ? item.input : Buffer.from(item.input_hex, "hex");
      assert.throws(
        () => parseStrict(input),
        (error) => error instanceof StrictJsonError && error.reason === item.reason,
        item.name,
      );
    }
  }
});

test("manifest verifier reports failures in contract order", () => {
  const manifest = parseStrict(read("sdk/compat/manifests/manifest.bootstrap-2.json"));
  const badDigest = "0".repeat(64);
  manifest.unexpected = true;
  manifest.profile_kind = "UNKNOWN";
  manifest.profile_sha256 = badDigest;
  manifest.contract.contract_only.sha256 = badDigest;
  manifest.contract.integration_gate.sha256 = badDigest;
  manifest.generator.toolchain = "node-0";
  manifest.generator.sha256 = badDigest;
  manifest.sdk_output.sha256 = badDigest;
  manifest.vectors[0].sha256 = badDigest;

  const directory = mkdtempSync(join(tmpdir(), "kix-sdk-order-"));
  try {
    const target = join(directory, "manifest.json");
    const canonical = canonicalStringify(manifest);
    writeFileSync(`${target}.sha256`, `${"1".repeat(64)}\n`);
    writeFileSync(target, `${canonical}\n`);
    const parseFailure = runVerifier(target);
    assert.equal(parseFailure.status, 1, parseFailure.stderr || parseFailure.stdout);
    assert.deepEqual(JSON.parse(parseFailure.stdout), { ok: false, errors: ["manifest trailing-bytes"] });

    writeFileSync(target, canonical);
    const result = runVerifier(target);
    assert.equal(result.status, 1, result.stderr || result.stdout);
    const verdict = JSON.parse(result.stdout);
    assert.equal(verdict.ok, false);
    const expected = [
      "manifest field set drift",
      "unknown profile_kind",
      "profile bytes drift",
      "contract_only bytes drift",
      "integration_gate bytes drift",
      "toolchain drift",
      "generator bytes drift",
      "sdk_output bytes drift",
      `vector bytes drift: ${manifest.vectors[0].name}`,
      "manifest sidecar digest drift",
    ];
    // Cross-checks can add diagnostics. Assert the ordered stages named in §4.
    assert.deepEqual(verdict.errors.filter((error) => expected.includes(error)), expected);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("mixed-input vectors and the committed manifest", () => {
  const manifestPath = resolve(ROOT, "sdk/compat/manifests/manifest.bootstrap-2.json");
  const happy = runVerifier(manifestPath);
  assert.equal(happy.status, 0, happy.stderr || happy.stdout);
  const verdict = JSON.parse(happy.stdout);
  assert.equal(verdict.ok, true);
  assert.equal(verdict.profile_kind, "BOOTSTRAP");
  assert.equal(verdict.profile_revision, "bootstrap-2");
  const sidecar = readFileSync(`${manifestPath}.sha256`, "utf8");
  assert.equal(sidecar, `${verdict.manifest_sha256}\n`);
  assert.equal(readFileSync(manifestPath, "utf8").includes(verdict.manifest_sha256), false);

  const original = parseStrict(readFileSync(manifestPath));
  const mixed = parseStrict(read(resolve(ROOT, "sdk/conformance/vectors/mixed-input.vectors.json")));
  assert.equal(mixed.profile, "kix-compat-mixed-input/1");
  const directory = mkdtempSync(join(tmpdir(), "kix-sdk-"));
  try {
    for (const item of mixed.cases) {
      const target = join(directory, `${item.name}.json`);
      if (item.op === "truncate") {
        writeFileSync(target, readFileSync(manifestPath).subarray(0, -1));
      } else if (item.op === "duplicate-key") {
        const text = readFileSync(manifestPath, "utf8");
        const open = text.indexOf("{");
        if (open !== 0) {
          throw new Error("committed manifest does not start with an object");
        }
        writeFileSync(target, `{"contract":{},${text.slice(1)}`);
      } else {
        const copy = parseStrict(canonicalStringify(original));
        const parts = item.path.split(".");
        let cursor = copy;
        for (const part of parts.slice(0, -1)) {
          cursor = cursor[part];
        }
        const leaf = parts[parts.length - 1];
        const value = item.name === "wrong-revision" ? "bootstrap-9" : item.value;
        cursor[leaf] = item.op === "copy" ? getPath(copy, item.from) : value;
        const encoded = canonicalStringify(copy);
        writeFileSync(target, encoded);
        writeFileSync(`${target}.sha256`, `${sha256Hex(encoded)}\n`);
      }
      const result = runVerifier(target);
      assert.notEqual(result.status, 0, item.name);
      const body = JSON.parse(result.stdout);
      assert.equal(body.ok, false, item.name);
      assert.ok(body.errors.length > 0, item.name);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

function getPath(root, path) {
  if (path === "") {
    return root;
  }
  return path.split(".").reduce(
    (cursor, part) => cursor[Array.isArray(cursor) ? Number(part) : part],
    root,
  );
}

function setPath(root, path, value) {
  const parts = path.split(".");
  const leaf = parts.pop();
  const parent = parts.length === 0 ? root : getPath(root, parts.join("."));
  if (Array.isArray(parent)) {
    parent[Number(leaf)] = value;
  } else {
    parent[leaf] = value;
  }
}

// One structured mutation per case. Callers re-encode and write the mutated
// document; no case composes two mutations.
function mutateDocument(document, item) {
  if (item.op === "set") {
    setPath(document, item.path, item.value);
  } else if (item.op === "add") {
    getPath(document, item.path)[item.key] = item.value;
  } else if (item.op === "delete") {
    delete getPath(document, item.path)[item.key];
  } else {
    throw new Error(`unsupported structured mutation ${item.op}`);
  }
}

function copyFixtures(targetRoot, files = NEGATIVE_FIXTURES) {
  for (const path of files) {
    const target = resolve(targetRoot, path);
    mkdirSync(dirname(target), { recursive: true });
    cpSync(resolve(ROOT, path), target);
  }
}

function writeManifest(targetRoot, manifestBytes) {
  writeFileSync(resolve(targetRoot, MANIFEST_PATH), manifestBytes);
  writeFileSync(resolve(targetRoot, `${MANIFEST_PATH}.sha256`), `${sha256Hex(manifestBytes)}\n`);
}

function applyManifestCase(targetRoot, pristineManifest, item) {
  let bytes;
  if (item.op === "truncate") {
    bytes = pristineManifest.subarray(0, -1);
  } else if (item.op === "duplicate-key") {
    const text = pristineManifest.toString("utf8");
    bytes = Buffer.from(`{"contract":{},${text.slice(1)}`, "utf8");
  } else if (item.op === "text-replace") {
    const text = pristineManifest.toString("utf8");
    if (!text.includes(item.from)) {
      throw new Error(`${item.name}: text to replace is absent`);
    }
    bytes = Buffer.from(text.replace(item.from, item.to), "utf8");
  } else {
    const manifest = parseStrict(pristineManifest);
    mutateDocument(manifest, item);
    bytes = Buffer.from(canonicalStringify(manifest), "utf8");
  }
  writeManifest(targetRoot, bytes);
}

// A profile fault is the only intended fault: the manifest is re-sealed to the
// mutated profile bytes so the profile digest check does not add a second one.
function applyProfileCase(targetRoot, pristineManifest, pristineProfile, item) {
  const profile = parseStrict(pristineProfile);
  mutateDocument(profile, item);
  const profileBytes = Buffer.from(canonicalStringify(profile), "utf8");
  writeFileSync(resolve(targetRoot, PROFILE_PATH), profileBytes);
  const manifest = parseStrict(pristineManifest);
  manifest.profile_sha256 = sha256Hex(profileBytes);
  writeManifest(targetRoot, Buffer.from(canonicalStringify(manifest), "utf8"));
}

function applySidecarCase(targetRoot, pristineManifest, item) {
  writeManifest(targetRoot, pristineManifest);
  const sidecarPath = resolve(targetRoot, `${MANIFEST_PATH}.sha256`);
  if (item.absent === true) {
    rmSync(sidecarPath, { force: true });
  } else if (item.from !== undefined) {
    const manifest = parseStrict(pristineManifest);
    writeFileSync(sidecarPath, `${getPath(manifest, item.from)}\n`);
  } else {
    writeFileSync(sidecarPath, item.text);
  }
}

function runVerifierAt(root, manifestPath, kind, revision, { nodeArgs = [], env } = {}) {
  return spawnSync(
    process.execPath,
    [
      ...nodeArgs,
      resolve(root, VERIFIER_PATH),
      "--manifest",
      manifestPath,
      "--expect-kind",
      kind,
      "--expect-revision",
      revision,
    ],
    { cwd: root, encoding: "utf8", env },
  );
}

function snapshotFixtureTree(root) {
  const entries = readdirSync(root, { recursive: true, withFileTypes: true });
  return new Map(entries.map((entry) => {
    const path = join(entry.parentPath, entry.name);
    assert.ok(entry.isDirectory() || entry.isFile(), `unexpected entry type: ${path}`);
    return [relative(root, path), entry.isDirectory() ? null : readFileSync(path)];
  }));
}

test("vendored producer manifests return one verdict without changing files", () => {
  for (const { revision, kind, digest, manifestPath, profilePath, missing } of [
    {
      revision: "bootstrap-2",
      kind: "BOOTSTRAP",
      digest: "eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0",
      manifestPath: MANIFEST_PATH,
      profilePath: PROFILE_PATH,
      missing: "mixed-input",
    },
    {
      revision: COMMERCE_REVISION,
      kind: SEMANTIC,
      digest: "76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f",
      manifestPath: COMMERCE_MANIFEST,
      profilePath: COMMERCE_PROFILE,
      missing: "commerce-fixture-request-to-receipt",
    },
  ]) {
    const manifestBytes = read(manifestPath);
    const sidecarPath = `${manifestPath}.sha256`;
    assert.equal(sha256Hex(manifestBytes), digest, revision);
    assert.equal(read(sidecarPath).toString("utf8"), `${digest}\n`, revision);
    const manifest = parseStrict(manifestBytes);
    const files = new Set([
      ...VERIFIER_FIXTURES,
      manifestPath,
      sidecarPath,
      profilePath,
      manifest.contract.contract_only.path,
      manifest.contract.integration_gate.path,
      manifest.generator.path,
      manifest.sdk_output.path,
      manifest.source_references.fixture_profile,
      manifest.source_references.extension_profile.path,
      ...manifest.vectors.map((vector) => vector.path),
    ]);
    const missingVector = manifest.vectors.find((vector) => vector.name === missing);
    assert.ok(missingVector, `${revision}: missing test vector binding`);

    const root = mkdtempSync(join(realpathSync(tmpdir()), "kix-sdk-vendored-"));
    try {
      const fromCheckout = relative(ROOT, root);
      assert.ok(fromCheckout.startsWith(`..${sep}`) || isAbsolute(fromCheckout), root);
      copyFixtures(root, files);
      const emptyPath = "empty-path";
      mkdirSync(join(root, emptyPath));

      const expected = new Map([[emptyPath, null]]);
      for (const path of files) {
        const copiedPath = relative(root, resolve(root, path));
        expected.set(copiedPath, read(path));
        for (let directory = dirname(copiedPath); directory !== "."; directory = dirname(directory)) {
          expected.set(directory, null);
        }
      }

      function verdict(exitStatus) {
        const context = `${revision}, expected exit ${exitStatus}`;
        const before = snapshotFixtureTree(root);
        assert.deepEqual(before, expected, `${context}: input inventory and bytes`);
        const result = runVerifierAt(root, resolve(root, manifestPath), kind, revision, {
          // No child-process permission, including execution by absolute path.
          nodeArgs: ["--permission", `--allow-fs-read=${root}`, `--allow-fs-write=${root}`],
          env: { PATH: join(root, emptyPath) },
        });
        assert.deepEqual(snapshotFixtureTree(root), before, `${context}: output inventory and bytes`);
        assert.ifError(result.error);
        assert.equal(result.signal, null, context);
        assert.equal(result.status, exitStatus, `${context}: ${result.stderr || result.stdout}`);
        assert.equal(result.stderr, "", context);
        const lines = result.stdout.split("\n");
        assert.equal(lines.length, 2, context);
        assert.equal(lines[1], "", context);
        assert.match(lines[0], /^[^\r\n]+$/u, context);
        return JSON.parse(lines[0]);
      }

      assert.deepEqual(verdict(0), {
        ok: true,
        manifest_sha256: digest,
        profile_kind: kind,
        profile_revision: revision,
      });

      const missingPath = resolve(root, missingVector.path);
      rmSync(missingPath);
      expected.delete(relative(root, missingPath));
      assert.deepEqual(verdict(1), { ok: false, errors: [`${missing} unreadable: ${missingPath}`] });
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  }
});

function digestSnapshot() {
  return Object.fromEntries(
    POSITIVE_ARTIFACTS.map((relative) => [relative, sha256Hex(readFileSync(resolve(ROOT, relative)))]),
  );
}

// Replacement paths depend on the temporary directory; normalising them keeps
// the expected error set stable. Sorting discards the verifier's check order on
// purpose: the matrix asserts which faults are reported, never which one wins.
function normalizedErrors(errors, targetRoot) {
  return errors.map((error) => error.split(targetRoot).join("<root>")).sort();
}

test("manifest-v1 verifier negative vectors reject exactly one fault each", () => {
  const vectorBytes = readFileSync(resolve(ROOT, NEGATIVE_VECTOR_PATH));
  const document = parseStrict(vectorBytes);
  assert.equal(document.profile, "kix-compat-manifest-negative/1");
  assert.equal(document.verifier, VERIFIER_PATH);
  assert.equal(canonicalStringify(document), vectorBytes.toString("utf8"));
  assert.equal(canonicalStringify(document.expect), '{"kind":"BOOTSTRAP","revision":"bootstrap-2"}');
  assert.equal(document.cases.length > 0, true);
  assert.equal(new Set(document.cases.map((item) => item.name)).size, document.cases.length);

  const before = digestSnapshot();

  const happy = runVerifierAt(ROOT, resolve(ROOT, MANIFEST_PATH), document.expect.kind, document.expect.revision);
  assert.equal(happy.status, 0, happy.stderr || happy.stdout);
  const verdict = JSON.parse(happy.stdout);
  assert.equal(verdict.ok, true);
  assert.equal(verdict.profile_kind, "BOOTSTRAP");
  assert.equal(verdict.profile_revision, "bootstrap-2");

  const pristineManifest = readFileSync(resolve(ROOT, MANIFEST_PATH));
  const pristineProfile = readFileSync(resolve(ROOT, PROFILE_PATH));
  const targetRoot = mkdtempSync(join(tmpdir(), "kix-sdk-negative-"));
  try {
    copyFixtures(targetRoot);
    for (const item of document.cases) {
      writeManifest(targetRoot, pristineManifest);
      writeFileSync(resolve(targetRoot, PROFILE_PATH), pristineProfile);
      if (item.surface === "manifest") {
        applyManifestCase(targetRoot, pristineManifest, item);
      } else if (item.surface === "profile") {
        applyProfileCase(targetRoot, pristineManifest, pristineProfile, item);
      } else if (item.surface === "sidecar") {
        applySidecarCase(targetRoot, pristineManifest, item);
      } else {
        throw new Error(`${item.name}: unsupported surface ${item.surface}`);
      }
      const result = runVerifierAt(
        targetRoot,
        resolve(targetRoot, MANIFEST_PATH),
        document.expect.kind,
        document.expect.revision,
      );
      assert.notEqual(result.status, 0, item.name);
      const body = JSON.parse(result.stdout);
      assert.equal(body.ok, false, item.name);
      assert.deepEqual(
        normalizedErrors(body.errors, targetRoot),
        [...item.expect_errors].sort(),
        item.name,
      );
    }
  } finally {
    rmSync(targetRoot, { recursive: true, force: true });
  }

  assert.deepEqual(digestSnapshot(), before);
});

test("client surface does not carry a URL, credential, or repeat-call API", () => {
  const clientSource = readFileSync(resolve(ROOT, "sdk/src/client.ts"), "utf8");
  const catalogue = readFileSync(resolve(ROOT, "sdk/generated/catalogue.ts"), "utf8");
  const packageJson = JSON.parse(readFileSync(resolve(ROOT, "sdk/package.json"), "utf8"));
  for (const token of ["http://", "https://", "fetch(", "baseUrl", "baseURL", "Authorization", "retry", "authenticate"]) {
    assert.equal(clientSource.includes(token), false, token);
  }
  assert.equal(catalogue.includes("http://"), false);
  assert.equal(catalogue.includes("https://"), false);
  assert.equal(Object.hasOwn(packageJson, "dependencies"), false);
  assert.equal(Object.hasOwn(packageJson, "devDependencies"), false);
  assert.equal(packageJson.private, true);
  assert.equal(packageJson.engines.node, ">=24 <25");
  const pin = JSON.parse(readFileSync(resolve(ROOT, "sdk/sdk-pin.json"), "utf8"));
  assert.equal(pin.openapi.sha256, OPENAPI_PIN.sha256);
  assert.equal(pin.source.sha256, OPENAPI_PIN.sourceSha256);
  assert.equal(createHash("sha256").update(read(OPENAPI_PATH)).digest("hex"), pin.openapi.sha256);
});
