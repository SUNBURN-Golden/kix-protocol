"""Reduce the RS-4 L1 load driver's raw samples into per-path results.

Reads `load-report.json` (written by client/load-l1.mjs) and the expanded
`load-scenarios.json` (load_plan.py --expand) that produced it, then writes,
per path and into the given output directory:

  <path>/samples.csv    one row per step sample (probe branches in probes.csv)
  <path>/probes.csv     branch-level rows for parallel probes
  <path>/summary.json   counts, per-op service/gas stats, probe results,
                        expectation mismatches and the conservation check

and a top-level `receipt.json` whose `status` is PASSED_MEASUREMENT only when
every expectation was met, no sample ended `unknown`/`driver_error`, the
requested workload counts were all processed, and every page/conservation
invariant in the generator's expected end-state matches the chain snapshot.

The checks here are arithmetic on the samples and the final snapshot, not a
model replay: the RS-1/RS-2 journeys already compare the same Move semantics
against model.py. All numbers are exploration data from a one-validator
localnet — no SLO, no throughput or production claims.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import model  # noqa: E402

OUTCOME_KINDS = ('ok', 'abort', 'submission_rejected', 'client_refused',
                 'unknown', 'driver_error', 'probe')


def _percentile(sorted_values, q):
    if not sorted_values:
        return None
    import math
    index = max(0, math.ceil(q * len(sorted_values)) - 1)
    return sorted_values[min(index, len(sorted_values) - 1)]


def stats(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return {
        'n': len(values), 'min': values[0], 'max': values[-1],
        'mean': round(sum(values) / len(values), 2),
        'p50': _percentile(values, 0.50), 'p95': _percentile(values, 0.95),
        'p99': _percentile(values, 0.99),
    }


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def gas_of(sample):
    g = sample.get('gas')
    if not g:
        return None
    return {k: _int(g.get(k)) for k in ('computation', 'storage', 'rebate')}


def flatten_sample(sample):
    row = {k: sample.get(k) for k in (
        'path', 'phase', 'seq', 'op', 'signer', 'outcome_kind', 'abort', 'module',
        'error', 'digest', 'service_ms', 'build_ms', 'step_ms', 'proof_ms',
        'witness_ms', 'scheduled_ms', 'parallel_k', 'congestion_reject_count',
        'expect_mismatch', 'recovered')}
    abort = sample.get('abort')
    row['abort_or_error'] = json.dumps(abort) if abort is not None else (sample.get('error') or None)
    g = gas_of(sample) or {}
    row['gas_computation'] = g.get('computation')
    row['gas_storage'] = g.get('storage')
    row['gas_rebate'] = g.get('rebate')
    row['expect'] = json.dumps(sample.get('expect'), separators=(',', ':'))
    row['detail'] = json.dumps(sample.get('detail'), separators=(',', ':')) \
        if sample.get('detail') is not None else None
    return row


def expect_label(expect):
    return json.dumps(expect, separators=(',', ':'))


def branch_rows(sample):
    rows = []
    for i, branch in enumerate(sample.get('branches') or []):
        g = branch.get('gas') or {}
        rows.append({
            'path': sample['path'], 'phase': sample['phase'], 'seq': sample['seq'],
            'probe': sample['op'], 'branch': i, 'op': branch.get('op'),
            'slot': branch.get('slot'), 'slots': json.dumps(branch.get('slots')),
            'signer': branch.get('signer'), 'outcome_kind': branch.get('outcome_kind'),
            'abort': json.dumps(branch.get('abort')) if branch.get('abort') is not None else None,
            'error': branch.get('error'), 'digest': branch.get('digest'),
            'service_ms': branch.get('service_ms'), 'build_ms': branch.get('build_ms'),
            'gas_computation': _int(g.get('computation')),
            'gas_storage': _int(g.get('storage')), 'gas_rebate': _int(g.get('rebate')),
            'detail': json.dumps(branch.get('detail'), separators=(',', ':'))
            if branch.get('detail') is not None else None,
        })
    return rows


def probe_summary(sample):
    branches = sample.get('branches') or []
    return {
        'seq': sample['seq'], 'expect': sample.get('expect'), 'met': not sample['expect_mismatch'],
        'parallel_k': sample.get('parallel_k'),
        'congestion_reject_count': sample.get('congestion_reject_count'),
        'service_ms': sample.get('service_ms'),
        'branches': [{'op': b.get('op'), 'slot': b.get('slot'),
                      'outcome_kind': b.get('outcome_kind'), 'abort': b.get('abort'),
                      'error': (b.get('error') or '')[:160],
                      'service_ms': b.get('service_ms'),
                      'gas': b.get('gas')} for b in branches],
    }


def check_pages(snapshot, expected_pages, checks, label):
    totals = {'free': 0, 'reserved': 0, 'issued': 0, 'retired': 0}
    divergent = []
    for page in snapshot.get('pages', []):
        size = page['end'] - page['start']
        conserved = page['free'] + page['reserved'] + page['issued'] + page['retired']
        if conserved != size:
            divergent.append({'page': page['index'], 'want_size': size, 'got_sum': conserved})
        for k in totals:
            totals[k] += page[k]
        exp = (expected_pages or {}).get(str(page['index']))
        if exp is not None and {k: exp[k] for k in totals} \
                != {k: page[k] for k in totals}:
            divergent.append({'page': page['index'], 'expected': exp,
                              'snapshot': {k: page[k] for k in totals}})
        if page.get('occupied') is not None \
                and page['occupied'] != page['reserved'] + page['issued'] + page['retired']:
            divergent.append({'page': page['index'], 'occupied': page['occupied'],
                              'reserved+issued+retired':
                              page['reserved'] + page['issued'] + page['retired']})
    checks.append({'name': label + '_page_conservation', 'ok': not divergent,
                   'divergences': divergent[:20]})
    return totals


def summarize_path(name, report, expected, checks):
    samples = [s for s in report['samples'] if s['path'] == name]
    counts = {k: 0 for k in OUTCOME_KINDS}
    for s in samples:
        counts[s['outcome_kind'] if s['outcome_kind'] in counts else 'driver_error'] += 1
    counts['expect_mismatches'] = sum(1 for s in samples if s.get('expect_mismatch'))
    counts['branch_unknowns'] = sum(
        1 for s in samples for b in (s.get('branches') or [])
        if b.get('outcome_kind') == 'unknown')
    counts['branch_submission_rejected'] = sum(
        1 for s in samples for b in (s.get('branches') or [])
        if b.get('outcome_kind') == 'submission_rejected')
    counts['steps'] = len(samples)

    by_op = {}
    for s in samples:
        entry = by_op.setdefault(s['op'], {'outcomes': {k: 0 for k in OUTCOME_KINDS},
                                           'service_ms': [], 'build_ms': [],
                                           'proof_ms': [], 'witness_ms': [],
                                           'gas_computation': [], 'gas_storage': [],
                                           'gas_rebate': []})
        entry['outcomes'][s['outcome_kind'] if s['outcome_kind'] in entry['outcomes']
                          else 'driver_error'] += 1
        for field in ('service_ms', 'build_ms', 'proof_ms', 'witness_ms'):
            if s.get(field) is not None:
                entry[field].append(s[field])
        g = gas_of(s)
        if g:
            for k in ('computation', 'storage', 'rebate'):
                if g[k] is not None:
                    entry['gas_' + k].append(g[k])
    op_stats = {}
    for op, entry in sorted(by_op.items()):
        g = {'computation': stats(entry['gas_computation']),
             'storage': stats(entry['gas_storage']), 'rebate': stats(entry['gas_rebate'])}
        op_stats[op] = {
            'outcomes': {k: v for k, v in entry['outcomes'].items() if v},
            'service_ms': stats(entry['service_ms']),
            'build_ms': stats(entry['build_ms']),
            'proof_ms': stats(entry['proof_ms']),
            'witness_ms': stats(entry['witness_ms']),
            'gas': g,
            'gas_total': {k: sum(entry['gas_' + k]) for k in ('computation', 'storage', 'rebate')
                          if entry['gas_' + k]},
        }

    probes = [probe_summary(s) for s in samples if s['op'] == 'parallel']
    mismatches = [{'seq': s['seq'], 'op': s['op'], 'expect': s['expect'],
                   'got': s['outcome_kind'], 'abort': s.get('abort'),
                   'error': (s.get('error') or '')[:200]}
                  for s in samples if s.get('expect_mismatch')]

    snapshot = (report.get('snapshots') or {}).get(name) or {}
    exp = expected.get(name) or {}
    path_checks = []
    totals = check_pages(snapshot, exp.get('pages'), path_checks, name)
    if exp.get('pages') is not None:
        path_checks.append({'name': name + '_expected_totals',
                            'expected': {str(i): p for i, p in exp['pages'].items()},
                            'totals': totals})
    private = snapshot.get('private') or {}
    if name == 'private' and private.get('zk_enabled'):
        for key in ('leaf_count', 'nullifiers', 'challenges', 'revocations'):
            path_checks.append({'name': 'private_' + key, 'expected': exp.get(key),
                                'snapshot': private.get(key),
                                'ok': private.get(key) == exp.get(key)})
        path_checks.append({'name': 'private_root_matches',
                            'note': private.get('cacheNoteRootMatch'),
                            'revocation': private.get('cacheRevocationRootMatch'),
                            'ok': bool(private.get('cacheNoteRootMatch')
                                       and private.get('cacheRevocationRootMatch'))})
    if name == 'delegated':
        grants = {g['label']: g for g in snapshot.get('grants', [])}
        exp_grants = exp.get('grants') or {}
        grant_diffs = []
        for label, want in exp_grants.items():
            got = grants.get(label)
            if not got or got['open'] != want['open'] or got['generation'] != want['generation']:
                grant_diffs.append({'grant': label, 'want': want, 'got': got})
        path_checks.append({'name': 'delegated_grant_states', 'ok': not grant_diffs,
                            'divergences': grant_diffs})
        exp_bind = exp.get('page_delegated_to') or {}
        bind_diffs = []
        label_of = {g['label']: g['id'] for g in snapshot.get('grants', [])}
        for page in snapshot.get('pages', []):
            want_label = exp_bind.get(str(page['index']))
            if want_label is None and str(page['index']) not in exp_bind:
                continue
            want = label_of.get(want_label) if want_label else None
            if (page.get('delegated_to') or None) != want:
                bind_diffs.append({'page': page['index'], 'want': want_label,
                                   'got': page.get('delegated_to')})
        path_checks.append({'name': 'delegated_page_bindings', 'ok': not bind_diffs,
                            'divergences': bind_diffs})

    failed = [c for c in path_checks if c.get('ok') is False]
    status = 'PASSED_MEASUREMENT'
    # A lost response stays unknown (RS-C03). That is recorded, and it is not a pass.
    if mismatches or failed or counts['unknown'] or counts['driver_error'] \
            or counts['branch_unknowns']:
        status = 'FAILED_MEASUREMENT'
    summary = {
        'path': name, 'status': status, 'counts': counts,
        'requested': report.get('requested'),
        'by_op': op_stats,
        'probes': probes,
        'expect_mismatches': mismatches,
        'checks': path_checks,
        'totals': totals,
        'control': snapshot.get('control'),
        'exploration_data': True,
        'note': ('One-validator localnet samples; closed-loop service times '
                 '(arrival_rate 0) plus fixed-k probes. Not SLOs, not throughput, '
                 'no production or durability claims.'),
    }
    return summary, samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', required=True)
    parser.add_argument('--scenarios', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    report = json.loads(Path(args.report).read_text())
    doc = json.loads(Path(args.scenarios).read_text())
    expected = doc.get('expected') or {}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    r_settings = report.get('settings') or {}
    r_show = r_settings.get('show') or {}
    r_zk = r_settings.get('zk') or {}
    r_shards = r_settings.get('shards') or {}
    fixture = '%s/%s/%s/depth-%s/K=%s' % (
        r_show.get('seated'), r_show.get('page_size'), r_shards.get('public'),
        r_zk.get('depth'), r_zk.get('root_history_k'))
    private_seated = r_show.get('private_seated')
    if private_seated is not None and private_seated != r_show.get('seated'):
        fixture += ' (private path capped at %s seats by 2^ZK_DEPTH)' % private_seated

    receipt = {
        'version': doc.get('version'), 'status': 'PASSED_MEASUREMENT',
        'packageId': report.get('packageId'), 'chain': report.get('chain'),
        'scenarioFingerprint': report.get('scenarioFingerprint'),
        'settings': report.get('settings'), 'requested': report.get('requested'),
        'constants': report.get('constants'), 'verifiers': report.get('verifiers'),
        'manifest': report.get('manifest'),
        'startedAt': report.get('startedAt'), 'endedAt': report.get('endedAt'),
        'timings': report.get('timings'), 'paths': {},
        'exploration_data': True,
        'limitation': ('Localnet load exploration only. One-validator local chain on a shared '
                       'virtual builder host; closed-loop baseline plus fixed-k probes; no '
                       'arrival-rate claim, no SLO, no throughput, no production readiness, '
                       'no durability or fault-tolerance claims. Fixture values '
                       '(%s) are Astra-owned test values, not protocol '
                       'values.' % fixture),
    }
    all_failed = []
    for name in doc.get('paths', {}):
        summary, samples = summarize_path(name, report, expected, [])
        path_dir = out / name
        path_dir.mkdir(parents=True, exist_ok=True)
        rows = [flatten_sample(s) for s in samples]
        if rows:
            with (path_dir / 'samples.csv').open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        branch = [row for s in samples for row in branch_rows(s)]
        if branch:
            with (path_dir / 'probes.csv').open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(branch[0]))
                writer.writeheader()
                writer.writerows(branch)
        (path_dir / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n')
        receipt['paths'][name] = {
            'status': summary['status'], 'counts': summary['counts'],
            'totals': summary['totals'], 'probes': len(summary['probes']),
            'expect_mismatches': len(summary['expect_mismatches']),
            'failed_checks': [c['name'] for c in summary['checks'] if c.get('ok') is False],
        }
        if summary['status'] != 'PASSED_MEASUREMENT':
            all_failed.append(name)

    # Requested-vs-actual coverage: the requested workload was either processed
    # or the shortfall is recorded — never silently shrunk.
    requested = report.get('requested') or {}
    actual = report.get('actual') or {}
    receipt['coverage'] = {
        'requested': requested,
        'actual_samples': {k: v for k, v in actual.items()},
        'shields_requested': requested.get('shield_count'),
        'shields_ok': sum(1 for s in report['samples']
                          if s['path'] == 'private' and s['op'] == 'shield'
                          and s['outcome_kind'] == 'ok'),
    }
    # Requested workload must be fully present. A shorter run is a failure
    # with the shortfall recorded, never a silent shrink of the request.
    shortfalls = []
    for name, steps in (doc.get('paths') or {}).items():
        got = sum(1 for s in report['samples'] if s.get('path') == name)
        if got != len(steps):
            shortfalls.append({'path': name, 'steps': len(steps), 'samples': got})
    shields_requested = requested.get('shield_count')
    shields_ok = receipt['coverage']['shields_ok']
    if shields_requested is not None and shields_ok != shields_requested:
        shortfalls.append({'shields_requested': shields_requested, 'shields_ok': shields_ok})
    receipt['coverage']['shortfalls'] = shortfalls
    if shortfalls:
        receipt['status'] = 'FAILED_MEASUREMENT'
        all_failed.append('coverage')
    if all_failed:
        receipt['status'] = 'FAILED_MEASUREMENT'
        receipt['failed_paths'] = all_failed
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps({'status': receipt['status'],
                      'paths': {k: v['status'] for k, v in receipt['paths'].items()},
                      'coverage': receipt['coverage']['shields_ok']}, indent=1))
    if all_failed:
        raise SystemExit('MEASUREMENT_CHECKS_FAILED: ' + ','.join(all_failed))


if __name__ == '__main__':
    main()
