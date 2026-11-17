"""Offline navigation validation only; no fixture writer or consumer invocation.

Import helper modules, never their TestCase classes. Existing replay suites own
behavioral evidence; this companion preserves their identities and limitations.
"""
from __future__ import annotations

import ast
import copy
import unittest

import test_commerce_journey_receipts as journey
import test_commerce_temporal_vectors as temporal
import test_commerce_historical_receipt_vectors as historical
import test_commerce_entry_resale_order_vectors as ordering
import test_commerce_bound_issuance_vectors as issuance
import test_commerce_bound_resale_vectors as resale
import test_commerce_resale_expiry_vectors as expiry
import test_commerce_admission_cancellation_vectors as cancellation
from integration_gate.catalogue import load_catalogue
from mock_gates import _canonical

ROOT = journey.ROOT
INDEX = 'docs/status/COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json'
BINDING = 'docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json'
PRODUCER = 'docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json'
# Fixed pairings independent of the companion record, reusing pinned modules.
PACKS = (
    ('journey', journey, 'CommerceJourneyReceiptTests', 'test_complete_output_bytes', 44),
    ('temporal', temporal, 'CommerceTemporalVectorTests', 'test_complete_output_bytes_and_references', 39),
    ('historical', historical, 'CommerceHistoricalReceiptVectorTests', 'test_complete_output_bytes_and_references', 54),
    ('entry_resale_order', ordering, 'CommerceEntryResaleOrderVectorTests', 'test_complete_output_bytes_and_references', 29),
    ('bound_issuance', issuance, 'CommerceBoundIssuanceVectorTests', 'test_complete_output_bytes_and_references', 25),
    ('bound_resale', resale, 'CommerceBoundResaleVectorTests', 'test_complete_output_bytes_and_references', 49),
    ('resale_expiry', expiry, 'CommerceResaleExpiryVectorTests', 'test_complete_output_bytes_and_references', 27),
    ('admission_cancellation', cancellation, 'CommerceAdmissionCancellationVectorTests', 'test_complete_output_bytes_and_references', 26),
)
QUALIFICATION = {
    'semanticConsumerStatus': 'HOLD_SEMANTIC',
    'bootstrapIsConsumerAcceptance': False,
    'readQueries': {'count': 13, 'status': 'NOT_BOUND'},
    'sd1': {'id': 'SD1', 'owner': 'User', 'userOwned': True, 'status': 'OPEN', 'resolved': False},
    'externalConsumerAcceptance': 'UNVERIFIED',
    'policyValues': 'UNDETERMINED_WITH_EXISTING_OWNERS',
}
NON_CLAIMS = [
    'Non-normative navigation only; no interface, adapter or consumer integration.',
    'BOOTSTRAP is not consumer acceptance; semantic consumption remains HOLD_SEMANTIC.',
    'Binding statuses are copied unchanged; later evidence does not promote BOOTSTRAP_SCHEMA_BOUND.',
    'All 13 reads remain NOT_BOUND; diagnostic snapshots are local observations, not published reads.',
    'SD1 remains OPEN and User-owned; no waiver, option or verifier order is selected.',
    'External kix-commerce-apps acceptance remains UNVERIFIED; no consumer invocation was performed.',
    'Source-informed in-process mock evidence is not clean-room independence or A2 non-author review.',
    'Historical receipts are first results and can differ from later state; replay grants no new authority.',
    'Rejected-key retention is process-local, not durable recovery evidence.',
    'Synthetic clocks, prices and fees are examples, not approved defaults; policy values remain UNDETERMINED with existing owners.',
    'Digests establish byte identity, not authenticity, durability, finality, legal compliance or production readiness.',
    'No real funds, real PG/bank/KYC calls, public endpoints, Sui testnet/mainnet or production runtime.',
    'Local checks do not substitute for hosted exact-head KTX/KIX CI or independent review.',
]
LIMITATIONS = {
    'journey': ['One ordered 44-step in-process mock journey; not exhaustive behavior or consumer acceptance.'],
    'temporal': ['Synthetic expiry and stale-ownership histories; no wall-clock or chain-currentness guarantee.'],
    'historical': ['First receipt snapshots differ from later state; diagnostics are test-only and reads remain NOT_BOUND.'],
    'entry_resale_order': ['Synthetic resale/admission ordering; local observations do not establish venue admission or ownership finality.'],
    'bound_issuance': ['Mock settlement binding, commitment and explicit issuance are separate facts; rejected-key retention is process-local.'],
    'bound_resale': ['Mock settlement binding, commitment and explicit transfer are separate facts; rejected-key retention is process-local.'],
    'resale_expiry': ['Synthetic unpaid/paid listing expiry preserves payment facts and historical receipts; no compensation, relisting or transfer policy is defined.'],
    'admission_cancellation': ['Synthetic cancellation/adoption ordering preserves issued credentials; rejected-key retention is process-local and legal effects remain UNDETERMINED—User/legal.'],
}
ENTRY_KEYS = {'case_id', 'step_id', 'action', 'input_ref', 'outcome_ref',
              'outcome_kind', 'binding_ref', 'binding_status'}


def _read(path):
    return (ROOT / path).read_bytes()


def _check(condition, message):
    if not condition:
        raise AssertionError(message)


def _same(left, right):
    # Preserve JSON scalar types (False != 0, True != 1).
    return _canonical(left) == _canonical(right)


def _resolve(documents, ref):
    try:
        path, pointer = ref.split('#')
        node = documents[path]
        _check(pointer.startswith('/'), 'reference pointer')
        for part in pointer[1:].split('/'):
            part = part.replace('~1', '/').replace('~0', '~')
            node = node[int(part)] if isinstance(node, list) else node[part]
        return node
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AssertionError('unresolvable reference: ' + str(ref)) from exc


def _pin_check(pin, path, read, label):
    _check(type(pin) is dict and pin.get('path') == path, label + ' path association')
    raw = read(path)
    _check(_same(pin, journey._pin(path, raw)), label + ' digest/pin drift')
    return journey._decode(raw)


def validate_index(document, read=_read):
    """Reject drift without writes; injected reads are for detached controls only."""
    _check(type(document) is dict and set(document) == {
        'record_schema_version', 'record_kind', 'normative', 'consumer',
        'binding_index', 'producer_tuple', 'qualification', 'nonClaims', 'packs',
    }, 'record fields')
    _check(document['record_schema_version'] == 'kix-commerce-companion-evidence-index/1', 'record version')
    _check(document['record_kind'] == 'NON_NORMATIVE_COMPANION_EVIDENCE_INDEX', 'record kind')
    _check(document['normative'] is False, 'normative claim')
    _check(document['consumer'] == 'kix-commerce-apps', 'consumer identity')
    _check(_same(document['qualification'], QUALIFICATION), 'qualification claim/type')
    _check(_same(document['nonClaims'], NON_CLAIMS), 'nonClaims omitted/changed/extra')
    binding = _pin_check(document['binding_index'], BINDING, read, 'binding index')
    producer = _pin_check(document['producer_tuple'], PRODUCER, read, 'producer tuple')
    _check(binding['normative'] is False and producer['normative'] is False, 'source normative claim')
    _check(binding['profile']['semanticConsumerStatus'] == 'HOLD_SEMANTIC' and
           binding['profile']['bootstrapIsConsumerAcceptance'] is False, 'source semantic claim')
    _check(_same({k: binding['sd1'][k] for k in QUALIFICATION['sd1']}, QUALIFICATION['sd1']),
           'source SD1 claim')
    _check(binding['externalConsumerExpectations']['consumer'] == document['consumer'] and
           binding['externalConsumerExpectations']['status'] == 'UNVERIFIED', 'source consumer claim')
    reads = binding['readQueries']
    _check(type(reads['count']) is int and reads['count'] == len(reads['items']) == 13 and
           [r['name'] for r in reads['items']] == sorted(journey.journey.READ_MODEL_QUERY_NAMES) and
           all(r['status'] == 'NOT_BOUND' for r in reads['items']), 'source read claim')
    catalogue = load_catalogue(ROOT)
    _check(not set(journey.journey.READ_MODEL_QUERY_NAMES) & set(catalogue.names), 'published read claim')
    commands = binding['commands']['items']
    actions = [item['action'] for item in commands]
    _check(len(actions) == len(set(actions)) and set(actions) == set(catalogue.names), 'binding action coverage')
    packs = document['packs']
    _check(type(packs) is list and [p.get('id') for p in packs] == [s[0] for s in PACKS],
           'pack coverage/order')
    documents = {BINDING: binding}
    total = 0
    for pack, (family, module, class_name, method, count) in zip(packs, PACKS):
        _check(set(pack) == {'id', 'input', 'output', 'replay_test', 'limitations', 'entries'}, 'pack fields')
        input_path = module.FIXTURE
        output_path = module.GOLDEN.relative_to(ROOT).as_posix()
        source = _pin_check(pack['input'], input_path, read, family + ' input')
        outcome = _pin_check(pack['output'], output_path, read, family + ' output')
        _check(_same(outcome['fixture'], pack['input']), 'output fixture association')
        documents.update({input_path: source, output_path: outcome})
        replay_path = 'reference/booking_resale_admission/' + module.__name__ + '.py'
        _check(pack['replay_test'] == {'path': replay_path, 'symbol': class_name + '.' + method}, 'replay location')
        tree = ast.parse(read(replay_path), filename=replay_path)
        classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
        _check(len(classes) == 1 and sum(isinstance(node, ast.FunctionDef) and node.name == method
                                       for node in classes[0].body) == 1, 'replay symbol absent')
        _check(_same(pack['limitations'], LIMITATIONS[family]), 'pack limitation claim')
        source_cases = source.get('cases', [source])
        outcome_cases = outcome.get('cases', [outcome])
        case_ids = [case.get('id') for case in source_cases]
        _check(len(case_ids) == len(set(case_ids)), 'duplicate source case')
        _check([case.get('id') for case in outcome_cases] == case_ids, 'outcome case association')
        expected = []
        for i, (case, result_case) in enumerate(zip(source_cases, outcome_cases)):
            steps, results = case['steps'], result_case['steps']
            ids = [step['id'] for step in steps]
            _check(len(ids) == len(set(ids)), 'duplicate source step')
            _check([step['id'] for step in results] == ids, 'outcome step association')
            for j, (step, result) in enumerate(zip(steps, results)):
                pointer = '/steps/%d' % j if family == 'journey' else '/cases/%d/steps/%d' % (i, j)
                input_ref = input_path + '#' + pointer + '/body'
                output_ref = output_path + '#' + pointer
                _check(result['action'] == step['action'], 'outcome action association')
                _check(result['input_ref'] == input_ref, 'outcome input association')
                kind = 'rejection_code' if 'expect_error' in step else 'receipt'
                _check(({ 'receipt', 'rejection_code'} & set(result)) == {kind}, 'outcome kind association')
                action = step['action']
                _check(action in catalogue.fsm_names, 'unpublished action')
                k = actions.index(action)
                command = commands[k]
                _check(command['name'] == action and command['source'] == 'fsm', 'binding action association')
                expected.append(dict(
                    case_id=case.get('id'), step_id=step['id'], action=action,
                    input_ref=input_ref, outcome_ref=output_ref, outcome_kind=kind,
                    binding_ref=BINDING + '#/commands/items/%d' % k,
                    binding_status=command['status']))
        entries = pack['entries']
        _check(type(entries) is list and len(entries) == len(expected) == count, 'entry coverage/count')
        _check(all(type(e) is dict and set(e) == ENTRY_KEYS for e in entries), 'entry fields')
        identities = [(entry['case_id'], entry['step_id']) for entry in entries]
        _check(len(set(identities)) == len(identities), 'duplicate entry identity')
        _check(identities == [(e['case_id'], e['step_id']) for e in expected], 'entry case/step association/order')
        for entry, wanted in zip(entries, expected):
            for field in ('action', 'input_ref', 'outcome_ref', 'outcome_kind', 'binding_ref', 'binding_status'):
                _check(_same(entry[field], wanted[field]), field + ' association')
            body = _resolve(documents, entry['input_ref'])
            result = _resolve(documents, entry['outcome_ref'])
            command = _resolve(documents, entry['binding_ref'])
            _check(result['id'] == entry['step_id'] and result['action'] == entry['action'] and
                   result['input_ref'] == entry['input_ref'], 'resolved outcome association')
            _check(_same(body, _resolve(documents, result['input_ref'])), 'resolved body association')
            _check(command['action'] == entry['action'] and command['status'] == entry['binding_status'],
                   'resolved binding association')
        total += len(entries)
    _check(total == 293, 'total coverage')
    return total


class CommerceCompanionEvidenceIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = _read(INDEX)
        cls.document = journey._decode(cls.raw)

    def _reject(self, mutate, diagnostic):
        document = copy.deepcopy(self.document)
        mutate(document)
        with self.assertRaisesRegex(AssertionError, diagnostic):
            validate_index(document)
        self.assertEqual(validate_index(self.document), 293)

    def test_complete_index(self):
        self.assertEqual(validate_index(self.document), 293)

    def test_coverage_controls(self):
        for mutate in (
            lambda d: d['packs'].pop(),
            lambda d: d['packs'].append(copy.deepcopy(d['packs'][0])),
            lambda d: d['packs'].reverse(),
            lambda d: d['packs'].__setitem__(1, copy.deepcopy(d['packs'][0])),
        ):
            with self.subTest(mutate=mutate):
                self._reject(mutate, 'pack coverage/order')
        for p in range(len(PACKS)):
            for mutate, diagnostic in (
                (lambda e: e.pop(), 'entry coverage/count'),
                (lambda e: e.append(copy.deepcopy(e[0])), 'entry coverage/count'),
                (lambda e: e.__setitem__(-1, copy.deepcopy(e[0])), 'duplicate entry identity'),
                (lambda e: e.reverse(), 'entry case/step association/order'),
                (lambda e: e[0].update(case_id='other-case'), 'entry case/step association/order'),
                (lambda e: e[0].update(step_id='other-step'), 'entry case/step association/order'),
            ):
                with self.subTest(pack=p, diagnostic=diagnostic):
                    self._reject(lambda d: mutate(d['packs'][p]['entries']), diagnostic)
        # Omit or duplicate a whole case, not just individual steps.
        self._reject(lambda d: d['packs'][1].update(entries=[e for e in d['packs'][1]['entries']
                         if e['case_id'] != 'paid-reservation-expiry']), 'entry coverage/count')
        def duplicate_case(d):
            entries = d['packs'][1]['entries']
            entries[-15:] = copy.deepcopy(entries[9:24])
        self._reject(duplicate_case, 'duplicate entry identity')

    def test_association_controls(self):
        def crossed_output(d):
            # Another valid pack pin, including its real digests, must still fail.
            d['packs'][1]['output'] = copy.deepcopy(d['packs'][2]['output'])
        self._reject(crossed_output, 'output path association')
        self._reject(lambda d: d['packs'][1].update(input=d['packs'][2]['input']), 'input path association')
        for field, value in (
            ('action', 'settlement_commit'),  # a different, still-published action
            ('input_ref', temporal.FIXTURE + '#/cases/1/steps/0/body'),
            ('outcome_ref', temporal.GOLDEN.relative_to(ROOT).as_posix() + '#/cases/1/steps/0'),
            ('outcome_kind', 'rejection_code'),
            ('binding_ref', BINDING + '#/commands/items/0'),
            ('binding_status', 'BOOTSTRAP_SCHEMA_BOUND'),
        ):
            with self.subTest(field=field):
                self._reject(lambda d: d['packs'][1]['entries'][0].update({field: value}), field + ' association')
        # Same action and step id in two different cases cannot share an outcome.
        entries = self.document['packs'][1]['entries']
        a, b = next((a, b) for a in entries for b in entries
                    if a['case_id'] != b['case_id'] and a['step_id'] == b['step_id'] and a['action'] == b['action'])
        self._reject(lambda d: d['packs'][1]['entries'][entries.index(a)].update(outcome_ref=b['outcome_ref']),
                     'outcome_ref association')
        # Later evidence must retain any original BOOTSTRAP_SCHEMA_BOUND status.
        p, e = next((p, e) for p, pack in enumerate(self.document['packs'])
                    for e, entry in enumerate(pack['entries']) if entry['binding_status'] == 'BOOTSTRAP_SCHEMA_BOUND')
        self._reject(lambda d: d['packs'][p]['entries'][e].update(binding_status='MOCK_EVIDENCE'),
                     'binding_status association')

    def test_admission_cancellation_association_controls(self):
        p = len(PACKS) - 1
        self._reject(lambda d: d['packs'][p].update(input=d['packs'][3]['input']), 'input path association')
        self._reject(lambda d: d['packs'][p].update(output=d['packs'][3]['output']), 'output path association')
        for field, value in (
            ('action', 'resale_set_clock'),
            ('input_ref', cancellation.FIXTURE + '#/cases/1/steps/0/body'),
            ('outcome_ref', cancellation.GOLDEN.relative_to(ROOT).as_posix() + '#/cases/1/steps/0'),
            ('outcome_kind', 'rejection_code'),
            ('binding_ref', BINDING + '#/commands/items/0'),
            ('binding_status', 'BOOTSTRAP_SCHEMA_BOUND'),
        ):
            with self.subTest(field=field):
                self._reject(lambda d: d['packs'][p]['entries'][0].update({field: value}), field + ' association')
        self._reject(lambda d: d['packs'][p].update(limitations=[]), 'pack limitation claim')
        self._reject(lambda d: d['packs'][p]['replay_test'].update(symbol='Missing.test_missing'), 'replay location')

    def test_digest_and_reference_controls(self):
        for p in range(len(PACKS)):
            for side in ('input', 'output'):
                for digest, value in (('sha256', '0' * 64), ('gitBlob', '0' * 40)):
                    with self.subTest(pack=p, side=side, digest=digest):
                        self._reject(lambda d: d['packs'][p][side].update({digest: value}), 'digest/pin drift')
                path = self.document['packs'][p][side]['path']
                def drifted_read(candidate):
                    return _read(candidate) + (b'\n' if candidate == path else b'')
                with self.subTest(byte_drift=path), self.assertRaisesRegex(AssertionError, 'digest/pin drift'):
                    validate_index(self.document, read=drifted_read)
        for pin in ('binding_index', 'producer_tuple'):
            for digest, value in (('sha256', '0' * 64), ('gitBlob', '0' * 40)):
                self._reject(lambda d: d[pin].update({digest: value}), 'digest/pin drift')
        self._reject(lambda d: d['packs'][0]['entries'][0].update(outcome_ref='missing.json#/steps/0'),
                     'outcome_ref association')
        self._reject(lambda d: d['packs'][0]['replay_test'].update(symbol='Missing.test_missing'), 'replay location')
        replay_path = self.document['packs'][0]['replay_test']['path']
        with self.assertRaisesRegex(AssertionError, 'replay symbol absent'):
            validate_index(self.document, read=lambda p: b'' if p == replay_path else _read(p))
        for ref in ('missing.json#/steps/0', 'pack.json#/steps/99', 'pack.json#/absent'):
            with self.subTest(ref=ref), self.assertRaisesRegex(AssertionError, 'unresolvable reference'):
                _resolve({'pack.json': {'steps': []}}, ref)
        # Re-pin detached malformed outcomes for every grouped pack.
        for p in range(1, len(PACKS)):
            for mutate, diagnostic in (
                (lambda d: d['cases'].reverse(), 'outcome case association'),
                (lambda d: d['cases'][0]['steps'].pop(), 'outcome step association'),
                (lambda d: d['cases'][0]['steps'][0].update(action='settlement_commit'), 'outcome action association'),
                (lambda d: d['cases'][0]['steps'][0].update(input_ref=temporal.FIXTURE + '#/cases/1/steps/0/body'),
                 'outcome input association'),
                (lambda d: d['cases'][0]['steps'][0].update(rejection_code='CHANGED'), 'outcome kind association'),
            ):
                document = copy.deepcopy(self.document)
                path = document['packs'][p]['output']['path']
                output = journey._decode(_read(path))
                mutate(output)
                raw = _canonical(output).encode()
                document['packs'][p]['output'] = journey._pin(path, raw)
                with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(AssertionError, diagnostic):
                    validate_index(document, read=lambda p: raw if p == path else _read(p))
        self.assertEqual(validate_index(self.document), 293)

    def test_qualification_controls(self):
        for mutate, diagnostic in (
            (lambda d: d.update(normative=True), 'normative claim'),
            (lambda d: d.update(normative=0), 'normative claim'),
            (lambda d: d.update(productionReadiness=True), 'record fields'),
            (lambda d: d['qualification'].update(semanticConsumerStatus='QUALIFIED'), 'qualification'),
            (lambda d: d['qualification'].update(bootstrapIsConsumerAcceptance=True), 'qualification'),
            (lambda d: d['qualification'].update(bootstrapIsConsumerAcceptance=0), 'qualification'),
            (lambda d: d['qualification']['readQueries'].update(count=12), 'qualification'),
            (lambda d: d['qualification']['readQueries'].update(status='MOCK_EVIDENCE'), 'qualification'),
            (lambda d: d['qualification']['sd1'].update(status='CLOSED'), 'qualification'),
            (lambda d: d['qualification']['sd1'].update(owner='Builder'), 'qualification'),
            (lambda d: d['qualification']['sd1'].update(resolved=True), 'qualification'),
            (lambda d: d['qualification']['sd1'].update(userOwned=1), 'qualification'),
            (lambda d: d['qualification'].update(externalConsumerAcceptance='VERIFIED'), 'qualification'),
            (lambda d: d['qualification'].update(policyValues='APPROVED'), 'qualification'),
            (lambda d: d['nonClaims'].pop(), 'nonClaims'),
            (lambda d: d['nonClaims'].append('Production-ready.'), 'nonClaims'),
            (lambda d: d['packs'][0].update(limitations=[]), 'pack limitation claim'),
            (lambda d: d['packs'][0]['entries'][0].update(qualified=True), 'entry fields'),
        ):
            with self.subTest(diagnostic=diagnostic, mutate=mutate):
                self._reject(mutate, diagnostic)

    def test_strict_json_controls(self):
        for raw in (b'{', b'\xff', b'{"normative":false,"normative":true}',
                    b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', self.raw + b'{}'):
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, UnicodeError)):
                journey._decode(raw)
        self.assertEqual(validate_index(self.document), 293)


if __name__ == '__main__':
    unittest.main()
