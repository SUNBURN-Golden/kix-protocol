"""Compares the private-path localnet journey (client/private-localnet.mjs) with model.py.

  --expand OUT.json     copy vectors/private_path.json to OUT (the driver reads the same list)
  --report R --scenarios S --out O
                        replay the scenarios on the model and compare the driver's recorded
                        outcomes and chain snapshot with the model state; write the receipt.

What is compared: every step's outcome (including the Groth16 rejections and the prover's
refusals), the control fields, every page, every ticket, and the private-path counters (leaf
count, root-history length, revocation count, revoked generations, spent nullifiers and
challenges). Root and nullifier VALUES are not compared here: the driver recomputes every
stored root with circomlibjs from public chain data and fails on any difference.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import replay_private as rp  # noqa: E402
from compare_localnet import object_id_bytes  # noqa: E402


def expand(out_path):
    doc = rp.load()
    Path(out_path).write_text(json.dumps(doc, indent=1) + '\n')
    print(f'expanded {len(doc["scenarios"])} private scenarios -> {out_path}')


def normal(outcome):
    if outcome == 'ok':
        return 'ok'
    return {k: v for k, v in outcome.items() if k in ('abort', 'client')}


def compare(report_path, scenarios_path, out_path):
    report = json.loads(Path(report_path).read_text())
    doc = json.loads(Path(scenarios_path).read_text())
    by_name = {s['name']: s for s in doc['scenarios']}
    failures = []
    if len(report.get('scenarios', [])) != len(by_name):
        failures.append(f'scenario count: driver {len(report.get("scenarios", []))} != {len(by_name)}')
    for record in report.get('scenarios', []):
        name = record['name']
        scenario = by_name.get(name)
        if scenario is None:
            failures.append(f'{name}: unknown scenario')
            continue
        ids = {n: object_id_bytes(cid) for n, cid in record['controlIds'].items()}
        world, model_outcomes = rp.run_scenario(scenario, doc, show_ids=ids)
        chain_outcomes = [normal(o) for o in record['outcomes']]
        if chain_outcomes != model_outcomes:
            diffs = [i for i, (a, b) in enumerate(zip(chain_outcomes, model_outcomes)) if a != b]
            failures.append(f'{name}: outcome mismatch at steps {diffs[:6]} '
                            f'chain={[chain_outcomes[i] for i in diffs[:4]]} model={[model_outcomes[i] for i in diffs[:4]]}')
            continue
        for show_name, show in world.shows.items():
            got = record['shows'][show_name]
            snap, want = got['snapshot'], show.snapshot()
            if snap['control'] != want['control']:
                failures.append(f'{name}/{show_name}: control chain={snap["control"]} model={want["control"]}')
            if snap['pages'] != want['pages']:
                for a, b in zip(snap['pages'], want['pages']):
                    if a != b:
                        failures.append(f'{name}/{show_name}: page {a.get("index")} chain={a} model={b}')
                if len(snap['pages']) != len(want['pages']):
                    failures.append(f'{name}/{show_name}: page count {len(snap["pages"])} != {len(want["pages"])}')
            model_tickets = list(show.tickets.values())
            if len(got['mints']) != len(model_tickets):
                failures.append(f'{name}/{show_name}: mint count {len(got["mints"])} != {len(model_tickets)}')
            for mint, t in zip(got['mints'], model_tickets):
                chain = snap['tickets'].get(mint['ticket'])
                expected = want['tickets'][t.id]
                if chain != expected:
                    failures.append(f'{name}/{show_name}: ticket {t.id} chain={chain} model={expected}')
            private = snap['private']
            expected = show.private_snapshot()
            if not expected['zk_enabled']:
                if private != {'zk_enabled': False}:
                    failures.append(f'{name}/{show_name}: private path should be off, chain={private}')
            elif private != expected:
                failures.append(f'{name}/{show_name}: private chain={private} model={expected}')
    receipt = {
        'chain': report.get('chain'), 'packageId': report.get('packageId'), 'actors': report.get('actors'),
        'manifest': report.get('manifest'), 'constants': report.get('constants'),
        'verifiers': report.get('verifiers'), 'alternateVerifierPinCheck': report.get('alternateVerifierPinCheck'),
        'scenarios': [s['name'] for s in report.get('scenarios', [])],
        'stepsByScenario': {s['name']: len(s['outcomes']) for s in report.get('scenarios', [])},
        'structure': {s['name']: s.get('structure') for s in report.get('scenarios', [])},
        'reconstructions': {s['name']: s.get('reconstructions') for s in report.get('scenarios', [])},
        'domains': report.get('measurements', {}).get('domains'),
        'shardSpread': {s['name']: {n: sh.get('shardSpread') for n, sh in s['shows'].items()} for s in report.get('scenarios', [])},
        'timings': report.get('timings'), 'gas': report.get('gas'),
        'authority': 'SUI_MOVE', 'kixServicesCalled': 0, 'ownGas': True, 'zk': True,
        'ceremony': 'INSECURE_SINGLE_PARTY_LOCAL_FIXTURE', 'failures': failures,
        'limitation': ('Localnet prototype only. Single-party fixture ceremony, not an operational or audited setup; '
                       'RPC is trusted; the anonymity set is the shielded notes of one show and early notes have a small '
                       'set; no private resale, refund, unshield or key rotation; no delegation (RS-3a); no coin/TIX '
                       'module; no performance, anonymity or production claims.'),
    }
    if failures:
        receipt['status'] = 'FAILED_MODEL_DIVERGENCE'
        Path(out_path).write_text(json.dumps(receipt, indent=2) + '\n')
        raise SystemExit('MODEL_DIVERGENCE: ' + json.dumps(failures[:10]))
    receipt['status'] = 'PASSED_ACTUAL_LOCALNET'
    Path(out_path).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ('status', 'scenarios', 'stepsByScenario', 'domains')}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expand', metavar='OUT')
    parser.add_argument('--report')
    parser.add_argument('--scenarios')
    parser.add_argument('--out')
    args = parser.parse_args()
    if args.expand:
        expand(args.expand)
        return
    if not (args.report and args.scenarios and args.out):
        parser.error('--report, --scenarios and --out are required together')
    compare(args.report, args.scenarios, args.out)


if __name__ == '__main__':
    main()
