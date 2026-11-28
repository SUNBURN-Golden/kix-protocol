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
import test_commerce_hold_release_vectors as hold_release
import test_commerce_linked_refund_vectors as linked_refund
import test_commerce_late_payment_after_cancel_vectors as late_payment
import test_commerce_payment_ref_scope_vectors as payment_ref_scope
import test_commerce_resale_buyer_release_vectors as resale_buyer_release
import test_commerce_admission_replay_after_resale_vectors as admission_replay
import test_commerce_replaced_admission_binding_vectors as replaced_admission
import test_commerce_admission_journal_after_transfer_vectors as admission_journal
import test_commerce_cross_order_issuance_vectors as cross_order_issuance
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
    ('hold_release', hold_release, 'CommerceHoldReleaseVectorTests', 'test_complete_output_bytes_and_references', 30),
    ('linked_refund', linked_refund, 'CommerceLinkedRefundVectorTests', 'test_complete_output_bytes_and_references', 18),
    ('late_payment_after_cancel', late_payment, 'CommerceLatePaymentAfterCancelVectorTests',
     'test_complete_output_bytes_and_references', 16),
    ('payment_ref_scope', payment_ref_scope, 'CommercePaymentRefScopeVectorTests',
     'test_complete_output_bytes_and_references', 16),
    ('resale_buyer_release', resale_buyer_release, 'CommerceResaleBuyerReleaseVectorTests',
     'test_complete_output_bytes_and_references', 16),
    ('admission_replay_after_resale', admission_replay, 'CommerceAdmissionReplayAfterResaleVectorTests',
     'test_complete_output_bytes_and_references', 18),
    ('replaced_admission_binding', replaced_admission, 'CommerceReplacedAdmissionBindingVectorTests',
     'test_complete_output_bytes_and_references', 15),
    ('admission_journal_after_transfer', admission_journal, 'CommerceAdmissionJournalAfterTransferVectorTests',
     'test_complete_output_bytes_and_references', 2),
    ('cross_order_issuance', cross_order_issuance, 'CommerceCrossOrderIssuanceVectorTests',
     'test_complete_output_bytes_and_references', 2),
)
TOTAL_ENTRIES = 426
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
    'hold_release': ['Synthetic expired HELD reservations retain their slot until explicit release; historical replay preserves current reuse and rejected-key retention is process-local.'],
    'linked_refund': ['Partial mock cancellation acceptance adjusts the linked settlement while preserving cash and the issued right. Compensation policy is UNDETERMINED with Astra and JunTae. Legal refund liability is UNDETERMINED with JunTae and legal counsel.'],
    'late_payment_after_cancel': [
        'The refusals apply to the synthetic reservation command. Actual provider facts remain subject to STATE_LIFECYCLE.md §3.',
        'Compensation is UNDETERMINED with Astra and JunTae. Refund liability and actual late-fact custody are outside this history.',
    ],
    'payment_ref_scope': [
        'Payment reference scope is observed across two shows in one in-process mock host. Cross-channel exclusivity, provider identity and funds finality are outside this evidence.',
        'Rejected-key retention is process-local. Product TTLs, fees and compensation remain UNDETERMINED with Astra and JunTae, and provider and legal terms remain with their existing owners.',
    ],
    'resale_buyer_release': [
        'Non-normative mock evidence with semantic consumption on HOLD_SEMANTIC. The resale_release_hold binding is BOOTSTRAP_SCHEMA_BOUND.',
        'The release replay preserves its first LISTED receipt while the current listing retains the fresh BUY_HELD hold. Payment observation and transfer are separate mock effects.',
    ],
    'admission_replay_after_resale': [
        'Non-normative mock evidence with semantic consumption on HOLD_SEMANTIC. The replay is a first receipt and gives no current admission authority.',
        'The fresh version-1 consume returns STALE_VERSION. Current ownership and accepted journals are test-harness evidence from one in-process host.',
    ],
    'replaced_admission_binding': [
        'Non-normative mock evidence with semantic consumption on HOLD_SEMANTIC. The gate and request checks use one replacement authorization and synthetic time.',
        'Detached diagnostics describe one in-process host. Product TTLs, fees and compensation remain UNDETERMINED with Astra and the User, and legal and provider terms retain their existing owners.',
    ],
    'admission_journal_after_transfer': [
        'Non-normative mock evidence with semantic consumption on HOLD_SEMANTIC. Both entries index published checkpoint receipts with separate local diagnostics.',
        'A journal match records historical replay equality only. The explicit transfer makes both diagnostics return STALE_VERSION with zero new consumptions.',
    ],
    'cross_order_issuance': [
        'Non-normative mock evidence with semantic consumption on HOLD_SEMANTIC. Each branch replays the same pinned payment-2 checkpoint in a fresh in-process host.',
        'The receipt and refusal describe local issuance binding. Both preserve the transferred resale right and record zero admission consumption.',
    ],
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
    write_names = set(catalogue.core_names + catalogue.fsm_names)
    _check(not set(journey.journey.READ_MODEL_QUERY_NAMES) & write_names, 'write catalogue read claim')
    commands = binding['commands']['items']
    actions = [item['action'] for item in commands]
    _check(len(actions) == len(set(actions)) and set(actions) == write_names, 'binding action coverage')
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
    _check(total == TOTAL_ENTRIES, 'total coverage')
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
        self.assertEqual(validate_index(self.document), TOTAL_ENTRIES)

    def test_complete_index(self):
        self.assertEqual(validate_index(self.document), TOTAL_ENTRIES)

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
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'admission_cancellation')
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

    def test_linked_refund_crossed_references(self):
        pack = next(p for p in self.document['packs'] if p['id'] == 'linked_refund')
        entries = {e['step_id']: e for e in pack['entries']}
        for field in ('input_ref', 'outcome_ref', 'binding_ref'):
            def cross(d):
                linked = next(p for p in d['packs'] if p['id'] == 'linked_refund')
                target = next(e for e in linked['entries'] if e['step_id'] == 'observe-mock-acceptance')
                target[field] = entries['bind-refund'][field]
            with self.subTest(field=field):
                self._reject(cross, field + ' association')

    def test_late_payment_crossed_references(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'late_payment_after_cancel')
        entries = self.document['packs'][p]['entries']
        original = next(i for i, entry in enumerate(entries) if entry['step_id'] == 'late-payment-a')
        for step_id in ('replay-late-payment-a', 'payment-b'):
            other = next(entry for entry in entries if entry['step_id'] == step_id)
            self.assertEqual(other['action'], entries[original]['action'])
            for field in ('input_ref', 'outcome_ref'):
                with self.subTest(step=step_id, field=field):
                    self._reject(
                        lambda d: d['packs'][p]['entries'][original].update({field: other[field]}),
                        field + ' association',
                    )

    def test_payment_ref_scope_crossed_references(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'payment_ref_scope')
        for field in ('input_ref', 'outcome_ref'):
            def swap(d):
                entries = {entry['step_id']: entry for entry in d['packs'][p]['entries']}
                refused, recorded = entries['reuse-primary'], entries['resale-payment']
                self.assertEqual(refused['action'], recorded['action'])
                refused[field], recorded[field] = recorded[field], refused[field]

            with self.subTest(field=field):
                self._reject(swap, field + ' association')

    def test_cross_order_issuance_swapped_references(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'cross_order_issuance')
        issued, refused = self.document['packs'][p]['entries']
        self.assertEqual(issued['action'], refused['action'])
        self.assertEqual(issued['step_id'], refused['step_id'])
        self.assertEqual((issued['outcome_kind'], refused['outcome_kind']), ('receipt', 'rejection_code'))
        for field in ('outcome_ref', 'input_ref'):
            def swap(document):
                left, right = document['packs'][p]['entries']
                left[field], right[field] = right[field], left[field]

            with self.subTest(field=field):
                self._reject(swap, field + ' association')

    def test_resale_buyer_release_crossed_outcome_references(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'resale_buyer_release')
        entries = {entry['step_id']: entry for entry in self.document['packs'][p]['entries']}
        for step_id in ('release-wrong-buyer', 'release-hold', 'replay-release-hold'):
            with self.subTest(step=step_id):
                self.assertEqual(entries[step_id]['binding_ref'], BINDING + '#/commands/items/65')
                self.assertEqual(entries[step_id]['binding_status'], 'BOOTSTRAP_SCHEMA_BOUND')

        def swap(document):
            entries = {entry['step_id']: entry for entry in document['packs'][p]['entries']}
            release, replay = entries['release-hold'], entries['replay-release-hold']
            self.assertEqual(release['action'], replay['action'])
            inputs = resale_buyer_release.FIXTURE
            documents = {inputs: journey._decode(_read(inputs))}
            self.assertTrue(_same(_resolve(documents, release['input_ref']),
                                  _resolve(documents, replay['input_ref'])))
            release['outcome_ref'], replay['outcome_ref'] = replay['outcome_ref'], release['outcome_ref']

        self._reject(swap, 'outcome_ref association')

    def test_admission_replay_crossed_outcome_references(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'admission_replay_after_resale')

        def swap(document):
            entries = {entry['step_id']: entry for entry in document['packs'][p]['entries']}
            original, replay = entries['authorize'], entries['replay-authorize']
            self.assertEqual(original['action'], replay['action'])
            inputs = admission_replay.FIXTURE
            documents = {inputs: journey._decode(_read(inputs))}
            self.assertTrue(_same(_resolve(documents, original['input_ref']),
                                  _resolve(documents, replay['input_ref'])))
            original['outcome_ref'], replay['outcome_ref'] = replay['outcome_ref'], original['outcome_ref']

        self._reject(swap, 'outcome_ref association')

    def test_replaced_admission_binding_crossed_outcome_references(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'replaced_admission_binding')
        for entry in self.document['packs'][p]['entries'][12:]:
            with self.subTest(step=entry['step_id']):
                self.assertEqual(entry['binding_ref'], BINDING + '#/commands/items/74')
                self.assertEqual(entry['binding_status'], 'MOCK_EVIDENCE')

        def swap(document):
            entries = {entry['step_id']: entry for entry in document['packs'][p]['entries']}
            old_gate, old_request = entries['consume-old-gate'], entries['consume-old-request']
            old_gate['outcome_ref'], old_request['outcome_ref'] = old_request['outcome_ref'], old_gate['outcome_ref']

        self._reject(swap, 'outcome_ref association')

    def test_admission_journal_checkpoint_associations(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'admission_journal_after_transfer')
        path = admission_journal.GOLDEN.relative_to(ROOT).as_posix()
        entries = self.document['packs'][p]['entries']
        for index, (case_id, step_id, action, binding_index) in enumerate((
            ('matching-ownership', 'resale-expiry-clock', 'resale_set_clock', 61),
            ('transferred-ownership', 'transfer', 'resale_accept_resale', 69),
        )):
            with self.subTest(case=case_id):
                pointer = f'#/cases/{index}/steps/0'
                self.assertEqual(entries[index], {
                    'case_id': case_id, 'step_id': step_id, 'action': action,
                    'input_ref': admission_journal.FIXTURE + pointer + '/body',
                    'outcome_ref': path + pointer, 'outcome_kind': 'receipt',
                    'binding_ref': BINDING + f'#/commands/items/{binding_index}',
                    'binding_status': 'MOCK_EVIDENCE',
                })

        def swap(document):
            matching, transferred = document['packs'][p]['entries']
            matching['outcome_ref'], transferred['outcome_ref'] = transferred['outcome_ref'], matching['outcome_ref']

        self._reject(swap, 'outcome_ref association')

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

        def cross_case(d):
            cases = d['cases']
            if len(cases) == 1:
                cases[0]['id'] = 'other-case'
            else:
                cases.reverse()

        # Re-pin detached malformed outcomes for every grouped pack.
        for p in range(1, len(PACKS)):
            for mutate, diagnostic in (
                (cross_case, 'outcome case association'),
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
                with self.subTest(pack=p, diagnostic=diagnostic), self.assertRaisesRegex(AssertionError, diagnostic):
                    validate_index(document, read=lambda p: raw if p == path else _read(p))
        self.assertEqual(validate_index(self.document), TOTAL_ENTRIES)

    def test_hold_release_association_controls(self):
        p = next(i for i, pack in enumerate(PACKS) if pack[0] == 'hold_release')
        for side in ('input', 'output'):
            self._reject(lambda d: d['packs'][p].update({side: d['packs'][1][side]}),
                         side + ' path association')
        for field, value in (
            ('action', 'resale_set_clock'),
            ('input_ref', hold_release.FIXTURE + '#/cases/1/steps/0/body'),
            ('outcome_ref', hold_release.GOLDEN.relative_to(ROOT).as_posix() + '#/cases/1/steps/0'),
            ('outcome_kind', 'rejection_code'),
            ('binding_ref', BINDING + '#/commands/items/0'),
            ('binding_status', 'BOOTSTRAP_SCHEMA_BOUND'),
        ):
            with self.subTest(field=field):
                self._reject(lambda d: d['packs'][p]['entries'][0].update({field: value}),
                             field + ' association')
        self._reject(lambda d: d['packs'][p].update(limitations=[]), 'pack limitation claim')
        self._reject(lambda d: d['packs'][p]['replay_test'].update(
            symbol='CommerceTemporalVectorTests.test_complete_output_bytes_and_references'), 'replay location')

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
        self.assertEqual(validate_index(self.document), TOTAL_ENTRIES)


if __name__ == '__main__':
    unittest.main()
