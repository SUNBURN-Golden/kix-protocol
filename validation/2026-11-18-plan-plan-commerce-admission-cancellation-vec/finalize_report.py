"""Render the actual command ledger and changed paths, without Git mutations."""
from pathlib import Path
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    commands = []
    for name in ('commands.json', 'checker-commands.json'):
        commands.extend(json.loads((HERE / name).read_bytes()))
    rows = ['| Command | Actual result | Log |', '|---|---|---|']
    for entry in commands:
        raw = Path(entry['log']).read_text(errors='replace')
        outcome = 'PASS' if entry['exit_code'] == 0 else 'FAIL'
        outcome += ' (exit %d)' % entry['exit_code']
        if 'log_note' in entry:
            outcome += '; mixed log, superseded'
        elif match := re.search(r'Ran (\d+) tests? in', raw):
            outcome += '; ' + match[1] + ' tests'
        elif 'cargo test ' in entry['command']:
            counts = re.findall(r'test result: ok\. (\d+) passed', raw)
            outcome += '; ' + str(sum(map(int, counts))) + ' tests'
        rows.append('| `' + entry['command'].replace('|', '\\|') + '` | ' + outcome + ' | [' + Path(entry['log']).name + '](' + Path(entry['log']).name + ') |')
    report = HERE / 'README.md'
    text = report.read_text()
    start = text.index('## Actual verification')
    end = text.index('## Preservation and limits', start)
    text = text[:start] + '''## Actual verification

The tables record commands actually run, including the failed discovery attempt.
The clean final booking-suite run covers every Commerce replay/index test, including
the added rejected-key check. Mixed `05.log` is retained only as diagnostic history;
its two terminal successes are not used as final verification evidence.
[Command ledger](commands.json) and [checker ledger](checker-commands.json) retain
exit codes and measured durations. Tests use `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=.:reference/booking_resale_admission` unless explicitly overridden,
and `CARGO_NET_OFFLINE=true`. The checker runner uses `PYTHONPATH=.`.
[Sequential test runner](run_checks.py) and [checker runner](run_checkers.py) are
retained for reproducibility; neither retries or updates goldens. The executed
checker list is drawn from `.github/workflows/protocol.yml` and `ktx-kernel.yml`.
Heavy Move/ZK/localnet/storage jobs and broader HTTP gate/fault suites were not
run because this patch touches offline fixtures/tests and evidence only. The
requested reference discovery itself includes existing loopback regressions.

''' + '\n'.join(rows) + '\n\n' + text[end:]
    text = text.replace('The final comparison and changed-path list will be recorded after verification.',
        '[After comparison](preservation-after.json) verifies 4,220 unchanged tracked paths, including all 108 frozen reference files, the 341-path before inventory and both locked blobs. [Read-only verifier](verify_preservation.py) also checks the serialized original seven-pack prefix and unchanged qualification metadata. Locked blobs after work match the before values; no merge occurred, so no merge-blob check applies.')
    if '## Complete changed-path list' in text:
        text = text[:text.index('## Complete changed-path list')]
    tracked = subprocess.check_output(['git', 'diff', 'd087cfa0bc77ee6e3969eb3354422f2c3ce5d1e8', '--name-only'], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    paths = sorted(set(tracked + untracked + [(HERE / 'changed-paths.txt').relative_to(ROOT).as_posix()]))
    (HERE / 'changed-paths.txt').write_text('\n'.join(paths) + '\n')
    text += '''\n## Complete changed-path list

[Every changed/new path](changed-paths.txt) is listed below. No Git index or history
was changed. Current HEAD remains the starting SHA; there is no committed
implementation/final-task SHA yet. Hosted exact-head KTX and KIX run IDs,
status and conclusion, A2 non-author review, merge SHA and post-merge CI are
NOT RUN / unavailable in this supervisor-owned delivery. Local READY means
ready to hand off this working-tree patch, not merge-ready.

''' + '\n'.join('- `' + path + '`' for path in paths) + '\n'
    report.write_text(text)
    print('rendered', len(commands), 'actual command results and', len(paths), 'changed paths')


if __name__ == '__main__':
    main()
