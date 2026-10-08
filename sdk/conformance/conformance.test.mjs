import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { createLocalCallClient } from "../src/client.ts";
import {
  ACTION_BODY_MAP,
  COMMAND_SCHEMAS,
  COMMANDS,
  ENVELOPE_REQUIRED,
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

function runVerifier(manifestPath) {
  return spawnSync(
    process.execPath,
    [
      resolve(ROOT, "sdk/compat/verify_compat.mjs"),
      "--manifest",
      manifestPath,
      "--expect-kind",
      "BOOTSTRAP",
      "--expect-revision",
      "bootstrap-1",
    ],
    { cwd: ROOT, encoding: "utf8" },
  );
}

test("catalogue pin matches the contract-only OpenAPI and the source contract", () => {
  const openapiBytes = read(OPENAPI_PATH);
  const sourceBytes = read(SOURCE_PATH);
  const openapi = JSON.parse(openapiBytes.toString("utf8"));
  assert.equal(COMMANDS.length, 40);
  assert.equal(OPENAPI_PIN.commandCount, 40);
  assert.equal(openapi["x-kix-source"].commandCount, 40);
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
    assert.equal(
      rejectionCode(() => client.invoke({ operationId: "op-1", actor: "actor-1", action: name, body: mismatched })),
      "DOMAIN_MISMATCH",
      name,
    );
    assert.equal(calls, 1, name);
  }
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

test("mixed-input vectors and the committed manifest", () => {
  const manifestPath = resolve(ROOT, "sdk/compat/manifests/manifest.bootstrap-1.json");
  const happy = runVerifier(manifestPath);
  assert.equal(happy.status, 0, happy.stderr || happy.stdout);
  const verdict = JSON.parse(happy.stdout);
  assert.equal(verdict.ok, true);
  assert.equal(verdict.profile_kind, "BOOTSTRAP");
  assert.equal(verdict.profile_revision, "bootstrap-1");
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
        cursor[leaf] = item.op === "copy" ? getPath(copy, item.from) : item.value;
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
  return path.split(".").reduce((cursor, part) => cursor[part], root);
}

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
