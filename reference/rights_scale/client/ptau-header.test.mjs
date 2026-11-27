// Source-informed characterization of ptauPower's existing reads only.
// Synthetic readable buffers are not valid PTAU files or cryptographic material.
// Powers below probe serialization, never ceremony parameters or capacity policy.
import test from 'node:test';
import assert from 'node:assert/strict';
import {ptauPower} from './zk-helpers.mjs';

const hex = value => Buffer.from(value, 'hex');
// Field bytes are literal LE vectors; no encoder or parser supplies expectations.
const preamble = (count = '01000000', version = '01000000') => Buffer.concat([
  Buffer.from('ptau'), hex(version), hex(count),
]);
const section = (id, size, body = Buffer.alloc(0)) => Buffer.concat([
  hex(id), hex(size), body,
]);
const header = (power = '04030201') => section(
  '01000000', '0b00000000000000',
  Buffer.concat([hex('03000000'), hex('a1b2c3'), hex(power)]),
);
const control = () => Buffer.concat([preamble(), header()]);

for (const [length, n8, size] of [
  [1, '01000000', '0900000000000000'],
  [3, '03000000', '0b00000000000000'],
  [32, '20000000', '2800000000000000'],
]) {
  test(`source-informed: ptauPower first header skips ${length} opaque modulus bytes`, () => {
    const bytes = Buffer.concat([
      preamble(), section('01000000', size, Buffer.concat([
        hex(n8), Buffer.alloc(length, 0xa5), hex('04030201'),
      ])),
    ]);
    assert.equal(ptauPower(bytes), 0x01020304);
  });
}

for (const [label, power, expected] of [
  ['zero', '00000000', 0],
  ['high bit set', '03020180', 0x80010203],
  ['unsigned maximum', 'ffffffff', 0xffffffff],
]) {
  test(`source-informed: ptauPower extracts unsigned LE power with ${label}`, () => {
    assert.equal(ptauPower(Buffer.concat([preamble(), header(power)])), expected);
  });
}

test('source-informed: ptauPower reaches a later header past distinct and empty sections', () => {
  const bytes = Buffer.concat([
    preamble('04000000'),
    section('02000000', '0300000000000000', hex('aabbcc')),
    section('03000000', '0000000000000000'),
    section('04000000', '0500000000000000', hex('1020304050')),
    header(),
  ]);
  assert.equal(ptauPower(bytes), 0x01020304);
});

test('source-informed: ptauPower reads multiple LE size bytes when skipping 257 bytes', () => {
  const bytes = Buffer.concat([
    preamble('02000000'),
    section('02000000', '0101000000000000', Buffer.alloc(257, 0xa5)),
    header(),
  ]);
  assert.equal(ptauPower(bytes), 0x01020304);
});

test('source-informed: ptauPower skipped-section size controls traversal over a decoy header', () => {
  const decoy = header('0d0c0b0a'); // 23 bytes, opaque payload of section 2.
  const bytes = Buffer.concat([
    preamble('02000000'), section('02000000', '1700000000000000', decoy), header(),
  ]);
  assert.equal(ptauPower(bytes), 0x01020304);
  const zeroSize = Buffer.from(bytes);
  zeroSize.fill(0, 16, 24); // Same payload, now declared outside skipped section 2.
  assert.equal(ptauPower(zeroSize), 0x0a0b0c0d);
});

for (const magic of ['pTau', 'xxxx', '\0\0\0\0']) {
  test(`source-informed: ptauPower wrong magic ${JSON.stringify(magic)} is PTAU_FORMAT`, () => {
    const bytes = control();
    assert.equal(ptauPower(bytes), 0x01020304);
    Buffer.from(magic).copy(bytes, 0);
    assert.throws(() => ptauPower(bytes), {message: 'PTAU_FORMAT'});
  });
}
for (const length of [0, 1, 2, 3]) {
  test(`source-informed: ptauPower ${length}-byte magic prefix is PTAU_FORMAT`, () => {
    const bytes = control();
    assert.equal(ptauPower(bytes), 0x01020304);
    assert.throws(() => ptauPower(bytes.subarray(0, length)), {message: 'PTAU_FORMAT'});
  });
}

test('source-informed: ptauPower zero declared sections is PTAU_HEADER_MISSING', () => {
  assert.throws(() => ptauPower(preamble('00000000')), {message: 'PTAU_HEADER_MISSING'});
});
test('source-informed: ptauPower complete non-header traversal is PTAU_HEADER_MISSING', () => {
  const bytes = Buffer.concat([
    preamble('02000000'),
    section('02000000', '0300000000000000', hex('aabbcc')),
    section('03000000', '0000000000000000'),
  ]);
  assert.throws(() => ptauPower(bytes), {message: 'PTAU_HEADER_MISSING'});
});
test('source-informed: ptauPower does not search beyond the declared section count', () => {
  const bytes = control();
  assert.equal(ptauPower(bytes), 0x01020304);
  bytes.fill(0, 8, 12);
  assert.throws(() => ptauPower(bytes), {message: 'PTAU_HEADER_MISSING'});
});

// Layout of control(): count [8,12), ID [12,16), size [16,24),
// n8 [24,28), opaque modulus [28,31), power [31,35).
for (const [field, cut] of [
  ['section count', 11], ['section ID', 15], ['eight-byte section size', 23],
  ['header n8', 27], ['power after incomplete declared modulus span', 30],
  ['power absent after modulus', 31], ['power partially present', 34],
]) {
  test(`source-informed: ptauPower truncated ${field} raises numeric-read RangeError`, () => {
    const bytes = control();
    assert.equal(ptauPower(bytes), 0x01020304);
    assert.throws(() => ptauPower(bytes.subarray(0, cut)), error => {
      assert.ok(error instanceof RangeError);
      assert.equal(error.code, 'ERR_OUT_OF_RANGE');
      return true;
    });
  });
}

// Class B: these permissive reads are observed behavior, not a format contract.
for (const version of ['00000000', 'ffffffff']) {
  test(`source-informed: ptauPower characterization ignores version bytes ${version}`, () => {
    assert.equal(ptauPower(control()), 0x01020304);
    assert.equal(ptauPower(Buffer.concat([preamble('01000000', version), header()])), 0x01020304);
  });
}
for (const [label, size] of [
  ['zero', '0000000000000000'], ['understated', '0a00000000000000'],
  ['overstated', '0001000000000000'],
]) {
  test(`source-informed: ptauPower characterization ignores ${label} header-section size`, () => {
    const bytes = control();
    assert.equal(ptauPower(bytes), 0x01020304);
    hex(size).copy(bytes, 16);
    assert.equal(ptauPower(bytes), 0x01020304);
  });
}
test('source-informed: ptauPower characterization ignores trailing garbage', () => {
  const bytes = control();
  assert.equal(ptauPower(bytes), 0x01020304);
  assert.equal(ptauPower(Buffer.concat([bytes, hex('deadbeef00ff')])), 0x01020304);
});
test('source-informed: ptauPower characterization returns the first of two headers', () => {
  const bytes = Buffer.concat([preamble('02000000'), header(), header('0d0c0b0a')]);
  assert.equal(ptauPower(bytes), 0x01020304);
});
test('source-informed: ptauPower characterization leaves later declared sections unread', () => {
  const bytes = Buffer.concat([preamble('02000000'), header(), header('0d0c0b0a')]);
  assert.equal(ptauPower(bytes), 0x01020304);
  // Keep one byte of the second section ID: no valid numeric read is possible.
  assert.equal(ptauPower(bytes.subarray(0, 36)), 0x01020304);
});
