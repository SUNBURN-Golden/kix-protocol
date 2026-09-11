#!/usr/bin/env python3
"""Install the checksum-pinned upstream Sui CLI inside this checkout.

Does not change system packages, shell profiles, wallet configuration or network
permissions. Only the `sui` regular file from the verified archive is installed.
"""
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def link_cli(binary):
    bindir = ROOT / '.local' / 'bin'
    bindir.mkdir(parents=True, exist_ok=True)
    link = bindir / 'sui'
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        raise RuntimeError('REFUSING_TO_REPLACE_NON_SYMLINK: ' + str(link))
    link.symlink_to(os.path.relpath(binary, bindir))


def main():
    spec = json.loads((ROOT / 'toolchains.json').read_text())['sui']
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
        raise SystemExit('This pinned installer targets Linux x86_64. Use the supplied Codespaces/devcontainer configuration.')
    tools = ROOT / '.local' / 'tools' / spec['release']
    tools.mkdir(parents=True, exist_ok=True)
    binary = tools / 'sui'
    receipt_path = tools / 'installation.json'
    if binary.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt.get('archiveSha256') == spec['sha256'] and receipt.get('binarySha256') == digest(binary):
            link_cli(binary)
            print(subprocess.check_output([str(binary), '--version'], text=True).strip(), flush=True)
            print('Verified cached CLI: ' + str(binary), flush=True)
            return
    archive = tools / 'release.tgz'
    if not archive.exists() or digest(archive) != spec['sha256']:
        partial = tools / 'release.tgz.partial'
        downloaded = 0
        next_report = 128 * 1024 * 1024
        print('Downloading pinned upstream release: ' + spec['release'], flush=True)
        req = urllib.request.Request(spec['url'], headers={'User-Agent': 'KIX-development-bootstrap'})
        try:
            with urllib.request.urlopen(req, timeout=45) as response, partial.open('wb') as target:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)
                    downloaded += len(chunk)
                    if downloaded >= next_report:
                        print(f'Downloaded {downloaded // (1024 * 1024)} MiB', flush=True)
                        next_report += 128 * 1024 * 1024
            if digest(partial) != spec['sha256']:
                raise RuntimeError('UPSTREAM_ARCHIVE_CHECKSUM_MISMATCH')
            partial.replace(archive)
        except Exception:
            partial.unlink(missing_ok=True)
            raise
    with tarfile.open(archive, 'r:gz') as source:
        candidates = [m for m in source.getmembers() if m.isfile() and Path(m.name).name == 'sui']
        if len(candidates) != 1:
            raise RuntimeError('EXPECTED_EXACTLY_ONE_SUI_BINARY')
        temporary = tools / 'sui.pending'
        with source.extractfile(candidates[0]) as incoming, temporary.open('wb') as target:
            shutil.copyfileobj(incoming, target)
        temporary.chmod(0o755)
        version = subprocess.check_output([str(temporary), '--version'], text=True).strip()
        if not version.startswith('sui ' + spec['version']):
            temporary.unlink()
            raise RuntimeError('SUI_BINARY_VERSION_MISMATCH: ' + version)
        temporary.replace(binary)
    receipt = {'release': spec['release'], 'url': spec['url'], 'archiveSha256': spec['sha256'],
               'binarySha256': digest(binary), 'version': version}
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    link_cli(binary)
    print(version, flush=True)
    print('Installed verified CLI: ' + str(binary), flush=True)


if __name__ == '__main__':
    main()
