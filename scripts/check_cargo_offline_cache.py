#!/usr/bin/env python3
"""Report registry archives missing from runtime/Cargo.lock, using only stdlib.

Read-only, offline, and never invokes Cargo. Plain inspection exits 0 even
with missing archives; --require exits 1 for missing archives. Invalid input,
usage or cache inspection errors exit 2, with only an error on stderr.
Only --self-test writes files, in a temporary synthetic fixture directory.

Archive presence does not verify integrity, registry indexes, source replacement,
toolchains, or successful offline compilation. On Python < 3.11 the conservative
fallback accepts only Cargo-generated root version, [[package]], quoted basic
string fields and dependency string arrays; it is not a general TOML parser.
Unsupported syntax is refused, never silently skipped.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

ROOT = Path(__file__).resolve().parents[1]
STRING = r'"(?:[^"\\\x00-\x1f\x7f]|\\(?:["\\btnfr]|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}))*"'
TOKEN = re.compile(r'([ \t]+|#[^\r\n]*|\r?\n|' + STRING
                   + r'|\[\[package\]\]|[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[=\[\],])')
FIELDS = {'name', 'version', 'source', 'checksum', 'dependencies'}


def legacy_loads(text):
    """Strict parser for the documented Cargo subset, including comments."""
    tokens = []
    offset = 0
    while offset < len(text):
        match = TOKEN.match(text, offset)
        if not match:
            raise ValueError('unsupported or malformed Cargo TOML near offset %d' % offset)
        token = match.group()
        if not token.startswith(('#', ' ', '\t')):
            tokens.append('\n' if token == '\r\n' else token)
        offset = match.end()
    tokens.append(None)
    index = 0
    result = {}
    table = result

    def string(token):
        if token is None or not re.fullmatch(STRING, token):
            raise ValueError('expected quoted Cargo TOML string')
        escapes = {'"': '"', '\\': '\\', 'b': '\b', 't': '\t',
                   'n': '\n', 'f': '\f', 'r': '\r'}

        def unescape(match):
            escape = match.group()[1:]
            return (chr(int(escape[1:], 16)) if escape[0] in 'uU'
                    else escapes[escape])

        value = re.sub(r'\\(?:["\\btnfr]|u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8})',
                       unescape, token[1:-1])
        if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ValueError('invalid Unicode scalar')
        return value

    while tokens[index] is not None:
        token = tokens[index]
        index += 1
        if token == '\n':
            continue
        if token == '[[package]]':
            table = {}
            result.setdefault('package', []).append(table)
        else:
            key = token
            allowed = {'version'} if table is result else FIELDS
            if key not in allowed or key in table or tokens[index] != '=':
                raise ValueError('unsupported or duplicate Cargo TOML key: ' + key)
            index += 1
            value = tokens[index]
            index += 1
            if table is result:
                if value is None or not re.fullmatch(r'0|[1-9][0-9]*', value):
                    raise ValueError('expected root integer version')
                value = int(value)
            elif key == 'dependencies':
                if value != '[':
                    raise ValueError('expected dependency array')
                value = []
                while True:
                    while tokens[index] == '\n':
                        index += 1
                    if tokens[index] == ']':
                        index += 1
                        break
                    value.append(string(tokens[index]))
                    index += 1
                    while tokens[index] == '\n':
                        index += 1
                    if tokens[index] == ']':
                        index += 1
                        break
                    if tokens[index] != ',':
                        raise ValueError('expected dependency comma or closing bracket')
                    index += 1
            else:
                value = string(value)
            table[key] = value
        if tokens[index] not in ('\n', None):
            raise ValueError('expected end of Cargo TOML statement')
    return result


def parse_lock(raw, parser=None):
    text = raw.decode('utf-8')
    # A TOML syntax error must never trigger fallback.
    loads = parser or (tomllib.loads if tomllib is not None else legacy_loads)
    data = loads(text)
    if not isinstance(data, dict) or type(data.get('version')) is not int:
        raise ValueError('missing integer lockfile version')
    packages = data.get('package')
    if not isinstance(packages, list):
        raise ValueError('missing package tables')
    registry = []
    for package in packages:
        if not isinstance(package, dict):
            raise ValueError('invalid package table')
        name, version = package.get('name'), package.get('version')
        if (not isinstance(name, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name)
                or not isinstance(version, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+\-]*', version)):
            raise ValueError('missing or unsafe package name/version')
        source = package.get('source')
        if 'source' in package and not isinstance(source, str):
            raise ValueError('package source must be a string')
        if 'dependencies' in package and (
                not isinstance(package['dependencies'], list)
                or any(not isinstance(d, str) for d in package['dependencies'])):
            raise ValueError('dependencies must be a string array')
        if source is not None and source.startswith('registry+'):
            registry.append({'name': name, 'version': version})
    return registry


def file_mode(path):
    """Missing paths are expected; permission/other stat failures propagate."""
    try:
        return path.stat().st_mode
    except FileNotFoundError:
        return 0


def build_report(lock_path, cargo_home, parser=None):
    raw = lock_path.read_bytes()
    packages = parse_lock(raw, parser)
    cargo_home = Path(cargo_home).expanduser().resolve()
    cache = cargo_home / 'registry' / 'cache'
    directories = []
    try:
        # Unlike glob/is_file, explicit scandir/stat propagates inspection errors.
        with os.scandir(cache) as entries:
            for entry in entries:
                if stat.S_ISDIR(file_mode(Path(entry.path))):
                    directories.append(Path(entry.path))
    except FileNotFoundError:
        pass
    missing = []
    for package in packages:
        archive = '{name}-{version}.crate'.format(**package)
        # Inspect every registry directory so an error is not hidden by a hit.
        matches = [stat.S_ISREG(file_mode(directory / archive))
                   for directory in directories]
        if not any(matches):
            missing.append(package)
    missing.sort(key=lambda p: (p['name'], p['version']))
    return {'lock_sha256': hashlib.sha256(raw).hexdigest(),
            'cargo_home': str(cargo_home), 'total': len(packages),
            'present': len(packages) - len(missing), 'missing': missing}


def main(argv, lock_path=None, cargo_home=None, parser=None):
    if argv == ['--self-test']:
        return self_test()
    if argv not in ([], ['--require']):
        print('usage: check_cargo_offline_cache.py [--require | --self-test]',
              file=sys.stderr)
        return 2
    try:
        report = build_report(
            lock_path if lock_path is not None else ROOT / 'runtime/Cargo.lock',
            cargo_home if cargo_home is not None else
            os.environ.get('CARGO_HOME') or Path.home() / '.cargo', parser)
    except (OSError, ValueError, RuntimeError) as exc:
        print('check_cargo_offline_cache: %s' % exc, file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return 1 if argv == ['--require'] and report['missing'] else 0


def self_test():
    """Fixtures cover both parsers, CLI exits and cache filesystem boundaries."""
    fixture = '''# Synthetic only
version = 4
[[package]]
name = "alpha"
version = "1.0.0"
source = "registry+https://invalid.example/index#fragment" # comment
dependencies = [
 "beta", # comment
]
[[package]]
name = "beta"
version = "2.0.0"
source = "registry+https://invalid.example/other"
[[package]]
name = "git-only"
version = "1.0.0"
source = "git+https://invalid.example/repo"
[[package]]
name = "path-only"
version = "1.0.0"
'''
    parsers = [('legacy', legacy_loads)]
    if tomllib is not None:
        parsers.append(('tomllib', tomllib.loads))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / 'cargo'
            lock = Path(tmp) / 'Cargo.lock'
            first = home / 'registry/cache/first'
            second = home / 'registry/cache/second'
            first.mkdir(parents=True)
            second.mkdir()

            def run(argv, parser, expected, text=fixture):
                lock.write_text(text, encoding='utf-8')
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = main(argv, lock, home, parser)
                assert code == expected, (argv, code, expected, err.getvalue())
                if code == 2:
                    assert not out.getvalue() and err.getvalue()
                    return None
                assert not err.getvalue(), err.getvalue()
                report = json.loads(out.getvalue())
                assert report['present'] + len(report['missing']) == report['total']
                assert report['lock_sha256'] == hashlib.sha256(lock.read_bytes()).hexdigest()
                assert report['cargo_home'] == str(home.resolve())
                return report

            for label, parser in parsers:
                alpha = first / 'alpha-1.0.0.crate'
                beta = second / 'beta-2.0.0.crate'
                alpha.touch()
                beta.touch()
                report = run([], parser, 0)
                assert (report['total'], report['present'], report['missing']) == (2, 2, [])
                run(['--require'], parser, 0)
                print('self-test: %s all present; git/path sources ignored' % label)
                beta.unlink()
                (second / 'beta-1.0.0.crate').touch()
                beta.mkdir()  # A matching directory is not an archive.
                nested = second / 'nested'
                nested.mkdir(exist_ok=True)
                (nested / 'beta-2.0.0.crate').touch()
                report = run([], parser, 0)
                assert report['missing'] == [{'name': 'beta', 'version': '2.0.0'}]
                assert report['present'] == 1
                run(['--require'], parser, 1)
                print('self-test: %s one missing; --require exit 1; cache controls' % label)
                beta.rmdir()
                # Entries count independently even if name/version pairs repeat.
                duplicate = fixture + '''[[package]]
name = "alpha"
version = "1.0.0"
source = "registry+https://invalid.example/third"
'''
                assert run([], parser, 0, duplicate)['total'] == 3
                malformed = [
                    'version = 4\n[[package]]\nname = "unterminated',
                    fixture + 'name = "duplicate"\n',
                    fixture.replace(' "beta",', ' "beta" "alpha",'),
                    fixture.replace(' "beta",', ' "beta",, '),
                    fixture.replace(']\n', ''),
                    fixture.replace('version = "2.0.0"', 'version = 2'),
                    fixture.replace('name = "alpha"', 'name = "../alpha"'),
                    fixture.replace('version = "2.0.0"', 'version = "../2"'),
                    fixture.replace('source = "git+https://invalid.example/repo"', 'source = 7'),
                    'version = 4\n[[package]]\n',
                ]
                for text in malformed:
                    run([], parser, 2, text)
                    run(['--require'], parser, 2, text)
                print('self-test: %s malformed lock refused with exit 2' % label)
                # Errors must not be converted into partial success, even with hits.
                with patch.object(Path, 'stat', side_effect=PermissionError('synthetic stat denial')):
                    run([], parser, 2)
                with patch('os.scandir', side_effect=PermissionError('synthetic cache denial')):
                    run([], parser, 2)
                with patch('os.scandir', side_effect=FileNotFoundError('synthetic absent cache')):
                    assert run([], parser, 0)['present'] == 0
            for text in (fixture + '[unsupported]\n', 'version = 04\n',
                         fixture.replace('"alpha"', '"bad\\q"')):
                run([], legacy_loads, 2, text)
            for literal, expected in ((r'"registry+\U00000041"', 'registry+A'),
                                      (r'"registry+\\U00000041"', r'registry+\U00000041')):
                parsed = legacy_loads('version = 4\n[[package]]\nsource = ' + literal)
                assert parsed['package'][0]['source'] == expected
            for argv in (['--bogus'], ['--require', '--self-test'], ['--require', '--require']):
                run(argv, legacy_loads, 2)
            # Exercise environment selection without touching the real home/cache.
            lock.write_text(fixture, encoding='utf-8')
            for setting, expected_home in ((str(home), home), ('', Path(tmp) / '.cargo')):
                out = io.StringIO()
                with patch.dict(os.environ, {'CARGO_HOME': setting}), \
                        patch.object(Path, 'home', return_value=Path(tmp)), \
                        contextlib.redirect_stdout(out):
                    assert main([], lock_path=lock) == 0
                report = json.loads(out.getvalue())
                assert report['cargo_home'] == str(expected_home.resolve())
                if not setting:
                    assert (report['present'], len(report['missing'])) == (0, 2)
            with patch.object(Path, 'read_bytes', side_effect=FileNotFoundError('synthetic absent lock')):
                run([], legacy_loads, 2)
            with patch('os.scandir', side_effect=NotADirectoryError('synthetic invalid cache')):
                run([], legacy_loads, 2)
            print('self-test: environment defaults, missing input and inspection errors')
    except (AssertionError, OSError, ValueError, RuntimeError) as exc:
        print('self-test: FAIL %s' % exc, file=sys.stderr)
        return 1
    print('self-test: pass')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
