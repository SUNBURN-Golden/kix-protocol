"""Additional consumer boundary gaps; exporter coverage is reused unchanged."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from authenticated_export import FULL_SNAPSHOT, INCREMENTAL, auth, exporter, files, verify
from authenticated_export.errors import ExportError
from authenticated_export.rollback import RollbackRegistry
from authenticated_export.test_pure import (
    CREATED_AT, KEY, KEY_VERSION, FixtureSource, load_manifest, write_manifest,
)
from analytics_audit.prepare_export import admit


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='kix-audit-admit-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.directory = self.root / 'export'
        self.registry = RollbackRegistry(self.root / 'registry.json')

    def export(self, mode=FULL_SNAPSHOT):
        exporter.export_source(FixtureSource(), self.directory, mode=mode,
                               key=KEY, key_version=KEY_VERSION, created_at=CREATED_AT)

    def admit(self, **kwargs):
        return admit(self.directory, registry=self.registry, export_seq=1, **kwargs)

    def test_full_and_keyed_trace(self):
        self.export()
        bundle = self.admit()
        self.assertTrue(bundle['exportTrace']['linksResolved'])
        self.assertEqual(bundle['tables']['command_result'][0]['command_id'], 'c1')
        with self.assertRaises(ExportError):
            self.admit()  # Replay is rejected before engine construction.

    def test_reject_incremental_partial_tampered_and_wrong_key(self):
        for case in ('incremental', 'missing', 'partial', 'tampered', 'key', 'extra'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp) / 'export'
                exporter.export_source(FixtureSource(), directory,
                                       mode=INCREMENTAL if case == 'incremental' else FULL_SNAPSHOT,
                                       key=KEY, key_version=KEY_VERSION, created_at=CREATED_AT)
                path = directory / files.table_path('command_result')
                if case == 'missing':
                    path.unlink()
                elif case == 'partial':
                    path.write_bytes(path.read_bytes()[:-1])
                elif case == 'tampered':
                    path.write_bytes(path.read_bytes().replace(b'c1', b'c9'))
                elif case == 'extra':
                    (directory / 'extra').write_text('partial upload')
                with self.assertRaises(ExportError):
                    admit(directory, registry=self.registry, export_seq=1,
                          key=b'wrong-public-fixture-key' if case == 'key' else KEY)

    def test_signed_wrong_versions_rejected(self):
        self.export()
        original = load_manifest(self.directory)
        for field in ('sourceSchemaVersion', 'exportSchemaVersion', 'kernelSemanticsVersions'):
            manifest = copy.deepcopy(original)
            if field == 'kernelSemanticsVersions':
                manifest[field]['typeMapping'] = 'wrong/99'
            else:
                manifest[field] = 'wrong/99'
            write_manifest(self.directory, auth.sign(manifest, KEY, KEY_VERSION))
            with self.subTest(field=field), self.assertRaises(ExportError):
                self.admit()

    def test_replacement_after_verification_does_not_change_loaded_bytes(self):
        self.export()
        original_verify = verify.verify_export

        def replace_original(*args, **kwargs):
            result = original_verify(*args, **kwargs)
            (self.directory / files.table_path('command_result')).write_text('tampered')
            return result

        with patch.object(verify, 'verify_export', side_effect=replace_original):
            bundle = self.admit()
        self.assertEqual(bundle['tables']['command_result'][0]['command_id'], 'c1')

    def test_symlink_rejected(self):
        self.export()
        (self.directory / 'extra-link').symlink_to(self.root / 'registry.json')
        with self.assertRaises(ExportError):
            self.admit()


if __name__ == '__main__':
    unittest.main()
