"""Run the shared workload and fault probes against one live candidate."""

from __future__ import annotations

import math
import shutil
import tempfile
import time
from pathlib import Path

from readiness.store import StoreError

from exploration.stage4.adapters import corrupt_probe_body
from exploration.stage4.workload import (
    CRASH_COMMAND,
    LOW_LOAD_NAME,
    U128_COMMAND,
    U128_MAX,
    WARMUP_COMMANDS,
    WORKLOAD_ORDER,
    budget_for,
    commands_for,
    counts,
    input_fingerprint,
    simulate,
)


def nearest_rank_p99(values):
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil(0.99 * len(ordered))
    return ordered[rank - 1]


def warmup(adapter):
    directory = Path(tempfile.mkdtemp(prefix='kixs4warm-'))
    unit = adapter.open_unit(directory, budget_for(LOW_LOAD_NAME))
    try:
        for command in WARMUP_COMMANDS:
            result = unit.apply(command)
            if result['outcome'] != 'new_success':
                raise RuntimeError('warmup failed: %s' % result)
    finally:
        unit.close()
        shutil.rmtree(directory, ignore_errors=True)


def run_workload(cluster, adapter, name):
    directory = Path(tempfile.mkdtemp(prefix='kixs4w-'))
    expected, entries, observations = simulate(name)
    unit = adapter.open_unit(directory, budget_for(name))
    samples = []
    try:
        before_disk = cluster.disk_bytes()
        begin = time.perf_counter_ns()
        for index, command in enumerate(commands_for(name)):
            started = time.perf_counter_ns()
            result = unit.apply(command)
            finished = time.perf_counter_ns()
            service_ns = finished - started
            samples.append({
                'workload': name,
                'index': index,
                'command_id': command.command_id,
                'outcome': result['outcome'],
                'service_ns': service_ns,
                'scheduled_latency_ns': service_ns,
                'log_delta': result['log_delta'],
                'admitted_entries': result['admitted_entries'],
                'capacity_reason': result['capacity_reason'],
            })
        elapsed_ns = time.perf_counter_ns() - begin
        after_disk = cluster.disk_bytes()
        cluster.note_rss()
    finally:
        unit.close()
        shutil.rmtree(directory, ignore_errors=True)
    outcomes = [sample['outcome'] for sample in samples]
    outcome_counts = counts(outcomes)
    capacity_indexes = [sample['index'] for sample in samples if sample['outcome'] == 'capacity']
    first_capacity = capacity_indexes[0] if capacity_indexes else None
    grouped = {}
    for sample in samples:
        grouped.setdefault(sample['outcome'], []).append(sample['service_ns'])
    new_success = outcome_counts['new_success']
    return {
        'workload': name,
        'exploration_data': True,
        'low_load': name == LOW_LOAD_NAME,
        'budget': budget_for(name),
        'outcomes_match_simulation': outcomes == expected,
        'expected_outcomes': expected,
        'counts': outcome_counts,
        'admitted_entries': samples[-1]['admitted_entries'] if samples else 0,
        'expected_admitted_entries': entries,
        'expected_observations': observations,
        'elapsed_ns': elapsed_ns,
        'exploration_new_success_per_elapsed_s': (
            None if elapsed_ns <= 0 else new_success * 1_000_000_000 // elapsed_ns
        ),
        'mixed_result_p99_service_ns': nearest_rank_p99([sample['service_ns'] for sample in samples]),
        'mixed_result_p99_scheduled_latency_ns': nearest_rank_p99(
            [sample['scheduled_latency_ns'] for sample in samples],
        ),
        'p99_is_product_slo': False,
        'outcomes': {
            outcome: {
                'count': len(values),
                'service_p99_ns': nearest_rank_p99(values),
                'scheduled_p99_ns': nearest_rank_p99(values),
            }
            for outcome, values in grouped.items()
        },
        'first_capacity_index': first_capacity,
        'samples_after_first_capacity': (
            None if first_capacity is None else len(samples) - first_capacity - 1
        ),
        'data_dir_delta_bytes': after_disk - before_disk,
        'log_delta_sum': _sum_optional(sample['log_delta'] for sample in samples),
        'samples': samples,
    }


def probe_u128(adapter):
    directory = Path(tempfile.mkdtemp(prefix='kixs4u128-'))
    unit = adapter.open_unit(directory, budget_for(LOW_LOAD_NAME))
    try:
        first = unit.apply(U128_COMMAND)
        stored = unit.read_amount(U128_COMMAND.command_id)
        replay = unit.apply(U128_COMMAND)
    finally:
        unit.close()
        shutil.rmtree(directory, ignore_errors=True)
    ok = (
        first['outcome'] == 'new_success'
        and stored == str(U128_MAX)
        and replay['outcome'] == 'replayed'
        and replay['first_result'] == first['first_result']
    )
    return {
        'ok': ok,
        'stored_amount_u128': stored,
        'stored_as_decimal_text': True,
        'signed_integer_narrowing': False,
    }


def probe_corrupt(adapter):
    directory = Path(tempfile.mkdtemp(prefix='kixs4bad-'))
    try:
        store = adapter.open_store(directory)
        store.append(corrupt_probe_body())
        store.close()
        adapter.corrupt_store(directory)
        try:
            opened = adapter.open_store(directory)
        except StoreError as exc:
            return {'ok': exc.code == 'CHECKSUM_MISMATCH', 'code': exc.code}
        else:
            opened.close()
            return {'ok': False, 'code': None}
    finally:
        shutil.rmtree(directory, ignore_errors=True)


def probe_process_crash(cluster, adapter):
    directory = Path(tempfile.mkdtemp(prefix='kixs4crash-'))
    unit = adapter.open_unit(directory, budget_for(LOW_LOAD_NAME))
    try:
        first = unit.apply(CRASH_COMMAND)
    finally:
        unit.close()
    if first['outcome'] != 'new_success':
        shutil.rmtree(directory, ignore_errors=True)
        return {'preserved': False, 'error': 'initial commit failed', 'detail': first}
    started = time.perf_counter_ns()
    cluster.kill()
    cluster.start()
    recovery_ns = time.perf_counter_ns() - started
    unit = adapter.open_unit(directory, budget_for(LOW_LOAD_NAME))
    try:
        second = unit.apply(CRASH_COMMAND)
    finally:
        unit.close()
        shutil.rmtree(directory, ignore_errors=True)
    return {
        'preserved': (
            second['outcome'] == 'replayed' and second['first_result'] == first['first_result']
        ),
        'restart_to_replay_ns': recovery_ns,
        'power_os_crash_injected': False,
        'hardware_flush_verified': False,
        'disk_retained_process_crash': True,
        'rto_slo': None,
    }


def exercise_candidate(cluster, adapter):
    warmup(adapter)
    workloads = [run_workload(cluster, adapter, name) for name in WORKLOAD_ORDER]
    probes = {
        'u128': probe_u128(adapter),
        'checksum_fail_closed': probe_corrupt(adapter),
        'process_crash': probe_process_crash(cluster, adapter),
    }
    match = all(item['outcomes_match_simulation'] for item in workloads)
    low_load = next(item for item in workloads if item['workload'] == LOW_LOAD_NAME)
    low_load_holds = (
        low_load['counts']['new_success'] == 8
        and all(
            low_load['counts'][name] == 0
            for name in (
                'replayed', 'business_rejected', 'conflict_retained', 'capacity',
                'unknown', 'error',
            )
        )
    )
    functional_ok = (
        match
        and low_load_holds
        and probes['u128']['ok']
        and probes['checksum_fail_closed']['ok']
        and probes['process_crash']['preserved']
    )
    return {
        'exploration_data': True,
        'input_fingerprint': input_fingerprint(),
        'functional_ok': functional_ok,
        'low_load_holds': low_load_holds,
        'workloads': workloads,
        'probes': probes,
    }


def _sum_optional(values):
    total = 0
    for value in values:
        if value is None:
            return None
        total += value
    return total
