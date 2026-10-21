"""Two jobs for the RS-1 localnet journey (scripts/run_localnet_rights_scale.py):

  --expand OUT.json     Expand vectors/public_path.json (named scenarios + every
                        matrix case) into one operation list the Node driver
                        executes literally. Single source of expansion so the
                        driver and this comparator can never drift apart.

  --report R --scenarios S --out O
                        Replay the same expanded steps on model.py, then compare
                        the driver's recorded outcomes and chain snapshot with
                        the model state, and write the journey receipt.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import model  # noqa: E402
import replay  # noqa: E402


def expand(out_path):
    vectors = replay.load()
    scenarios = list(vectors['scenarios'])
    for case in vectors['matrix']['cases']:
        scenarios.append(replay.matrix_scenario(case))
    Path(out_path).write_text(json.dumps({'scenarios': scenarios}, indent=2) + '\n')
    print(f'expanded {len(scenarios)} scenarios -> {out_path}')


def object_id_bytes(value):
    """0x-prefixed object id -> 32 raw bytes, the form model.route() expects."""
    raw = value[2:] if value.startswith('0x') else value
    return bytes.fromhex(raw.zfill(64))


def normal_outcome(outcome):
    if outcome == 'ok':
        return 'ok'
    code = outcome.get('abort')
    return {'abort': code}


def coverage(context, expected, actual, failures):
    """Require exact membership; order is immaterial."""
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        failures.append(f'{context}: missing={missing} extra={extra}')
        return False
    return True


def scenario_lookup(scenarios, records, failures):
    expected = Counter(s['name'] for s in scenarios)
    actual = Counter(r['name'] for r in records)
    for label, counts in (('expected', expected), ('reported', actual)):
        duplicates = sorted(n for n, count in counts.items() if count > 1)
        if duplicates:
            failures.append(f'scenarios: duplicate {label} names={duplicates}')
    coverage('scenarios (extra names are unexpected)', expected, actual, failures)
    # Do not replay ambiguous expected inputs using an arbitrary last value.
    return {s['name']: s for s in scenarios if expected[s['name']] == 1}


def ticket_mapping(context, mints, model_tickets, snapshots, failures):
    """Validate the bijection before using mint order to map object IDs."""
    valid = True
    if len(mints) != len(model_tickets):
        failures.append(f'{context}: mint count {len(mints)} != model {len(model_tickets)}')
        valid = False
    missing_ids = [i for i, mint in enumerate(mints) if mint.get('ticket') is None]
    if missing_ids:
        failures.append(f'{context}: missing mint ticket IDs at indexes={missing_ids}')
        return None
    ids = [mint['ticket'] for mint in mints]
    duplicates = sorted(cid for cid, count in Counter(ids).items() if count > 1)
    if duplicates:
        failures.append(f'{context}: duplicate mint ticket IDs={duplicates}')
        valid = False
    complete = coverage(f'{context}: ticket snapshots', ids, snapshots, failures)
    if not valid or not complete:
        return None
    return {mint['ticket']: t.id for mint, t in zip(mints, model_tickets)}


def compare(report_path, scenarios_path, out_path):
    report = json.loads(Path(report_path).read_text())
    scenarios = json.loads(Path(scenarios_path).read_text())['scenarios']
    failures = []
    by_name = scenario_lookup(scenarios, report.get('scenarios', []), failures)
    for record in report.get('scenarios', []):
        name = record['name']
        scenario = by_name.get(name)
        if scenario is None:
            failures.append(f'{name}: driver reported an unknown scenario')
            continue
        if record.get('controlId') is None:
            failures.append(f'{name}: missing controlId for show')
            continue
        show, labels, model_outcomes = replay.run_scenario(
            scenario, show_id=object_id_bytes(record['controlId']))
        # 1. per-step outcomes: chain actual == model actual (== scripted expect).
        chain_outcomes = [normal_outcome(o) for o in record['outcomes']]
        if chain_outcomes != model_outcomes:
            diffs = [i for i, (a, b) in enumerate(zip(chain_outcomes, model_outcomes)) if a != b]
            if len(chain_outcomes) != len(model_outcomes):
                diffs.append('length')
            failures.append(f'{name}: outcome mismatch at steps {diffs[:6]} '
                            f'chain={chain_outcomes[:8]} model={model_outcomes[:8]}')
            continue  # a divergent run makes the snapshot meaningless
        snap = record['snapshot']
        want = show.snapshot()
        # 2. control fields.
        if snap['control'] != want['control']:
            failures.append(f'{name}: control mismatch chain={snap["control"]} model={want["control"]}')
        # 3. grants (RS-3a): chain GrantControl objects map to model grants by
        # creation order, so grant_map translates chain ids to model ids for the
        # pages' delegated_to comparison.
        chain_grants = snap.get('grants', [])
        want_grants = want['grants']
        if len(chain_grants) != len(want_grants):
            failures.append(f'{name}: grant count chain {len(chain_grants)} != model {len(want_grants)}')
        grant_map = {}
        for cg, wg in zip(chain_grants, want_grants):
            grant_map[cg['id']] = wg['id']
            for field in ('delegate', 'generation', 'open'):
                if cg.get(field) != wg[field]:
                    failures.append(f'{name}: grant {wg["id"]} chain {field}={cg.get(field)} '
                                    f'!= model {wg[field]}')
        # 4. pages (all fields, in index order); delegated_to is translated.
        for p in snap['pages']:
            p['delegated_to'] = grant_map.get(p.get('delegated_to'), p.get('delegated_to'))
        if snap['pages'] != want['pages']:
            for a, b in zip(snap['pages'], want['pages']):
                if a != b:
                    failures.append(f'{name}: page {a.get("index")} mismatch chain={a} model={b}')
            if len(snap['pages']) != len(want['pages']):
                failures.append(f'{name}: page count {len(snap["pages"])} != {len(want["pages"])}')
        # 5. shards (reference sets per index).
        if snap['shards'] != want['shards']:
            failures.append(f'{name}: shard refs mismatch chain={snap["shards"]} model={want["shards"]}')
        # 6. tickets: chain objects map to model tickets by mint order.
        mints = record.get('mints', [])
        model_tickets = list(show.tickets.values())
        ticket_map = ticket_mapping(name, mints, model_tickets, snap.get('tickets', {}), failures)
        if ticket_map is None:
            continue
        for mint, t in zip(mints, model_tickets):
            if mint['slot'] != t.slot or mint['generation'] != t.generation:
                failures.append(f'{name}: mint {t.id} chain slot/gen {mint["slot"]}/{mint["generation"]}'
                                f' != model {t.slot}/{t.generation}')
        for chain_id, mid in ticket_map.items():
            fields = snap['tickets'][chain_id]
            if fields != want['tickets'][mid]:
                failures.append(f'{name}: ticket {mid} mismatch chain={fields} model={want["tickets"][mid]}')
        # 7. outstanding issuance payments and payment evidence. A delegated
        # attestation mints the payment object to the delegate; holder records who.
        payments = sorted(snap.get('payments', []), key=lambda p: p['slot'])
        want_payments = sorted(({'holder': p.holder, 'slot': p.slot, 'expected_generation': p.expected_generation,
                                 'buyer': p.buyer, 'amount': p.amount, 'payment_ref': p.payment_ref.hex()}
                                for p in show.payments.values()), key=lambda p: p['slot'])
        if payments != want_payments:
            failures.append(f'{name}: payments mismatch chain={payments} model={want_payments}')
        evidence = sorted(({'ticket': ticket_map.get(e['ticket'], e['ticket']), 'version': e['version'],
                            'buyer': e['buyer'], 'seller': e['seller'], 'amount': e['amount'],
                            'payment_ref': e['payment_ref']} for e in snap.get('evidence', [])),
                          key=lambda e: (e['ticket'], e['version']))
        want_evidence = sorted(({'ticket': ev.ticket, 'version': ev.version, 'buyer': ev.buyer,
                                 'seller': ev.seller, 'amount': ev.amount,
                                 'payment_ref': ev.payment_ref.hex()}
                                for ev in show.evidence.values()), key=lambda e: (e['ticket'], e['version']))
        if evidence != want_evidence:
            failures.append(f'{name}: evidence mismatch chain={evidence} model={want_evidence}')
    receipt = {
        'chain': report.get('chain'),
        'packageId': report.get('packageId'),
        'actors': report.get('actors'),
        'probes': report.get('probes'),
        'measurements': report.get('measurements'),
        'scenarios': [s['name'] for s in report.get('scenarios', [])],
        'authority': 'SUI_MOVE',
        'kixServicesCalled': 0,
        'ownGas': True,
        'zk': False,
        'failures': failures,
        'limitation': ('Localnet prototype only. RPC is trusted; the private path (RS-2) is exercised by '
                       'the separate private journey; delegation is limited to the RS-3a primitives '
                       '(page grant, GrantControl, the revocation cut) — no RS-3b executor mapping, no '
                       'GA redistribution (DECISION_REQUIRED, Astra), no coin/TIX module, no performance '
                       'or production claims.'),
    }
    if failures:
        receipt['status'] = 'FAILED_MODEL_DIVERGENCE'
        Path(out_path).write_text(json.dumps(receipt, indent=2) + '\n')
        raise SystemExit('MODEL_DIVERGENCE: ' + json.dumps(failures[:10]))
    receipt['status'] = 'PASSED_ACTUAL_LOCALNET'
    Path(out_path).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expand', metavar='OUT', help='write expanded scenarios to OUT and exit')
    parser.add_argument('--report', metavar='PATH', help='driver chain-report.json')
    parser.add_argument('--scenarios', metavar='PATH', help='expanded scenarios.json')
    parser.add_argument('--out', metavar='PATH', help='journey-result.json output')
    args = parser.parse_args()
    if args.expand:
        expand(args.expand)
        return
    if not (args.report and args.scenarios and args.out):
        parser.error('--report, --scenarios and --out are required together')
    compare(args.report, args.scenarios, args.out)


if __name__ == '__main__':
    main()
