"""Frozen CE1 vectors and actual commerce computations shared with TypeScript.

Expected values are checked-in literals. Tests never regenerate the fixture.
"""
import json
import hashlib
from pathlib import Path
import unittest

from assets import AssetSpec
from canonical_encoding import (MAX_DEPTH, MAX_INPUT_BYTES, MAX_SAFE_INTEGER,
                                UNICODE_TABLE_SHA256, UNICODE_VERSION,
                                canonical, canonical_bytes, decode_json, digest,
                                machine_id)
from commerce import build_quote, plan_payments, propose_line_refund, proportional
from common import Rejected


FIXTURE = Path(__file__).resolve().parent / 'fixtures/canonical_encoding_v1.json'


def verify_golden_vectors():
    vectors = json.loads(FIXTURE.read_text(encoding='utf-8'))
    for vector in vectors['encodingVectors']:
        assert canonical(vector['value']) == vector['canonicalUtf8'], vector['name']
        assert canonical_bytes(vector['value']) == vector['canonicalUtf8'].encode('utf-8'), vector['name']
        assert digest(vector['domain'], vector['value']) == vector['hash'], vector['name']
        assert decode_json(vector['canonicalUtf8'].encode('utf-8')) == vector['value'], vector['name']
    for vector in vectors['invalidWireVectors']:
        try:
            decode_json(vector['wire'].encode('utf-8'))
        except Rejected:
            pass
        else:
            raise AssertionError('accepted wire: ' + vector['name'])
    for value in vectors['invalidMachineIds']:
        try:
            machine_id(value)
        except Rejected:
            pass
        else:
            raise AssertionError('accepted identifier: ' + repr(value))
    for vector in vectors['allocationVectors']:
        computed = proportional(int(vector['total']),
                                {key: int(value) for key, value in vector['capacities'].items()})
        assert {key: str(value) for key, value in computed.items()} == vector['expected'], vector['name']
    for vector in vectors['assetVectors']:
        assert AssetSpec.from_dict(vector['spec']).asset_id == vector['assetId']
    for vector in vectors['commerceVectors']:
        quote = build_quote(vector['request'])
        plan = plan_payments(quote, vector['legs'], quote['quoteHash'], vector['now'])
        proposal = propose_line_refund(quote, plan, vector['refundLineIds'], plan['planHash'])
        for actual, expected, expected_text in (
                (quote, vector['expectedQuote'], vector['quoteCanonicalUtf8']),
                (plan, vector['expectedPlan'], vector['planCanonicalUtf8']),
                (proposal, vector['expectedProposal'], vector['proposalCanonicalUtf8'])):
            assert actual == expected, vector['name']
            assert canonical_bytes(actual) == expected_text.encode('utf-8'), vector['name']
    for vector in vectors['invalidCommerceVectors']:
        try:
            build_quote(vector['request'])
        except Rejected:
            pass
        else:
            raise AssertionError('accepted commerce request: ' + vector['name'])
    return {key: len(vectors[key]) for key in (
        'encodingVectors', 'invalidWireVectors', 'invalidMachineIds',
        'allocationVectors', 'assetVectors', 'commerceVectors', 'invalidCommerceVectors')}


class CanonicalEncodingTests(unittest.TestCase):
    def test_unicode_repertoire_is_pinned_sorted_and_disjoint(self):
        path = FIXTURE.parent / 'unicode15_assigned_ranges.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), UNICODE_TABLE_SHA256)
        table = json.loads(path.read_bytes())
        self.assertEqual(table['unicodeVersion'], UNICODE_VERSION)
        last = -1
        for start, end in table['ranges']:
            self.assertTrue(last < start <= end <= 0x10ffff)
            self.assertTrue(end < 0xd800 or start > 0xdfff)
            last = end
        for text in ('\u0378', '\uffff', '\U0010ffff', '\u1c89', '\U000105d2\u0307',
                     '\U00011382\U000113c9'):
            with self.subTest(text=repr(text)), self.assertRaises(Rejected):
                canonical(text)

    def test_frozen_encoding_hash_allocation_and_real_commerce_vectors(self):
        counts = verify_golden_vectors()
        self.assertGreaterEqual(counts['commerceVectors'], 5)

    def test_runtime_values_reject_lossy_numbers_and_non_json_containers(self):
        for value in (1.0, -0.0, float('nan'), float('inf'), MAX_SAFE_INTEGER + 1,
                      -(MAX_SAFE_INTEGER + 1), (1, 2), {1, 2}, b'bytes', {1: 'key'},
                      {'a': '\ud800'}, {'text': 'e\u0301'}):
            with self.subTest(value=repr(value)), self.assertRaises(Rejected):
                canonical(value)

    def test_depth_size_and_utf8_bounds(self):
        wire = ('[' * MAX_DEPTH + '0' + ']' * MAX_DEPTH).encode()
        self.assertEqual(canonical_bytes(decode_json(wire)), wire)
        for value in (b'[' + wire + b']', b' ' * (MAX_INPUT_BYTES + 1),
                      b'"\xff"', b'"\xed\xa0\x80"', b'"\xc0\xaf"'):
            with self.subTest(prefix=value[:20]), self.assertRaises(Rejected):
                decode_json(value)
        cyclic = []; cyclic.append(cyclic)
        with self.assertRaises(Rejected):
            canonical(cyclic)

    def test_equivalent_wire_escapes_have_one_encoding_without_normalization(self):
        self.assertEqual(canonical(decode_json(b' { "b" : "\\u00e9", "a" : "\\/" } ')),
                         '{"a":"/","b":"é"}')
        self.assertEqual(decode_json(b'"\\ud83d\\ude00"'), '😀')
        for payload in (b'"e\\u0301"', b'"\\ud800"'):
            with self.assertRaises(Rejected):
                decode_json(payload)

    def test_domain_framing_and_identifier_bounds_are_explicit(self):
        self.assertNotEqual(digest('kix:a:1', {}), digest('kix:b:1', {}))
        self.assertNotEqual(digest('a', 'bc'), digest('ab', 'c'))
        for domain in ('', 'a\x00b', 'é', 'a' * 129):
            with self.subTest(domain=domain), self.assertRaises(Rejected):
                digest(domain, {})
        self.assertEqual(machine_id('a' * 128), 'a' * 128)
        self.assertEqual(machine_id('a' * 256, max_length=256), 'a' * 256)
        with self.assertRaises(Rejected):
            machine_id('a' * 257, max_length=256)


if __name__ == '__main__':
    unittest.main()
