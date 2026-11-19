"""Evidence must fail closed for partial runs or substituted engine metadata."""
import unittest

from analytics_audit.report import validate_run


class ReportTests(unittest.TestCase):
    def test_partial_pass_cannot_be_reported_as_complete(self):
        versions = dict(polarsCrate='0.55.2', duckdbCrate='1.20000.1',
                        duckdbLibrary='v2.0.0', extensionsDownloaded=False,
                        externalConnections=False, fundsExecuted=False,
                        productionRuntime=False, productionConformance=False,
                        productionReadiness=False)
        with self.assertRaisesRegex(ValueError, 'missing acceptance'):
            validate_run(versions, [dict(caseId='money-text', status='PASS')])
        for field, value in [('polarsCrate', 'wrong'),
                             ('extensionsDownloaded', True),
                             ('productionRuntime', None)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_run(dict(versions, **{field: value}), [])


if __name__ == '__main__':
    unittest.main()
