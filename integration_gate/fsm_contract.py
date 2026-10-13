"""Second pinned source for the FSM replayable commands.

Core commands stay in protocol_contract.json. This module builds and checks
the additive catalogue. It does not add operations outside the public
REPLAYABLE sets, and it does not copy handler limits into the schema.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FSM_PATH = ROOT / 'docs/contracts/openapi/fsm-command-contract.json'
FSM_DOMAIN = 'kix:fixture:fsm-catalogue:0.3'
HANDLER_CONSTRAINTS = (
    'Ident checks, monetary signs, enums, windows, versions, balances, '
    'conditional bindings, and real-funds refusals are enforced in the FSM '
    'handlers. This exported catalogue is not a full business validator. '
    'Field limits that are not parameters of the public operation are not '
    'added here. Real payment, KYC, and public endpoints are not defined.'
)

# Decision order. The drift check compares these as sets to each REPLAYABLE.
MACHINE_TABLE = (
    {
        'name': 'settlement',
        'sysPath': 'reference/settlement_f01_f03',
        'module': 'reference/settlement_f01_f03/settlement_fsm.py',
        'importName': 'settlement_fsm',
        'className': 'SettlementMachine',
        'replayable': (
            'initiate', 'authorize', 'capture', 'commit', 'fail', 'cancel',
            'observe_statement', 'distribute', 'bind_refund',
            'observe_mock_cancel_acceptance',
        ),
    },
    {
        'name': 'reservation',
        'sysPath': 'reference/booking_resale_admission',
        'module': 'reference/booking_resale_admission/reservation_fsm.py',
        'importName': 'reservation_fsm',
        'className': 'ReservationMachine',
        'replayable': (
            'set_clock', 'register_show', 'hold', 'release', 'confirm', 'cancel',
            'observe_payment', 'bind_settlement', 'issue', 'authorize_admission',
            'consume',
        ),
    },
    {
        'name': 'resale',
        'sysPath': 'reference/booking_resale_admission',
        'module': 'reference/booking_resale_admission/resale_fsm.py',
        'importName': 'resale_fsm',
        'className': 'ResaleMachine',
        'replayable': (
            'set_clock', 'adopt_issued', 'list_resale', 'hold_buy', 'release_hold',
            'cancel_listing', 'observe_resale_payment', 'bind_settlement',
            'accept_resale', 'close',
        ),
    },
    {
        'name': 'admission',
        'sysPath': 'reference/booking_resale_admission',
        'module': 'reference/booking_resale_admission/admission_fsm.py',
        'importName': 'admission_fsm',
        'className': 'AdmissionMachine',
        'replayable': (
            'set_clock', 'adopt_issued', 'authorize_admission', 'consume',
        ),
    },
    {
        'name': 'credit',
        'sysPath': 'reference/credit_advance_f04',
        'module': 'reference/credit_advance_f04/credit_fsm.py',
        'importName': 'credit_fsm',
        'className': 'CreditMachine',
        'replayable': (
            'offer', 'approve', 'reject', 'cancel', 'bind_settlement', 'draw',
            'repay', 'close', 'default',
        ),
    },
)

# Approved point queries. List queries stay out until Astra names their policy values.
# subject_field is the first live parameter. Extra fields come from the signature.
QUERY_TABLE = (
    {'name': 'get_show', 'machine': 'reservation', 'method': 'view_show', 'subject_field': 'show_id'},
    {'name': 'get_booking', 'machine': 'reservation', 'method': 'view', 'subject_field': 'reservation_id'},
    {'name': 'get_right', 'machine': 'resale', 'method': 'view_right', 'subject_field': 'right_id'},
    {'name': 'get_presentation', 'machine': 'resale', 'method': 'view_presentation', 'subject_field': 'right_id'},
    {'name': 'get_listing', 'machine': 'resale', 'method': 'view', 'subject_field': 'listing_id'},
    {'name': 'get_admission', 'machine': 'admission', 'method': 'view', 'subject_field': 'right_id'},
    {'name': 'get_credential', 'machine': 'admission', 'method': 'view_credential', 'subject_field': 'right_id'},
    {'name': 'get_settlement', 'machine': 'settlement', 'method': 'view', 'subject_field': 'settlement_id'},
    {'name': 'get_credit_advance', 'machine': 'credit', 'method': 'view', 'subject_field': 'advance_id'},
    {'name': 'get_credit_claim', 'machine': 'credit', 'method': 'view_claim', 'subject_field': 'claim_id'},
)

INTEGER_FIELDS = frozenset({
    'gross', 'amount', 'fee', 'tax', 'held', 'adjustment', 'capacity',
    'primary_price', 'resale_cap', 'organizer_bps', 'platform_bps', 'slot',
    'version', 'now_ms', 'expires_ms', 'sequence',
})
OBJECT_FIELDS = frozenset({'policy', 'face'})
ARRAY_FIELDS = frozenset({'gate_roles', 'order'})
BOOLEAN_FIELDS = frozenset({'resale_allowed'})


def render(document):
    return json.dumps(document, ensure_ascii=False, indent=2) + '\n'


def _import_class(spec):
    directory = str(ROOT / spec['sysPath'])
    if directory not in sys.path:
        sys.path.insert(0, directory)
    module = __import__(spec['importName'])
    return getattr(module, spec['className']), module


def live_signatures():
    """Return machine name -> op -> (parameter names, required names, subject)."""
    found = {}
    for spec in MACHINE_TABLE:
        cls, module = _import_class(spec)
        replayable = set(module.REPLAYABLE)
        ops = {}
        for op in spec['replayable']:
            fn = getattr(cls, op)
            names = []
            required = []
            subject = None
            for param in inspect.signature(fn).parameters.values():
                if param.name == 'self':
                    continue
                if subject is None:
                    subject = param.name
                names.append(param.name)
                if param.default is inspect.Parameter.empty:
                    required.append(param.name)
            ops[op] = (names, required, subject)
        found[spec['name']] = {'replayable': replayable, 'ops': ops, 'class': cls}
    return found


def _signature_parts(fn):
    names = []
    required = []
    subject = None
    defaults = {}
    for param in inspect.signature(fn).parameters.values():
        if param.name == 'self':
            continue
        if subject is None:
            subject = param.name
        names.append(param.name)
        defaults[param.name] = param.default
        if param.default is inspect.Parameter.empty:
            required.append(param.name)
    return names, required, subject, defaults


def live_query_signatures():
    """Return query name -> method metadata from the live view* signatures."""
    machines = live_signatures()
    replayable = set()
    for spec in MACHINE_TABLE:
        replayable |= machines[spec['name']]['replayable']
    found = {}
    for spec in QUERY_TABLE:
        live = machines[spec['machine']]
        method_name = spec['method']
        fn = getattr(live['class'], method_name, None)
        if fn is None:
            found[spec['name']] = None
            continue
        names, required, subject, defaults = _signature_parts(fn)
        found[spec['name']] = {
            'machine': spec['machine'],
            'method': method_name,
            'subject': subject,
            'names': names,
            'required': required,
            'defaults': defaults,
            'replayable': method_name in replayable,
            'view': method_name.startswith('view'),
        }
    return found


def _property_schema(name, optional_null):
    if name in OBJECT_FIELDS:
        schema = {'type': 'object'}
    elif name in ARRAY_FIELDS:
        schema = {'type': 'array'}
    elif name in BOOLEAN_FIELDS:
        schema = {'type': 'boolean'}
    elif name in INTEGER_FIELDS:
        schema = {'type': 'integer'}
    else:
        schema = {'type': 'string'}
    if optional_null:
        schema = {'type': [schema['type'], 'null']}
    return schema


def canonical_fsm_document():
    """Body schemas from public signatures. Types are the handler's JSON kinds.

    Numeric windows, ident length, and enums stay handler constraints.
    """
    signatures = live_signatures()
    machines = {}
    commands = {}
    for spec in MACHINE_TABLE:
        live = signatures[spec['name']]
        machines[spec['name']] = {
            'module': spec['module'],
            'class': spec['className'],
            'replayable': list(spec['replayable']),
        }
        for op in spec['replayable']:
            names, required, subject = live['ops'][op]
            fn = getattr(live['class'], op)
            _names, _required, _subject, defaults = _signature_parts(fn)
            properties = {}
            for name in names:
                optional_null = (
                    defaults[name] is None
                    and defaults[name] is not inspect.Parameter.empty
                )
                properties[name] = _property_schema(name, optional_null)
            commands[spec['name'] + '_' + op] = {
                'machine': spec['name'],
                'op': op,
                'subject_field': subject,
                'schema': {
                    'type': 'object',
                    'additionalProperties': False,
                    'required': list(required),
                    'properties': properties,
                },
            }
    queries = {}
    query_live = live_query_signatures()
    for spec in QUERY_TABLE:
        live = query_live[spec['name']]
        properties = {}
        for name in live['names']:
            default = live['defaults'][name]
            optional_null = default is None and default is not inspect.Parameter.empty
            properties[name] = _property_schema(name, optional_null)
        queries[spec['name']] = {
            'machine': spec['machine'],
            'method': spec['method'],
            'subject_field': live['subject'],
            'schema': {
                'type': 'object',
                'additionalProperties': False,
                'required': list(live['required']),
                'properties': properties,
            },
        }
    return {
        'domain': FSM_DOMAIN,
        'unknownFields': 'REJECT',
        'sourceAuthentication': 'FIXTURE_ONLY',
        'handlerConstraints': HANDLER_CONSTRAINTS,
        'machines': machines,
        'commands': commands,
        'queries': queries,
    }


def drift_problems(document):
    """Return error strings. Empty means the document matches the live FSMs."""
    errors = []

    def need(condition, message):
        if not condition:
            errors.append(message)

    if not isinstance(document, dict):
        return ['fsm source is not an object']
    need(document.get('domain') == FSM_DOMAIN, 'fsm domain drift')
    need(document.get('unknownFields') == 'REJECT', 'fsm unknownFields is not REJECT')
    need(document.get('sourceAuthentication') == 'FIXTURE_ONLY',
         'fsm sourceAuthentication is not FIXTURE_ONLY')
    need(document.get('handlerConstraints') == HANDLER_CONSTRAINTS,
         'fsm handlerConstraints drift')
    machines = document.get('machines')
    commands = document.get('commands')
    need(isinstance(machines, dict) and isinstance(commands, dict),
         'fsm machines or commands missing')
    if not isinstance(machines, dict) or not isinstance(commands, dict):
        return errors
    expected_names = [spec['name'] for spec in MACHINE_TABLE]
    need(list(machines) == expected_names, 'fsm machine set drift')
    signatures = live_signatures()
    expected_commands = []
    for spec in MACHINE_TABLE:
        live = signatures[spec['name']]
        entry = machines.get(spec['name']) or {}
        need(entry.get('module') == spec['module'], 'fsm module drift: ' + spec['name'])
        need(entry.get('class') == spec['className'], 'fsm class drift: ' + spec['name'])
        replayable = entry.get('replayable')
        need(isinstance(replayable, list), 'fsm replayable is not a list: ' + spec['name'])
        if not isinstance(replayable, list):
            continue
        need(len(replayable) == len(set(replayable)),
             'fsm replayable has duplicates: ' + spec['name'])
        need(set(replayable) == live['replayable'] == set(spec['replayable']),
             'fsm REPLAYABLE drift: ' + spec['name'])
        for op in spec['replayable']:
            expected_commands.append(spec['name'] + '_' + op)
            action = spec['name'] + '_' + op
            command = commands.get(action)
            if not isinstance(command, dict):
                errors.append('fsm command missing: ' + action)
                continue
            names, required, subject = live['ops'][op]
            need(command.get('machine') == spec['name'], 'fsm machine field drift: ' + action)
            need(command.get('op') == op, 'fsm op field drift: ' + action)
            need(command.get('subject_field') == subject, 'fsm subject_field drift: ' + action)
            schema = command.get('schema')
            if not isinstance(schema, dict):
                errors.append('fsm schema missing: ' + action)
                continue
            need(schema.get('type') == 'object', 'fsm schema type drift: ' + action)
            need(schema.get('additionalProperties') is False,
                 'additionalProperties is not false: ' + action)
            properties = schema.get('properties')
            need(isinstance(properties, dict), 'fsm properties missing: ' + action)
            if isinstance(properties, dict):
                need(list(properties) == names, 'fsm signature properties drift: ' + action)
            need(schema.get('required') == required, 'fsm signature required drift: ' + action)
    need(list(commands) == expected_commands, 'fsm command set drift')
    queries = document.get('queries')
    need(isinstance(queries, dict), 'fsm queries missing')
    if isinstance(queries, dict):
        expected_queries = [spec['name'] for spec in QUERY_TABLE]
        need(list(queries) == expected_queries, 'fsm query set drift')
        query_live = live_query_signatures()
        replayable_names = set()
        for spec in MACHINE_TABLE:
            replayable_names |= signatures[spec['name']]['replayable']
        for spec in QUERY_TABLE:
            action = spec['name']
            query = queries.get(action)
            live = query_live.get(action)
            if not isinstance(query, dict) or live is None:
                errors.append('fsm query missing: ' + action)
                continue
            documented = query.get('method')
            need(query.get('machine') == spec['machine'], 'fsm query machine drift: ' + action)
            need(isinstance(documented, str) and documented.startswith('view'),
                 'fsm query method is not a view method: ' + action)
            need(documented not in replayable_names,
                 'fsm query method is replayable: ' + action)
            need(documented == spec['method'] == live['method'],
                 'fsm query method drift: ' + action)
            need(live['view'] and not live['replayable'],
                 'fsm query live method is not a read: ' + action)
            need(query.get('subject_field') == spec['subject_field'] == live['subject'],
                 'fsm query subject_field drift: ' + action)
            schema = query.get('schema')
            if not isinstance(schema, dict):
                errors.append('fsm query schema missing: ' + action)
                continue
            need(schema.get('type') == 'object', 'fsm query schema type drift: ' + action)
            need(schema.get('additionalProperties') is False,
                 'additionalProperties is not false: ' + action)
            properties = schema.get('properties')
            need(isinstance(properties, dict), 'fsm query properties missing: ' + action)
            if isinstance(properties, dict):
                need(list(properties) == live['names'], 'fsm query signature properties drift: ' + action)
                need('idempotency_key' not in properties, 'fsm query has idempotency_key: ' + action)
            need(schema.get('required') == live['required'], 'fsm query signature required drift: ' + action)
    return errors


def load_fsm(root=None):
    root = Path(root) if root is not None else ROOT
    path = root / 'docs/contracts/openapi/fsm-command-contract.json'
    source_bytes = path.read_bytes()
    document = json.loads(source_bytes)
    return document, source_bytes
