"""Recorder of dynamic host conditions for RS-4 load runs.

The L1 record's host.json holds static facts only (cpu_count, mem_total_bytes,
versions). The rs-4-l2 decision attributes its FAILED_MEASUREMENT to shared-host
conditions that change during a run (load average, memory pressure, a VM
suspend); nothing committed captured them. This module is stdlib only and has
two subcommands.

  sample     append one JSON line per interval to a JSONL file: /proc/loadavg,
             /proc/meminfo (MemTotal, MemAvailable, SwapTotal, SwapFree),
             /proc/uptime, the btime line of /proc/stat, os.cpu_count(),
             the sched_getaffinity size, the wall clock and the monotonic clock.
             Runs until --count samples were written or SIGTERM/SIGINT.
  summarize  reduce such a JSONL to host-conditions-summary.json: min/median/max
             of each load average field, raw and divided by the affinity core
             count, min/median/max MemAvailable and SwapFree, and every
             wall-clock gap between consecutive samples larger than
             gap-factor x interval.

Measured values and detected gaps only. There is no threshold, no verdict and no
default for the interval or the gap factor: the acceptable load level for an
RS-4 L2 attempt is UNDETERMINED (owner: User), so both numbers are required
arguments. A reported gap is not labelled: a VM suspend widens the wall clock
gap but not the monotonic gap, a scheduling stall widens both, and the summary
lists both numbers without interpreting them.

This module measures nothing by itself and is not wired into the L1 runner.
Exit status is non-zero only for unreadable or malformed input.

  sample    --out F --interval S [--count N] [--proc DIR]
  summarize --samples F --interval S --gap-factor N [--out F]
"""
import argparse
import json
import os
import signal
import statistics
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

SAMPLE_VERSION = 'kix-rs4-host-conditions-sample-v1'
SUMMARY_VERSION = 'kix-rs4-host-conditions-summary-v1'
SUMMARY_FILENAME = 'host-conditions-summary.json'
LOAD_FIELDS = ('load1', 'load5', 'load15')
MEM_FIELDS = (('mem_total_bytes', 'MemTotal'),
              ('mem_available_bytes', 'MemAvailable'),
              ('swap_total_bytes', 'SwapTotal'),
              ('swap_free_bytes', 'SwapFree'))

SUMMARY_NOTE = ('Measured values and detected clock gaps only. No threshold, '
                'no verdict: the acceptable load level is UNDETERMINED (User).')


# --- parsers: text in, dict out, ValueError on malformed text ---------------

def parse_loadavg(text):
    parts = text.split()
    if len(parts) < 5 or '/' not in parts[3]:
        raise ValueError('malformed /proc/loadavg: ' + repr(text[:80]))
    try:
        runnable, total = parts[3].split('/', 1)
        return {'load1': float(parts[0]), 'load5': float(parts[1]),
                'load15': float(parts[2]), 'runnable': int(runnable),
                'total_threads': int(total), 'last_pid': int(parts[4])}
    except ValueError:
        raise ValueError('malformed /proc/loadavg: ' + repr(text[:80]))


def parse_meminfo(text):
    """Bytes for MemTotal/MemAvailable/SwapTotal/SwapFree; a key absent from
    the text is None. A malformed value for a wanted key is a ValueError."""
    wanted = {key for _, key in MEM_FIELDS}
    kb = {}
    for line in text.splitlines():
        key, sep, rest = line.partition(':')
        if not sep or key not in wanted:
            continue
        fields = rest.split()
        if not fields or not fields[0].isdigit() or fields[1:] not in ([], ['kB']):
            raise ValueError('malformed /proc/meminfo line: ' + repr(line))
        kb[key] = int(fields[0])
    return {name: (kb[key] * 1024 if key in kb else None) for name, key in MEM_FIELDS}


def parse_uptime(text):
    parts = text.split()
    try:
        if len(parts) != 2:
            raise ValueError
        return {'uptime_s': float(parts[0]), 'idle_s': float(parts[1])}
    except ValueError:
        raise ValueError('malformed /proc/uptime: ' + repr(text[:80]))


def parse_stat_btime(text):
    """The btime line of /proc/stat as int; None when the line is absent."""
    for line in text.splitlines():
        parts = line.split()
        if parts and parts[0] == 'btime':
            try:
                return int(parts[1])
            except (IndexError, ValueError):
                raise ValueError('malformed /proc/stat btime: ' + repr(line))
    return None


# --- sampler -----------------------------------------------------------------

def affinity_cores():
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return None


def _utc(epoch_s):
    return datetime.fromtimestamp(epoch_s, tz=timezone.utc).strftime(
        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def read_sample(proc=Path('/proc'), now=None):
    """One sample. A missing or malformed proc file never raises: its fields
    become None and errors[<name>] holds the message. `now` is an optional
    (wall_epoch_s, mono_s) pair for callers that supply the clocks."""
    proc = Path(proc)
    wall, mono = now if now is not None else (time.time(), time.monotonic())
    errors = {}

    def read(name, parser, empty):
        try:
            return parser((proc / name).read_text())
        except (OSError, ValueError) as exc:
            errors[name] = str(exc)
            return empty

    loadavg = read('loadavg', parse_loadavg, None)
    mem = read('meminfo', parse_meminfo, {name: None for name, _ in MEM_FIELDS})
    uptime = read('uptime', parse_uptime, {'uptime_s': None, 'idle_s': None})
    btime = read('stat', parse_stat_btime, None)
    return {'v': SAMPLE_VERSION, 'wall_utc': _utc(wall), 'wall_epoch_s': wall,
            'mono_s': mono, 'loadavg': loadavg, 'mem': mem,
            'uptime_s': uptime['uptime_s'], 'idle_s': uptime['idle_s'],
            'btime': btime, 'cpu_count': os.cpu_count(),
            'affinity_cores': affinity_cores(), 'errors': errors}


def sample_loop(out, interval_s, count=None, stop=None, proc=Path('/proc')):
    """Append one JSON line per interval to `out`, flushing every line. Stops
    after `count` samples or when the `stop` event is set; returns the number
    of lines written."""
    stop = stop if stop is not None else threading.Event()
    written = 0
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('a') as fh:
        while not stop.is_set() and (count is None or written < count):
            fh.write(json.dumps(read_sample(proc), sort_keys=True) + '\n')
            fh.flush()
            written += 1
            if count is not None and written >= count:
                break
            stop.wait(interval_s)
    return written


# --- summarizer --------------------------------------------------------------

def load_samples(path):
    """Samples from a JSONL file, in file order. Blank lines are skipped; an
    unreadable file, a line that is not a JSON object or a sample without a
    numeric wall_epoch_s ends in SystemExit('UNREADABLE_INPUT ...')."""
    samples = []
    try:
        lines = Path(path).read_text().splitlines()
    except OSError as exc:
        raise SystemExit('UNREADABLE_INPUT ' + str(path) + ': ' + str(exc))
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            sample = json.loads(line)
        except ValueError as exc:
            raise SystemExit('UNREADABLE_INPUT %s line %d: %s' % (path, number, exc))
        if (not isinstance(sample, dict) or isinstance(sample.get('wall_epoch_s'), bool)
                or not isinstance(sample.get('wall_epoch_s'), (int, float))):
            raise SystemExit('UNREADABLE_INPUT %s line %d: not a sample object '
                             'with numeric wall_epoch_s' % (path, number))
        samples.append(sample)
    return samples


def stats(values):
    values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if not values:
        return None
    return {'n': len(values), 'min': min(values),
            'median': statistics.median(values), 'max': max(values)}


def clock_gaps(samples, interval_s, gap_factor):
    """Every consecutive pair whose wall-clock distance exceeds
    gap_factor x interval_s. mono_gap_s is listed beside it, uninterpreted."""
    threshold = gap_factor * interval_s
    gaps = []
    for index in range(1, len(samples)):
        prev, nxt = samples[index - 1], samples[index]
        wall_gap = nxt['wall_epoch_s'] - prev['wall_epoch_s']
        if wall_gap > threshold:
            mono_gap = None
            if isinstance(prev.get('mono_s'), (int, float)) and isinstance(
                    nxt.get('mono_s'), (int, float)):
                mono_gap = nxt['mono_s'] - prev['mono_s']
            gaps.append({'index': index, 'prev_wall_utc': prev.get('wall_utc'),
                         'next_wall_utc': nxt.get('wall_utc'),
                         'wall_gap_s': wall_gap, 'mono_gap_s': mono_gap,
                         'threshold_s': threshold})
    return gaps


def _cores(sample):
    for key in ('affinity_cores', 'cpu_count'):
        value = sample.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
    return None


def _field(sample, group, key):
    container = sample.get(group)
    return container.get(key) if isinstance(container, dict) else None


def _range(values):
    values = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
    return {'min': min(values), 'max': max(values)} if values else None


def summarize(samples, interval_s, gap_factor):
    walls = [s['wall_epoch_s'] for s in samples]
    gaps = clock_gaps(samples, interval_s, gap_factor)
    loadavg = {}
    for field in LOAD_FIELDS:
        loadavg[field] = stats([_field(s, 'loadavg', field) for s in samples])
        per_core = []
        for s in samples:
            value, cores = _field(s, 'loadavg', field), _cores(s)
            if isinstance(value, (int, float)) and cores:
                per_core.append(value / cores)
        loadavg[field + '_per_core'] = stats(per_core)
    uptimes = [s.get('uptime_s') for s in samples]
    uptime_pairs = [(a, b) for a, b in zip(uptimes, uptimes[1:])
                    if isinstance(a, (int, float)) and isinstance(b, (int, float))]
    return {
        'version': SUMMARY_VERSION,
        'interval_s': interval_s, 'gap_factor': gap_factor,
        'sample_count': len(samples),
        'first_wall_utc': samples[0].get('wall_utc') if samples else None,
        'last_wall_utc': samples[-1].get('wall_utc') if samples else None,
        'span_s': (walls[-1] - walls[0]) if samples else None,
        'cpu_count': _range([s.get('cpu_count') for s in samples]),
        'affinity_cores': _range([s.get('affinity_cores') for s in samples]),
        'normalised_by': 'affinity_cores (cpu_count when affinity is unavailable)',
        'loadavg': loadavg,
        'mem': {'mem_available_bytes': stats([_field(s, 'mem', 'mem_available_bytes')
                                              for s in samples]),
                'swap_free_bytes': stats([_field(s, 'mem', 'swap_free_bytes')
                                          for s in samples])},
        'btime_values': sorted({s['btime'] for s in samples
                                if isinstance(s.get('btime'), int)}),
        'uptime_regressions': sum(1 for a, b in uptime_pairs if b < a),
        'wall_clock_backward_steps': sum(1 for a, b in zip(walls, walls[1:]) if b < a),
        'clock_gaps': gaps, 'clock_gap_count': len(gaps),
        'largest_wall_gap_s': max((b - a for a, b in zip(walls, walls[1:])), default=None),
        'samples_with_errors': sum(1 for s in samples if s.get('errors')),
        'exploration_data': True,
        'note': SUMMARY_NOTE,
    }


# --- CLI ---------------------------------------------------------------------

def _positive(parser, name, value):
    if not value > 0:
        parser.error(name + ' must be greater than 0')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)

    p_sample = sub.add_parser('sample', help='append samples to a JSONL file')
    p_sample.add_argument('--out', required=True, help='JSONL file (appended)')
    p_sample.add_argument('--interval', required=True, type=float,
                          help='seconds between samples (no default)')
    p_sample.add_argument('--count', type=int,
                          help='stop after N samples; otherwise run until SIGTERM/SIGINT')
    p_sample.add_argument('--proc', default='/proc', help='proc directory (tests)')

    p_sum = sub.add_parser('summarize', help='write host-conditions-summary.json')
    p_sum.add_argument('--samples', required=True, help='JSONL written by sample')
    p_sum.add_argument('--interval', required=True, type=float,
                       help='the sampling interval in seconds (no default)')
    p_sum.add_argument('--gap-factor', required=True, type=float,
                       help='report gaps larger than this x interval (no default)')
    p_sum.add_argument('--out', help='summary path; default: %s beside --samples'
                       % SUMMARY_FILENAME)
    args = parser.parse_args(argv)
    _positive(parser, '--interval', args.interval)

    if args.command == 'sample':
        if args.count is not None and args.count < 1:
            parser.error('--count must be at least 1')
        stop = threading.Event()
        for signum in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signum, lambda *_: stop.set())
        written = sample_loop(args.out, args.interval, args.count, stop, Path(args.proc))
        print(json.dumps({'samples_written': written, 'out': args.out}))
        return 0

    _positive(parser, '--gap-factor', args.gap_factor)
    samples = load_samples(args.samples)
    summary = summarize(samples, args.interval, args.gap_factor)
    out = Path(args.out) if args.out else Path(args.samples).with_name(SUMMARY_FILENAME)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1) + '\n')
    mem = summary['mem']['mem_available_bytes']
    print(json.dumps({'sample_count': summary['sample_count'],
                      'clock_gap_count': summary['clock_gap_count'],
                      'min_mem_available_bytes': mem['min'] if mem else None,
                      'out': str(out)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
