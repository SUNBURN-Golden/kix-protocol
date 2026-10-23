// Source-informed characterizations of the existing metadata guards only.
// All hashes/counts/points below are fabricated, not measured artifacts, policy
// defaults, usable verification keys, or evidence of cryptographic verification.
import test from 'node:test';
import assert from 'node:assert/strict';
import {MANIFEST_FORMAT, requirePhase2ManifestV2, requirePhase2Key} from './zk-policy-v2.mjs';
import {
  DEPTH, SLOT_BITS, PROFILE_VERSION, ROOT_HISTORY_K,
  MINT, SPEND, MINT_PUBLIC, SPEND_PUBLIC,
} from './profile-constants.mjs';

const HASH = 'ab'.repeat(32);
const CIRCUITS = [MINT, SPEND];
const SOURCES = ['common', 'mint_scale', 'spend_scale'];
const artifactPaths = name => [
  `${name}.r1cs`, `${name}.zkey`, `${name}.vkey.json`,
  `${name}.vk.bin`, `${name}_js/${name}.wasm`,
];

function validManifest() {
  return {
    format: MANIFEST_FORMAT,
    depth: DEPTH,
    slotBits: SLOT_BITS,
    profileVersion: PROFILE_VERSION,
    rootHistoryK: ROOT_HISTORY_K, // Imported test-only value; operational K remains UNDETERMINED.
    phase1: {ptauSha256: HASH, source: 'SYNTHETIC_METADATA_ONLY', ptauPower: 4},
    phase2Contributions: {[MINT]: 1, [SPEND]: 1},
    constraints: {[MINT]: 1, [SPEND]: 1},
    circuits: Object.fromEntries(SOURCES.map(name => [`${name}.circom`, HASH])),
    files: Object.fromEntries(CIRCUITS.flatMap(artifactPaths).map(path => [path, HASH])),
  };
}

function validKey(expectedPublic) {
  return {
    protocol: 'groth16', curve: 'bn128', nPublic: expectedPublic,
    IC: Array.from({length: expectedPublic + 1}, () => ['1', '2', '1']),
    vk_gamma_2: [['1', '2'], ['3', '4'], ['1', '0']],
    vk_delta_2: [['5', '6'], ['7', '8'], ['1', '0']],
  };
}

// Every isolated mutation starts from a fresh, checked positive control.
function rejectsManifest(mutate, message, expected) {
  const manifest = validManifest();
  assert.doesNotThrow(() => requirePhase2ManifestV2(manifest, expected));
  mutate(manifest);
  assert.throws(() => requirePhase2ManifestV2(manifest, expected), {message});
}

function rejectsKey(expectedPublic, mutate, message) {
  const key = validKey(expectedPublic);
  assert.doesNotThrow(() => requirePhase2Key(key, expectedPublic));
  mutate(key);
  assert.throws(() => requirePhase2Key(key, expectedPublic), {message});
}

// Undefined marks property deletion, so absence is distinct from explicit null.
function setField(object, field, value) {
  if (value === undefined) delete object[field];
  else object[field] = value;
}

const invalidPositiveIntegers = [
  ['missing', undefined], ['null', null], ['numeric string', '1'],
  ['fractional', 1.5], ['zero', 0], ['negative', -1],
  ['NaN', NaN], ['positive infinity', Infinity], ['negative infinity', -Infinity],
];
const invalidHashes = [
  ['missing', undefined], ['null', null], ['empty', ''],
  ['short', 'a'.repeat(63)], ['long', 'a'.repeat(65)],
  ['uppercase', HASH.toUpperCase()], ['nonhex', 'g'.repeat(64)], ['number', 123],
];

test('source-informed: synthetic manifest control and matching explicit pins pass', () => {
  assert.doesNotThrow(() => requirePhase2ManifestV2(validManifest()));
  assert.doesNotThrow(() => requirePhase2ManifestV2(validManifest(), {
    depth: DEPTH, slotBits: SLOT_BITS, profileVersion: PROFILE_VERSION, rootHistoryK: ROOT_HISTORY_K,
  }));
  const manifest = validManifest();
  manifest.rootHistoryK = ROOT_HISTORY_K + 1;
  assert.doesNotThrow(() => requirePhase2ManifestV2(manifest));
  assert.doesNotThrow(() => requirePhase2ManifestV2(manifest, {rootHistoryK: manifest.rootHistoryK}));
});

// The existing artifact-backed regression already covers ordinary mismatches.
for (const [field, good, code] of [
  ['format', MANIFEST_FORMAT, 'CIRCUIT_MANIFEST_FORMAT'],
  ['depth', DEPTH, 'CIRCUIT_MANIFEST_DEPTH'],
  ['slotBits', SLOT_BITS, 'CIRCUIT_MANIFEST_SLOTBITS'],
  ['profileVersion', PROFILE_VERSION, 'CIRCUIT_MANIFEST_PROFILEVERSION'],
]) {
  for (const [label, value] of [
    ['missing', undefined], ['null', null], ['wrong type', typeof good === 'number' ? String(good) : 2],
  ]) {
    test(`source-informed: ${field} ${label}`, () => {
      rejectsManifest(m => setField(m, field, value), code);
    });
  }
}

// Missing K and an unequal explicit pin already have assertions in zk-regression.mjs.
for (const [label, value] of invalidPositiveIntegers.filter(([label]) => label !== 'missing')) {
  test(`source-informed: rootHistoryK ${label}`, () => {
    rejectsManifest(m => { m.rootHistoryK = value; }, 'CIRCUIT_MANIFEST_ROOT_HISTORY_K');
  });
}

for (const [label, value] of invalidHashes) {
  test(`source-informed: phase1.ptauSha256 ${label}`, () => {
    rejectsManifest(m => setField(m.phase1, 'ptauSha256', value), 'PHASE1_RECORD_MISSING');
  });
}
// The implementation checks truthiness of source, not a source type or allowlist.
for (const [label, value] of [
  ['missing', undefined], ['null', null], ['empty', ''], ['false', false], ['zero', 0],
]) {
  test(`source-informed: phase1.source ${label}`, () => {
    rejectsManifest(m => setField(m.phase1, 'source', value), 'PHASE1_RECORD_MISSING');
  });
}
for (const [label, value] of [
  ['missing', undefined], ['null', null], ['numeric string', '4'], ['fractional', 4.5],
  ['NaN', NaN], ['positive infinity', Infinity], ['negative infinity', -Infinity],
]) {
  test(`source-informed: phase1.ptauPower ${label}`, () => {
    rejectsManifest(m => setField(m.phase1, 'ptauPower', value), 'PHASE1_RECORD_MISSING');
  });
}
for (const power of [0, -1]) {
  test(`source-informed: integer power ${power} reaches the capacity guard`, () => {
    rejectsManifest(m => { m.phase1.ptauPower = power; }, `PTAU_POWER_TOO_SMALL:${MINT}`);
  });
}

for (const name of CIRCUITS) {
  for (const [label, value] of invalidPositiveIntegers) {
    test(`source-informed: ${name} contribution ${label}`, () => {
      rejectsManifest(m => setField(m.phase2Contributions, name, value), `PHASE2_CONTRIBUTION_REQUIRED:${name}`);
    });
    test(`source-informed: ${name} constraint count ${label}`, () => {
      rejectsManifest(m => setField(m.constraints, name, value), `CONSTRAINT_COUNT_MISSING:${name}`);
    });
  }
  test(`source-informed: ${name} metadata capacity boundary is constraints + 1`, () => {
    // Arithmetic characterization only. setup-zk.mjs separately adds public inputs.
    const manifest = validManifest();
    manifest.constraints[name] = 15;
    assert.doesNotThrow(() => requirePhase2ManifestV2(manifest));
    manifest.constraints[name] = 16;
    assert.throws(() => requirePhase2ManifestV2(manifest), {message: `PTAU_POWER_TOO_SMALL:${name}`});
  });
  for (const path of artifactPaths(name)) {
    for (const [label, value] of invalidHashes) {
      test(`source-informed: artifact ${path} hash ${label}`, () => {
        rejectsManifest(m => setField(m.files, path, value), `MISSING_ARTIFACT_HASH:${path}`);
      });
    }
  }
}

for (const source of SOURCES) {
  for (const [label, value] of invalidHashes) {
    test(`source-informed: circuit ${source} hash ${label}`, () => {
      rejectsManifest(m => setField(m.circuits, `${source}.circom`, value), `MISSING_CIRCUIT_HASH:${source}`);
    });
  }
}

for (const [field, code] of [
  ['phase1', 'PHASE1_RECORD_MISSING'],
  ['phase2Contributions', `PHASE2_CONTRIBUTION_REQUIRED:${MINT}`],
  ['constraints', `CONSTRAINT_COUNT_MISSING:${MINT}`],
  ['files', `MISSING_ARTIFACT_HASH:${MINT}.r1cs`],
  ['circuits', 'MISSING_CIRCUIT_HASH:common'],
]) {
  for (const [label, value] of [['missing', undefined], ['null', null]]) {
    test(`source-informed: ${field} container ${label}`, () => {
      rejectsManifest(m => setField(m, field, value), code);
    });
  }
}

for (const [name, expectedPublic] of [[MINT, MINT_PUBLIC.length], [SPEND, SPEND_PUBLIC.length]]) {
  test(`source-informed: ${name} guard-compatible synthetic key passes`, () => {
    assert.doesNotThrow(() => requirePhase2Key(validKey(expectedPublic), expectedPublic));
  });
  for (const [field, variants] of [
    ['protocol', [['missing', undefined], ['null', null], ['wrong type', 1], ['other protocol', 'plonk']]],
    ['curve', [['missing', undefined], ['null', null], ['wrong type', 1], ['other spelling', 'BN254']]],
    ['nPublic', [
      ...invalidPositiveIntegers, ['matching numeric string', String(expectedPublic)],
      ['too few', expectedPublic - 1], ['too many', expectedPublic + 1],
    ]],
    ['IC', [
      ['missing', undefined], ['null', null], ['number', 1], ['object without length', {}],
      ['empty string', ''], ['short array', Array(expectedPublic).fill(['1', '2'])],
      ['long array', Array(expectedPublic + 2).fill(['1', '2'])],
    ]],
  ]) {
    for (const [label, value] of variants) {
      test(`source-informed: ${name} key ${field} ${label}`, () => {
        rejectsKey(expectedPublic, key => setField(key, field, value), 'VK_FORMAT');
      });
    }
  }
  for (const field of ['vk_gamma_2', 'vk_delta_2']) {
    for (const [label, value] of [['missing', undefined], ['null', null], ['false', false]]) {
      test(`source-informed: ${name} key ${field} ${label}`, () => {
        rejectsKey(expectedPublic, key => setField(key, field, value), 'UNCONTRIBUTED_PHASE2_KEY');
      });
    }
  }
  for (const representation of ['identical', 'numeric equivalents']) {
    test(`source-informed: ${name} equal gamma/delta (${representation})`, () => {
      rejectsKey(expectedPublic, key => {
        key.vk_delta_2 = representation === 'identical'
          ? structuredClone(key.vk_gamma_2)
          : [['0x1', '02'], ['+3', '004'], ['01', '0x0']];
      }, 'UNCONTRIBUTED_PHASE2_KEY');
    });
  }
}
