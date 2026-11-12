"""One fail-closed error type for the export boundary.

Every refusal carries a stable local code. Codes are local to this fixture
package; they are not protocol error-catalogue entries and register nothing.
"""

from __future__ import annotations


class ExportError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code
