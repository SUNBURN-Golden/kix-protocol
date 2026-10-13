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


def compare(report_path, scenarios_path, out_path):
    report = json.loads(Path(report_path).read_text())
    scenarios = json.loads(Path(scenarios_path).read_text())['scenarios']
    failures = []
    by_name = {s['name']: s for s in scenarios}
    if len(report.get('scenarios', [])) != len(scenarios):
        failures.append(f'scenario count: driver {len(report.get("scenarios", []))} != expanded {len(scenarios)}')
    for record in report.get('scenarios', []):
        name = record['name']
        scenario = by_name.get(name)
        if scenario is None:
            failures.append(f'{name}: driver reported an unknown scenario')
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
        # 3. pages (all fields, in index order).
        if snap['pages'] != want['pages']:
            for a, b in zip(snap['pages'], want['pages']):
                if a != b:
                    failures.append(f'{name}: page {a.get("index")} mismatch chain={a} model={b}')
            if len(snap['pages']) != len(want['pages']):
                failures.append(f'{name}: page count {len(snap["pages"])} != {len(want["pages"])}')
        # 4. shards (reference sets per index).
        if snap['shards'] != want['shards']:
            failures.append(f'{name}: shard refs mismatch chain={snap["shards"]} model={want["shards"]}')
        # 5. tickets: chain objects map to model tickets by mint order.
        mints = record.get('mints', [])
        model_tickets = list(show.tickets.values())
        if len(mints) != len(model_tickets):
            failures.append(f'{name}: mint count chain {len(mints)} != model {len(model_tickets)}')
        ticket_map = {}
        for mint, t in zip(mints, model_tickets):
            ticket_map[mint['ticket']] = t.id
            if mint['slot'] != t.slot or mint['generation'] != t.generation:
                failures.append(f'{name}: mint {t.id} chain slot/gen {mint["slot"]}/{mint["generation"]}'
                                f' != model {t.slot}/{t.generation}')
        for chain_id, fields in snap['tickets'].items():
            mid = ticket_map.get(chain_id)
            if mid is None or mid not in want['tickets']:
                failures.append(f'{name}: chain ticket {chain_id} has no model counterpart')
                continue
            if fields != want['tickets'][mid]:
                failures.append(f'{name}: ticket {mid} mismatch chain={fields} model={want["tickets"][mid]}')
        # 6. outstanding issuance payments and payment evidence.
        payments = sorted(snap.get('payments', []), key=lambda p: p['slot'])
        want_payments = sorted(({'slot': p.slot, 'expected_generation': p.expected_generation,
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
        'limitation': ('Localnet prototype only. RPC is trusted; no private path (RS-2), no delegation '
                       '(RS-3a), no GA redistribution (DECISION_REQUIRED, Astra), no coin/TIX module, '
                       'no performance or production claims.'),
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
