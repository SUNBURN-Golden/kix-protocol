// Source-informed RR-4 / IM-19 reader coverage. Synthetic public bytes only;
// no chain, proofs, credentials, event decoding or retention claim.
import test from 'node:test';
import assert from 'node:assert/strict';
import {syncBuiltinESMExports} from 'node:module';
import http from 'node:http';
import https from 'node:https';
import net from 'node:net';
import tls from 'node:tls';
import http2 from 'node:http2';
import dgram from 'node:dgram';

test('offline event sources', {concurrency: false}, async t => {
  const unexpected = [];
  const deny = name => () => {
    unexpected.push(name);
    throw Error('OFFLINE_UNEXPECTED_CALL:' + name);
  };
  // Install before importing the SDK/readers, including named builtin exports.
  for (const [target, methods] of [
    [globalThis, ['fetch', 'WebSocket']],
    [http, ['request', 'get']], [https, ['request', 'get']],
    [net, ['connect', 'createConnection']], [net.Socket.prototype, ['connect']],
    [tls, ['connect']], [http2, ['connect']], [dgram, ['createSocket']],
  ]) {
    for (const method of methods) t.mock.method(target, method, deny(method));
  }
  syncBuiltinESMExports();
  t.after(() => {
    t.mock.restoreAll();
    syncBuiltinESMExports();
    assert.deepEqual(unexpected, [], 'no network or retry timer attempts');
  });

  const {SuiJsonRpcClient} = await import('@mysten/sui/jsonRpc');
  const {jsonRpcEventSource, checkpointEventSource} = await import('./chain-witness.mjs');
  const {NoteAdded, RevocationLeaf} = await import('./types.mjs');
  const address = n => '0x' + n.toString(16).padStart(64, '0');
  const pkg = '0xa', paddedPkg = address(10), show = address(20);
  const type = (name, packageId = pkg, module = 'rights_scale') => `${packageId}::${module}::${name}`;
  const bytes = {
    a: Buffer.from(NoteAdded.serialize({show, index: 0, commitment: 255n, root: 256n}).toBytes()),
    b: Buffer.from(NoteAdded.serialize({show, index: 1, commitment: 65536n, root: 257n}).toBytes()),
    c: Buffer.from(NoteAdded.serialize({show, index: 2, commitment: 258n, root: 259n}).toBytes()),
    d: Buffer.from(NoteAdded.serialize({show, index: 3, commitment: 260n, root: 261n}).toBytes()),
    r: Buffer.from(RevocationLeaf.serialize({show, slot: 7, generation: 1, root: 262n}).toBytes()),
    s: Buffer.from(RevocationLeaf.serialize({show, slot: 7, generation: 2, root: 263n}).toBytes()),
    u: Buffer.from(RevocationLeaf.serialize({show, slot: 8, generation: 3, root: 264n}).toBytes()),
  };
  const record = (key, digest, seq) => ({bcs: bytes[key], digest, seq});
  const project = records => records.map(({bcs, digest, seq}) => ({bcs, digest, seq}));
  const wire = ({bcs, digest, seq}) => ({bcs: bcs.toString('base64'), id: {txDigest: digest, eventSeq: String(seq)}});
  const page = (records, hasNextPage = false, nextCursor = null) => ({data: records.map(wire), hasNextPage, nextCursor});
  const request = (name, cursor = null, packageId = pkg) => ({
    query: {MoveEventType: type(name, packageId)}, cursor, limit: 50, order: 'ascending',
  });
  const step = (name, cursor, response, packageId = pkg) => ({request: request(name, cursor, packageId), response});
  const cursor1 = {txDigest: 'cursor-one', eventSeq: '12'};
  const cursor2 = {txDigest: 'cursor-two', eventSeq: '42'};
  const ignoredCursor = {txDigest: 'terminal-must-not-be-read', eventSeq: '99'};

  function scope(t) {
    // transient() catches assertion failures too. Fail immediately if it tries
    // to retry a broken fixture; never wait or alter the reader/retry policy.
    t.mock.method(globalThis, 'setTimeout', deny('retry timer'));
  }
  function track(t, source, name) {
    assert.equal(source.name, name);
    assert.equal(source.retries(), 0);
    t.after(() => assert.equal(source.retries(), 0, name + ' had no retries'));
    return source;
  }
  const jsonSource = t => track(t, jsonRpcEventSource('http://127.0.0.1:1'), 'jsonrpc-queryEvents');
  const checkpointSource = (t, ledgerService) => track(t, checkpointEventSource({ledgerService}), 'grpc-checkpoint-scan');

  function stubJson(t, scripts) {
    const clients = new Map();
    const calls = [];
    t.mock.method(SuiJsonRpcClient.prototype, 'queryEvents', async function (args) {
      if (!clients.has(this)) {
        assert.ok(clients.size < scripts.length, 'unexpected SDK client');
        clients.set(this, {script: scripts[clients.size], index: 0});
      }
      const state = clients.get(this);
      const expected = state.script[state.index++];
      calls.push(args);
      assert.ok(expected, 'unexpected queryEvents call');
      assert.deepEqual(args, expected.request);
      return expected.response;
    });
    t.after(() => {
      assert.equal(clients.size, scripts.length);
      for (const {script, index} of clients.values()) assert.equal(index, script.length, 'all pages consumed exactly once');
    });
    return calls;
  }

  const event = (eventType, bcs) => ({eventType, contents: {value: Uint8Array.from(bcs)}});
  // Explicit expected records do not use the filtering/sequencing algorithm.
  const notes = [record('a', 'tx-a', 1), record('b', 'tx-a', 6), record('c', 'tx-b', 0), record('d', 'tx-c', 1)];
  const revocations = [record('r', 'tx-a', 3), record('s', 'tx-b', 1), record('u', 'tx-c', 0)];
  function history() {
    return [
      [], // checkpoint zero exists and is empty
      [
        {digest: 'tx-a', events: {events: [
          event(type('Other'), [0, 255]),
          event(type('NoteAdded'), bytes.a),
          event(type('NoteAdded', '0xb'), bytes.d),
          event(type('RevocationLeaf'), bytes.r),
          event(type('NoteAdded', pkg, 'another_module'), bytes.d),
          event(type('NoteAddedExtra'), bytes.d),
          event(type('NoteAdded', paddedPkg), bytes.b),
          event(type('RevocationLeafExtra'), bytes.u),
          event(type('RevocationLeaf', '0xb'), bytes.u),
          event(type('RevocationLeaf', pkg, 'another_module'), bytes.u),
        ]}},
        {digest: 'tx-without-events'},
        {digest: 'tx-b', events: {events: [event(type('NoteAdded'), bytes.c), event(type('RevocationLeaf', paddedPkg), bytes.s)]}},
      ],
      [], // an empty checkpoint between populated ones
      [{digest: 'tx-c', events: {events: [event(type('RevocationLeaf'), bytes.u), event(type('NoteAdded'), bytes.d)]}}],
    ];
  }
  function ledger(checkpoints, initialHeight = checkpoints.length - 1) {
    let height = initialHeight;
    const calls = [], infoCalls = [];
    const ledgerService = {
      async getServiceInfo(args) {
        assert.deepEqual(args, {});
        infoCalls.push(height);
        return {response: {checkpointHeight: BigInt(height)}};
      },
      async getCheckpoint(args) {
        const n = calls.length;
        assert.deepEqual(args, {
          checkpointId: {oneofKind: 'sequenceNumber', sequenceNumber: BigInt(n)},
          readMask: {paths: ['transactions.digest', 'transactions.events']},
        });
        assert.ok(n <= height && n < checkpoints.length, 'only advertised checkpoints');
        calls.push(n);
        return {response: {checkpoint: {transactions: checkpoints[n]}}};
      },
    };
    return {ledgerService, calls, infoCalls, advance: n => { height = n; }};
  }

  await t.test('jsonrpc_pages_preserve_records', async t => {
    scope(t);
    const expectedNotes = [record('b', 'opaque-digest-z', 9007199254740991), record('a', 'opaque-digest-a', 17), record('c', 'opaque-digest-a', 0)];
    const expectedRevocations = [record('s', 'opaque-rev-z', 8), record('r', 'opaque-rev-a', 2)];
    stubJson(t, [[
      step('NoteAdded', null, page(expectedNotes.slice(0, 1), true, cursor1)),
      step('NoteAdded', cursor1, page([], true, cursor2)),
      step('NoteAdded', cursor2, page(expectedNotes.slice(1), false, ignoredCursor)),
      step('RevocationLeaf', null, page(expectedRevocations.slice(0, 1), true, cursor1)),
      step('RevocationLeaf', cursor1, page(expectedRevocations.slice(1), false, ignoredCursor)),
    ]]);
    const source = jsonSource(t);
    assert.deepEqual(await source.events(pkg, 'NoteAdded'), expectedNotes);
    assert.deepEqual(await source.events(pkg, 'RevocationLeaf'), expectedRevocations);
  });

  await t.test('jsonrpc_empty_result', async t => {
    scope(t);
    stubJson(t, [[step('NoteAdded', null, page([], false, ignoredCursor))]]);
    assert.deepEqual(await jsonSource(t).events(pkg, 'NoteAdded'), []);
  });

  await t.test('checkpoint_traverses_advertised_height', async t => {
    scope(t);
    const fake = ledger(history(), 0);
    const source = checkpointSource(t, fake.ledgerService);
    assert.deepEqual(await source.events(pkg, 'NoteAdded'), []);
    assert.deepEqual(fake.calls, [0]);
    fake.advance(3);
    assert.deepEqual(project(await source.events(pkg, 'NoteAdded')), notes);
    assert.deepEqual(fake.calls, [0, 1, 2, 3]);
    assert.deepEqual(fake.infoCalls, [0, 3]);
  });

  await t.test('checkpoint_filters_without_renumbering', async t => {
    scope(t);
    const fake = ledger(history());
    const source = checkpointSource(t, fake.ledgerService);
    assert.deepEqual(await source.events(paddedPkg, 'NoteAdded'), notes.map((r, i) => ({
      type: type('NoteAdded', i === 1 ? paddedPkg : pkg), ...r,
    })));
    assert.deepEqual(await source.events(pkg, 'RevocationLeaf'), revocations.map((r, i) => ({
      type: type('RevocationLeaf', i === 1 ? paddedPkg : pkg), ...r,
    })));
    assert.deepEqual(fake.calls, [0, 1, 2, 3]);
    assert.deepEqual(fake.infoCalls, [3, 3]);
  });

  await t.test('checkpoint_reuses_history_and_appends_once', async t => {
    scope(t);
    const checkpoints = history().slice(0, 3);
    const fake = ledger(checkpoints, 0);
    const source = checkpointSource(t, fake.ledgerService);
    assert.deepEqual(await source.events(pkg, 'RevocationLeaf'), []);
    fake.advance(2);
    assert.deepEqual(project(await source.events(pkg, 'NoteAdded')), notes.slice(0, 3));
    assert.deepEqual(project(await source.events(pkg, 'RevocationLeaf')), revocations.slice(0, 2));
    assert.deepEqual(project(await source.events(pkg, 'NoteAdded')), notes.slice(0, 3));
    assert.deepEqual(fake.calls, [0, 1, 2]);
    checkpoints.push(history()[3]);
    fake.advance(3);
    assert.deepEqual(project(await source.events(pkg, 'RevocationLeaf')), revocations);
    assert.deepEqual(project(await source.events(pkg, 'NoteAdded')), notes);
    assert.deepEqual(project(await source.events(pkg, 'RevocationLeaf')), revocations);
    assert.deepEqual(fake.calls, [0, 1, 2, 3]);
    assert.deepEqual(fake.infoCalls, [0, 2, 2, 2, 3, 3, 3]);
  });

  await t.test('sources_project_equivalent_histories', async t => {
    scope(t);
    stubJson(t, [[
      step('NoteAdded', null, page(notes.slice(0, 2), true, cursor1)),
      step('NoteAdded', cursor1, page(notes.slice(2, 3), true, cursor2)),
      step('NoteAdded', cursor2, page(notes.slice(3), false, ignoredCursor)),
      step('RevocationLeaf', null, page(revocations.slice(0, 1), true, cursor1)),
      step('RevocationLeaf', cursor1, page(revocations.slice(1), false, ignoredCursor)),
    ]]);
    const fake = ledger(history());
    const rpc = jsonSource(t), checkpoints = checkpointSource(t, fake.ledgerService);
    for (const [name, expected] of [['NoteAdded', notes], ['RevocationLeaf', revocations]]) {
      const a = project(await rpc.events(pkg, name));
      const b = project(await checkpoints.events(pkg, name));
      assert.deepEqual(a, expected);
      assert.deepEqual(b, expected);
      assert.deepEqual(a, b); // no sorting, deduplication or byte normalization
    }
    assert.deepEqual(fake.calls, [0, 1, 2, 3]);
  });

  await t.test('source_instances_are_isolated', async t => {
    scope(t);
    const otherPkg = '0xf';
    const first = [record('a', 'instance-a', 0)], second = [record('s', 'instance-b', 0)];
    stubJson(t, [
      [step('NoteAdded', null, page(first)), step('NoteAdded', null, page(first))],
      [step('RevocationLeaf', null, page(second), otherPkg), step('RevocationLeaf', null, page(second), otherPkg)],
    ]);
    const rpcA = jsonSource(t), rpcB = jsonSource(t);
    const historyA = [[{digest: 'instance-a', events: {events: [event(type('NoteAdded'), bytes.a)]}}]];
    const fakeA = ledger(historyA);
    const fakeB = ledger([[{digest: 'instance-b', events: {events: [event(type('RevocationLeaf', otherPkg), bytes.s)]}}]]);
    const cpA = checkpointSource(t, fakeA.ledgerService), cpB = checkpointSource(t, fakeB.ledgerService);
    assert.deepEqual(await rpcA.events(pkg, 'NoteAdded'), first);
    assert.deepEqual(project(await cpA.events(pkg, 'NoteAdded')), first);
    assert.deepEqual(await rpcB.events(otherPkg, 'RevocationLeaf'), second);
    assert.deepEqual(project(await cpB.events(otherPkg, 'RevocationLeaf')), second);
    assert.deepEqual(await cpA.events(otherPkg, 'RevocationLeaf'), []);
    assert.deepEqual(await cpB.events(pkg, 'NoteAdded'), []);
    historyA.push([{digest: 'instance-a-new', events: {events: [event(type('NoteAdded'), bytes.d)]}}]);
    fakeA.advance(1);
    assert.deepEqual(project(await cpB.events(otherPkg, 'RevocationLeaf')), second);
    assert.deepEqual(project(await cpA.events(pkg, 'NoteAdded')), [...first, record('d', 'instance-a-new', 0)]);
    assert.deepEqual(await rpcA.events(pkg, 'NoteAdded'), first);
    assert.deepEqual(await rpcB.events(otherPkg, 'RevocationLeaf'), second);
    assert.deepEqual(fakeA.calls, [0, 1]);
    assert.deepEqual(fakeB.calls, [0]);
    assert.deepEqual(fakeA.infoCalls, [0, 0, 1]);
    assert.deepEqual(fakeB.infoCalls, [0, 0, 0]);
  });
});
