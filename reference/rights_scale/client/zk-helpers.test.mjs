// Source-informed encoding characterization of fabricated public coordinates.
// No curve membership, proof validity, usable key, independent cryptographic
// verification, or production-readiness claim. No artifacts or dependencies.
import test from 'node:test';
import assert from 'node:assert/strict';
import {little, proofBytes, vkBytes} from './zk-helpers.mjs';

// Coordinate field, deliberately distinct from the scalar modulus FR.
const FQ = 21888242871839275222246405745257275088696311157297823662689037894645226208583n;
const HALF = (FQ - 1n) / 2n;
// Independently obtained using Python int.to_bytes(32, 'little'), then pinned.
const FQ_MAX_BYTES = Buffer.from('46fd7cd8168c203c8dca7168916a81975d588181b64550b829a031e1724e6430', 'hex');

// Only pad literal expected hex bytes; never derive expectations with an encoder
// under test, coordinate shifts, or a copy of the sign-selection algorithm.
const word = (prefix, last = '00') => Buffer.from(prefix.padEnd(62, '0') + last, 'hex');
const expectedProof = () => Buffer.concat([
  word('0102'), word('0304'), word('0506'), word('0708'),
]);
const expectedKey = (count = 2, countHex = '0200000000000000') => Buffer.concat([
  word('0102'), word('0304'), word('0506'), word('0708'), word('090a'),
  word('0b0c'), word('0d0e'), Buffer.from(countHex, 'hex'),
  ...Array.from({length: count}, (_, i) => word(i % 2 ? '1112' : '0f10')),
]);

function syntheticProof() {
  return {
    pi_a: ['513', '2', '1'],
    pi_b: [['1027', '1541'], ['3', '4'], ['1', '0']],
    pi_c: ['2055', '5', '1'],
  };
}

function syntheticKey(nPublic = 1) {
  return {
    protocol: 'groth16', curve: 'bn128', nPublic,
    vk_alpha_1: ['513', '2', '1'],
    vk_beta_2: [['1027', '1541'], ['3', '4'], ['1', '0']],
    vk_gamma_2: [['2055', '2569'], ['5', '6'], ['1', '0']],
    vk_delta_2: [['3083', '3597'], ['7', '8'], ['1', '0']],
    IC: Array.from({length: nPublic + 1}, (_, i) => [i % 2 ? '4625' : '4111', '9', '1']),
  };
}

for (const size of [8, 32]) {
  for (const [label, value, expected] of [
    ['zero', 0n, Buffer.alloc(size)],
    ['one', 1n, Buffer.from('01' + '00'.repeat(size - 1), 'hex')],
    ['255', 255n, Buffer.from('ff' + '00'.repeat(size - 1), 'hex')],
    ['256', 256n, Buffer.from('0001' + '00'.repeat(size - 2), 'hex')],
    ['unsigned maximum', 2n ** BigInt(8 * size) - 1n, Buffer.alloc(size, 0xff)],
  ]) {
    test(`little: ${size} bytes ${label}`, () => {
      const actual = little(value, size);
      assert.equal(actual.length, size);
      assert.deepEqual(actual, expected);
    });
  }
  for (const [label, value] of [['negative one', -1n], ['first overflow', 2n ** BigInt(8 * size)]]) {
    test(`little: ${size} bytes rejects ${label}`, () => {
      assert.throws(() => little(value, size), {message: 'INTEGER_ENCODING_RANGE'});
    });
  }
}

for (const [size, value, hex] of [
  [8, 0x0123456789abcdefn, 'efcdab8967452301'],
  [32, 0x0123456789abcdeffedcba987654321000112233445566778899aabbccddeeffn,
    'ffeeddccbbaa998877665544332211001032547698badcfeefcdab8967452301'],
]) {
  test(`little: asymmetric full-width ${size}-byte order`, () => {
    assert.deepEqual(little(value, size), Buffer.from(hex, 'hex'));
  });
}
test('little: omitted width is 32 bytes', () => {
  assert.deepEqual(little(256n), word('0001'));
});

test('source-informed: proof A / B.x0 / B.x1 / C order and widths', () => {
  const bytes = proofBytes(syntheticProof());
  assert.equal(bytes.length, 128);
  assert.deepEqual(bytes, expectedProof());
  for (const [offset, hex] of [[0, '0102'], [32, '0304'], [64, '0506'], [96, '0708']]) {
    assert.deepEqual(bytes.subarray(offset, offset + 32), word(hex));
  }
});

for (const [label, y, sign] of [
  ['zero', 0n, 0x00], ['half', HALF, 0x00], ['half plus one', HALF + 1n, 0x80],
]) {
  for (const [component, offset] of [['pi_a', 0], ['pi_c', 96]]) {
    test(`source-informed: G1 ${component} sign at ${label}`, () => {
      const proof = syntheticProof(), expected = expectedProof();
      proof[component][1] = String(y);
      expected[offset + 31] = sign;
      assert.deepEqual(proofBytes(proof), expected);
    });
  }
}
for (const [label, y0, y1, sign] of [
  ['y1 half dominates high y0', FQ - 1n, HALF, 0x00],
  ['y1 half plus one dominates low y0', 0n, HALF + 1n, 0x80],
  ['tie y1 zero / y0 zero', 0n, 0n, 0x00],
  ['tie y1 zero / y0 half', HALF, 0n, 0x00],
  ['tie y1 zero / y0 half plus one', HALF + 1n, 0n, 0x80],
]) {
  test(`source-informed: G2 sign ${label}`, () => {
    const proof = syntheticProof(), expected = expectedProof();
    proof.pi_b[1] = [String(y0), String(y1)];
    expected[95] = sign;
    assert.deepEqual(proofBytes(proof), expected);
  });
}
test('source-informed: sign bits preserve high canonical x bytes in G1 and G2', () => {
  const proof = syntheticProof();
  proof.pi_a = [String(FQ - 1n), String(FQ - 1n), '1'];
  proof.pi_b = [[String(FQ - 1n), String(FQ - 1n)], ['0', String(FQ - 1n)], ['1', '0']];
  proof.pi_c = [String(FQ - 1n), String(HALF), '1'];
  const signedMax = Buffer.from('46fd7cd8168c203c8dca7168916a81975d588181b64550b829a031e1724e64b0', 'hex');
  assert.deepEqual(proofBytes(proof), Buffer.concat([
    signedMax, FQ_MAX_BYTES, signedMax, FQ_MAX_BYTES,
  ]));
});

for (const [count, countHex] of [[1, '0100000000000000'], [2, '0200000000000000'], [256, '0001000000000000']]) {
  test(`source-informed: VK component order and eight-byte IC count ${count}`, () => {
    // Synthetic serialization counts only; these are not profile policy values.
    const bytes = vkBytes(syntheticKey(count - 1));
    assert.equal(bytes.length, 232 + 32 * count);
    assert.deepEqual(bytes, expectedKey(count, countHex));
    assert.deepEqual(bytes.subarray(224, 232), Buffer.from(countHex, 'hex'));
  });
}
test('source-informed: VK sign flags stay in their own compressed points', () => {
  const key = syntheticKey(), expected = expectedKey();
  key.vk_alpha_1[1] = String(HALF + 1n);
  key.vk_beta_2[1] = [String(HALF + 1n), '0'];
  key.vk_gamma_2[1] = ['0', String(HALF + 1n)];
  key.vk_delta_2[1] = [String(FQ - 1n), String(HALF)];
  key.IC[1][1] = String(HALF + 1n);
  for (const at of [31, 95, 159, 295]) expected[at] = 0x80;
  assert.deepEqual(vkBytes(key), expected);
});

const pointTargets = [
  [syntheticProof, proofBytes, expectedProof, [
    ['pi_a', p => p.pi_a, 'G1', 0],
    ['pi_b', p => p.pi_b, 'G2', 32],
    ['pi_c', p => p.pi_c, 'G1', 96],
  ]],
  [syntheticKey, vkBytes, expectedKey, [
    ['alpha', k => k.vk_alpha_1, 'G1', 0],
    ['beta', k => k.vk_beta_2, 'G2', 32],
    ['gamma', k => k.vk_gamma_2, 'G2', 96],
    ['delta', k => k.vk_delta_2, 'G2', 160],
    ['IC[0]', k => k.IC[0], 'G1', 232],
    ['IC[1]', k => k.IC[1], 'G1', 264],
  ]],
];

for (const [factory, encode, baseline, targets] of pointTargets) {
  test(`source-informed: ${encode.name} accepts omitted affine coordinates`, () => {
    const value = factory();
    assert.deepEqual(encode(value), baseline()); // explicit 1 / [1,0] control
    for (const [, select] of targets) select(value).pop();
    assert.deepEqual(encode(value), baseline());
  });
  for (const [name, select, kind, offset] of targets) {
    const fields = kind === 'G1'
      ? [['x', [0], offset], ['y', [1], null]]
      : [['x0', [0, 0], offset], ['x1', [0, 1], offset + 32], ['y0', [1, 0], null], ['y1', [1, 1], null]];
    for (const [field, path, byteOffset] of fields) {
      for (const [label, endpoint] of [['zero', 0n], ['FQ minus one', FQ - 1n]]) {
        test(`source-informed: ${encode.name} ${name}.${field} accepts ${label}`, () => {
          const value = factory(), expected = baseline();
          assert.deepEqual(encode(value), expected);
          const point = select(value), parent = path.length === 1 ? point : point[path[0]];
          parent[path.at(-1)] = String(endpoint);
          if (byteOffset !== null) {
            (endpoint === 0n ? Buffer.alloc(32) : FQ_MAX_BYTES).copy(expected, byteOffset);
          } else {
            // Other G2 y limb remains low and nonzero: y1 dominates y0.
            const flag = endpoint !== 0n && field !== 'y0' ? 0x80 : 0x00;
            expected[offset + (kind === 'G1' ? 31 : 63)] = flag;
          }
          assert.deepEqual(encode(value), expected);
        });
      }
      for (const [label, bad] of [['negative', '-1'], ['FQ', String(FQ)]]) {
        test(`source-informed: ${encode.name} ${name}.${field} rejects ${label}`, () => {
          const value = factory();
          assert.deepEqual(encode(value), baseline());
          const point = select(value), parent = path.length === 1 ? point : point[path[0]];
          parent[path.at(-1)] = bad;
          assert.throws(() => encode(value), {message: 'NONCANONICAL_FQ'});
        });
      }
    }
    const nonAffine = kind === 'G1'
      ? [['z zero', '0'], ['z two', '2']]
      : [['z0 zero', ['0', '0']], ['z1 one', ['1', '1']]];
    for (const [label, z] of nonAffine) {
      test(`source-informed: ${encode.name} ${name} rejects ${label}`, () => {
        const value = factory();
        assert.deepEqual(encode(value), baseline());
        select(value)[2] = z;
        assert.throws(() => encode(value), {message: 'AFFINE_POINT_REQUIRED'});
      });
    }
  }
}

for (const [label, mutate] of [
  ['missing protocol', k => { delete k.protocol; }],
  ['wrong protocol', k => { k.protocol = 'plonk'; }],
  ['missing curve', k => { delete k.curve; }],
  ['wrong curve', k => { k.curve = 'BN254'; }],
  ['short IC', k => { k.IC.pop(); }],
  ['long IC', k => { k.IC.push(['13', '14', '1']); }],
  ['mismatched nPublic', k => { k.nPublic = 2; }],
  ['missing nPublic', k => { delete k.nPublic; }],
]) {
  test(`source-informed: vkBytes rejects ${label}`, () => {
    const key = syntheticKey();
    assert.deepEqual(vkBytes(key), expectedKey());
    mutate(key);
    assert.throws(() => vkBytes(key), {message: 'VK_FORMAT'});
  });
}
