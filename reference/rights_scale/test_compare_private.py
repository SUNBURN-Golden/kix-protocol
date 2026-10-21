"""SYNTHETIC_OFFLINE_COMPARATOR_ONLY: no proofs, ceremony or chain execution."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

import compare_private as comparator
import replay_private as rp
from compare_localnet import object_id_bytes
from test_compare_localnet import ComparatorChecks, LABEL, object_id, ticket_report


def private_fixture():
    doc = rp.load()
    records = []
    for index, scenario in enumerate(doc['scenarios']):
        ids = {name: object_id(10000 + index * 100 + i) for i, name in enumerate(scenario['shows'])}
        world, outcomes = rp.run_scenario(scenario, doc, show_ids={n: object_id_bytes(cid) for n, cid in ids.items()})
        shows = {}
        for i, (name, show) in enumerate(world.shows.items()):
            snap, mints, _ = ticket_report(show, 20000 + index * 1000 + i * 100)
            snap = {k: snap[k] for k in ('control', 'pages', 'tickets')}
            private = show.private_snapshot()
            snap['private'] = private if private['zk_enabled'] else {'zk_enabled': False}
            shows[name] = dict(controlId=ids[name], snapshot=snap, mints=mints)
        records.append(dict(name=scenario['name'], controlIds=ids, outcomes=outcomes, shows=shows))
    return doc, {'chain': LABEL, 'scenarios': records}


class PrivateComparator(ComparatorChecks, unittest.TestCase):
    module = comparator
    fixture = staticmethod(private_fixture)

    @staticmethod
    def shows(record):
        return record['shows'].items()

    def test_show_coverage_and_identity(self):
        for mutation in ('missing shows', 'extra shows', 'missing controlIds', 'extra controlIds',
                         'missing shows field', 'missing controlIds field', 'missing show controlId', 'mismatch', 'alias'):
            with self.subTest(mutation=mutation):
                report = copy.deepcopy(self.report)
                record = next(r for r in report['scenarios'] if len(r['shows']) > 1)
                names = list(record['shows'])
                if mutation == 'missing show controlId':
                    del record['shows'][names[0]]['controlId']
                elif mutation.endswith(' field'):
                    del record[mutation.split()[1]]
                elif mutation.startswith(('missing', 'extra')):
                    kind, field = mutation.split()
                    if kind == 'missing':
                        del record[field][names[0]]
                    else:
                        record[field]['EXTRA'] = copy.deepcopy(record[field][names[0]])
                elif mutation == 'mismatch':
                    record['shows'][names[0]]['controlId'] = object_id(999999)
                else:
                    # Different textual spellings of the same object still alias.
                    alias = '0x' + record['controlIds'][names[0]][2:].lstrip('0')
                    record['controlIds'][names[1]] = alias
                    record['shows'][names[1]]['controlId'] = alias
                message = self.invoke(report, rejected=True, cli=True)
                self.assertIn(record['name'], message)
                diagnostic = ('duplicate' if mutation == 'alias' else 'mismatch' if mutation in
                              ('mismatch', 'missing show controlId') else mutation.split()[0])
                self.assertIn(diagnostic, message)

    def test_private_counters_diverge(self):
        for field in ('leaf_count', 'history_len', 'revocations', 'revoked', 'nullifiers', 'challenges'):
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                record, name, show = self.target(report)
                private = show['snapshot']['private']
                if field == 'revoked':
                    private[field]['99999'] = 1
                else:
                    private[field] += 1
                self.assertIn(f'{record["name"]}/{name}: private', self.invoke(report, rejected=True))

    def test_outcome_length_diagnostic(self):
        for delta in (-1, 1):
            with self.subTest(delta=delta):
                report = copy.deepcopy(self.report)
                record = report['scenarios'][0]
                expected = len(record['outcomes'])
                if delta < 0:
                    record['outcomes'].pop()
                else:
                    record['outcomes'].append('ok')
                message = self.invoke(report, rejected=True, cli=True)
                self.assertIn(f'length chain={expected + delta} model={expected}', message)

    def test_expansion_and_show_reordering(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            path = Path(temp) / 'expanded.json'
            comparator.expand(path)
            self.assertEqual(json.loads(path.read_text()), self.doc)
        for record in self.report['scenarios']:
            for field in ('shows', 'controlIds'):
                record[field] = dict(reversed(list(record[field].items())))
        self.invoke()

    def test_zero_ticket_and_private_off_control(self):
        scenario = copy.deepcopy(self.doc['scenarios'][0])
        scenario['steps'] = []
        doc = dict(self.doc, scenarios=[scenario])
        world, outcomes = rp.run_scenario(scenario, doc)
        ids = {n: '0x' + s.show_id.hex() for n, s in world.shows.items()}
        shows = {}
        for name, show in world.shows.items():
            snap, mints, _ = ticket_report(show, 100)
            snap['private'] = {'zk_enabled': False}
            shows[name] = dict(controlId=ids[name], mints=mints, snapshot=snap)
        self.invoke({'chain': LABEL, 'scenarios': [dict(name=scenario['name'], controlIds=ids,
                     shows=shows, outcomes=outcomes)]}, doc)
        next(iter(shows.values()))['snapshot']['private'] = {'zk_enabled': True}
        self.assertIn('private path should be off', self.invoke({'chain': LABEL, 'scenarios': [dict(
            name=scenario['name'], controlIds=ids, shows=shows, outcomes=outcomes)]}, doc, rejected=True))


if __name__ == '__main__':
    unittest.main()
