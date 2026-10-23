// Offline RR-4 / IM-19 regressions for the existing reconstruction boundary.
// Synthetic public events; no RPC clients, chain, keys or proof artifacts are used.
import test from 'node:test';
import assert from 'node:assert/strict';
import {rebuildTreeView} from './chain-witness.mjs';
import {NoteAdded, RevocationLeaf, NoteTree, RevocationState} from './types.mjs';
import {poseidon} from './private-scale.mjs';
import {DEPTH} from './profile-constants.mjs';

const address = n => '0x' + n.toString(16).padStart(64, '0');
const packageId = address(1), controlId = address(2), treeId = address(3);
const revocationId = address(4), otherShow = address(5), domain = 77n;
const sourceName = 'offline-synthetic-public-events';
const H = await poseidon();

// Deliberately dense bottom-up folding, independent of SparseTree/noteTreeOf/
// revocationTreeOf. The circomlibjs Poseidon primitive and DEPTH are shared with
// the client: this is a structural cross-check, NOT independent cryptography.
function denseRoot(entries) {
  let level = Array(2 ** DEPTH).fill(0n);
  for (const [index, value] of entries) {
    assert.ok(Number.isInteger(index) && index >= 0 && index < level.length);
    level[index] = BigInt(value);
  }
  while (level.length > 1) {
    const parents = [];
    for (let i = 0; i < level.length; i += 2) parents.push(H([level[i], level[i + 1]]));
    level = parents;
  }
  return level[0];
}

const leaves = [101n, 102n, 103n, 104n, 105n];
const emptyRoot = denseRoot([]);
const noteRoots = leaves.map((_, i) => denseRoot(leaves.slice(0, i + 1).map((v, j) => [j, v])));
// Genuine increasing-generation history, then a different slot. Each event's
// root reflects its chronological prefix, even when tests reorder delivery.
const revocationHistory = [[5, 1n], [5, 3n], [700, 9n]];
const revocationRoots = [
  denseRoot([[5, 1n]]),
  denseRoot([[5, 3n]]),
  denseRoot([[5, 3n], [700, 9n]]),
];

function makeFixture({empty = false} = {}) {
  const notes = empty ? [] : leaves.map((commitment, index) => ({
    show: controlId, index: String(index), commitment: String(commitment), root: String(noteRoots[index]),
  }));
  const revocations = empty ? [] : revocationHistory.map(([slot, generation], i) => ({
    show: controlId, slot: String(slot), generation: String(generation), root: String(revocationRoots[i]),
  }));
  // Injected parsed-field projections, NOT a test of object BCS decoding.
  const tree = {root: String(empty ? emptyRoot : noteRoots.at(-1)), leaf_count: String(notes.length)};
  const rev = {root: String(empty ? emptyRoot : revocationRoots.at(-1)), revocations: String(revocations.length)};
  const eventCalls = [];
  const source = {
    name: sourceName,
    async events(pkg, name) {
      assert.equal(pkg, packageId, 'only the named package is queried');
      eventCalls.push(name);
      assert.ok(name === 'NoteAdded' || name === 'RevocationLeaf', 'only public tree events are queried');
      const [schema, records] = name === 'NoteAdded' ? [NoteAdded, notes] : [RevocationLeaf, revocations];
      return records.map(record => ({bcs: schema.serialize(record).toBytes()}));
    },
  };
  return {notes, revocations, tree, rev, source, eventCalls, empty};
}

function makeReadSpy(fixture) {
  const calls = [];
  return {
    calls,
    async getFields(id, schema) {
      calls.push([id, schema]);
      if (id === treeId && schema === NoteTree) return {...fixture.tree};
      if (id === revocationId && schema === RevocationState) return {...fixture.rev};
      assert.fail('unexpected object/schema read: ' + id);
    },
  };
}

function reconstruct(fixture, spy) {
  return rebuildTreeView({source: fixture.source, packageId, controlId, treeId, revocationId,
    domain, getFields: spy.getFields});
}

const allowedReads = [[treeId, NoteTree], [revocationId, RevocationState]];
async function accepts(fixture) {
  const spy = makeReadSpy(fixture);
  assert.deepEqual(await reconstruct(fixture, spy), {
    domain, noteLeaves: fixture.empty ? [] : leaves,
    revoked: fixture.empty ? new Map() : new Map([[5, 3n], [700, 9n]]),
    source: sourceName, noteEvents: fixture.empty ? 0 : 5, revocationEvents: fixture.empty ? 0 : 3,
  });
  // These two projections are the entire permitted object-read surface: no
  // InventoryPage or inventory vectors can be fetched through this injection.
  assert.deepEqual(spy.calls, allowedReads);
  assert.deepEqual(fixture.eventCalls, ['NoteAdded', 'RevocationLeaf']);
}

async function rejectsChange(change, diagnostic, {early = false} = {}) {
  const fixture = makeFixture();
  change(fixture);
  const spy = makeReadSpy(fixture);
  await assert.rejects(() => reconstruct(fixture, spy), {message: diagnostic});
  assert.deepEqual(spy.calls, early ? [] : allowedReads);
  assert.deepEqual(fixture.eventCalls, early ? ['NoteAdded'] : ['NoteAdded', 'RevocationLeaf']);
}

test('dense_fixture_matches_existing_move_known_answers', () => {
  // Copied from sui/tests/root_math_tests.move; originally generated with the
  // SAME circomlibjs primitive. No Move execution is claimed by this check.
  assert.equal(emptyRoot, 12413880268183407374852357075976609371175688755676981206018884971008854919922n);
  assert.deepEqual(noteRoots, [
    13435157595452499831328342371188872370195603936081551072324668619215518361592n,
    11894166152725933167799962082781238356992134909095608370740726318210113531042n,
    15198915676663620714989452771055542096236157964614070370198930474590801349403n,
    12497660747801460804045916613486574742363061972261539687119204602169762583870n,
    17162178407478046736786119174946953698818562625526652776447028614558469203139n,
  ]);
  assert.equal(revocationRoots[1], 13244524416568403798025217453455705458746775544182100578009770988457660307114n);
  assert.equal(revocationRoots[2], 3152138033071002246062408124070017822973530135719734160069333386947667197940n);
});

test('empty_tree', () => accepts(makeFixture({empty: true})));
test('populated_tree', () => accepts(makeFixture()));
test('reordered_notes', async () => {
  const fixture = makeFixture();
  const ordered = [...fixture.notes];
  fixture.notes.splice(0, 5, ...[4, 1, 3, 0, 2].map(i => ordered[i]));
  await accepts(fixture);
});
test('unrelated_show_events', async () => {
  const fixture = makeFixture();
  // The foreign note index would fail contiguity; the foreign revocation would
  // change both the maximum and count if filtering did not precede rebuilding.
  fixture.notes.splice(2, 0, {show: otherShow, index: '999', commitment: '999', root: '1'});
  fixture.revocations.splice(1, 0, {show: otherShow, slot: '5', generation: '99', root: '1'});
  await accepts(fixture);
});
test('maximum_revoked_generation', async () => {
  const fixture = makeFixture();
  const [low, high, other] = fixture.revocations;
  fixture.revocations.splice(0, 3, high, other, low);
  await accepts(fixture);
});

test('missing_note_index', () => rejectsChange(f => f.notes.splice(2, 1), 'NOTE_EVENT_GAP:2', {early: true}));
test('duplicate_note_index', () => rejectsChange(f => f.notes.splice(2, 0, {...f.notes[1]}), 'NOTE_EVENT_GAP:2', {early: true}));
test('corrupt_intermediate_note_root', () => rejectsChange(f => {
  // Keep commitments and the final object root/count intact.
  f.notes[1].root = String(BigInt(f.notes[1].root) + 1n);
}, 'NOTE_EVENT_ROOT_MISMATCH:1'));
test('note_root_mismatch', () => rejectsChange(f => {
  f.tree.root = String(BigInt(f.tree.root) + 1n);
}, 'REBUILT_NOTE_ROOT_MISMATCH:' + sourceName));
test('note_count_mismatch', () => rejectsChange(f => {
  f.tree.leaf_count = String(Number(f.tree.leaf_count) + 1);
}, 'REBUILT_NOTE_ROOT_MISMATCH:' + sourceName));
test('revocation_root_mismatch', () => rejectsChange(f => {
  f.rev.root = String(BigInt(f.rev.root) + 1n);
}, 'REBUILT_REVOCATION_ROOT_MISMATCH:' + sourceName));
test('revocation_count_mismatch', () => rejectsChange(f => {
  f.rev.revocations = String(Number(f.rev.revocations) + 1);
}, 'REBUILT_REVOCATION_ROOT_MISMATCH:' + sourceName));
test('omitted_maximal_revocation', () => rejectsChange(f => {
  f.revocations.splice(1, 1); // slot 5 now reconstructs to generation 1, not 3
}, 'REBUILT_REVOCATION_ROOT_MISMATCH:' + sourceName));
test('omitted_nonmaximal_revocation', () => rejectsChange(f => {
  f.revocations.splice(0, 1); // same final root, fewer events: the count must catch it
}, 'REBUILT_REVOCATION_ROOT_MISMATCH:' + sourceName));
test('duplicated_revocation', () => rejectsChange(f => {
  f.revocations.push({...f.revocations[0]}); // same final root, one extra event
}, 'REBUILT_REVOCATION_ROOT_MISMATCH:' + sourceName));
