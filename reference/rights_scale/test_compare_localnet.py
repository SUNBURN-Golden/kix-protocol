"""SYNTHETIC_OFFLINE_COMPARATOR_ONLY: fabricated reports, never chain evidence."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import compare_localnet as comparator
import replay

HERE = Path(__file__).resolve().parent
LABEL = 'SYNTHETIC_OFFLINE_COMPARATOR_ONLY'


def object_id(number):
    return f'0x{number:064x}'


def ticket_report(show, seed):
    snap = show.snapshot()
    ids = {t.id: object_id(seed + i) for i, t in enumerate(show.tickets.values())}
    snap['tickets'] = {ids[mid]: fields for mid, fields in snap['tickets'].items()}
    mints = [dict(ticket=ids[t.id], slot=t.slot, generation=t.generation)
             for t in show.tickets.values()]
    return snap, mints, ids


def public_fixture(scenarios=None):
    vectors = replay.load()
    if scenarios is None:
        scenarios = vectors['scenarios'] + [replay.matrix_scenario(c) for c in vectors['matrix']['cases']]
    records = []
    for index, scenario in enumerate(scenarios):
        cid = object_id(10000 + index)
        show, _, outcomes = replay.run_scenario(scenario, show_id=comparator.object_id_bytes(cid))
        snap, mints, ids = ticket_report(show, 20000 + index * 100)
        grants = {g['id']: object_id(50000 + index * 100 + i) for i, g in enumerate(snap['grants'])}
        for grant in snap['grants']:
            grant['id'] = grants[grant['id']]
        for page in snap['pages']:
            page['delegated_to'] = grants.get(page['delegated_to'], page['delegated_to'])
        snap['payments'] = [dict(holder=p.holder, slot=p.slot, expected_generation=p.expected_generation,
                                 buyer=p.buyer, amount=p.amount, payment_ref=p.payment_ref.hex())
                            for p in show.payments.values()]
        snap['evidence'] = [dict(ticket=ids[e.ticket], version=e.version, buyer=e.buyer, seller=e.seller,
                                 amount=e.amount, payment_ref=e.payment_ref.hex())
                            for e in show.evidence.values()]
        records.append(dict(name=scenario['name'], controlId=cid, outcomes=outcomes,
                            mints=mints, snapshot=snap))
    return {'scenarios': scenarios}, {'chain': LABEL, 'scenarios': records}


class ComparatorChecks:
    """Shared assertions; every receipt is temporary and stdout is captured."""

    def setUp(self):
        self.doc, self.report = self.fixture()

    def invoke(self, report=None, doc=None, cli=False, rejected=False):
        report = self.report if report is None else report
        doc = self.doc if doc is None else doc
        with tempfile.TemporaryDirectory(prefix='synthetic-offline-comparator-') as temp:
            paths = [Path(temp) / n for n in ('report.json', 'scenarios.json', 'receipt.json')]
            paths[0].write_text(json.dumps(report))
            paths[1].write_text(json.dumps(doc))
            if cli:
                result = subprocess.run([sys.executable, str(HERE / self.module.__name__) + '.py',
                                         '--report', str(paths[0]), '--scenarios', str(paths[1]),
                                         '--out', str(paths[2])], capture_output=True, text=True)
                self.assertEqual(result.returncode != 0, rejected, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                if rejected:
                    self.assertIn('MODEL_DIVERGENCE', result.stderr)
            else:
                with contextlib.redirect_stdout(io.StringIO()):
                    if rejected:
                        with self.assertRaises(SystemExit) as raised:
                            self.module.compare(*paths)
                        self.assertIn('MODEL_DIVERGENCE', str(raised.exception))
                    else:
                        self.module.compare(*paths)
            receipt = json.loads(paths[2].read_text())
            self.assertEqual(receipt['status'], 'FAILED_MODEL_DIVERGENCE' if rejected else 'PASSED_ACTUAL_LOCALNET')
            self.assertEqual(bool(receipt['failures']), rejected)
            return '\n'.join(receipt['failures'])

    def target(self, report):
        for record in report['scenarios']:
            for name, show in self.shows(record):
                if len(show['mints']) >= 2:
                    return record, name, show
        self.fail('fixture needs at least two tickets')

    def test_complete_positive_controls_and_reordering(self):
        self.invoke()
        self.report['scenarios'].reverse()
        self.invoke(cli=True)

    def test_duplicate_scenario_hides_omission(self):
        omitted = self.report['scenarios'][1]['name']
        duplicate = self.report['scenarios'][0]['name']
        self.report['scenarios'][1] = copy.deepcopy(self.report['scenarios'][0])
        message = self.invoke(rejected=True)
        for term in ('duplicate', 'missing', omitted, duplicate):
            self.assertIn(term, message)

    def test_scenario_membership(self):
        for mutation in ('missing', 'extra', 'unexpected', 'duplicate'):
            with self.subTest(mutation=mutation):
                report = copy.deepcopy(self.report)
                if mutation == 'missing':
                    report['scenarios'].pop()
                elif mutation == 'extra':
                    report['scenarios'].append(dict(copy.deepcopy(report['scenarios'][0]), name='unexpected'))
                elif mutation == 'unexpected':
                    report['scenarios'][0]['name'] = 'unexpected'
                else:
                    report['scenarios'].append(copy.deepcopy(report['scenarios'][0]))
                self.assertIn(mutation, self.invoke(report, rejected=True, cli=True))

    def test_duplicate_expected_names_are_ambiguous(self):
        self.doc['scenarios'].append(copy.deepcopy(self.doc['scenarios'][0]))
        self.assertIn('duplicate expected', self.invoke(rejected=True, cli=True))

    def test_missing_ticket_snapshot(self):
        record, name, show = self.target(self.report)
        ticket = next(iter(show['snapshot']['tickets']))
        del show['snapshot']['tickets'][ticket]
        message = self.invoke(rejected=True)
        for term in (record['name'], name, 'missing', ticket):
            self.assertIn(term, message)

    def test_ticket_and_mint_coverage(self):
        for mutation in ('extra snapshot', 'substituted snapshot', 'missing tickets', 'missing mint ticket ID',
                         'missing mint', 'extra mint', 'duplicate mint'):
            with self.subTest(mutation=mutation):
                report = copy.deepcopy(self.report)
                record, name, show = self.target(report)
                tickets = show['snapshot']['tickets']
                if mutation in ('extra snapshot', 'substituted snapshot'):
                    tickets[object_id(999999)] = copy.deepcopy(next(iter(tickets.values())))
                    if mutation == 'substituted snapshot':
                        del tickets[next(iter(tickets))]
                elif mutation == 'missing tickets':
                    del show['snapshot']['tickets']
                elif mutation == 'missing mint ticket ID':
                    del show['mints'][0]['ticket']
                elif mutation == 'missing mint':
                    show['mints'].pop()
                elif mutation == 'extra mint':
                    show['mints'].append(dict(show['mints'][0], ticket=object_id(999999)))
                else:
                    show['mints'][1]['ticket'] = show['mints'][0]['ticket']
                message = self.invoke(report, rejected=True, cli=True)
                self.assertIn(record['name'], message)
                self.assertIn(name, message)
                diagnostic = ('duplicate' if mutation == 'duplicate mint' else
                              'ticket' if 'snapshot' in mutation or 'ticket' in mutation else 'mint count')
                self.assertIn(diagnostic, message)

    def test_outcome_and_snapshot_divergences(self):
        for field in ('outcomes', 'outcome length', 'control', 'pages', 'ticket'):
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                record, name, show = self.target(report)
                snap = show['snapshot']
                if field == 'outcomes':
                    record['outcomes'][0] = {'abort': -1}
                elif field == 'outcome length':
                    record['outcomes'].append('ok')
                elif field == 'control':
                    snap['control']['open'] = not snap['control']['open']
                elif field == 'pages':
                    snap['pages'][0]['issued'] += 1
                else:
                    next(iter(snap['tickets'].values()))['version'] += 1
                message = self.invoke(report, rejected=True)
                self.assertIn(record['name'], message)
                self.assertIn('outcome' if field.startswith('outcome') else 'page' if field == 'pages' else field, message)
                if field == 'outcome length':
                    self.assertIn('length', message)


class PublicComparator(ComparatorChecks, unittest.TestCase):
    module = comparator
    fixture = staticmethod(public_fixture)

    @staticmethod
    def shows(record):
        return [('', record)]

    def test_expansion_and_delegated_control(self):
        self.assertIn('rs3a_delegation_cut', [s['name'] for s in self.doc['scenarios']])
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            path = Path(temp) / 'expanded.json'
            comparator.expand(path)
            self.assertEqual(json.loads(path.read_text()), self.doc)

    def test_zero_ticket_control(self):
        scenario = copy.deepcopy(self.doc['scenarios'][0])
        scenario['steps'] = []
        show, _, outcomes = replay.run_scenario(scenario, show_id=comparator.object_id_bytes(object_id(1)))
        snap, mints, _ = ticket_report(show, 10)
        self.invoke({'chain': LABEL, 'scenarios': [dict(name=scenario['name'], controlId=object_id(1),
                     outcomes=outcomes, snapshot=snap, mints=mints)]}, {'scenarios': [scenario]})

    def test_missing_show_control_id(self):
        record = self.report['scenarios'][0]
        del record['controlId']
        self.assertIn(f'{record["name"]}: missing controlId', self.invoke(rejected=True, cli=True))

    def test_public_divergence_checks(self):
        for field in ('grants', 'shards', 'payments', 'slot', 'generation'):
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                if field in ('slot', 'generation'):
                    record, _, show = self.target(report)
                    show['mints'][0][field] += 1
                    diagnostic = 'slot/gen'
                else:
                    record = next(r for r in report['scenarios'] if r['snapshot'][field])
                    snap = record['snapshot']
                    if field == 'grants':
                        snap[field][0]['generation'] += 1
                    elif field == 'shards':
                        snap[field][0]['refs'].append('fabricated')
                    else:
                        snap[field][0]['amount'] += 1
                    diagnostic = 'grant' if field == 'grants' else 'shard' if field == 'shards' else field
                message = self.invoke(report, rejected=True)
                self.assertIn(record['name'], message)
                self.assertIn(diagnostic, message)

    def test_outstanding_evidence_translation_and_divergence(self):
        # Full vectors consume their payment evidence. Stop an existing script
        # immediately after a successful attestation to exercise retained evidence.
        scenario = copy.deepcopy(next(s for s in self.doc['scenarios'] if any(
            step['op'] == 'attest_payment' and step.get('expect', 'ok') == 'ok' for step in s['steps'])))
        end = next(i for i, step in enumerate(scenario['steps']) if
                   step['op'] == 'attest_payment' and step.get('expect', 'ok') == 'ok')
        scenario['steps'] = scenario['steps'][:end + 1]
        doc, report = public_fixture([scenario])
        self.invoke(report, doc)
        record = report['scenarios'][0]
        record['snapshot']['evidence'][0]['amount'] += 1
        self.assertIn(f'{record["name"]}: evidence mismatch', self.invoke(report, doc, rejected=True))


if __name__ == '__main__':
    unittest.main()
