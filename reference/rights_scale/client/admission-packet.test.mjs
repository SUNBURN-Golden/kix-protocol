// Offline packet-construction regressions, source-informed within EV-RS.
// All witness scalars are published synthetic values. Coordinates are fabricated
// encoder fixtures, not generated or valid proofs. No keys, artifacts or RPC.
import {test, mock, after} from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import {resolve, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import * as helpers from './zk-helpers.mjs';
import {DEPTH, MINT, SPEND} from './profile-constants.mjs';

const artifactRoot = resolve(fileURLToPath(new URL('../zk/artifacts', import.meta.url)));
const keys = {
  [MINT]: {tag: 'synthetic mint key sentinel'},
  [SPEND]: {tag: 'synthetic spend key sentinel'},
};
const keyBytes = {
  [MINT]: Buffer.from('synthetic mint encoding sentinel'),
  [SPEND]: Buffer.from('synthetic spend encoding sentinel'),
};
const files = new Map([
  ['spend_scale_js/spend_scale.wasm', Buffer.from('synthetic wasm sentinel')],
  ['spend_scale.zkey', Buffer.from('synthetic zkey sentinel; not a key')],
]);
const manifest = {tag: 'synthetic manifest sentinel',
  files: Object.fromEntries([...files].map(([name, bytes]) => [name, helpers.sha256(bytes)]))};
const manifestBytes = Buffer.from(JSON.stringify(manifest));
for (const name of [MINT, SPEND]) files.set(name + '.vk.bin', keyBytes[name]);
files.set('manifest.json', manifestBytes);

function syntheticProof() {
  // Same public coordinate fixture as zk-helpers.test.mjs; no curve claim.
  return {
    pi_a: ['513', '2', '1'],
    pi_b: [['1027', '1541'], ['3', '4'], ['1', '0']],
    pi_c: ['2055', '5', '1'],
  };
}
// Literal little-endian words, independent of proofBytes under test.
const expectedProof = Array.from(Buffer.from(
  '0102' + '00'.repeat(30) + '0304' + '00'.repeat(30) +
  '0506' + '00'.repeat(30) + '0708' + '00'.repeat(30), 'hex'));

let state;
function keyName(key) {
  const name = [MINT, SPEND].find(name => keys[name] === key);
  assert.ok(name, 'unexpected key sentinel');
  return name;
}
async function readJSON(path) {
  const name = [MINT, SPEND].find(name => path === join(artifactRoot, name + '.vkey.json'));
  assert.ok(name, 'unexpected JSON read: ' + path);
  state.events.push('readJSON:' + name);
  return keys[name];
}

// Register dependency mocks BEFORE importing the actual client. Real FR, sha256
// and proofBytes are retained; policy validation and key encoding are sentinels.
mock.module('node:fs/promises', {namedExports: {...fs, readFile: async path => {
  const entry = [...files].find(([name]) => path === join(artifactRoot, name));
  assert.ok(entry, 'unexpected artifact read: ' + path);
  state.events.push('readFile:' + entry[0]);
  return Buffer.from(entry[1]);
}}});
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
    assert.equal(count, name === MINT ? 4 : 6);
  },
}});
mock.module('snarkjs', {namedExports: {groth16: {
  fullProve: async (input, wasmPath, zkeyPath) => {
    state.events.push('prove');
    assert.equal(wasmPath, join(artifactRoot, 'spend_scale_js/spend_scale.wasm'));
    assert.equal(zkeyPath, join(artifactRoot, 'spend_scale.zkey'));
    // Check that the real spendWitness input reaches the prover boundary.
    assert.equal(input.secret, '17');
    assert.equal(input.slot, '700');
    assert.equal(input.generation, '4');
    for (const path of ['noteBits', 'noteSiblings', 'revocationSiblings']) {
      assert.equal(input[path].length, DEPTH);
    }
    if (state.error) throw state.error;
    return {proof: state.proof, publicSignals: state.signals};
  },
  verify: async (key, signals, proof) => {
    state.events.push('verify');
    assert.equal(key, keys[SPEND]);
    assert.equal(signals, state.signals);
    assert.equal(proof, state.proof);
    return state.verifies;
  },
}}});
after(() => mock.restoreAll());

const {admissionProof, poseidon} = await import('./private-scale.mjs');
const H = await poseidon();
const expiry = 1900000000123n;
const gate = 37n * 2n ** 128n + 19n;

function fixture() {
  const commitment = H([17n, 700n, 4n, 77n, 1n]);
  return {
    tree: {domain: 77n, noteLeaves: [101n, 102n, commitment, 104n, 105n],
      revoked: new Map([[700, 3n], [2, 1n], [701, 2n]])},
    note: {secret: '17', slot: '700', generation: '4', domain: '77', commitment: String(commitment)},
    options: {challenge: 23n},
  };
}

// Dense bottom-up fold, without SparseTree/path helpers. Shares actual Poseidon
// and depth: structural expectations, not independent cryptographic evidence.
function denseRoot(entries) {
  let level = Array(2 ** DEPTH).fill(0n);
  for (const [index, value] of entries) level[index] = BigInt(value);
  while (level.length > 1) {
    const parents = [];
    for (let i = 0; i < level.length; i += 2) parents.push(H([level[i], level[i + 1]]));
    level = parents;
  }
  return level[0];
}
// Expectations are stated before any prover call; never read captured inputs,
// returned packet fields or SPEND_PUBLIC to derive them.
const expectedSignals = [
  denseRoot([[0, 101n], [1, 102n], [2, H([17n, 700n, 4n, 77n, 1n])], [3, 104n], [4, 105n]]),
  denseRoot([[700, 3n], [2, 1n], [701, 2n]]),
  H([17n, 700n, 4n, 77n, 2n]), H([19n, 37n, 23n, 1900000000123n, 1n]), 77n, 1n,
].map(String);
assert.equal(new Set(expectedSignals).size, 6, 'order mutation requires distinct signals');

const artifactEvents = [
  'readFile:manifest.json', 'manifestPolicy',
  'readFile:spend_scale_js/spend_scale.wasm', 'readFile:spend_scale.zkey',
  'readJSON:mint_scale', 'keyPolicy:mint_scale', 'vkBytes:mint_scale', 'readFile:mint_scale.vk.bin',
  'readJSON:spend_scale', 'keyPolicy:spend_scale', 'vkBytes:spend_scale', 'readFile:spend_scale.vk.bin',
  'readFile:mint_scale.vk.bin', 'readFile:spend_scale.vk.bin',
];
function reset(overrides = {}) {
  state = {events: [], proof: syntheticProof(), signals: [...expectedSignals], verifies: true, ...overrides};
}
async function invoke() {
  const f = fixture(), before = structuredClone(f);
  const leaves = f.tree.noteLeaves, revoked = f.tree.revoked;
  try {
    return await admissionProof(f.tree, f.note, gate, expiry, f.options);
  } finally {
    assert.deepEqual(f, before);
    assert.equal(f.tree.noteLeaves, leaves);
    assert.equal(f.tree.revoked, revoked);
  }
}
const forbidden = new Set(['note', 'secret', 'slot', 'generation', 'inverse', 'input',
  'noteBits', 'noteSiblings', 'revocationSiblings']);
function assertPublicStructure(value) {
  if (value === null || typeof value !== 'object') return;
  for (const key of Reflect.ownKeys(value)) {
    assert.ok(!forbidden.has(key), 'private witness field: ' + String(key));
    assertPublicStructure(value[key]);
  }
}

// Sequential cases share only reset mock state; nested mutations are awaited.
test('packet_contains_only_public_fields', {concurrency: false}, async () => {
  reset();
  const packet = await invoke();
  assert.deepEqual(Reflect.ownKeys(packet).sort(),
    ['noteRoot', 'revocationRoot', 'nullifier', 'challenge', 'expiresMs', 'proof', 'publicSignals'].sort());
  assert.deepEqual(packet, {
    noteRoot: expectedSignals[0], revocationRoot: expectedSignals[1], nullifier: expectedSignals[2],
    challenge: '23', expiresMs: '1900000000123', proof: expectedProof, publicSignals: expectedSignals,
  });
  for (const field of ['noteRoot', 'revocationRoot', 'nullifier', 'challenge', 'expiresMs']) {
    assert.equal(typeof packet[field], 'string');
    assert.match(packet[field], /^(0|[1-9][0-9]*)$/);
  }
  assert.ok(Array.isArray(packet.proof));
  assert.ok(packet.proof.every(byte => Number.isInteger(byte) && byte >= 0 && byte <= 255));
  assertPublicStructure(packet);
  assert.deepEqual(state.events, [...artifactEvents, 'prove', 'readJSON:spend_scale', 'verify', 'encode']);
});

test('public_signal_layout_rejections', {concurrency: false}, async t => {
  const swapped = [...expectedSignals];
  [swapped[0], swapped[1]] = [swapped[1], swapped[0]];
  const mutations = [
    ['wrong order', swapped], ['missing signal', expectedSignals.slice(0, -1)],
    ['extra signal', [...expectedSignals, '0']],
    ...expectedSignals.map((_, i) => ['wrong value at ' + i,
      expectedSignals.map((value, j) => j === i ? String(BigInt(value) + 1n) : value)]),
  ];
  for (const [name, signals] of mutations) {
    await t.test(name, async () => {
      reset({signals});
      await assert.rejects(invoke, {message: 'CIRCUIT_PUBLIC_INPUT_LAYOUT'});
      assert.deepEqual(state.events, [...artifactEvents, 'prove']);
    });
  }
});

test('local_verification_failure', {concurrency: false}, async () => {
  reset({verifies: false});
  await assert.rejects(invoke, {message: 'LOCAL_GROTH16_VERIFICATION_FAILED'});
  assert.deepEqual(state.events, [...artifactEvents, 'prove', 'readJSON:spend_scale', 'verify']);
});

test('prover_failure_propagates', {concurrency: false}, async () => {
  const error = new Error('synthetic prover failure');
  reset({error});
  await assert.rejects(invoke, actual => actual === error);
  assert.deepEqual(state.events, [...artifactEvents, 'prove']);
});
