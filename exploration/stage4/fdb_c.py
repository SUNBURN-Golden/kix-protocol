"""Minimal FoundationDB C client. Not a storage engine."""

from __future__ import annotations

import ctypes
import threading
from ctypes import POINTER, byref, c_char_p, c_int, c_void_p, string_at

from exploration.stage4.budget import FDB_API_VERSION

_lib = None
_network_started = False
_network_lock = threading.Lock()


class FdbError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _library():
    global _lib
    if _lib is not None:
        return _lib
    lib = ctypes.CDLL('libfdb_c.so')
    lib.fdb_select_api_version_impl.argtypes = [c_int, c_int]
    lib.fdb_select_api_version_impl.restype = c_int
    lib.fdb_get_error.argtypes = [c_int]
    lib.fdb_get_error.restype = c_char_p
    lib.fdb_setup_network.argtypes = []
    lib.fdb_setup_network.restype = c_int
    lib.fdb_run_network.argtypes = []
    lib.fdb_run_network.restype = c_int
    lib.fdb_create_database.argtypes = [c_char_p, POINTER(c_void_p)]
    lib.fdb_create_database.restype = c_int
    lib.fdb_database_destroy.argtypes = [c_void_p]
    lib.fdb_database_destroy.restype = None
    lib.fdb_database_create_transaction.argtypes = [c_void_p, POINTER(c_void_p)]
    lib.fdb_database_create_transaction.restype = c_int
    lib.fdb_transaction_destroy.argtypes = [c_void_p]
    lib.fdb_transaction_destroy.restype = None
    lib.fdb_transaction_set.argtypes = [c_void_p, c_char_p, c_int, c_char_p, c_int]
    lib.fdb_transaction_set.restype = None
    lib.fdb_transaction_get.argtypes = [c_void_p, c_char_p, c_int, c_int]
    lib.fdb_transaction_get.restype = c_void_p
    lib.fdb_transaction_commit.argtypes = [c_void_p]
    lib.fdb_transaction_commit.restype = c_void_p
    lib.fdb_future_block_until_ready.argtypes = [c_void_p]
    lib.fdb_future_block_until_ready.restype = c_int
    lib.fdb_future_get_error.argtypes = [c_void_p]
    lib.fdb_future_get_error.restype = c_int
    lib.fdb_future_destroy.argtypes = [c_void_p]
    lib.fdb_future_destroy.restype = None
    lib.fdb_future_get_value.argtypes = [
        c_void_p, POINTER(c_int), POINTER(c_void_p), POINTER(c_int),
    ]
    lib.fdb_future_get_value.restype = c_int
    err = lib.fdb_select_api_version_impl(FDB_API_VERSION, FDB_API_VERSION)
    if err:
        raise FdbError(_error_text(lib, err))
    _lib = lib
    return lib


def _error_text(lib, code):
    raw = lib.fdb_get_error(code)
    if not raw:
        return 'fdb error %s' % code
    return raw.decode()


def error_text(code):
    return _error_text(_library(), code)


def _check(lib, code):
    if code:
        raise FdbError(_error_text(lib, code))


def ensure_network():
    global _network_started
    with _network_lock:
        if _network_started:
            return
        lib = _library()
        _check(lib, lib.fdb_setup_network())

        def run():
            lib.fdb_run_network()

        thread = threading.Thread(target=run, name='fdb-network', daemon=True)
        thread.start()
        _network_started = True


class Database:
    def __init__(self, cluster_file):
        ensure_network()
        lib = _library()
        handle = c_void_p()
        _check(lib, lib.fdb_create_database(cluster_file.encode(), byref(handle)))
        self._lib = lib
        self.handle = handle

    def close(self):
        if self.handle:
            self._lib.fdb_database_destroy(self.handle)
            self.handle = None

    def transaction(self):
        handle = c_void_p()
        _check(
            self._lib,
            self._lib.fdb_database_create_transaction(self.handle, byref(handle)),
        )
        return Transaction(self._lib, handle)


class Transaction:
    def __init__(self, lib, handle):
        self._lib = lib
        self.handle = handle

    def close(self):
        if self.handle:
            self._lib.fdb_transaction_destroy(self.handle)
            self.handle = None

    def set(self, key, value):
        self._lib.fdb_transaction_set(self.handle, key, len(key), value, len(value))

    def get(self, key, snapshot=False):
        future = self._lib.fdb_transaction_get(
            self.handle, key, len(key), 1 if snapshot else 0,
        )
        try:
            _check(self._lib, self._future_error(future))
            present = c_int()
            value = c_void_p()
            length = c_int()
            _check(self._lib, self._lib.fdb_future_get_value(
                future, byref(present), byref(value), byref(length),
            ))
            if not present.value:
                return None
            return string_at(value, length.value)
        finally:
            self._lib.fdb_future_destroy(future)

    def commit(self):
        future = self._lib.fdb_transaction_commit(self.handle)
        try:
            code = self._future_error(future)
        finally:
            self._lib.fdb_future_destroy(future)
        if code:
            raise FdbError(error_text(code))

    def _future_error(self, future):
        blocked = self._lib.fdb_future_block_until_ready(future)
        if blocked:
            return blocked
        return self._lib.fdb_future_get_error(future)
