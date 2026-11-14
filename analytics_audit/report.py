"""Aggregate actual engine observations; refuses missing or inconsistent runs."""
import argparse
import json
from pathlib import Path
import subprocess

from authenticated_export import TYPE_MAPPING_VERSION
from analytics_audit import (
    PROTOCOL_TRUTH, PRODUCTION_RUNTIME, PRODUCTION_CONFORMANCE,
    PRODUCTION_READINESS, PRODUCTION_ENDPOINT, FUNDS_EXECUTED, CHAIN_WRITER,
)


def validate_run(versions, cases):
    """Do not turn a partial or substituted engine run into acceptance evidence."""
    if (versions.get('polarsCrate'), versions.get('duckdbCrate'),
            versions.get('duckdbLibrary')) != ('0.55.2', '1.20000.1', 'v2.0.0'):
        raise ValueError('unexpected engine versions')
    for flag in ('extensionsDownloaded', 'externalConnections', 'fundsExecuted',
                 'productionRuntime', 'productionConformance', 'productionReadiness'):
        if versions.get(flag) is not False:
            raise ValueError('missing or enabled execution flag: ' + flag)
    ids = [case['caseId'] for case in cases]
    required = {
        'null-filter', 'aggregate-empty', 'aggregate-all-null', 'aggregate-nonempty',
        'group-Include', 'group-Exclude', 'money-lossless', 'money-text',
        'overflow-before-limit', 'export-left-join-null-filter',
        'export-left-join-null-values', 'export-null-sort-First', 'export-null-sort-Last',
    }
    required.update('export-table-%d' % i for i in range(11))
    required.update('join-%s-%s' % (kind, policy)
                    for kind in ('Inner', 'Left', 'Semi', 'Anti')
                    for policy in ('Equal', 'Unequal'))
    required.update('sort-%s-%s' % (descending, nulls)
                    for descending in ('false', 'true') for nulls in ('First', 'Last'))
    required.update('nullable-%s-%s' % (kind, op)
                    for kind in ('I64', 'U64') for op in ('Add', 'Sub', 'Mul'))
    required.update('sum-' + suffix for suffix in
                    ('i64-boundary', 'i64-negative', 'i64-positive',
                     'u64-boundary', 'u64-positive'))
    if len(ids) != len(set(ids)) or not required.issubset(ids):
        raise ValueError('duplicate or missing acceptance predicates')
    for kind in ('i64', 'u64'):
        if len([case for case in ids if case.startswith(kind + '-')]) < 11:
            raise ValueError('incomplete integer boundary matrix: ' + kind)
    if any(case.get('status') != 'PASS' for case in cases):
        raise ValueError('failed or unfinished engine observation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = []
    versions = None
    matrix = None
    for directory in args.results:
        root = Path(directory)
        observed_versions = json.loads((root / 'engine-versions.json').read_text())
        if versions is None:
            versions = observed_versions
        assert versions == observed_versions, 'engine versions differ across runs'
        group = []
        for path in sorted(root.glob('*.json')):
            if path.name == 'engine-versions.json':
                continue
            case = json.loads(path.read_text())
            assert case['status'] == 'PASS', path
            case['auditRun'] = root.name
            group.append(case)
        validate_run(observed_versions, group)
        assert group, 'missing engine observations: %s' % root
        case_ids = {case['caseId'] for case in group}
        assert len(case_ids) == len(group), 'duplicate case IDs'
        if matrix is None:
            matrix = case_ids
        assert case_ids == matrix, 'acceptance matrix differs across runs'
        cases.extend(group)
    report = {
        'schemaVersion': 1, 'nodeId': 'k-stage7-cpu-analytics-sql-audit',
        'sourceHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'headMeaning': 'uncommitted builder base; no final commit or CI assertion',
        'engineVersions': versions, 'mappingVersion': TYPE_MAPPING_VERSION,
        'localCatalogBindingVersion': 1, 'cases': cases,
        'flags': dict(protocolTruth=PROTOCOL_TRUTH, productionRuntime=PRODUCTION_RUNTIME,
                      productionConformance=PRODUCTION_CONFORMANCE,
                      productionReadiness=PRODUCTION_READINESS,
                      productionEndpoint=PRODUCTION_ENDPOINT, fundsExecuted=FUNDS_EXECUTED,
                      chainWriter=CHAIN_WRITER),
        'contractViolationsFound': [],
        'characterizations': [
            'NULL arithmetic propagates NULL in this harness and pinned engines; '
            'Feature Semantics v1 does not explicitly define this rule (Class B)',
        ],
        'undetermined': ['F64 tolerance/normalization — User/Astra',
                         'Fast64 execution profile adoption — User/Astra',
                         'Cancellation-sensitive intermediate SUM overflow order — User/Astra'],
        'nonClaims': ['production authentication', 'durability', 'economic writes',
                      'global consistency', 'incremental catch-up', 'GPU', 'performance'],
    }
    assert not any(report['flags'].values())
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('PASS: %d observations, %d cases per run, %d runs; all flags false' %
          (len(cases), len(matrix), len(args.results)))


if __name__ == '__main__':
    main()
