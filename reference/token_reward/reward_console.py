"""Guided synthetic F4 rewards in one fresh local session (in-process or subprocess)."""

import argparse
from pathlib import Path
import re
import sys

from reward_cli import _error, dispatch_request
from reward_client import RewardClient, RewardTransportUncertainty
from reward_fixture import FixtureError, decode_json, exact_fields, load_fixture, validate_json
from token_reward_model import SOURCE_FINALITY_FLAGS, TokenRewardError, _canonical


# Prompt order only: dispatch and all economic predicates remain in the desk.
_FIELDS = {
    'observe': ('reward_key', 'source_view', 'rule_version', 'amount', 'source_kind'),
    'hold': ('reward_id_value',),
    'mark_eligible': ('reward_id_value', 'window_closed', 'source_view', 'abuse_clear'),
    'submit': ('reward_id_value', 'approval_ref', 'signed_bytes_digest', 'spend_pool'),
    'observe_transfer_effects': ('reward_id_value', 'effects_digest', 'outcome'),
    'reconcile_unknown': ('reward_id_value', 'same_digest', 'resolution'),
    'observe_source_cancel': ('reward_id_value', 'source_view', 'reason'),
    'observe_krw_refund': ('reward_id_value', 'source_view', 'reason'),
    'supersede': ('reward_id_value', 'approval_ref', 'rule_version'),
    'view': ('reward_id_value',),
    'reward_ids': (),
    'pool_view': (),
}
_READS = {'view', 'reward_ids', 'pool_view'}
_OPTIONALS = {
    'mark_eligible': {'abuse_kind', 'recipient_cap', 'program_cap'},
    'submit': {'budget_ceiling', 'execution_permit'},
}
_APPROVAL_FIELDS = {'record_id', 'generation', 'authority_id', 'actor_type',
                    'action', 'scope_ref', 'evidence_refs'}
_HINTS = {
    'reward_key': 'JSON object or :guided: program, source_op_id, recipient, kind',
    'source_view': 'JSON object or :guided; complete caller snapshot, no defaults',
    'approval_ref': 'JSON object or :guided; caller synthetic approval record',
    'window_closed': 'JSON boolean: true or false; caller assertion',
    'abuse_clear': 'JSON boolean: true or false',
    'amount': 'explicit decimal integer in synthetic POINT_F4',
    'source_kind': 'SETTLEMENT, RESALE, RESERVATION',
    'spend_pool': 'PROTOCOL_REVENUE, TOKEN_TREASURY_REWARD; FSM checks caller value',
    'outcome': 'SUCCESS, FAILED, UNKNOWN',
    'resolution': 'SUCCESS, FAILED',
}


class _InputError(ValueError):
    pass


def _compose_reward_key(prompt):
    """Collect caller text only; no identity generation or session access."""
    return {name: prompt(name + ' (verbatim string)')
            for name in ('program', 'source_op_id', 'recipient', 'kind')}


def _compose_source_view(prompt):
    """Collect synthetic source assertions; domain predicates stay in the FSM."""
    value = {name: prompt(name + ' (verbatim string)') for name in ('phase', 'currency')}
    for name in SOURCE_FINALITY_FLAGS:
        flag = decode_json(prompt(name + ' (JSON boolean; explicit caller assertion)'))
        if type(flag) is not bool:
            raise _InputError(name + ' requires a JSON boolean')
        value[name] = flag
    extra = decode_json(prompt('additional source fields (JSON object; {} supplies none)'))
    if type(extra) is not dict:
        raise _InputError('additional source fields requires a JSON object')
    collisions = set(value) & set(extra)
    if collisions:
        raise _InputError('additional source fields cannot overwrite: ' + ', '.join(sorted(collisions)))
    value.update(extra)
    return value


def _compose_approval_ref(prompt):
    """Collect a synthetic assertion, without inferring actors or evidence."""
    value = {'record_id': prompt('record_id (verbatim string)')}
    generation = decode_json(prompt('generation (JSON integer)'))
    if type(generation) is not int:
        raise _InputError('generation requires a JSON integer')
    value['generation'] = generation
    for name in ('authority_id', 'actor_type', 'action', 'scope_ref'):
        value[name] = prompt(name + ' (verbatim string)')
    count = decode_json(prompt('evidence_refs item count (nonnegative JSON integer)'))
    if type(count) is not int or count < 0:
        raise _InputError('evidence_refs item count requires a nonnegative JSON integer')
    value['evidence_refs'] = [prompt(f'evidence_refs item {index + 1} (verbatim string)')
                              for index in range(count)]
    choice = prompt('prior_record (include / omit; explicit choice required)')
    if choice not in {'include', 'omit'}:
        raise _InputError('prior_record requires literal include or omit')
    if choice == 'include':
        prior = decode_json(prompt('prior_record (JSON string or null)'))
        if prior is not None and type(prior) is not str:
            raise _InputError('prior_record requires a JSON string or null')
        value['prior_record'] = prior
    return value


def _diagnostic(error, stream, *, last_reply=None):
    # Diagnostic failure must never permit a subsequent dispatch.
    try:
        detail = {'exceptions': [], 'last_reply': last_reply}
        seen = set()
        while error is not None and id(error) not in seen:
            seen.add(id(error))
            detail['exceptions'].append({'type': type(error).__name__, 'message': str(error)})
            if isinstance(error, RewardTransportUncertainty):
                detail.update(request=error.request, request_bytes_hex=error.request_bytes.hex(),
                              reply_bytes_hex=error.reply_bytes.hex())
            error = error.__cause__ or (None if error.__suppress_context__ else error.__context__)
        print('FENCED: ' + _canonical(detail), file=stream, flush=True)
    except (Exception, KeyboardInterrupt):
        pass


def run_console(session, *, input_stream, output_stream, error_stream) -> int:
    """Preserve the importable in-process console entry point."""
    return _run_console(lambda request: dispatch_request(session, request), state={},
                        input_stream=input_stream, output_stream=output_stream, error_stream=error_stream)


def run_subprocess_console(fixture, *, cleanup_timeout, input_stream, output_stream, error_stream) -> int:
    """Own one desk child until quit or failure; cleanup never authorizes a retry."""
    state, client, status = {}, None, 2
    try:
        client = RewardClient.launch(fixture, cleanup_timeout=cleanup_timeout)
        status = _run_console(client.request, state=state, input_stream=input_stream,
                              output_stream=output_stream, error_stream=error_stream)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream, last_reply=state.get('last_reply'))
    finally:
        if client is not None:
            try:
                code = client.close()
                if code != 0 and not (code == 1 and status == 1):
                    raise RuntimeError(f'local reward desk exited with status {code}')
            except (Exception, KeyboardInterrupt) as error:
                # A separate cleanup diagnostic retains the primary failure above.
                _diagnostic(error, error_stream, last_reply=state.get('last_reply'))
                status = 2
    return status


def _run_console(send_request, *, state, input_stream, output_stream, error_stream) -> int:
    """Return 0 on clean quit, sticky 1 on domain refusal, 2 on terminal failure.

    No startup reads, implicit fields, automatic transitions, retries or cleanup
    mutations. Each confirmed selection dispatches once, including explicit replays.
    """
    state['last_reply'] = None
    rejected = False

    def prompt(label):
        print(label + ': ', end='', file=output_stream, flush=True)
        line = input_stream.readline()
        if line == '':
            raise EOFError('terminal input ended; no further submissions')
        return line.removesuffix('\n').removesuffix('\r')

    def field(name):
        hint = _HINTS.get(name)
        raw = prompt(name + (' (' + hint + ')' if hint else ''))
        if name in {'reward_key', 'source_view', 'approval_ref', 'window_closed', 'abuse_clear'}:
            if raw == ':guided' and name == 'reward_key':
                value = _compose_reward_key(prompt)
            elif raw == ':guided' and name == 'source_view':
                value = _compose_source_view(prompt)
            elif raw == ':guided' and name == 'approval_ref':
                value = _compose_approval_ref(prompt)
            else:
                value = decode_json(raw)
            if name in {'window_closed', 'abuse_clear'}:
                if type(value) is not bool:
                    raise _InputError(name + ' requires a JSON boolean')
            elif name == 'reward_key':
                exact_fields(value, {'program', 'source_op_id', 'recipient', 'kind'}, name)
            elif name == 'approval_ref':
                exact_fields(value, _APPROVAL_FIELDS, name, {'prior_record'})
                if type(value['evidence_refs']) is not list:
                    raise _InputError('approval evidence_refs requires a JSON array')
            elif type(value) is not dict:
                raise _InputError('source_view requires a JSON object')
            validate_json(value)
            return value
        if name == 'amount':
            if re.fullmatch(r'-?[0-9]+', raw) is None:
                raise _InputError('amount requires an explicit decimal integer')
            try:
                return int(raw)
            except ValueError as error:
                raise _InputError('amount integer is too long') from error
        if not raw or raw != raw.strip():
            raise _InputError(name + ' requires an explicit value without surrounding whitespace')
        return raw

    try:
        print('Local synthetic reward console — MOCK_TOKEN_REWARD_ONLY, POINT_F4, in-memory.\n'
              'Receipts are historical action snapshots; explicit reads are current observations.\n'
              'Non-transferable; token_issued, onchain_recorded, funds_executed, krw_paid,\n'
              'chain_finality, durable, legal_authority remain false.\n'
              'Amounts, caps, budgets, durations and approval policy: UNDETERMINED — Astra/User.\n'
              'Actual approver designation: User-owned; caller inputs are synthetic assertions.\n'
              'UNKNOWN requires a separate explicit action; no automatic reads or retries.',
              file=output_stream)
        while True:
            print('Actions: ' + ', '.join(_FIELDS) + ', quit', file=output_stream)
            action = prompt('action')
            if action == 'quit':
                return int(rejected)
            if action not in _FIELDS:
                print('Unknown action; choose an action from the menu.', file=output_stream)
                continue
            mutation = action not in _READS
            try:
                arguments = {name: field(name) for name in _FIELDS[action]}
                if action in _OPTIONALS:
                    optional = decode_json(prompt('optional arguments (JSON object; {} omits all; allowed: '
                                                  + ', '.join(sorted(_OPTIONALS[action])) + ')'))
                    exact_fields(optional, set(), 'optional arguments', _OPTIONALS[action])
                    if optional.get('execution_permit') is not None:
                        exact_fields(optional['execution_permit'],
                                     {'fence_ref', 'signed_bytes_digest'}, 'execution_permit')
                    arguments.update(optional)
                if mutation:
                    arguments['idempotency_key'] = field('idempotency_key')
                request = {'operation': action, 'arguments': arguments}
                if mutation:
                    print('proposed=' + _canonical(request), file=output_stream, flush=True)
                    if prompt('Type literal SUBMIT to send once; anything else declines') != 'SUBMIT':
                        print('Declined; no request sent.', file=output_stream)
                        continue
            except (FixtureError, _InputError) as error:
                print('input_error=' + _canonical({'type': type(error).__name__, 'message': str(error)}),
                      file=output_stream)
                continue
            terminal = None
            try:
                reply = send_request(request)
            except TokenRewardError as error:
                reply = _error(action, error)
                rejected = True
            except FixtureError as error:
                reply = _error(action, error)
                terminal = error
            state['last_reply'] = reply  # Preserve the complete envelope before rendering.
            print('desk=' + _canonical(reply), file=output_stream, flush=True)
            if terminal is not None:
                raise terminal
            if 'error' in reply:
                if reply['operation'] != action or set(reply['error']) != {'code'}:
                    raise RuntimeError('local reward desk returned a terminal error')
                rejected = True
            if 'receipt' in reply:
                print('Historical action snapshot (including duplicate receipts).', file=output_stream)
            elif 'error' not in reply:
                print('Current session observation (explicit read).', file=output_stream)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream, last_reply=state['last_reply'])
        return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', required=True, type=Path,
                        help='caller-selected synthetic opening balances; no default')
    parser.add_argument('--mode', choices=('in-process', 'subprocess'), default='in-process')
    parser.add_argument('--cleanup-timeout', type=float,
                        help='required in subprocess mode; finite positive seconds for child cleanup only')
    args = parser.parse_args(argv)
    if args.mode == 'subprocess':
        if args.cleanup_timeout is None:
            parser.error('--mode subprocess requires --cleanup-timeout')
        return run_subprocess_console(args.fixture, cleanup_timeout=args.cleanup_timeout,
                                      input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)
    if args.cleanup_timeout is not None:
        parser.error('--cleanup-timeout requires --mode subprocess')
    try:
        session = load_fixture(args.fixture)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, sys.stderr, last_reply=_error(None, error))
        return 2
    return run_console(session, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)


if __name__ == '__main__':
    raise SystemExit(main())
