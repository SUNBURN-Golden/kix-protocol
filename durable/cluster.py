"""The pinned local PostgreSQL process for stage 5.

Reuses the stage-4 local cluster (unix socket only, listen_addresses empty,
fsync/synchronous_commit/full_page_writes/data_checksums asserted) and adds a
fail-closed check of the adopted pin. No TCP, no public endpoint.
"""

from __future__ import annotations

import getpass

import psycopg

from exploration.stage4.clusters import PostgresCluster

from durable import PINNED_POSTGRES


class PinnedPostgresCluster(PostgresCluster):
    def connect(self):
        return psycopg.connect(
            host=str(self.sock),
            dbname='postgres',
            user=getpass.getuser(),
            autocommit=True,
            application_name='kix_stage5_durable',
        )

    def start(self):
        super().start()
        if not self.version or PINNED_POSTGRES not in self.version:
            observed = self.version
            self.stop()
            raise RuntimeError('postgres pin mismatch: %s != %s' % (observed, PINNED_POSTGRES))
