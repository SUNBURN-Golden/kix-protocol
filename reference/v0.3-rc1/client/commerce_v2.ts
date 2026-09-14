/** Independent CE1 commerce calculations. These outputs never authorize execution. */
import { canonical, decodeJson, digest, machineId } from './canonical_encoding.ts';

export const SCHEMA = 'kix:commerce:2';
export const MAX_ATOMS = (1n << 128n) - 1n;
const MAX_LINES = 300;
const MAX_RULES = 64;
const MAX_LEGS = 16;
type WireObject = Record<string, any>;
export type AssetSpec = {
  namespace: string;
  reference: string;
  decimals: number;
  maxAtoms: string;
};
type Amount = { asset: AssetSpec; atoms: string };
type Row = {
  lineId: string;
  inventoryId: string;
  grossAtoms: bigint;
  discountAtoms: bigint;
  payableAtoms: bigint;
  discounts: { ruleId: string; bearerRef: string; atoms: string }[];
};

function requireCondition(condition: unknown, code: string): asserts condition {
  if (!condition) throw new Error(code);
}

function fields(value: unknown, names: string, code = 'INVALID_FIELDS'): asserts value is WireObject {
  requireCondition(value !== null && typeof value === 'object' && !Array.isArray(value), 'OBJECT_REQUIRED');
  const expected = names.split(' ').sort();
  const actual = Object.keys(value).sort();
  requireCondition(actual.length === expected.length && actual.every((key, index) => key === expected[index]), code);
}

function integer(value: unknown, minimum = 0, maximum = Number.MAX_SAFE_INTEGER): number {
  requireCondition(typeof value === 'number' && Number.isSafeInteger(value)
    && !Object.is(value, -0) && minimum <= value && value <= maximum, 'INVALID_COUNTER');
  return value;
}

function atoms(value: unknown, maximum: bigint, code = 'CANONICAL_ATOMS_REQUIRED'): bigint {
  requireCondition(typeof value === 'string' && value.length <= 39 && /^(?:0|[1-9][0-9]*)$/.test(value)
    && !value.includes('\n') && !value.includes('\r'), code);
  const parsed = BigInt(value);
  requireCondition(parsed <= maximum, 'AMOUNT_OVERFLOW');
  return parsed;
}

function identifiers(value: unknown, maximum: number): string[] {
  requireCondition(Array.isArray(value) && value.length > 0 && value.length <= maximum, 'INVALID_ID_LIST');
  const result = value.map((item) => machineId(item));
  requireCondition(new Set(result).size === result.length, 'DUPLICATE_ID');
  return result;
}

function clone<T>(value: T): T {
  return decodeJson(canonical(value)) as T;
}

export function validateAssetSpec(value: unknown): AssetSpec {
  const spec = clone(value);
  fields(spec, 'namespace reference decimals maxAtoms', 'INVALID_ASSET_WIRE');
  requireCondition(typeof spec.namespace === 'string'
    && /^[a-z][a-z0-9-]{0,62}$/.test(spec.namespace)
    && !spec.namespace.includes('\n') && !spec.namespace.includes('\r'), 'INVALID_ASSET_NAMESPACE');
  machineId(spec.reference, 256);
  integer(spec.decimals, 0, 38);
  requireCondition(atoms(spec.maxAtoms, MAX_ATOMS, 'INVALID_ASSET_LIMIT_WIRE') > 0n, 'INVALID_ASSET_LIMIT');
  return spec as AssetSpec;
}

export function assetId(value: unknown): string {
  return 'asset-v2-' + digest('kix:asset:2', validateAssetSpec(value));
}

function makeAmount(asset: AssetSpec, value: bigint): Amount {
  requireCondition(value >= 0n && value <= BigInt(asset.maxAtoms), 'INVALID_ASSET_AMOUNT');
  return { asset: { ...asset }, atoms: value.toString() };
}

function parseAmount(value: unknown): { asset: AssetSpec; atoms: bigint } {
  fields(value, 'asset atoms', 'INVALID_AMOUNT_WIRE');
  const asset = validateAssetSpec(value.asset);
  return { asset, atoms: atoms(value.atoms, BigInt(asset.maxAtoms), 'INVALID_AMOUNT_ATOMS_WIRE') };
}

function sameAsset(left: AssetSpec, right: AssetSpec): boolean {
  return left.namespace === right.namespace && left.reference === right.reference
    && left.decimals === right.decimals && left.maxAtoms === right.maxAtoms;
}

/** Exact largest-remainder allocation; ascending ASCII ID breaks remainder ties. */
export function proportional(total: bigint, capacities: Record<string, bigint>): Record<string, bigint> {
  requireCondition(typeof total === 'bigint' && total >= 0n, 'INVALID_ALLOCATION_TOTAL');
  requireCondition(capacities !== null && typeof capacities === 'object' && !Array.isArray(capacities), 'INVALID_CAPACITY');
  const entries = Object.entries(capacities);
  for (const [key, value] of entries) {
    machineId(key);
    requireCondition(typeof value === 'bigint' && value >= 0n, 'INVALID_CAPACITY');
  }
  const size = entries.reduce((sum, [, value]) => sum + value, 0n);
  requireCondition(total <= size, 'ALLOCATION_EXCEEDS_CAPACITY');
  const ordered = entries.sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0);
  if (size === 0n) return Object.fromEntries(ordered.map(([key]) => [key, 0n]));
  const divided = ordered.map(([key, value]) => ({ key, assigned: total * value / size, remainder: total * value % size }));
  let residual = total - divided.reduce((sum, item) => sum + item.assigned, 0n);
  const priority = [...divided].sort((a, b) => a.remainder > b.remainder ? -1
    : a.remainder < b.remainder ? 1 : a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
  for (const item of priority) {
    if (residual === 0n) break;
    item.assigned += 1n;
    residual -= 1n;
  }
  requireCondition(residual === 0n, 'ALLOCATION_REMAINDER_FAILED');
  return Object.fromEntries(divided.map(({ key, assigned }) => [key, assigned]));
}

export function buildQuote(input: unknown): WireObject {
  const request = clone(input);
  fields(request, 'schemaVersion orderId orderVersion scope policyRef expiresAt lines discounts');
  requireCondition(request.schemaVersion === SCHEMA, 'UNSUPPORTED_COMMERCE_SCHEMA');
  machineId(request.orderId); machineId(request.policyRef);
  integer(request.orderVersion, 1, 4294967295);
  // expiresAt and checkedAt are Unix milliseconds within the CE1 safe range.
  integer(request.expiresAt, 1);
  fields(request.scope, 'issuerId eventId performanceId');
  for (const value of Object.values(request.scope)) machineId(value);
  requireCondition(Array.isArray(request.lines) && request.lines.length > 0 && request.lines.length <= MAX_LINES, 'INVALID_LINES');
  requireCondition(Array.isArray(request.discounts) && request.discounts.length <= MAX_RULES, 'INVALID_DISCOUNTS');
  const rows = new Map<string, Row>();
  const inventory = new Set<string>();
  const registry = new Map<string, AssetSpec>();
  let asset: AssetSpec | undefined;
  for (const line of request.lines) {
    fields(line, 'lineId inventoryId gross');
    const lineId = machineId(line.lineId);
    const inventoryId = machineId(line.inventoryId);
    requireCondition(!rows.has(lineId), 'DUPLICATE_LINE');
    requireCondition(!inventory.has(inventoryId), 'DUPLICATE_INVENTORY');
    inventory.add(inventoryId);
    const money = parseAmount(line.gross);
    const registryKey = money.asset.namespace + '\x00' + money.asset.reference;
    const registered = registry.get(registryKey);
    requireCondition(registered === undefined || sameAsset(registered, money.asset), 'ASSET_METADATA_CONFLICT');
    registry.set(registryKey, money.asset);
    asset ??= money.asset;
    requireCondition(sameAsset(asset, money.asset), 'MIXED_QUOTE_ASSETS');
    rows.set(lineId, { lineId, inventoryId, grossAtoms: money.atoms,
      discountAtoms: 0n, payableAtoms: money.atoms, discounts: [] });
  }
  requireCondition(asset !== undefined, 'INVALID_LINES');
  const gross = [...rows.values()].reduce((sum, row) => sum + row.grossAtoms, 0n);
  makeAmount(asset, gross);
  const seenRules = new Set<string>();
  for (const rule of request.discounts) {
    fields(rule, 'ruleId bearerRef kind value eligibleLineIds capAtoms');
    const ruleId = machineId(rule.ruleId);
    machineId(rule.bearerRef);
    requireCondition(!seenRules.has(ruleId), 'DUPLICATE_DISCOUNT_RULE');
    seenRules.add(ruleId);
    const eligible = identifiers(rule.eligibleLineIds, MAX_LINES);
    requireCondition(eligible.every((key) => rows.has(key)), 'UNKNOWN_DISCOUNT_LINE');
    const remaining = Object.fromEntries(eligible.map((key) => [key, rows.get(key)!.payableAtoms]));
    const basis = Object.values(remaining).reduce((sum, value) => sum + value, 0n);
    requireCondition(rule.kind === 'FIXED' || rule.kind === 'BPS', 'UNSUPPORTED_DISCOUNT_KIND');
    const value = atoms(rule.value, rule.kind === 'BPS' ? 10000n : BigInt(asset.maxAtoms));
    let discount = rule.kind === 'BPS' ? basis * value / 10000n : value;
    if (rule.capAtoms !== null) {
      const cap = atoms(rule.capAtoms, BigInt(asset.maxAtoms));
      if (cap < discount) discount = cap;
    }
    requireCondition(discount <= basis, 'DISCOUNT_EXCEEDS_PAYABLE');
    for (const [key, assigned] of Object.entries(proportional(discount, remaining))) {
      const row = rows.get(key)!;
      row.discountAtoms += assigned;
      row.payableAtoms -= assigned;
      if (assigned !== 0n) row.discounts.push({ ruleId, bearerRef: rule.bearerRef, atoms: assigned.toString() });
    }
  }
  const resultRows = [...rows.keys()].sort().map((key) => {
    const row = rows.get(key)!;
    return { ...row, grossAtoms: row.grossAtoms.toString(),
      discountAtoms: row.discountAtoms.toString(), payableAtoms: row.payableAtoms.toString() };
  });
  const result: WireObject = {
    schemaVersion: SCHEMA, evidenceClass: 'CALCULATION_ONLY', request,
    asset: { ...asset }, lines: resultRows,
    totals: { grossAtoms: gross.toString(),
      discountAtoms: [...rows.values()].reduce((sum, row) => sum + row.discountAtoms, 0n).toString(),
      payableAtoms: [...rows.values()].reduce((sum, row) => sum + row.payableAtoms, 0n).toString() },
  };
  result.quoteHash = digest('kix:quote:2', result);
  return result;
}

export function validateQuote(value: unknown): WireObject {
  requireCondition(value !== null && typeof value === 'object' && !Array.isArray(value)
    && Object.hasOwn(value, 'request'), 'INVALID_QUOTE');
  const quote = value as WireObject;
  requireCondition(quote.schemaVersion === SCHEMA, 'UNSUPPORTED_COMMERCE_SCHEMA');
  const rebuilt = buildQuote(quote.request);
  requireCondition(canonical(quote) === canonical(rebuilt), 'QUOTE_CONTENT_MISMATCH');
  return rebuilt;
}

export function planPayments(value: unknown, inputLegs: unknown, expectedQuoteHash: unknown, now: unknown): WireObject {
  const quote = validateQuote(value);
  requireCondition(typeof expectedQuoteHash === 'string' && quote.quoteHash === expectedQuoteHash, 'STALE_QUOTE');
  const checkedAt = integer(now);
  requireCondition(checkedAt < quote.request.expiresAt, 'QUOTE_EXPIRED');
  const legs = clone(inputLegs);
  requireCondition(Array.isArray(legs) && legs.length <= MAX_LEGS, 'INVALID_PAYMENT_LEGS');
  const asset = validateAssetSpec(quote.asset);
  const checked: { leg: WireObject; money: { asset: AssetSpec; atoms: bigint } }[] = [];
  const seen = new Set<string>();
  for (const leg of legs) {
    fields(leg, 'legId providerRef routeRef amount');
    const legId = machineId(leg.legId);
    machineId(leg.providerRef); machineId(leg.routeRef);
    requireCondition(!seen.has(legId), 'DUPLICATE_PAYMENT_LEG');
    seen.add(legId);
    const money = parseAmount(leg.amount);
    requireCondition(sameAsset(money.asset, asset), 'PAYMENT_ASSET_MISMATCH');
    requireCondition(money.atoms > 0n, 'EMPTY_PAYMENT_LEG');
    checked.push({ leg, money });
  }
  requireCondition(checked.reduce((sum, { money }) => sum + money.atoms, 0n)
    === BigInt(quote.totals.payableAtoms), 'PAYMENT_TOTAL_MISMATCH');
  const remaining: Record<string, bigint> = Object.fromEntries(quote.lines.map((row: WireObject) => [row.lineId, BigInt(row.payableAtoms)]));
  const outputLegs = checked.map(({ leg, money }) => {
    const assigned = proportional(money.atoms, remaining);
    for (const [key, amount] of Object.entries(assigned)) remaining[key] -= amount;
    return { legId: leg.legId, providerRef: leg.providerRef, routeRef: leg.routeRef,
      amount: makeAmount(money.asset, money.atoms),
      allocations: Object.fromEntries(Object.entries(assigned).map(([key, amount]) => [key, amount.toString()])) };
  });
  requireCondition(Object.values(remaining).every((amount) => amount === 0n), 'UNALLOCATED_PAYMENT');
  const result: WireObject = { schemaVersion: SCHEMA, evidenceClass: 'CALCULATION_ONLY',
    quoteHash: quote.quoteHash, checkedAt, legs: outputLegs };
  result.planHash = digest('kix:payment-plan:2', result);
  return result;
}

export function validatePaymentPlan(quote: unknown, value: unknown): WireObject {
  const plan = clone(value);
  fields(plan, 'schemaVersion evidenceClass quoteHash checkedAt legs planHash');
  requireCondition(plan.schemaVersion === SCHEMA, 'UNSUPPORTED_COMMERCE_SCHEMA');
  requireCondition(Array.isArray(plan.legs), 'INVALID_PAYMENT_LEGS');
  const legs = plan.legs.map((leg: unknown) => {
    fields(leg, 'legId providerRef routeRef amount allocations');
    return { legId: leg.legId, providerRef: leg.providerRef, routeRef: leg.routeRef, amount: leg.amount };
  });
  const rebuilt = planPayments(quote, legs, plan.quoteHash, plan.checkedAt);
  requireCondition(canonical(plan) === canonical(rebuilt), 'PAYMENT_PLAN_CONTENT_MISMATCH');
  return rebuilt;
}

export function proposeLineRefund(value: unknown, paymentPlan: unknown, lineIds: unknown, expectedPlanHash: unknown): WireObject {
  const quote = validateQuote(value);
  const plan = validatePaymentPlan(quote, paymentPlan);
  requireCondition(typeof expectedPlanHash === 'string' && plan.planHash === expectedPlanHash, 'STALE_PAYMENT_PLAN');
  const selected = identifiers(lineIds, MAX_LINES).sort();
  const rows = new Map<string, WireObject>(quote.lines.map((row: WireObject) => [row.lineId, row]));
  requireCondition(selected.every((key) => rows.has(key)), 'UNKNOWN_REFUND_LINE');
  const asset = validateAssetSpec(quote.asset);
  const routes: WireObject[] = [];
  for (const leg of plan.legs) {
    const assigned = Object.fromEntries(selected.map((key) => [key, leg.allocations[key]]));
    const total = Object.values(assigned).reduce((sum: bigint, amount) => sum + BigInt(amount), 0n);
    if (total > 0n) routes.push({ legId: leg.legId, providerRef: leg.providerRef, routeRef: leg.routeRef,
      amount: makeAmount(asset, total), allocations: assigned });
  }
  const burdens = new Map<string, bigint>();
  for (const key of selected) {
    for (const discount of rows.get(key)!.discounts) {
      burdens.set(discount.bearerRef, (burdens.get(discount.bearerRef) ?? 0n) + BigInt(discount.atoms));
    }
  }
  const customer = selected.reduce((sum, key) => sum + BigInt(rows.get(key)!.payableAtoms), 0n);
  const gross = selected.reduce((sum, key) => sum + BigInt(rows.get(key)!.grossAtoms), 0n);
  requireCondition(customer + [...burdens.values()].reduce((sum, amount) => sum + amount, 0n) === gross, 'REFUND_CONSERVATION_FAILED');
  const result: WireObject = { schemaVersion: SCHEMA, evidenceClass: 'CALCULATION_ONLY',
    policy: 'FROZEN_LINE_PRICE_FULL_REVERSAL_V1', quoteHash: quote.quoteHash, planHash: plan.planHash,
    lineIds: selected, grossReversed: makeAmount(asset, gross), customerRefund: makeAmount(asset, customer),
    originalRoutes: routes,
    discountBurdenReversal: Object.fromEntries([...burdens.keys()].sort().map((key) => [key, burdens.get(key)!.toString()])),
    executionAuthorized: false,
    requiredEvidence: ['CONFIRMED_ORIGINAL_PAYMENTS', 'CURRENT_LINE_RIGHT_STATE', 'REFUND_POLICY_AUTHORITY',
      'UNRESOLVED_REFUND_RESERVATIONS', 'CURRENT_PROVIDER_REFUNDABLE_CAPACITY'] };
  result.proposalHash = digest('kix:line-refund-proposal:2', result);
  return result;
}

// Explicit aliases ease inspection against the independent Python API.
export const build_quote = buildQuote;
export const validate_quote = validateQuote;
export const plan_payments = planPayments;
export const validate_payment_plan = validatePaymentPlan;
export const propose_line_refund = proposeLineRefund;
