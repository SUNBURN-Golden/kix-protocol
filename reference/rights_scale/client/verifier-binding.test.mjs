// Source-informed offline integration tests of artifacts(expectedHash) and checkVerifier
// within EV-RS (IM-17 / IM-27 evidence). Everything is synthetic: an in-memory file map,
// fabricated public key coordinates and a fake RPC object. No real artifact, key, ceremony,
// proof, RPC or chain is involved, so nothing here is actual-chain verification or
// operational qualification.
//
// Mocked boundaries (all others are the real, unchanged implementation):
//   1. node:fs/promises readFile  -> in-memory map rooted at the real artifactRoot; an
//      unexpected path fails the test. Real readJSON (zk-helpers) reads through the same map.
//   2. ./types.mjs Verifier.parse -> explicit stub returning a caller-supplied object. It
//      replaces BCS decoding entirely: layout and currentness of the Verifier decoder are NOT
//      tested here (that stays with the extended-decoder node).
//   3. rpc.getObject              -> fake object recording its arguments.
// Real and shared with the implementation: sha256, vkBytes, readJSON, requirePhase2ManifestV2,
// requirePhase2Key. The metadata validator matrix stays in zk-policy-v2.test.mjs and the
// encoder matrix in zk-helpers.test.mjs; neither is repeated.
import {test, mock, after} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as fs from 'node:fs/promises';
import {resolve, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {MINT, SPEND, DEPTH, SLOT_BITS, PROFILE_VERSION, ROOT_HISTORY_K} from './profile-constants.mjs';

const artifactRootExpected = resolve(fileURLToPath(new URL('../zk/artifacts', import.meta.url)));

// Coordinate field, deliberately distinct from the scalar modulus FR.
const FQ = 21888242871839275222246405745257275088696311157297823662689037894645226208583n;
const HALF = (FQ - 1n) / 2n;

// Fabricated public coordinates, the encoder shapes of zk-helpers.test.mjs; gamma differs from
// delta so the real key policy passes. Not curve points and not usable verification keys.
function syntheticKey(nPublic) {
  return {
    protocol: 'groth16', curve: 'bn128', nPublic,
    vk_alpha_1: ['513', '2', '1'],
    vk_beta_2: [['1027', '1541'], ['3', '4'], ['1', '0']],
    vk_gamma_2: [['2055', '2569'], ['5', '6'], ['1', '0']],
    vk_delta_2: [['3083', '3597'], ['7', '8'], ['1', '0']],
    IC: Array.from({length: nPublic + 1}, (_, i) => [i % 2 ? '4625' : '4111', '9', '1']),
  };
}
// Expected verifier bytes are assembled from literal hex words, never via vkBytes.
const word = (prefix, last = '00') => Buffer.from(prefix.padEnd(62, '0') + last, 'hex');
const expectedKey = (count, countHex) => Buffer.concat([
  word('0102'), word('0304'), word('0506'), word('0708'), word('090a'),
  word('0b0c'), word('0d0e'), Buffer.from(countHex, 'hex'),
  ...Array.from({length: count}, (_, i) => word(i % 2 ? '1112' : '0f10')),
]);
const MINT_BYTES = expectedKey(5, '0500000000000000'); // nPublic 4: IC length 5
const SPEND_BYTES = expectedKey(7, '0700000000000000'); // nPublic 6: IC length 7
assert.notDeepEqual(MINT_BYTES, SPEND_BYTES);

const PKG = '0x' + 'ab'.repeat(32);
const VERIFIER_ID = '0x' + 'cd'.repeat(32);
const HASH = 'ab'.repeat(32); // fabricated digest for metadata-only manifest fields
const SHA = bytes => createHash('sha256').update(bytes).digest('hex');

// Literal manifest.files order; the implementation reads artifacts in this insertion order.
const ARTIFACT_NAMES = [
  'mint_scale.r1cs', 'mint_scale.zkey', 'mint_scale.vkey.json', 'mint_scale.vk.bin', 'mint_scale_js/mint_scale.wasm',
  'spend_scale.r1cs', 'spend_scale.zkey', 'spend_scale.vkey.json', 'spend_scale.vk.bin', 'spend_scale_js/spend_scale.wasm',
];
const reads = names => names.map(name => 'readFile:' + name);
const MANIFEST_READ = reads(['manifest.json']);
const KEY_READS = reads([
  'mint_scale.vkey.json', 'mint_scale.vk.bin', 'spend_scale.vkey.json', 'spend_scale.vk.bin',
  'mint_scale.vk.bin', 'spend_scale.vk.bin',
]);
const FULL_ARTIFACT_TRACE = [...MANIFEST_READ, ...reads(ARTIFACT_NAMES), ...KEY_READS];

// A fresh fixture per case. The artifact map excludes manifest.json until sealed, so a case
// either re-derives digests and the pin (seal) or deliberately leaves them stale.
function baseFixture() {
  const keys = {[MINT]: syntheticKey(4), [SPEND]: syntheticKey(6)};
  const files = new Map();
  for (const name of [MINT, SPEND]) {
    files.set(`${name}.r1cs`, Buffer.from(`synthetic ${name} r1cs sentinel`));
    files.set(`${name}.zkey`, Buffer.from(`synthetic ${name} zkey sentinel; not a key`));
    files.set(`${name}.vkey.json`, Buffer.from(JSON.stringify(keys[name])));
    files.set(`${name}.vk.bin`, Buffer.from(name === MINT ? MINT_BYTES : SPEND_BYTES));
    files.set(`${name}_js/${name}.wasm`, Buffer.from(`synthetic ${name} wasm sentinel`));
  }
  const manifest = {
    format: 'kix-zk-artifacts-v2',
    depth: DEPTH,
    slotBits: SLOT_BITS,
    profileVersion: PROFILE_VERSION,
    rootHistoryK: ROOT_HISTORY_K, // test-only fixture value; the operational K is UNDETERMINED
    phase1: {ptauSha256: HASH, source: 'SYNTHETIC_METADATA_ONLY', ptauPower: 4},
    phase2Contributions: {[MINT]: 1, [SPEND]: 1},
    constraints: {[MINT]: 1, [SPEND]: 1},
    circuits: Object.fromEntries(['common', MINT, SPEND].map(name => [`${name}.circom`, HASH])),
    files: {},
  };
  for (const name of ARTIFACT_NAMES) manifest.files[name] = SHA(files.get(name));
  return {keys, files, manifest};
}
function redigest(fx, name) { fx.manifest.files[name] = SHA(fx.files.get(name)); }
function seal(fx) {
  const bytes = Buffer.from(JSON.stringify(fx.manifest));
  fx.files.set('manifest.json', bytes);
  fx.hash = SHA(bytes);
  return fx;
}
const sealed = mutate => { const fx = baseFixture(); mutate?.(fx); return seal(fx); };

let state;
const reset = (fx = sealed()) => {
  state = {
    files: fx.files, events: [], calls: [], parseError: null,
    object: {type: PKG + '::zk_gate::Verifier', owner: {$kind: 'Immutable'}, content: {tag: 'synthetic bcs sentinel'}},
    parsed: {
      circuit_manifest_hash: Array.from(Buffer.from(fx.hash, 'hex')),
      mint_vk: Array.from(MINT_BYTES), spend_vk: Array.from(SPEND_BYTES),
    },
  };
  return fx;
};
reset();

// Dependency mocks precede the dynamic imports of the unchanged implementation.
const {default: fsDefault, ...fsNamed} = fs;
const mockedReadFile = async (path, encoding) => {
  const entry = [...state.files].find(([name]) => path === join(artifactRootExpected, name));
  assert.ok(entry, 'unexpected artifact read: ' + path);
  state.events.push('readFile:' + entry[0]);
  const bytes = Buffer.from(entry[1]);
  return encoding ? bytes.toString(encoding) : bytes;
};
mock.module('node:fs/promises', {defaultExport: {...fsDefault, readFile: mockedReadFile},
  namedExports: {...fsNamed, readFile: mockedReadFile}});
mock.module('./types.mjs', {namedExports: {Verifier: {parse: content => {
  state.events.push('parse');
  assert.equal(content, state.object.content, 'parse must receive the fetched object content');
  if (state.parseError) throw state.parseError;
  return state.parsed;
}}}});
after(() => mock.restoreAll());

const {artifacts, checkVerifier, artifactRoot} = await import('./private-scale.mjs');
const {sha256} = await import('./zk-helpers.mjs');
assert.equal(artifactRoot, artifactRootExpected);

const rpc = {getObject: async args => {
  state.events.push('getObject');
  state.calls.push(structuredClone(args));
  return {object: state.object};
}};
const run = fx => checkVerifier(rpc, PKG, VERIFIER_ID, fx.hash);
const assertRequested = () => assert.deepEqual(state.calls, [{objectId: VERIFIER_ID, include: {content: true}}]);
function controlResult(fx) {
  return {manifest: JSON.parse(fx.files.get('manifest.json')), hash: fx.hash,
    mintVK: Array.from(MINT_BYTES), spendVK: Array.from(SPEND_BYTES)};
}
// The failure must reject (no successful return) and stop at exactly this trace.
async function rejectsAt(call, message, trace) {
  await assert.rejects(call(), {message});
  assert.deepEqual(state.events, trace);
}

test('fixture sanity: independent digest agrees with the shared sha256 helper', () => {
  const fx = reset();
  assert.equal(sha256(fx.files.get('manifest.json')), fx.hash);
  assert.equal(fx.hash.length, 64);
  assert.equal(Object.keys(fx.manifest.files).length, 10);
  assert.deepEqual(Object.keys(fx.manifest.files), ARTIFACT_NAMES);
});

test('artifacts_control', {concurrency: false}, async () => {
  const fx = reset();
  for (const pin of [fx.hash, undefined]) {
    reset(fx);
    const result = await artifacts(pin);
    assert.deepEqual(Object.keys(result), ['manifest', 'hash', 'mintVK', 'spendVK']);
    assert.deepEqual(result, controlResult(fx));
    assert.deepEqual(result.manifest, fx.manifest);
    assert.equal(result.hash, fx.hash);
    assert.deepEqual(state.events, FULL_ARTIFACT_TRACE);
  }
});

test('manifest_pin_mismatch', {concurrency: false}, async () => {
  const fx = reset();
  for (const [label, pin] of [['zero digest', '00'.repeat(32)], ['digest of other bytes', SHA(Buffer.from('other manifest bytes'))]]) {
    await test(label, async () => {
      reset(fx);
      assert.notEqual(pin, fx.hash);
      await rejectsAt(() => artifacts(pin), 'CIRCUIT_MANIFEST_PIN_MISMATCH', MANIFEST_READ);
    });
  }
});

test('artifact_byte_hash_mismatch', {concurrency: false}, async () => {
  await test('loaded bytes differ from manifest digest', async () => {
    const fx = reset(sealed());
    const bytes = Buffer.from(fx.files.get('spend_scale.zkey'));
    bytes[0] ^= 1;
    fx.files.set('spend_scale.zkey', bytes);
    const upTo = ARTIFACT_NAMES.indexOf('spend_scale.zkey') + 1;
    await rejectsAt(() => artifacts(fx.hash), 'CIRCUIT_ARTIFACT_HASH_MISMATCH:spend_scale.zkey',
      [...MANIFEST_READ, ...reads(ARTIFACT_NAMES.slice(0, upTo))]);
  });
  await test('manifest digest differs from loaded bytes, pin follows the manifest', async () => {
    const fx = reset(sealed(f => { f.manifest.files['mint_scale.r1cs'] = 'cd'.repeat(32); }));
    await rejectsAt(() => artifacts(fx.hash), 'CIRCUIT_ARTIFACT_HASH_MISMATCH:mint_scale.r1cs',
      [...MANIFEST_READ, ...reads(['mint_scale.r1cs'])]);
  });
});

test('artifact_path_escape', {concurrency: false}, async () => {
  // Sibling-prefix, parent traversal, interior traversal and absolute entries; all carry
  // fabricated valid-looking digests and follow the ten real entries.
  for (const escaped of ['../escape.bin', '../artifacts-evil/x', 'sub/../../escape.bin', '/etc/synthetic-escape']) {
    await test(escaped, async () => {
      const fx = reset(sealed(f => { f.manifest.files[escaped] = HASH; }));
      await rejectsAt(() => artifacts(fx.hash), 'ARTIFACT_PATH', [...MANIFEST_READ, ...reads(ARTIFACT_NAMES)]);
    });
  }
});

test('encoded_verifier_byte_mismatch', {concurrency: false}, async () => {
  await test('one byte of the mint vk.bin differs', async () => {
    const fx = reset(sealed(f => {
      const bytes = Buffer.from(MINT_BYTES);
      bytes[40] ^= 1;
      f.files.set('mint_scale.vk.bin', bytes);
      redigest(f, 'mint_scale.vk.bin');
    }));
    await rejectsAt(() => artifacts(fx.hash), 'VERIFIER_ENCODING_MISMATCH',
      [...MANIFEST_READ, ...reads(ARTIFACT_NAMES), ...reads(['mint_scale.vkey.json', 'mint_scale.vk.bin'])]);
  });
  await test('spend vkey.json changes an encoded point, still policy-valid', async () => {
    const fx = reset(sealed(f => {
      f.keys[SPEND].IC[0][1] = String(HALF + 1n); // flips the compressed sign bit of IC[0]
      f.files.set('spend_scale.vkey.json', Buffer.from(JSON.stringify(f.keys[SPEND])));
      redigest(f, 'spend_scale.vkey.json');
    }));
    await rejectsAt(() => artifacts(fx.hash), 'VERIFIER_ENCODING_MISMATCH',
      [...MANIFEST_READ, ...reads(ARTIFACT_NAMES),
        ...reads(['mint_scale.vkey.json', 'mint_scale.vk.bin', 'spend_scale.vkey.json', 'spend_scale.vk.bin'])]);
  });
});

test('check_verifier_control', {concurrency: false}, async () => {
  const fx = reset();
  const result = await run(fx);
  assert.deepEqual(result, controlResult(fx));
  assertRequested();
  assert.deepEqual(state.events, ['getObject', 'parse', ...FULL_ARTIFACT_TRACE]);
});

test('check_verifier_object_pin_rejections', {concurrency: false}, async () => {
  const other = '0x' + 'ee'.repeat(32);
  for (const [label, change] of [
    ['other package id', o => { o.type = other + '::zk_gate::Verifier'; }],
    ['other type name', o => { o.type = PKG + '::zk_gate::Other'; }],
    ['other module', o => { o.type = PKG + '::rights_scale::Verifier'; }],
    ['address-owned', o => { o.owner = {$kind: 'AddressOwner', AddressOwner: other}; }],
    ['shared', o => { o.owner = {$kind: 'Shared', Shared: {initialSharedVersion: '1'}}; }],
    ['object-owned', o => { o.owner = {$kind: 'ObjectOwner', ObjectOwner: other}; }],
  ]) {
    await test(label, async () => {
      const fx = reset();
      change(state.object);
      await rejectsAt(() => run(fx), 'VERIFIER_OBJECT_PIN_MISMATCH', ['getObject']);
      assertRequested();
    });
  }
  // Characterization (contract-undefined): an object without ownership information is not
  // reported with the pin diagnostic. Only "rejects, nothing decoded or read" is recorded.
  await test('characterization: missing owner', async () => {
    const fx = reset();
    delete state.object.owner;
    await assert.rejects(run(fx), TypeError);
    assert.deepEqual(state.events, ['getObject']);
    assertRequested();
  });
});

test('check_verifier_key_pin_rejections', {concurrency: false}, async () => {
  const flip = bytes => { const copy = Array.from(bytes); copy[100] ^= 1; return copy; };
  for (const [label, change] of [
    ['differing manifest hash', p => { p.circuit_manifest_hash = Array.from(Buffer.from('99'.repeat(32), 'hex')); }],
    ['one mint key byte, spend equal', p => { p.mint_vk = flip(MINT_BYTES); }],
    ['one spend key byte, mint equal', p => { p.spend_vk = flip(SPEND_BYTES); }],
    ['mint key truncated', p => { p.mint_vk = Array.from(MINT_BYTES.subarray(0, MINT_BYTES.length - 1)); }],
    ['spend key empty', p => { p.spend_vk = []; }],
    ['mint and spend keys swapped', p => { [p.mint_vk, p.spend_vk] = [p.spend_vk, p.mint_vk]; }],
  ]) {
    await test(label, async () => {
      const fx = reset();
      change(state.parsed);
      await rejectsAt(() => run(fx), 'VERIFIER_KEY_PIN_MISMATCH', ['getObject', 'parse', ...FULL_ARTIFACT_TRACE]);
      assertRequested();
    });
  }
});

test('check_verifier_supplied_hash_mismatch', {concurrency: false}, async () => {
  // Characterization: the supplied pin is compared with the loaded manifest bytes inside
  // artifacts(), after getObject and parse, and before the object's own hash is compared.
  const fx = reset();
  await rejectsAt(() => checkVerifier(rpc, PKG, VERIFIER_ID, '00'.repeat(32)),
    'CIRCUIT_MANIFEST_PIN_MISMATCH', ['getObject', 'parse', ...MANIFEST_READ]);
  assertRequested();
  assert.notEqual(fx.hash, '00'.repeat(32));
});

test('check_verifier_failure_propagation', {concurrency: false}, async () => {
  await test('stubbed parse failure propagates by identity', async () => {
    const fx = reset();
    state.parseError = new Error('synthetic parse failure');
    const thrown = state.parseError;
    await assert.rejects(run(fx), error => error === thrown);
    assert.deepEqual(state.events, ['getObject', 'parse']);
    assertRequested();
  });
  await test('artifact failure inside checkVerifier propagates before any comparison', async () => {
    const fx = reset(sealed(f => { f.manifest.files['spend_scale.r1cs'] = 'cd'.repeat(32); }));
    state.parsed.mint_vk = []; // would fail the key pin, but the artifact guard comes first
    await rejectsAt(() => run(fx), 'CIRCUIT_ARTIFACT_HASH_MISMATCH:spend_scale.r1cs',
      ['getObject', 'parse', ...MANIFEST_READ, ...reads(ARTIFACT_NAMES.slice(0, 6))]);
  });
  await test('getObject failure propagates before parse or reads', async () => {
    const fx = reset();
    const failure = new Error('synthetic rpc failure');
    const failing = {getObject: async () => { state.events.push('getObject'); throw failure; }};
    await assert.rejects(checkVerifier(failing, PKG, VERIFIER_ID, fx.hash), error => error === failure);
    assert.deepEqual(state.events, ['getObject']);
  });
});
