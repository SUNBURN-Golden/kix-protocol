// Offline IM-14/IM-15 client construction checks, within EV-RS's reference boundary.
// All scalars are public synthetic fixtures, including the value named secret.
// No minting, randomness, proving, artifacts, RPC or chain execution.
import test from 'node:test';
import assert from 'node:assert/strict';
import {spendWitness, poseidon} from './private-scale.mjs';
import {DEPTH} from './profile-constants.mjs';
import {FR} from './zk-helpers.mjs';

const H = await poseidon();
const limbBase = 2n ** 128n;
const expiry = 1900000000123n;
const defaultContext = {low: 19n, high: 37n, challenge: 23n, expires: expiry};

function fixture(domain = 77n) {
  const commitment = H([17n, 700n, 4n, domain, 1n]);
  return {
    tree: {domain, noteLeaves: [101n, 102n, commitment, 104n, 105n],
      revoked: new Map([[700, 3n], [2, 1n], [701, 2n]])},
    note: {secret: '17', slot: '700', generation: '4', domain: String(domain), commitment: String(commitment)},
  };
}

// Dense bottom-up oracle: no SparseTree, noteTreeOf or revocationTreeOf.
// Source-informed structural expectations share the client's Poseidon primitive
// and DEPTH. This is not an independent cryptographic or circuit verification.
function densePath(entries, index) {
  let level = Array(2 ** DEPTH).fill(0n);
  for (const [i, value] of entries) level[i] = BigInt(value);
  const bits = [], siblings = [];
  while (level.length > 1) {
    bits.push(index % 2);
    siblings.push(level[index % 2 === 0 ? index + 1 : index - 1]);
    const parents = [];
    for (let i = 0; i < level.length; i += 2) parents.push(H([level[i], level[i + 1]]));
    index = Math.floor(index / 2);
    level = parents;
  }
  return {root: level[0], bits, siblings};
}

function foldPath(leaf, siblings, bits) {
  return siblings.reduce((value, sibling, i) =>
    Number(bits[i]) === 0 ? H([value, BigInt(sibling)]) : H([BigInt(sibling), value]), BigInt(leaf));
}

// Every successful or rejected call checks values AND retained container identity.
async function invoke({tree, note}, {low, high, challenge, expires} = defaultContext, options = {challenge}) {
  const before = structuredClone({tree, note, options});
  const leaves = tree.noteLeaves, revoked = tree.revoked;
  try {
    return await spendWitness(tree, note, high * limbBase + low, expires, options);
  } finally {
    assert.deepEqual({tree, note, options}, before);
    assert.equal(tree.noteLeaves, leaves);
    assert.equal(tree.revoked, revoked);
  }
}

async function accepts(f, context = defaultContext) {
  const w = await invoke(f, context);
  const {low, high, challenge, expires} = context;
  const {secret, slot, generation, domain, commitment} = f.note;
  const leaves = f.tree.noteLeaves.slice(0, f.tree.noteCount ?? f.tree.noteLeaves.length);
  const index = leaves.findIndex(value => BigInt(value) === BigInt(commitment));
  assert.ok(index >= 0);
  const np = densePath(leaves.map((value, i) => [i, value]), index);
  const rp = densePath(f.tree.revoked, Number(slot));
  const nullifier = H([BigInt(secret), BigInt(slot), BigInt(generation), BigInt(domain), 2n]);
  const boundContext = H([low, high, challenge, expires, 1n]);

  assert.equal(BigInt(secret) * BigInt(w.input.inverse) % FR, 1n);
  const expectedScalars = {
    noteRoot: np.root, revocationRoot: rp.root, nullifier, context: boundContext,
    domain, action: 1n, secret, inverse: w.input.inverse, slot, generation,
    revokedMaxGeneration: f.tree.revoked.get(Number(slot)) ?? 0n,
    gateLow: low, gateHigh: high, challenge, expiresMs: expires,
  };
  for (const key of Object.keys(expectedScalars)) {
    assert.equal(typeof w.input[key], 'string', key);
    assert.match(w.input[key], /^(0|[1-9][0-9]*)$/, key);
  }
  assert.deepEqual(w, {
    input: {
      ...Object.fromEntries(Object.entries(expectedScalars).map(([key, value]) => [key, String(value)])),
      noteBits: np.bits.map(String), noteSiblings: np.siblings.map(String), revocationSiblings: rp.siblings.map(String),
    },
    // Literal order, assembled from expectations, not returned fields or SPEND_PUBLIC.
    publicSignals: [np.root, rp.root, nullifier, boundContext, BigInt(domain), 1n].map(String),
    challenge, expires,
  });
  for (const name of ['noteBits', 'noteSiblings', 'revocationSiblings']) assert.equal(w.input[name].length, DEPTH);
  return w;
}

test('domain_mismatch: passing controls and exact domain diagnostic', async () => {
  await accepts(fixture());
  const f = fixture();
  f.tree.domain = 78n; // Only the tree domain changes; the note remains internally coherent.
  await assert.rejects(() => invoke(f), {message: 'NOTE_DOMAIN_MISMATCH'});
  await accepts(fixture(78n)); // A coherent alternate domain is accepted.
});

test('commitment_binding: isolated secret, slot, generation, commitment and coherent domain changes', async t => {
  await accepts(fixture());
  for (const [field, value] of [['secret', '18'], ['slot', '701'], ['generation', '5'], ['commitment', '1']]) {
    await t.test(field, async () => {
      const f = fixture();
      f.note[field] = value;
      await assert.rejects(() => invoke(f), {message: 'NOTE_COMMITMENT_MISMATCH'});
    });
  }
  await t.test('domain binding after the domain guard passes', async () => {
    const f = fixture();
    f.tree.domain = 78n;
    f.note.domain = '78'; // Both domains agree, but commitment still binds domain 77.
    await assert.rejects(() => invoke(f), {message: 'NOTE_COMMITMENT_MISMATCH'});
    await accepts(fixture(78n));
  });
});

test('selected_prefix: inclusion, exclusion, missing commitment and suffix independence', async t => {
  const full = await accepts(fixture());
  const explicitFull = fixture();
  explicitFull.tree.noteCount = 5;
  assert.deepEqual(await accepts(explicitFull), full);
  const prefix = fixture();
  prefix.tree.noteCount = 3; // Index 2 is the final included note.
  const short = await accepts(prefix);
  assert.notEqual(short.input.noteRoot, full.input.noteRoot);
  const suffix = fixture();
  suffix.tree.noteCount = 3;
  suffix.tree.noteLeaves.splice(3, 2, 999n, 888n, 777n);
  assert.deepEqual(await accepts(suffix), short);
  for (const count of [2, 0]) {
    await t.test('excluded by noteCount ' + count, async () => {
      const f = fixture();
      f.tree.noteCount = count;
      await assert.rejects(() => invoke(f), {message: 'NOTE_NOT_ON_CHAIN'});
    });
  }
  await t.test('commitment absent from full tree', async () => {
    const f = fixture();
    f.tree.noteLeaves[2] = 103n;
    await assert.rejects(() => invoke(f), {message: 'NOTE_NOT_ON_CHAIN'});
  });
});

test('distinct_indices: note insertion 2 and revocation slot 700 use different paths and leaves', async () => {
  const f = fixture();
  const w = await accepts(f);
  assert.deepEqual(w.input.noteBits, Array.from({length: DEPTH}, (_, i) => String(Math.floor(2 / 2 ** i) % 2)));
  const slotBits = Array.from({length: DEPTH}, (_, i) => Math.floor(700 / 2 ** i) % 2);
  assert.notDeepEqual(w.input.noteBits, slotBits.map(String));
  assert.equal(w.input.revokedMaxGeneration, '3'); // Slot 2's leaf is 1.
  assert.equal(foldPath(f.note.commitment, w.input.noteSiblings, w.input.noteBits), BigInt(w.input.noteRoot));
  assert.equal(foldPath(3n, w.input.revocationSiblings, slotBits), BigInt(w.input.revocationRoot));
  assert.notEqual(foldPath(1n, w.input.revocationSiblings, w.input.noteBits), BigInt(w.input.revocationRoot));

  const otherInsertionLeaf = fixture();
  otherInsertionLeaf.tree.revoked.set(2, 2n);
  const other = await accepts(otherInsertionLeaf);
  assert.equal(other.input.revokedMaxGeneration, '3');
  assert.notEqual(other.input.revocationRoot, w.input.revocationRoot);
  const otherSlotLeaf = fixture();
  otherSlotLeaf.tree.revoked.set(700, 2n);
  const changed = await accepts(otherSlotLeaf);
  assert.equal(changed.input.revokedMaxGeneration, '2');
  assert.equal(changed.input.noteRoot, w.input.noteRoot);
  assert.notEqual(changed.input.revocationRoot, w.input.revocationRoot);
});

test('gate_limbs_and_public_order: zero, low maximum, 128-bit boundary and unequal limbs', async t => {
  for (const [label, low, high] of [
    ['zero', 0n, 0n], ['low maximum', limbBase - 1n, 0n],
    ['128-bit boundary', 0n, 1n], ['unequal nonzero limbs', 19n, 37n],
  ]) {
    await t.test(label, () => accepts(fixture(), {...defaultContext, low, high, challenge: 0n}));
  }
});

test('context_binding: each gate limb, challenge and expiry changes context alone', async t => {
  const base = await accepts(fixture());
  for (const [field, value] of [['low', 20n], ['high', 38n], ['challenge', 0n], ['expires', expiry + 1n]]) {
    await t.test(field, async () => {
      const changed = await accepts(fixture(), {...defaultContext, [field]: value});
      assert.notEqual(changed.input.context, base.input.context);
      for (const index of [0, 1, 2, 4, 5]) assert.equal(changed.publicSignals[index], base.publicSignals[index]);
    });
  }
});

test('repeat_calls_preserve_inputs: identical outputs and snapshots on success and rejection', async () => {
  const f = fixture(), context = {...defaultContext, challenge: 0n};
  const options = {challenge: 0n}; // Explicit zero must not take the random fallback.
  const before = structuredClone({f, options});
  const first = await invoke(f, context, options);
  const second = await invoke(f, context, options);
  assert.deepEqual(first, second);
  assert.deepEqual(first, await accepts(f, context));
  assert.deepEqual({f, options}, before);
  for (const [change, message] of [
    [x => { x.tree.domain = 78n; }, 'NOTE_DOMAIN_MISMATCH'],
    [x => { x.note.secret = '18'; }, 'NOTE_COMMITMENT_MISMATCH'],
    [x => { x.tree.noteCount = 2; }, 'NOTE_NOT_ON_CHAIN'],
  ]) {
    const rejected = fixture();
    change(rejected);
    await assert.rejects(() => invoke(rejected, context, options), {message});
  }
  assert.deepEqual(options, before.options);
});
