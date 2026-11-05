"""Navigate four synthetic ticket consoles over one live local desk session."""

import argparse
from pathlib import Path
import sys

import admission_console
import booking_console
import resale_console
import settlement_console
from booking_console import _diagnostic
from ticket_operations_client import TicketOperationsClient


_SURFACES = {
    'booking': booking_console,
    'resale': resale_console,
    'admission': admission_console,
    'settlement': settlement_console,
}


def run_console(client, *, input_stream, output_stream, error_stream):
    """Return 0 clean, 1 after a known refusal, 2 after terminal failure.

    The caller owns close(). After status 2 it must close and retire the session,
    including when the transport remains usable after a terminal I/O failure.
    Navigation performs no requests. Each booking invocation has fresh local
    quote/target/preview state; only the client's service graph is shared.
    """
    rejected = False
    try:
        print('Shared local synthetic ticket console — one in-memory desk.\n'
              'Choose a surface; its quit returns here. Menu quit closes the session.\n'
              'Leaving booking discards quote text, target and pending confirmation.\n'
              'Receipts are action snapshots; request views explicitly for current observations.\n'
              'Product policy: UNDETERMINED — Astra/User; legal effects: UNDETERMINED — User/legal.',
              file=output_stream)
        while True:
            print('Surfaces: ' + ', '.join(_SURFACES) + ', quit', file=output_stream)
            print('surface: ', end='', file=output_stream, flush=True)
            line = input_stream.readline()
            if line == '':
                raise EOFError('terminal input ended; no further submissions')
            surface = line.removesuffix('\n').removesuffix('\r')
            if surface == 'quit':
                return int(rejected)
            if surface not in _SURFACES:
                print('Unknown surface; choose a surface from the menu.', file=output_stream)
                continue
            status = _SURFACES[surface].run_console(
                client, input_stream=input_stream, output_stream=output_stream, error_stream=error_stream)
            if type(status) is not int or status not in (0, 1, 2):
                raise ValueError('unexpected surface result: ' + repr(status))
            if status == 2:
                return 2
            rejected = rejected or status == 1
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream)
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path, help='caller-selected synthetic desk fixture')
    parser.add_argument('--cleanup-timeout', required=True, type=float,
                        help='finite positive child cleanup budget; not a response deadline')
    args = parser.parse_args(argv)
    try:
        client = TicketOperationsClient.launch(args.fixture, cleanup_timeout=args.cleanup_timeout)
    except ValueError as error:
        parser.error(str(error))
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, sys.stderr)
        return 2
    status = 2
    try:
        status = run_console(client, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)
    finally:
        try:
            child_status = client.close()
        except (Exception, KeyboardInterrupt) as error:
            _diagnostic(error, sys.stderr)
            status = 2
        else:
            if child_status != 0:
                try:
                    print('Child exit status=' + str(child_status), file=sys.stderr, flush=True)
                except (OSError, ValueError, UnicodeError):
                    pass
                status = status or 1
    return status


if __name__ == '__main__':
    raise SystemExit(main())
