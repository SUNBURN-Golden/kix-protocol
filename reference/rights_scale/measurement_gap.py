"""Offline per-path measurement-gap report for RS-4 load records.

Reads the same record files summarize_load.py consumes — the expanded
`load-scenarios.json` (load_plan.py --expand) and the driver's
`load-report.json` — plus the record's `receipt.json` when present, then
writes `gap-report.json` computing, per path (public/private/delegated):

  planned vs measured step counts, split by phase and by op;
  which expectation-bearing ("predicate") steps and named concurrency
  probes were never sampled, listed individually;
  the shield denominator (shields_ok vs shields_requested);
  whether the path's expected end-state is evaluable at all (it is only
  evaluable when every planned step was sampled).

A receipt status is quoted, never trusted: the recorded L2 failure carries
paths whose receipt row says PASSED_MEASUREMENT on zero samples, and a
delegated_grant_states check that "failed" against an empty snapshot. This
report recomputes the denominators from the scenario/report pair itself so
any consumer — including whichever L2 option is picked — sees the same
missing-path structure without re-running anything.

Coverage arithmetic on the record files only. This runs no measurement,
decides nothing, and passes/fails no gate: it exits non-zero only when its
inputs are unreadable or malformed.

  --record DIR     read DIR/{load-scenarios.json,load-report.json,receipt.json}
  --report F --scenarios F --out F
                   read/write explicit paths instead
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import summarize_load  # noqa: E402

OUTCOME_KINDS = summarize_load.OUTCOME_KINDS
_int = summarize_load._int

VERSION = 'kix-rs4-load-gap-report-v1'

# expected[] entries that only echo the requested workload are not
# end-state checks.
WORKLOAD_ECHOES = ('invalidation_count', 'consume_count')


def _is_predicate(step):
    """A predicate step asserts something: a named parallel probe, or an
    expectation other than plain ok/any (expected abort or client refusal)."""
    if step.get('op') == 'parallel':
        return True
    return step.get('expect') not in (None, 'ok', 'any')


def _end_state_checks(expected):
    """End-state check names a path's snapshot would be evaluated against."""
    return [k for k in (expected or {}) if k not in WORKLOAD_ECHOES]


def path_gap(name, steps, samples, expected, receipt_path, snapshot_present):
    planned_seqs = {}
    for step in steps:
        seq = _int(step.get('seq'))
        if seq is not None:
            planned_seqs[seq] = step

    by_seq = {}
    unplanned = 0
    for sample in samples:
        seq = _int(sample.get('seq'))
        if seq is None or seq not in planned_seqs:
            unplanned += 1
        if seq is not None:
            by_seq[seq] = sample

    if by_seq:
        lo, hi = min(by_seq), max(by_seq)
        missing = [s for s in sorted(planned_seqs) if lo <= s <= hi and s not in by_seq]
    else:
        lo = hi = None
        missing = []

    if not samples:
        coverage = 'none'
    elif all(s in by_seq for s in planned_seqs):
        coverage = 'full'
    else:
        coverage = 'partial'

    phases = {}
    by_op = {}
    predicates = []
    probes_planned = []
    probes_measured = []
    for step in steps:
        seq = _int(step.get('seq'))
        sample = by_seq.get(seq)
        phase = step.get('phase') or 'unphased'
        phases.setdefault(phase, {'planned': 0, 'measured': 0})
        phases[phase]['planned'] += 1
        by_op.setdefault(step.get('op'), {'planned': 0, 'measured': 0})
        by_op[step.get('op')]['planned'] += 1
        if sample is not None:
            phases[phase]['measured'] += 1
            by_op[step.get('op')]['measured'] += 1
        if step.get('op') == 'parallel':
            probe = {'seq': seq, 'name': step.get('name'),
                     'k': len(step.get('of') or []), 'expect': step.get('expect')}
            probes_planned.append(probe)
            if sample is not None:
                measured_probe = dict(probe)
                measured_probe['met'] = not sample.get('expect_mismatch')
                measured_probe['outcome_kind'] = sample.get('outcome_kind')
                probes_measured.append(measured_probe)
        if _is_predicate(step):
            predicates.append({'seq': seq, 'phase': phase, 'op': step.get('op'),
                               'name': step.get('name'), 'expect': step.get('expect'),
                               'comment': step.get('comment'), 'measured': sample is not None})

    outcomes = {k: 0 for k in OUTCOME_KINDS}
    for sample in samples:
        kind = sample.get('outcome_kind')
        outcomes[kind if kind in outcomes else 'driver_error'] += 1

    return {
        'planned_steps': len(steps),
        'measured_steps': len(samples),
        'coverage': coverage,
        'measured_seqs': {'min': lo, 'max': hi, 'missing_in_range': missing,
                          'unplanned': unplanned},
        'outcomes': {k: v for k, v in outcomes.items() if v},
        'expect_mismatches': sum(1 for s in samples if s.get('expect_mismatch')),
        'phases': phases,
        'by_op': by_op,
        'predicates': {
            'planned': len(predicates),
            'measured': sum(1 for p in predicates if p['measured']),
            'unmeasured': [{k: p[k] for k in ('seq', 'phase', 'op', 'name', 'expect', 'comment')}
                           for p in predicates if not p['measured']],
        },
        'probes': {
            'planned': probes_planned,
            'measured': probes_measured,
            'unmeasured': [p for p in probes_planned
                           if p['seq'] not in {m['seq'] for m in probes_measured}],
        },
        'end_state': {'evaluable': coverage == 'full',
                      'checks': _end_state_checks(expected),
                      'snapshot_present': snapshot_present},
        'receipt_path_status': (receipt_path or {}).get('status'),
        'receipt_failed_checks': (receipt_path or {}).get('failed_checks'),
    }


def build_gap_report(doc, report, receipt=None):
    """Compute the gap report for one scenario/report pair (+optional receipt)."""
    receipt = receipt or {}
    requested = report.get('requested') or doc.get('requested') or {}
    snapshots = report.get('snapshots') or {}
    receipt_paths = receipt.get('paths') or {}

    paths = {}
    for name, steps in (doc.get('paths') or {}).items():
        samples = [s for s in report.get('samples') or [] if s.get('path') == name]
        expected = doc.get('expected', {}).get(name) or {}
        paths[name] = path_gap(name, steps, samples, expected, receipt_paths.get(name),
                               name in snapshots)

    shields_ok = sum(1 for s in report.get('samples') or []
                     if s.get('path') == 'private' and s.get('op') == 'shield'
                     and s.get('outcome_kind') == 'ok')
    shields_requested = requested.get('shield_count')

    shortfalls = []
    for name, steps in (doc.get('paths') or {}).items():
        got = sum(1 for s in report.get('samples') or [] if s.get('path') == name)
        if got != len(steps):
            shortfalls.append({'path': name, 'steps': len(steps), 'samples': got})
    if shields_requested is not None and shields_ok != shields_requested:
        shortfalls.append({'shields_requested': shields_requested, 'shields_ok': shields_ok})

    return {
        'version': VERSION,
        'record_status': receipt.get('status'),
        'scenario_fingerprint': report.get('scenarioFingerprint'),
        'requested': requested,
        'paths': paths,
        'coverage': {'shields_requested': shields_requested, 'shields_ok': shields_ok,
                     'shortfalls': shortfalls},
        'exploration_data': True,
        'note': ('Coverage arithmetic on the record files only; runs no '
                 'measurement, decides nothing. Workload predicate steps '
                 'only — no RS-C/RR profile-id claim.'),
    }


def _load(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise SystemExit('UNREADABLE_INPUT ' + str(path) + ': ' + str(exc))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', help='record directory holding '
                        'load-scenarios.json, load-report.json and, if '
                        'present, receipt.json')
    parser.add_argument('--report', help='load-report.json path')
    parser.add_argument('--scenarios', help='expanded load-scenarios.json path')
    parser.add_argument('--receipt', help='receipt.json path (quoted, not trusted)')
    parser.add_argument('--out', help='gap-report.json destination; defaults '
                        'to <record>/gap-report.json')
    args = parser.parse_args()

    report_path = args.report
    scenarios_path = args.scenarios
    receipt_path = args.receipt
    out_path = args.out
    if args.record:
        record = Path(args.record)
        scenarios_path = scenarios_path or str(record / 'load-scenarios.json')
        report_path = report_path or str(record / 'load-report.json')
        if receipt_path is None and (record / 'receipt.json').exists():
            receipt_path = str(record / 'receipt.json')
        out_path = out_path or str(record / 'gap-report.json')
    if not report_path or not scenarios_path:
        parser.error('--report and --scenarios are required unless --record supplies them')
    if not out_path:
        parser.error('--out is required unless --record supplies it')

    doc = _load(scenarios_path)
    report = _load(report_path)
    receipt = _load(receipt_path) if receipt_path else None
    gap = build_gap_report(doc, report, receipt)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(gap, indent=1) + '\n')
    print(json.dumps({'record_status': gap['record_status'],
                      'paths': {k: v['coverage'] for k, v in gap['paths'].items()},
                      'shields_ok': gap['coverage']['shields_ok']}, indent=1))


if __name__ == '__main__':
    main()
