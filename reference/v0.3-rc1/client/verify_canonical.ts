#!/usr/bin/env node
/** Verify literal CE1 bytes/hashes and independently computed commerce results. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { canonical, canonicalBytes, decodeJson, digest, machineId } from './canonical_encoding.ts';
import { assetId, buildQuote, planPayments, proposeLineRefund, proportional,
  validateQuote, validatePaymentPlan } from './commerce_v2.ts';

const fixturePath = process.argv[2] ?? fileURLToPath(new URL('../fixtures/canonical_encoding_v1.json', import.meta.url));
// The outer fixture includes intentionally invalid CE1 strings. Only the actual
// wire values under test pass through the strict CE1 parser.
const fixtures = JSON.parse(readFileSync(fixturePath, 'utf8'));
const counts = { encoding: 0, invalidWire: 0, invalidMachineId: 0, allocation: 0,
  commerce: 0, invalidCommerce: 0, asset: 0, invariants: 0 };

function equalCanonical(actual: unknown, expected: unknown, label: string): void {
  assert.equal(canonical(actual), canonical(expected), label);
}

for (const vector of fixtures.encodingVectors) {
  assert.equal(canonical(vector.value), vector.canonicalUtf8, vector.name + ': canonical text');
  assert.deepEqual(Buffer.from(canonicalBytes(vector.value)), Buffer.from(vector.canonicalUtf8, 'utf8'), vector.name + ': canonical bytes');
  assert.equal(digest(vector.domain, vector.value), vector.hash, vector.name + ': domain-separated hash');
  equalCanonical(decodeJson(vector.canonicalUtf8), vector.value, vector.name + ': decode text');
  equalCanonical(decodeJson(Buffer.from(vector.canonicalUtf8, 'utf8')), vector.value, vector.name + ': decode bytes');
  counts.encoding += 1;
}

for (const vector of fixtures.invalidWireVectors) {
  assert.throws(() => decodeJson(vector.wire), undefined, vector.name);
  counts.invalidWire += 1;
}

for (const value of fixtures.invalidMachineIds) {
  assert.throws(() => machineId(value), undefined, 'invalid machine identifier: ' + JSON.stringify(value));
  counts.invalidMachineId += 1;
}

for (const vector of fixtures.allocationVectors) {
  const capacities = Object.fromEntries(Object.entries(vector.capacities).map(([key, amount]) => [key, BigInt(amount as string)]));
  const assigned = proportional(BigInt(vector.total), capacities);
  equalCanonical(Object.fromEntries(Object.entries(assigned).map(([key, amount]) => [key, amount.toString()])), vector.expected, vector.name);
  assert.equal(Object.values(assigned).reduce((sum, amount) => sum + amount, 0n), BigInt(vector.total), vector.name + ': conservation');
  for (const [key, amount] of Object.entries(assigned)) assert.ok(amount >= 0n && amount <= capacities[key], vector.name + ': capacity');
  counts.allocation += 1;
}

for (const vector of fixtures.assetVectors) {
  assert.equal(assetId(vector.spec), vector.assetId, 'asset identifier');
  counts.asset += 1;
}

for (const vector of fixtures.commerceVectors) {
  const quote = buildQuote(vector.request);
  const plan = planPayments(quote, vector.legs, quote.quoteHash, vector.now);
  const proposal = proposeLineRefund(quote, plan, vector.refundLineIds, plan.planHash);
  for (const [label, actual, expected, expectedCanonical] of [
    ['quote', quote, vector.expectedQuote, vector.quoteCanonicalUtf8],
    ['plan', plan, vector.expectedPlan, vector.planCanonicalUtf8],
    ['proposal', proposal, vector.expectedProposal, vector.proposalCanonicalUtf8],
  ]) {
    equalCanonical(actual, expected, vector.name + ': ' + label + ' calculation');
    assert.equal(canonical(actual), expectedCanonical, vector.name + ': ' + label + ' literal bytes');
  }
  equalCanonical(validateQuote(quote), quote, vector.name + ': quote recomputation');
  equalCanonical(validatePaymentPlan(quote, plan), plan, vector.name + ': plan recomputation');
  assert.throws(() => validateQuote({ ...quote, schemaVersion: 'kix:commerce:1' }), /UNSUPPORTED_COMMERCE_SCHEMA/, vector.name + ': legacy quote schema');
  assert.throws(() => validatePaymentPlan(quote, { ...plan, schemaVersion: 'kix:commerce:1' }), /UNSUPPORTED_COMMERCE_SCHEMA/, vector.name + ': legacy plan schema');
  assert.equal(proposal.executionAuthorized, false, vector.name + ': calculation only');
  assert.equal(BigInt(proposal.customerRefund.atoms) + Object.values(proposal.discountBurdenReversal)
    .reduce((sum: bigint, amount) => sum + BigInt(amount as string), 0n), BigInt(proposal.grossReversed.atoms), vector.name + ': refund conservation');
  assert.equal(proposal.originalRoutes.reduce((sum: bigint, route: any) => sum + BigInt(route.amount.atoms), 0n),
    BigInt(proposal.customerRefund.atoms), vector.name + ': original-route conservation');
  const corruptedQuote = structuredClone(quote);
  corruptedQuote.lines[0].payableAtoms = (BigInt(corruptedQuote.lines[0].payableAtoms) + 1n).toString();
  delete corruptedQuote.quoteHash;
  corruptedQuote.quoteHash = digest('kix:quote:2', corruptedQuote);
  assert.throws(() => validateQuote(corruptedQuote), /QUOTE_CONTENT_MISMATCH/, vector.name + ': recomputed tamper hash');
  const corruptedPlan = structuredClone(plan);
  corruptedPlan.checkedAt = Math.max(0, vector.now - 1);
  // A changed hashed field must fail even where its value is otherwise valid.
  if (corruptedPlan.checkedAt === plan.checkedAt) corruptedPlan.checkedAt += 1;
  assert.throws(() => validatePaymentPlan(quote, corruptedPlan), undefined, vector.name + ': changed plan field');
  assert.throws(() => planPayments(quote, vector.legs, quote.quoteHash, quote.request.expiresAt), /QUOTE_EXPIRED/, vector.name + ': expiry boundary');
  assert.throws(() => proposeLineRefund(quote, plan, vector.refundLineIds, '0'.repeat(64)), /STALE_PAYMENT_PLAN/, vector.name + ': stale plan');
  counts.commerce += 1;
}

for (const vector of fixtures.invalidCommerceVectors ?? []) {
  assert.throws(() => buildQuote(vector.request), undefined, vector.name);
  counts.invalidCommerce += 1;
}

// Runtime-specific risks not expressible as ordinary fixture JSON values.
for (const value of [NaN, Infinity, -Infinity, -0, 1.5, 9007199254740992, undefined, 1n,
  '\ud800', '\udfff', 'e\u0301', '\u0378', '\u1c89', '\uffff', '\u{10ffff}',
  { 'é': 1 }, { '': 1 }, { 'a b': 1 }, { ['x'.repeat(129)]: 1 }]) {
  assert.throws(() => canonical(value));
  counts.invariants += 1;
}
for (const bytes of [Buffer.from([0xc0, 0xaf]), Buffer.from([0xed, 0xa0, 0x80]), Buffer.from([0xf4, 0x90, 0x80, 0x80]),
  Buffer.from([0xef, 0xbb, 0xbf, 0x30])]) {
  assert.throws(() => decodeJson(bytes));
  counts.invariants += 1;
}
assert.equal(canonical({ '2': true, '10': false }), '{"10":false,"2":true}');
assert.throws(() => digest('', {}));
assert.throws(() => digest('valid\x00other', {}));
assert.throws(() => machineId('valid', 257));
assert.throws(() => proportional(1n, { 'é': 1n }));
assert.throws(() => decodeJson(' '.repeat(262144) + '0'));
assert.throws(() => canonical('x'.repeat(262143)));
assert.throws(() => canonical(Array(1)));
assert.throws(() => canonical(new Date(0)));
const cyclic: any[] = [];
cyclic.push(cyclic);
assert.throws(() => canonical(cyclic));
let maxDepth: unknown = 0;
for (let index = 0; index < 64; index += 1) maxDepth = [maxDepth];
equalCanonical(decodeJson(canonical(maxDepth)), maxDepth, 'depth 64 boundary');
assert.throws(() => canonical([maxDepth]));
assert.throws(() => decodeJson('['.repeat(65) + '0' + ']'.repeat(65)));
counts.invariants += 13;

console.log(JSON.stringify({ result: 'PASS', status: 'passed', implementation: 'independent-typescript-ce1-commerce-v2', counts }));
