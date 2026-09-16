import { Buffer } from 'node:buffer';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { TextDecoder, types } from 'node:util';

export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

const MAX_BYTES = 262_144;
const MAX_DEPTH = 64;
const MAX_KEY_LENGTH = 128;
const UTF8 = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
// Pin the accepted repertoire so newer host Unicode versions cannot accept
// characters absent from the protocol's normative Unicode 15.0 table.
const UNICODE_TABLE_SHA256 = '7a4a0f8ea869cca7bc3d88d93d85d3f104b52a807bb4c112171c8d232c09f90c';
const repertoireBytes = readFileSync(new URL('../fixtures/unicode15_assigned_ranges.json', import.meta.url));
if (createHash('sha256').update(repertoireBytes).digest('hex') !== UNICODE_TABLE_SHA256) {
  throw new Error('CE1 Unicode repertoire integrity mismatch');
}
if (Number.parseInt(process.versions.unicode ?? '0', 10) < 15) {
  throw new Error('CE1 requires Unicode normalization tables >= 15.0.0');
}
const UNICODE_REPERTOIRE = JSON.parse(repertoireBytes.toString('utf8')) as {
  unicodeVersion: string;
  ranges: [number, number][];
};
if (UNICODE_REPERTOIRE.unicodeVersion !== '15.0.0') throw new Error('Unsupported CE1 Unicode repertoire');

function assignedScalar(point: number): boolean {
  let lower = 0;
  let upper = UNICODE_REPERTOIRE.ranges.length - 1;
  while (lower <= upper) {
    const middle = lower + Math.floor((upper - lower) / 2);
    const [start, end] = UNICODE_REPERTOIRE.ranges[middle];
    if (point < start) upper = middle - 1;
    else if (point > end) lower = middle + 1;
    else return true;
  }
  return false;
}

function invalid(message: string): never {
  throw new TypeError(`Invalid CE1 value: ${message}`);
}

function scalarString(value: string, requireNfc = true): void {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    let point = unit;
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) invalid('unpaired surrogate');
      point = 0x10000 + (unit - 0xd800) * 0x400 + next - 0xdc00;
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) {
      invalid('unpaired surrogate');
    }
    if (!assignedScalar(point)) invalid('scalar is not assigned in Unicode 15.0');
  }
  if (requireNfc && value.normalize('NFC') !== value) invalid('string is not NFC');
}

function keyString(value: string): void {
  if (value.length === 0 || value.length > MAX_KEY_LENGTH) invalid('object key length');
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit < 0x21 || unit > 0x7e) invalid('object keys must be visible ASCII');
  }
}

/** Validate a protocol machine identifier without accepting a trailing newline. */
export function machineId(value: unknown, maxLength = 128): string {
  if (!Number.isSafeInteger(maxLength) || maxLength < 1 || maxLength > 256) invalid('machine ID length limit');
  if (typeof value !== 'string' || value.length === 0 || value.length > maxLength) {
    invalid('machine ID length or type');
  }
  if (!/^[A-Za-z0-9]/u.test(value) || /[^A-Za-z0-9:_./-]/u.test(value)) {
    invalid('machine ID characters');
  }
  return value;
}

/** Encode CE1 JSON directly, so integer-looking object keys retain lexical order. */
export function canonical(value: unknown): string {
  const chunks: string[] = [];
  const ancestors = new Set<object>();
  let bytes = 0;

  function append(chunk: string): void {
    bytes += Buffer.byteLength(chunk, 'utf8');
    if (bytes > MAX_BYTES) invalid('encoded size exceeds 262144 bytes');
    chunks.push(chunk);
  }

  function write(item: unknown, parentDepth: number): void {
    if (parentDepth > MAX_DEPTH) invalid('value depth exceeds 64');
    if (item === null) {
      append('null');
      return;
    }
    if (typeof item === 'boolean') {
      append(item ? 'true' : 'false');
      return;
    }
    if (typeof item === 'number') {
      if (!Number.isSafeInteger(item) || Object.is(item, -0)) invalid('number must be a safe integer other than -0');
      append(String(item));
      return;
    }
    if (typeof item === 'string') {
      if (item.length > MAX_BYTES) invalid('string exceeds size limit');
      scalarString(item);
      append(JSON.stringify(item));
      return;
    }
    if (typeof item !== 'object' || types.isProxy(item)) invalid('unsupported value type');
    const depth = parentDepth + 1;
    if (ancestors.has(item)) invalid('circular reference');

    const array = Array.isArray(item);
    const prototype = Object.getPrototypeOf(item);
    if (array ? prototype !== Array.prototype : prototype !== Object.prototype && prototype !== null) {
      invalid('only plain objects and ordinary arrays are supported');
    }
    const ownKeys = Reflect.ownKeys(item);
    if (ownKeys.some((key) => typeof key !== 'string')) invalid('symbol property');
    ancestors.add(item);
    try {
      if (array) {
        const length = Object.getOwnPropertyDescriptor(item, 'length')!.value as number;
        if (length > MAX_BYTES || ownKeys.length !== length + 1) invalid('sparse array or extra array property');
        append('[');
        for (let index = 0; index < length; index += 1) {
          const descriptor = Object.getOwnPropertyDescriptor(item, String(index));
          if (!descriptor || !descriptor.enumerable || !Object.hasOwn(descriptor, 'value')) {
            invalid('array entries must be enumerable data properties');
          }
          if (index !== 0) append(',');
          write(descriptor.value, depth);
        }
        append(']');
      } else {
        const keys = (ownKeys as string[]).sort();
        append('{');
        for (let index = 0; index < keys.length; index += 1) {
          const key = keys[index];
          keyString(key);
          const descriptor = Object.getOwnPropertyDescriptor(item, key)!;
          if (!descriptor.enumerable || !Object.hasOwn(descriptor, 'value')) {
            invalid('object entries must be enumerable data properties');
          }
          if (index !== 0) append(',');
          append(JSON.stringify(key));
          append(':');
          write(descriptor.value, depth);
        }
        append('}');
      }
    } finally {
      ancestors.delete(item);
    }
  }

  write(value, 0);
  return chunks.join('');
}

export function canonicalBytes(value: unknown): Buffer {
  return Buffer.from(canonical(value), 'utf8');
}

/** Decode JSON while retaining the lexical restrictions JSON.parse would erase. */
export function decodeJson(input: Uint8Array | string): JsonValue {
  let source: string;
  if (typeof input === 'string') {
    if (input.length > MAX_BYTES || Buffer.byteLength(input, 'utf8') > MAX_BYTES) invalid('input size exceeds 262144 bytes');
    scalarString(input, false);
    source = input;
  } else {
    if (!(input instanceof Uint8Array)) invalid('input must be UTF-8 bytes or a string');
    if (input.byteLength > MAX_BYTES) invalid('input size exceeds 262144 bytes');
    try {
      source = UTF8.decode(input);
    } catch {
      invalid('malformed UTF-8');
    }
  }
  let index = 0;

  function whitespace(): void {
    while (source[index] === ' ' || source[index] === '\t' || source[index] === '\n' || source[index] === '\r') index += 1;
  }

  function string(): string {
    if (source[index] !== '"') invalid('expected string');
    index += 1;
    let start = index;
    const parts: string[] = [];
    while (index < source.length) {
      const character = source[index];
      if (character === '"') {
        parts.push(source.slice(start, index));
        index += 1;
        const result = parts.join('');
        scalarString(result);
        return result;
      }
      if (source.charCodeAt(index) < 0x20) invalid('unescaped control character');
      if (character !== '\\') {
        index += 1;
        continue;
      }
      parts.push(source.slice(start, index));
      index += 1;
      const escape = source[index++];
      switch (escape) {
        case '"': parts.push('"'); break;
        case '\\': parts.push('\\'); break;
        case '/': parts.push('/'); break;
        case 'b': parts.push('\b'); break;
        case 'f': parts.push('\f'); break;
        case 'n': parts.push('\n'); break;
        case 'r': parts.push('\r'); break;
        case 't': parts.push('\t'); break;
        case 'u': {
          const digits = source.slice(index, index + 4);
          if (digits.length !== 4 || /[^0-9a-fA-F]/u.test(digits)) invalid('invalid Unicode escape');
          parts.push(String.fromCharCode(Number.parseInt(digits, 16)));
          index += 4;
          break;
        }
        default: invalid('invalid string escape');
      }
      start = index;
    }
    invalid('unterminated string');
  }

  function number(): number {
    const start = index;
    if (source[index] === '-') index += 1;
    if (source[index] === '0') {
      index += 1;
    } else {
      if (!(source[index] >= '1' && source[index] <= '9')) invalid('invalid number');
      do { index += 1; } while (source[index] >= '0' && source[index] <= '9');
    }
    const next = source[index];
    if ((next >= '0' && next <= '9') || next === '.' || next === 'e' || next === 'E') {
      invalid('numbers must use integer syntax without leading zeros');
    }
    const result = Number(source.slice(start, index));
    if (!Number.isSafeInteger(result) || Object.is(result, -0)) invalid('number must be a safe integer other than -0');
    return result;
  }

  function value(parentDepth: number): JsonValue {
    if (parentDepth > MAX_DEPTH) invalid('value depth exceeds 64');
    whitespace();
    const character = source[index];
    if (character === '"') return string();
    if (character === '-' || (character >= '0' && character <= '9')) return number();
    for (const [token, result] of [['true', true], ['false', false], ['null', null]] as const) {
      if (source.startsWith(token, index)) {
        index += token.length;
        return result;
      }
    }
    if (character !== '[' && character !== '{') invalid('expected JSON value');
    const depth = parentDepth + 1;
    index += 1;
    whitespace();

    if (character === '[') {
      const result: JsonValue[] = [];
      if (source[index] === ']') { index += 1; return result; }
      while (true) {
        result.push(value(depth));
        whitespace();
        if (source[index] === ']') { index += 1; return result; }
        if (source[index++] !== ',') invalid('expected array separator');
      }
    }

    const result: { [key: string]: JsonValue } = {};
    const keys = new Set<string>();
    if (source[index] === '}') { index += 1; return result; }
    while (true) {
      whitespace();
      const key = string();
      keyString(key);
      if (keys.has(key)) invalid('duplicate object key');
      keys.add(key);
      whitespace();
      if (source[index++] !== ':') invalid('expected object colon');
      Object.defineProperty(result, key, { value: value(depth), enumerable: true, writable: true, configurable: true });
      whitespace();
      if (source[index] === '}') { index += 1; return result; }
      if (source[index++] !== ',') invalid('expected object separator');
    }
  }

  const result = value(0);
  whitespace();
  if (index !== source.length) invalid('trailing JSON content');
  // Validate the canonical output bound as well as the incoming byte bound.
  canonical(result);
  return result;
}

/** SHA-256(UTF8("KIX-CE1\\0") || ASCII(domain) || 0x00 || canonicalBytes(value)). */
export function digest(domain: unknown, value: unknown): string {
  const identifier = machineId(domain);
  return createHash('sha256')
    .update('KIX-CE1\x00', 'utf8')
    .update(identifier, 'ascii')
    .update(Buffer.from([0]))
    .update(canonicalBytes(value))
    .digest('hex');
}
