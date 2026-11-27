#!/usr/bin/env python3
"""Check that every offline test suite is reached by a protocol.yml step.

In scope, using only the stdlib:

- every ``test_*.py`` under each ``reference/<dir>/`` (recursively);
- every ``reference/rights_scale/client/**/*.test.mjs``;
- every ``test_*.py`` module at any depth under ``readiness/`` and
  ``integration_gate/``, with or without ``__init__.py``.

A reference file or node test is reached when a workflow step runs it
with ``node --test``, names it with ``python -m unittest MODULE`` or
reaches it through ``python -m unittest discover`` (including the
``for VAR in ...; do ... done`` suite list). Discover follows Python
3.11+ rules: ``test*.py`` directly under the start directory, then only
subdirectories that are packages. A readiness/integration_gate test
module is also reached when a module CI runs binds every one of its
TestCase classes at top level, through ``from X import Cls`` or ``*``
(for example ``readiness.test_faults`` importing
``ConformanceSensitivityTests``). ``import X`` and ``from pkg import
test_mod`` bind no TestCase class, so they do not reach a module.

The historical trees in EXCLUDED are skipped by name with a written
reason; the guard does not claim they run. This is a textual check: it
does not evaluate YAML, ``if:`` guards or shell semantics beyond the
recognised forms, does not parse scripts that run tests internally,
ignores ``load_tests`` and runtime sys.path changes, and does not judge
whether test assertions are adequate. --self-test uses only temporary
fixture trees and synthetic workflow text.
"""
import ast
import fnmatch
import os
import posixpath
import re
import shlex
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = '.github/workflows/protocol.yml'
REFERENCE = 'reference'
NODE_ROOT = 'reference/rights_scale/client'
MODULE_ROOTS = ('readiness', 'integration_gate')
SKIP_DIRS = {'node_modules', '__pycache__'}
EXCLUDED = {
    'reference/v0.1':
        'historical v0.1 reference tree; no protocol.yml step runs its '
        'tests and this guard does not claim they run',
    'reference/v0.2':
        'historical v0.2 reference tree; no protocol.yml step runs its '
        'tests and this guard does not claim they run',
    'reference/v0.3-rc1':
        'historical v0.3-rc1 tree; its Python tests are invoked inside '
        'scripts/verify_runtime.py, which this guard does not parse, so '
        'no run is claimed here',
}
DISCOVER_PATTERN = 'test*.py'
PYTHON = re.compile(r'python(3(\.\d+)?)?')
ASSIGN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*=')
JOB = re.compile(r'^  ([A-Za-z0-9_-]+):\s*(#.*)?$')
DASH = re.compile(r'^(\s*)- (.*)$')
KEY = re.compile(r'^(name|run):\s?(.*)$')
FOR = re.compile(r'^for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.*?)\s*;\s*do$')
SEPARATORS = {';', '&&', '||', '|', '&', '(', ')'}
UNITTEST_FLAGS = {'-v', '-q', '-b', '-c', '-f', '--locals', '--verbose',
                  '--quiet', '--buffer', '--catch', '--failfast'}


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '\'"':
        return value[1:-1]
    return value


def parse_steps(text):
    """Return [(label, run text)] for each step with a run key."""
    steps, job, steps_seen, step_indent = [], None, False, None
    step, count, block = None, 0, None

    def finish():
        if step is not None and step['run'] is not None:
            name = step['name'] or 'step#%d' % step['index']
            steps.append(('%s/%s' % (job, name), step['run']))

    def key_line(indent, content):
        nonlocal block
        match = KEY.match(content)
        if not match or step is None or indent != step_indent + 2:
            return
        if match.group(1) == 'name':
            step['name'] = _unquote(match.group(2).split(' #')[0])
        elif match.group(2).strip()[:1] in ('|', '>'):
            step['run'], block = '', (indent, [])
        else:
            step['run'] = _unquote(match.group(2))

    in_jobs = False
    for line in text.splitlines():
        indent = len(line) - len(line.lstrip(' '))
        if block is not None:
            if not line.strip() or indent > block[0]:
                block[1].append(line)
                continue
            lines = block[1]
            depth = min((len(l) - len(l.lstrip(' ')) for l in lines
                         if l.strip()), default=0)
            step['run'] = '\n'.join(l[depth:] for l in lines)
            block = None
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if indent == 0:
            finish()
            step, job = None, None
            in_jobs = line.rstrip().startswith('jobs:')
            continue
        if not in_jobs:
            continue
        match = JOB.match(line)
        if match:
            finish()
            job, steps_seen, step_indent, step, count = (
                match.group(1), False, None, None, 0)
            continue
        if job is None:
            continue
        if step_indent is None and line.strip() == 'steps:':
            steps_seen = True
            continue
        match = DASH.match(line)
        if match and steps_seen and (step_indent is None
                                     or len(match.group(1)) == step_indent):
            finish()
            step_indent = len(match.group(1))
            count += 1
            step = {'name': None, 'run': None, 'index': count}
            key_line(step_indent + 2, match.group(2))
            continue
        key_line(indent, line.strip())
    if block is not None:
        step['run'] = '\n'.join(l.strip() for l in block[1])
    finish()
    return steps


def logical_lines(run):
    """Drop blanks/comments, join continuations and expand for-loops."""
    lines, pending = [], ''
    for raw in run.splitlines():
        line = raw.strip()
        if not pending and (not line or line.startswith('#')):
            continue
        if line.endswith('\\'):
            pending += line[:-1] + ' '
            continue
        lines.append(pending + line)
        pending = ''
    if pending.strip():
        lines.append(pending.strip())
    return _expand(lines)


def _expand(lines):
    out, index = [], 0
    while index < len(lines):
        match = FOR.match(lines[index])
        if not match:
            out.append(lines[index])
            index += 1
            continue
        depth, end = 1, index + 1
        while end < len(lines) and depth:
            first = lines[end].split()[0] if lines[end].split() else ''
            if lines[end].rstrip().endswith('; do') or first in ('do',):
                depth += 1
            elif first == 'done' or first.startswith('done;'):
                depth -= 1
            end += 1
        body = lines[index + 1:end - 1 if not depth else end]
        try:
            values = shlex.split(match.group(2))
        except ValueError:
            values = None
        if values is None or any('$' in value for value in values):
            out.extend(_expand(body))
        else:
            name = match.group(1)
            for value in values:
                out.extend(_expand([
                    line.replace('${%s}' % name, value).replace('$' + name, value)
                    for line in body]))
        index = end
    return out


def _segments(line):
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    segment = []
    for token in lexer:
        if token in SEPARATORS:
            if segment:
                yield segment
            segment = []
        else:
            segment.append(token)
    if segment:
        yield segment


def parse_commands(label, run, errors):
    """Return [(kind, data)]: ('node', path), ('module', name), ('discover', (s, t))."""
    found = []
    for line in logical_lines(run):
        try:
            segments = list(_segments(line))
        except ValueError:
            if 'unittest' in line or '--test' in line:
                errors.append('unparseable test command: %s: %s' % (label, line))
            continue
        for tokens in segments:
            while tokens and ASSIGN.match(tokens[0]):
                tokens = tokens[1:]
            if not tokens:
                continue
            program = posixpath.basename(tokens[0])
            if program == 'node' and '--test' in tokens:
                rest = tokens[tokens.index('--test') + 1:]
                found.extend(('node', path) for path in rest
                             if not path.startswith('-'))
            elif PYTHON.fullmatch(program):
                found.extend(_unittest(label, tokens[1:], errors))
    return found


def _unittest(label, args, errors):
    index = 0
    while index < len(args) and args[index].startswith('-') \
            and args[index] not in ('-m', '-c'):
        index += 1
    if args[index:index + 2] != ['-m', 'unittest']:
        return []
    args = args[index + 2:]
    if args[:1] != ['discover']:
        found = []
        for arg in args:
            if arg in UNITTEST_FLAGS:
                continue
            if arg.startswith('-'):
                errors.append('unsupported unittest option: %s: %s' % (label, arg))
            else:
                found.append(('module', arg))
        return found
    start, top, index, args = '.', None, 0, args[1:]
    while index < len(args):
        arg = args[index]
        if arg in ('-v', '--verbose'):
            index += 1
            continue
        if arg in ('-s', '--start-directory', '-t', '--top-level-directory',
                   '-p', '--pattern') and index + 1 < len(args):
            value = args[index + 1]
            if arg in ('-s', '--start-directory'):
                start = value
            elif arg in ('-t', '--top-level-directory'):
                top = value
            elif value != DISCOVER_PATTERN:
                errors.append('unsupported unittest option: %s: %s %s'
                              % (label, arg, value))
                return []
            index += 2
            continue
        errors.append('unsupported unittest option: %s: %s' % (label, arg))
        return []
    for path in (start, top):
        if path is not None and '$' in path:
            errors.append('unresolved discover path: %s: %s' % (label, path))
            return []
    return [('discover', (posixpath.normpath(start),
                          posixpath.normpath(top or start)))]


def _walk(base, wanted):
    """Yield repo-relative posix paths under base whose name matches wanted."""
    for directory, dirs, files in os.walk(base):
        dirs[:] = sorted(d for d in dirs
                         if d not in SKIP_DIRS and not d.startswith('.'))
        for name in sorted(files):
            if wanted(name):
                yield Path(directory, name)


def collect(root):
    """Return (reference suites, node tests, module files) from the tree."""
    suites = {}
    reference = root / REFERENCE
    if reference.is_dir():
        for child in sorted(reference.iterdir()):
            if child.is_dir():
                files = [p.relative_to(root).as_posix() for p in _walk(
                    child, lambda n: fnmatch.fnmatch(n, 'test_*.py'))]
                if files:
                    suites[child.relative_to(root).as_posix()] = files
    node = sorted(p.relative_to(root).as_posix() for p in _walk(
        root / NODE_ROOT, lambda n: n.endswith('.test.mjs')))
    modules = {}
    for top in MODULE_ROOTS:
        for path in _walk(root / top, lambda n: n.endswith('.py')):
            parts = path.relative_to(root).with_suffix('').parts
            if parts[-1] == '__init__':
                parts = parts[:-1]
            modules['.'.join(parts)] = path
    return suites, node, modules


def _discover(root, start):
    """Files unittest discover (3.11+) loads from start with test*.py."""
    base = root / start
    for path in sorted(base.iterdir()):
        if path.is_file() and fnmatch.fnmatch(path.name, DISCOVER_PATTERN):
            yield path.relative_to(root).as_posix()
        elif (path.is_dir() and path.name not in SKIP_DIRS
              and (path / '__init__.py').is_file()):
            yield from _discover(root, path.relative_to(root).as_posix())


def _module_file(root, name):
    if name.endswith('.py'):
        candidates = [name]
    else:
        stem = name.replace('.', '/')
        candidates = [stem + '.py', stem + '/__init__.py']
    for candidate in candidates:
        if (root / candidate).is_file():
            return posixpath.normpath(candidate)
    return None


def _statements(body):
    for node in body:
        yield node
        if isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
            for field in ('body', 'orelse', 'finalbody'):
                yield from _statements(getattr(node, field, []))
            for handler in getattr(node, 'handlers', []):
                yield from _statements(handler.body)


class Modules:
    """Top-level TestCase bindings of readiness/integration_gate modules."""

    def __init__(self, files, errors):
        self.files, self.trees, self.own, self.memo = files, {}, {}, {}
        for name, path in sorted(files.items()):
            try:
                self.trees[name] = ast.parse(
                    path.read_text(encoding='utf-8'), filename=str(path))
            except (SyntaxError, UnicodeError) as error:
                errors.append('unparseable module: %s: %s' % (name, error))
        for name in self.trees:
            self.namespace(name, set())

    def _target(self, name, node):
        if not node.level:
            return node.module
        package = name.split('.')
        if self.files[name].name == '__init__.py':
            package.append('')
        base = package[:len(package) - node.level]
        return '.'.join(base + ([node.module] if node.module else []))

    def namespace(self, name, stack):
        """Map bound name -> (origin module, class) for TestCase classes."""
        if name in self.memo:
            return self.memo[name]
        if name in stack or name not in self.trees:
            return {}
        stack.add(name)
        bound, own = {}, []
        for node in _statements(self.trees[name].body):
            if isinstance(node, ast.ImportFrom):
                target = self._target(name, node)
                source = self.namespace(target, stack) if target else {}
                for alias in node.names:
                    if alias.name == '*':
                        bound.update((key, value) for key, value in source.items()
                                     if not key.startswith('_'))
                    elif alias.name in source:
                        bound[alias.asname or alias.name] = source[alias.name]
                    else:
                        bound.pop(alias.asname or alias.name, None)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bound.pop(alias.asname or alias.name.split('.')[0], None)
            elif isinstance(node, ast.ClassDef):
                if any(_is_testcase(base, bound) for base in node.bases):
                    bound[node.name] = (name, node.name)
                    own.append(node.name)
                else:
                    bound.pop(node.name, None)
        stack.discard(name)
        self.memo[name], self.own[name] = bound, own
        return bound


def _is_testcase(base, bound):
    if isinstance(base, ast.Name):
        return base.id.endswith('TestCase') or base.id in bound
    return isinstance(base, ast.Attribute) and base.attr.endswith('TestCase')


def check(root, workflow_text, excluded=None):
    """Return (errors, report lines) for the tree at root."""
    excluded = EXCLUDED if excluded is None else excluded
    errors, report = [], []
    suites, node_tests, module_files = collect(root)
    reached_files, reached_node, seeds = {}, {}, {}
    commands = 0

    def credit(table, key, label):
        table.setdefault(key, [])
        if label not in table[key]:
            table[key].append(label)

    for label, run in parse_steps(workflow_text):
        for kind, data in parse_commands(label, run, errors):
            commands += 1
            if kind == 'node':
                path = posixpath.normpath(data)
                if not (root / path).is_file():
                    errors.append('workflow names missing node test: %s: %s'
                                  % (label, data))
                credit(reached_node, path, label)
                continue
            if kind == 'module':
                path = _module_file(root, data)
                if path is None:
                    errors.append('workflow names missing test module: %s: %s'
                                  % (label, data))
                    continue
                paths = [path]
            else:
                start, _ = data
                if not (root / start).is_dir():
                    errors.append('workflow discover path missing: %s: %s'
                                  % (label, start))
                    continue
                for directory in excluded:
                    if start == directory or start.startswith(directory + '/'):
                        errors.append('excluded but wired: %s: %s'
                                      % (directory, label))
                paths = list(_discover(root, start))
            for path in paths:
                credit(reached_files, path, label)
                parts = Path(path).with_suffix('').parts
                if parts[-1] == '__init__':
                    parts = parts[:-1]
                if parts and parts[0] in MODULE_ROOTS:
                    credit(seeds, '.'.join(parts), label)
    if not commands:
        errors.append('sanity: no test-running steps')

    for directory, reason in sorted(excluded.items()):
        if not str(reason).strip():
            errors.append('exclusion without reason: ' + directory)
        if directory not in suites:
            errors.append('exclusion names no test suite: ' + directory)
        for path in reached_files.keys() | reached_node.keys():
            if path.startswith(directory + '/'):
                for label in reached_files.get(path, reached_node.get(path)):
                    error = 'excluded but wired: %s: %s' % (directory, label)
                    if error not in errors:
                        errors.append(error)

    for directory, files in sorted(suites.items()):
        if directory in excluded:
            continue
        labels = []
        for path in files:
            if path not in reached_files:
                errors.append('unreached test file: ' + path)
            for label in reached_files.get(path, []):
                if label not in labels:
                    labels.append(label)
        report.append('reached: %s files=%d <- %s'
                      % (directory, len(files), ', '.join(labels) or '-'))
    for path in node_tests:
        if path in reached_node:
            report.append('reached: %s <- %s'
                          % (path, ', '.join(reached_node[path])))
        else:
            errors.append('unreached node test: ' + path)

    modules = Modules(module_files, errors)
    running = {}
    for seed in sorted(seeds):
        for origin in modules.namespace(seed, set()).values():
            running.setdefault(origin, []).append(seed)
    tests = sorted(name for name in module_files
                   if name.rsplit('.', 1)[-1].startswith('test_'))
    for name in tests:
        if name in seeds:
            report.append('reached: %s <- %s' % (name, ', '.join(seeds[name])))
            continue
        own = modules.own.get(name, [])
        hit = [cls for cls in own if (name, cls) in running]
        if own and len(hit) == len(own):
            via = sorted({seed for cls in own for seed in running[(name, cls)]})
            labels = []
            for seed in via:
                labels.extend(l for l in seeds[seed] if l not in labels)
            report.append('reached: %s <- %s via %s'
                          % (name, ', '.join(labels), ', '.join(via)))
        elif hit:
            errors.append('partially imported test module: %s: missing %s'
                          % (name, ', '.join(c for c in own if c not in hit)))
        else:
            errors.append('unreached test module: ' + name)
    for directory, reason in sorted(excluded.items()):
        report.append('excluded: %s: %s' % (directory, reason))
    report.append('ci test discovery ok: reference_suites=%d node_tests=%d '
                  'modules=%d excluded=%d'
                  % (len([d for d in suites if d not in excluded]),
                     len(node_tests), len(tests), len(excluded)))
    return sorted(errors), report


SELF_TEST_WORKFLOW = '''name: synthetic
on: [push]
jobs:
  node-job:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - name: Node regressions
        run: node --experimental-test-module-mocks --test reference/rights_scale/client/a.test.mjs
      - name: Model tests
        run: |
          source scripts/env.sh
          python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale
  protocol:
    runs-on: ubuntu-24.04
    steps:
      - name: Gate
        if: always()
        run: python3 -m unittest integration_gate.test_gate readiness.test_faults
      - name: Suites
        run: |
          for suite in suite_a suite_b; do
            PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite"
          done
          python3 -m unittest readiness.subpackage.test_deep
'''
CASE = 'import unittest\n\n\nclass %s(unittest.TestCase):\n    pass\n'
SELF_TEST_FILES = {
    'reference/suite_a/test_a.py': CASE % 'ATests',
    'reference/suite_a/pkg/__init__.py': '',
    'reference/suite_a/pkg/test_pkg.py': CASE % 'PkgTests',
    'reference/suite_b/test_b.py': CASE % 'BTests',
    'reference/rights_scale/test_model.py': CASE % 'ModelTests',
    'reference/rights_scale/client/a.test.mjs': '',
    'reference/rights_scale/client/node_modules/dep/b.test.mjs': '',
    'reference/read_model/generate_fixtures.py': '',
    'reference/v0.1/test_core.py': CASE % 'CoreTests',
    'reference/v0.2/test_core.py': CASE % 'CoreTests',
    'reference/v0.3-rc1/test_v03.py': CASE % 'V03Tests',
    'readiness/__init__.py': '',
    'readiness/helper.py': 'VALUE = 1\n',
    'readiness/test_sens.py': CASE % 'SensTests',
    'readiness/test_faults.py': (
        'import unittest\n'
        'from .helper import VALUE\n'
        'from readiness.test_sens import SensTests\n\n\n'
        'class FaultTests(unittest.TestCase):\n    pass\n\n\n'
        'class DerivedTests(FaultTests):\n    pass\n'),
    'readiness/subpackage/__init__.py': '',
    'readiness/subpackage/test_deep.py': CASE % 'DeepTests',
    'integration_gate/__init__.py': '',
    'integration_gate/test_gate.py': CASE % 'GateTests',
}
GATE_LINE = 'run: python3 -m unittest integration_gate.test_gate readiness.test_faults'


def _fixture(root, files):
    for name, text in files.items():
        if text is None:
            continue
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def _run_fixture(files, workflow, excluded=None):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _fixture(root, files)
        return check(root, workflow, excluded)


def self_test():
    """Require each negative control to report its own rule, not just fail."""
    errors, report = _run_fixture(SELF_TEST_FILES, SELF_TEST_WORKFLOW)
    expected = ('ci test discovery ok: reference_suites=3 node_tests=1 '
                'modules=4 excluded=3')
    via = ('reached: readiness.test_sens <- protocol/Gate via '
           'readiness.test_faults')
    if errors or report[-1] != expected or via not in report:
        print('self-test: synthetic baseline failed: %r %r' % (errors, report),
              file=sys.stderr)
        return 1
    faults = SELF_TEST_FILES['readiness/test_faults.py']
    unrolled = SELF_TEST_WORKFLOW.replace(
        'for suite in suite_a suite_b; do', 'for suite in $SUITES; do')
    cases = [
        ('unwired suite directory',
         {'reference/new_suite/test_x.py': CASE % 'XTests'}, None, None,
         'unreached test file: reference/new_suite/test_x.py'),
        ('unwired node test',
         {'reference/rights_scale/client/new.test.mjs': ''}, None, None,
         'unreached node test: reference/rights_scale/client/new.test.mjs'),
        ('unreached top-level module',
         {'readiness/test_orphan.py': CASE % 'OrphanTests'}, None, None,
         'unreached test module: readiness.test_orphan'),
        ('unreached nested module',
         {'readiness/subpackage/test_orphan.py': CASE % 'OrphanTests'},
         None, None,
         'unreached test module: readiness.subpackage.test_orphan'),
        ('unreached module outside a package',
         {'integration_gate/sub/test_y.py': CASE % 'YTests'}, None, None,
         'unreached test module: integration_gate.sub.test_y'),
        ('exclusion without reason', {}, None,
         dict(EXCLUDED, **{'reference/v0.1': ' '}),
         'exclusion without reason: reference/v0.1'),
        ('module reached only by import statement',
         {'readiness/test_x.py': CASE % 'XTests',
          'readiness/test_faults.py': 'import readiness.test_x\n' + faults},
         None, None, 'unreached test module: readiness.test_x'),
        ('module reached only as a package attribute',
         {'readiness/test_x.py': CASE % 'XTests',
          'readiness/test_faults.py': 'from readiness import test_x\n' + faults},
         None, None, 'unreached test module: readiness.test_x'),
        ('partial from-import',
         {'readiness/test_two.py': CASE % 'OneTests'
          + '\n\nclass TwoTests(unittest.TestCase):\n    pass\n',
          'readiness/test_faults.py':
              'from readiness.test_two import OneTests\n' + faults},
         None, None,
         'partially imported test module: readiness.test_two: missing TwoTests'),
        ('reference test in a non-package subdirectory',
         {'reference/suite_a/plain/test_hidden.py': CASE % 'HiddenTests'},
         None, None, 'unreached test file: reference/suite_a/plain/test_hidden.py'),
        ('commented-out wiring line', {},
         SELF_TEST_WORKFLOW.replace(
             'run: node --experimental',
             'run: |\n          # node --experimental'),
         None, 'unreached node test: reference/rights_scale/client/a.test.mjs'),
        ('unexpanded loop variable', {}, unrolled, None,
         'unresolved discover path: protocol/Suites: reference/$suite'),
        ('unsupported discover option', {},
         SELF_TEST_WORKFLOW.replace('-t reference/rights_scale',
                                    '-t reference/rights_scale -k model'),
         None, 'unsupported unittest option: node-job/Model tests: -k'),
        ('workflow names missing module', {},
         SELF_TEST_WORKFLOW + '          python3 -m unittest readiness.test_gone\n',
         None, 'workflow names missing test module: protocol/Suites: '
               'readiness.test_gone'),
        ('workflow names missing node test', {},
         SELF_TEST_WORKFLOW + '          node --test reference/gone.test.mjs\n',
         None, 'workflow names missing node test: protocol/Suites: '
               'reference/gone.test.mjs'),
        ('exclusion of an absent tree', {}, None,
         dict(EXCLUDED, **{'reference/v9': 'absent tree'}),
         'exclusion names no test suite: reference/v9'),
        ('excluded tree wired by discover', {},
         SELF_TEST_WORKFLOW + '          python3 -m unittest discover -s '
                              'reference/v0.2 -p "test*.py"\n',
         None, 'excluded but wired: reference/v0.2: protocol/Suites'),
        ('empty workflow', {}, '', None, 'sanity: no test-running steps'),
    ]
    for label, extra, workflow, excluded, marker in cases:
        files = dict(SELF_TEST_FILES, **extra)
        text = SELF_TEST_WORKFLOW if workflow is None else workflow
        errors, _ = _run_fixture(files, text, excluded)
        if not any(error.startswith(marker) for error in errors):
            print('self-test: failed to detect %s: %r' % (label, errors),
                  file=sys.stderr)
            return 1
        print('self-test: detected ' + label)
    print('self-test: pass (%d negative controls)' % len(cases))
    return 0


def main(argv):
    if argv not in ([], ['--self-test']):
        print('usage: check_ci_test_discovery.py [--self-test]', file=sys.stderr)
        return 2
    if argv:
        return self_test()
    try:
        workflow = (ROOT / WORKFLOW).read_text(encoding='utf-8')
        errors, report = check(ROOT, workflow)
    except (OSError, UnicodeError) as error:
        print('ci test discovery input error: ' + str(error), file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print('\n'.join(report))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
