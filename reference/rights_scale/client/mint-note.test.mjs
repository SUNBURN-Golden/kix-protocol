// Source-informed offline mint wrapper tests within EV-RS. Published synthetic
// scalars and fabricated encoder coordinates; no valid proofs, keys or RPC.
import {test, mock, after} from 'node:test';
import assert from 'node:assert/strict';
import * as crypto from 'node:crypto';
import * as fs from 'node:fs/promises';
import {resolve, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildPoseidon} from 'circomlibjs';
import * as helpers from './zk-helpers.mjs';

// Expectations are assembled before invoking the wrapper, without its helpers,
// captured prover inputs, returned notes or MINT_PUBLIC. Poseidon is shared.
const p = await buildPoseidon();
const commitment = String(p.F.toObject(p([17n, 700n, 4n, 77n, 1n])));
function inverseEuclid(value, modulus) {
  let [r, nextR, coefficient, nextCoefficient] = [modulus, value, 0n, 1n];
  while (nextR !== 0n) {
    const quotient = r / nextR;
    [r, nextR] = [nextR, r - quotient * nextR];
    [coefficient, nextCoefficient] = [nextCoefficient, coefficient - quotient * nextCoefficient];
  }
  assert.equal(r, 1n);
  return ((coefficient % modulus) + modulus) % modulus;
}
const expectedInput = {
  commitment, slot: '700', generation: '4', domain: '77', secret: '17',
  inverse: String(inverseEuclid(17n, helpers.FR)),
};
const expectedSignals = [commitment, '700', '4', '77'];
assert.equal(new Set(expectedSignals).size, 4, 'order mutation requires distinct signals');
const artifactRoot = resolve(fileURLToPath(new URL('../zk/artifacts', import.meta.url)));
const keys = {
  mint_scale: {tag: 'synthetic mint key sentinel'},
  spend_scale: {tag: 'synthetic spend key sentinel'},
};
const keyBytes = {
  mint_scale: Buffer.from('synthetic mint encoding sentinel'),
  spend_scale: Buffer.from('synthetic spend encoding sentinel'),
};
const files = new Map([
  ['mint_scale_js/mint_scale.wasm', Buffer.from('synthetic wasm sentinel')],
  ['mint_scale.zkey', Buffer.from('synthetic zkey sentinel; not a key')],
]);
const manifest = {tag: 'synthetic manifest sentinel',
  files: Object.fromEntries([...files].map(([name, bytes]) => [name, helpers.sha256(bytes)]))};
for (const name of ['mint_scale', 'spend_scale']) files.set(name + '.vk.bin', keyBytes[name]);
files.set('manifest.json', Buffer.from(JSON.stringify(manifest)));

function syntheticProof() {
  // Same fabricated public coordinates as zk-helpers.test.mjs, no curve claim.
  return {
    pi_a: ['513', '2', '1'],
    pi_b: [['1027', '1541'], ['3', '4'], ['1', '0']],
    pi_c: ['2055', '5', '1'],
  };
}
// Literal padded little-endian words; do not derive via proofBytes.
const expectedProof = Array.from(Buffer.from(
  '0102' + '00'.repeat(30) + '0304' + '00'.repeat(30) +
  '0506' + '00'.repeat(30) + '0708' + '00'.repeat(30), 'hex'));

let state;
function keyName(key) {
  const name = Object.keys(keys).find(name => keys[name] === key);
  assert.ok(name, 'unexpected key sentinel');
  return name;
}
async function readJSON(path) {
  const name = Object.keys(keys).find(name => path === join(artifactRoot, name + '.vkey.json'));
  assert.ok(name, 'unexpected JSON read: ' + path);
  state.events.push('readJSON:' + name);
  return keys[name];
}

// Dependency mocks precede the dynamic import of the unchanged wrapper.
// Keep real FR, sha256 and proofBytes, and all other crypto exports.
const {default: cryptoDefault, ...cryptoNamed} = crypto;
const mockedRandomBytes = size => {
  assert.equal(size, 32);
  assert.equal(++state.draws, 1, 'unexpected extra randomness draw');
  state.events.push('randomBytes');
  return Buffer.from('00'.repeat(31) + '11', 'hex');
};
// Copy the default export too: Node's CJS mock bridge defines named properties
// on it, and the real crypto object has non-configurable constants.
mock.module('node:crypto', {defaultExport: {...cryptoDefault, randomBytes: mockedRandomBytes},
  namedExports: {...cryptoNamed, randomBytes: mockedRandomBytes}});
const {default: fsDefault, ...fsNamed} = fs;
const mockedReadFile = async path => {
  const entry = [...files].find(([name]) => path === join(artifactRoot, name));
  assert.ok(entry, 'unexpected artifact read: ' + path);
  state.events.push('readFile:' + entry[0]);
  return Buffer.from(entry[1]);
};
mock.module('node:fs/promises', {defaultExport: {...fsDefault, readFile: mockedReadFile},
  namedExports: {...fsNamed, readFile: mockedReadFile}});
mock.module('./zk-helpers.mjs', {namedExports: {...helpers, readJSON,
  vkBytes: key => {
    const name = keyName(key);
    state.events.push('vkBytes:' + name);
    return Buffer.from(keyBytes[name]);
  },
  proofBytes: proof => {
    state.events.push('encode');
    assert.equal(proof, state.proof);
    return helpers.proofBytes(proof);
  },
}});
mock.module('./zk-policy-v2.mjs', {namedExports: {
  requirePhase2ManifestV2: value => {
    state.events.push('manifestPolicy');
    assert.deepEqual(value, manifest);
  },
  requirePhase2Key: (key, count) => {
    const name = keyName(key);
    state.events.push('keyPolicy:' + name);
    assert.equal(count, name === 'mint_scale' ? 4 : 6);
  },
}});
mock.module('snarkjs', {namedExports: {groth16: {
  fullProve: async (input, wasmPath, zkeyPath) => {
    state.events.push('prove');
    state.input = structuredClone(input);
    state.wasmPath = wasmPath;
    state.zkeyPath = zkeyPath;
    if (state.error) throw state.error;
    return {proof: state.proof, publicSignals: state.signals};
  },
  verify: async (key, signals, proof) => {
    state.events.push('verify');
    assert.equal(key, keys.mint_scale);
    assert.equal(signals, state.signals);
    assert.equal(proof, state.proof);
    return state.verifies;
  },
}}});
after(() => mock.restoreAll());
const {mintNote} = await import('./private-scale.mjs');

const artifactEvents = [
  'readFile:manifest.json', 'manifestPolicy',
  'readFile:mint_scale_js/mint_scale.wasm', 'readFile:mint_scale.zkey',
  'readJSON:mint_scale', 'keyPolicy:mint_scale', 'vkBytes:mint_scale', 'readFile:mint_scale.vk.bin',
  'readJSON:spend_scale', 'keyPolicy:spend_scale', 'vkBytes:spend_scale', 'readFile:spend_scale.vk.bin',
  'readFile:mint_scale.vk.bin', 'readFile:spend_scale.vk.bin',
];
const beforeVerification = ['randomBytes', ...artifactEvents, 'prove'];
const throughVerification = [...beforeVerification, 'readJSON:mint_scale', 'verify'];
function reset(overrides = {}) {
  state = {events: [], draws: 0, proof: syntheticProof(), signals: [...expectedSignals], verifies: true, ...overrides};
}
async function invoke() {
  const ticket = {slot: '700', generation: '4'}, before = structuredClone(ticket);
  try {
    return await mintNote(77n, ticket);
  } finally {
    assert.deepEqual(ticket, before, 'caller ticket must be unchanged on success or rejection');
    assert.equal(state.draws, 1);
  }
}
function assertDecimal(value) {
  assert.equal(typeof value, 'string');
  assert.match(value, /^(0|[1-9][0-9]*)$/);
}

// Sequential cases reset all mutable mock state; nested cases are awaited.
test('mint_witness_binding', {concurrency: false}, async () => {
  reset();
  await invoke();
  assert.deepEqual(Reflect.ownKeys(state.input).sort(),
    ['commitment', 'slot', 'generation', 'domain', 'secret', 'inverse'].sort());
  assert.deepEqual(state.input, expectedInput);
  for (const value of Object.values(state.input)) assertDecimal(value);
  assert.equal((17n * BigInt(state.input.inverse)) % helpers.FR, 1n);
});

test('mint_artifact_binding', {concurrency: false}, async () => {
  reset();
  await invoke();
  assert.equal(state.wasmPath, join(artifactRoot, 'mint_scale_js/mint_scale.wasm'));
  assert.equal(state.zkeyPath, join(artifactRoot, 'mint_scale.zkey'));
  assert.deepEqual(state.signals, expectedSignals);
  // Includes mint vkey selection, both policy counts, real artifact hashing and
  // verification before encoding, with no filesystem fallback.
  assert.deepEqual(state.events, [...throughVerification, 'encode']);
});

test('holder_note_shape', {concurrency: false}, async () => {
  reset();
  const result = await invoke();
  assert.deepEqual(Reflect.ownKeys(result).sort(), ['commitment', 'proof', 'note'].sort());
  assert.deepEqual(Reflect.ownKeys(result.note).sort(),
    ['secret', 'slot', 'generation', 'domain', 'commitment'].sort());
  assert.deepEqual(result, {commitment, proof: expectedProof,
    note: {secret: '17', slot: '700', generation: '4', domain: '77', commitment}});
  assertDecimal(result.commitment);
  for (const value of Object.values(result.note)) assertDecimal(value);
  assert.ok(Array.isArray(result.proof));
  assert.equal(result.proof.length, 128);
  assert.ok(result.proof.every(byte => Number.isInteger(byte) && byte >= 0 && byte <= 255));
  // Exact keys exclude roots, paths, inverse and a premature insertion index.
});

test('mint_public_signal_layout_rejections', {concurrency: false}, async t => {
  const swapped = [...expectedSignals];
  [swapped[0], swapped[1]] = [swapped[1], swapped[0]];
  const mutations = [
    ['wrong order', swapped], ['missing signal', expectedSignals.slice(0, -1)],
    ['extra signal', [...expectedSignals, '1']],
    ...expectedSignals.map((_, index) => {
      const signals = [...expectedSignals];
      signals[index] = String(BigInt(signals[index]) + 1n);
      return ['altered position ' + index, signals];
    }),
  ];
  for (const [label, signals] of mutations) {
    await t.test(label, async () => {
      reset({signals});
      await assert.rejects(invoke, {message: 'CIRCUIT_PUBLIC_INPUT_LAYOUT'});
      assert.deepEqual(state.events, beforeVerification); // zero verify/encode calls
    });
  }
});

test('mint_local_verification_failure', {concurrency: false}, async () => {
  reset({verifies: false});
  await assert.rejects(invoke, {message: 'LOCAL_GROTH16_VERIFICATION_FAILED'});
  assert.deepEqual(state.events, throughVerification); // no encoding or returned note
});

test('mint_prover_failure_propagates', {concurrency: false}, async () => {
  const error = new Error('synthetic mint prover failure');
  reset({error});
  await assert.rejects(invoke, actual => actual === error);
  assert.deepEqual(state.events, beforeVerification); // no verification/encoding/note
});
