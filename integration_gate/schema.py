"""Published command-schema checks for the integration gate.

The keyword set is the one present in protocol_contract.json. Any other
keyword fails closed so a constraint cannot be skipped silently.
"""
from __future__ import annotations

KNOWN_KEYWORDS = frozenset({
    'additionalProperties',
    'maxLength',
    'maximum',
    'minLength',
    'minimum',
    'properties',
    'required',
    'type',
})
TYPE_NAMES = frozenset({'object', 'array', 'string', 'integer', 'boolean', 'null'})
ENVELOPE_FIELDS = ('operationId', 'actor', 'action', 'body')


class EnvelopeError(Exception):
    def __init__(self, error, detail=None):
        super().__init__(error)
        self.error = error
        self.detail = detail


def unsupported_schema(schema, path='$'):
    """Return human-readable problems. Empty means the schema is enforceable."""
    found = []

    def walk(node, at):
        if not isinstance(node, dict):
            found.append(at + ': schema is not an object')
            return
        extra = sorted(set(node) - KNOWN_KEYWORDS)
        if extra:
            found.append(at + ': unsupported keyword ' + ','.join(extra))
        if 'additionalProperties' in node and node['additionalProperties'] is not False:
            found.append(at + ': additionalProperties must be false or omitted')
        declared = node.get('type')
        if declared is not None:
            types = declared if isinstance(declared, list) else [declared]
            if not types or any(item not in TYPE_NAMES for item in types):
                found.append(at + ': unsupported type')
        props = node.get('properties')
        if props is not None:
            if not isinstance(props, dict):
                found.append(at + ': properties is not an object')
            else:
                for key, child in props.items():
                    walk(child, at + '.' + str(key))

    walk(schema, path)
    return found


def problems(instance, schema, path='$'):
    """Validate instance. Does not echo instance values."""
    blocked = unsupported_schema(schema, path)
    if blocked:
        return blocked[:12]
    errors = []

    def add(message):
        if len(errors) < 12:
            errors.append(message)

    declared = schema.get('type')
    if not _type_matches(instance, declared):
        add(path + ': expected ' + _type_label(declared))
        return errors
    if instance is None:
        return errors
    if isinstance(instance, str):
        if 'minLength' in schema and len(instance) < schema['minLength']:
            add(path + ': shorter than minLength')
        if 'maxLength' in schema and len(instance) > schema['maxLength']:
            add(path + ': longer than maxLength')
    if type(instance) is int:
        if 'minimum' in schema and instance < schema['minimum']:
            add(path + ': below minimum')
        if 'maximum' in schema and instance > schema['maximum']:
            add(path + ': above maximum')
    if isinstance(instance, dict):
        props = schema.get('properties') or {}
        if schema.get('additionalProperties') is False:
            extra = sorted(set(instance) - set(props))
            if extra:
                shown = ','.join(_clip(name) for name in extra[:8])
                add(path + ': unknown fields ' + shown)
        required = schema.get('required') or []
        missing = [key for key in required if key not in instance]
        if missing:
            add(path + ': missing ' + ','.join(missing))
        for key, child in props.items():
            if key in instance:
                for item in problems(instance[key], child, path + '.' + key):
                    add(item)
    return errors


def parse_envelope(payload, commands):
    """Return operationId, actor, action, body or raise EnvelopeError.

    Command-body failures use the published schema. They are not Core results.
    """
    if not isinstance(payload, dict):
        raise EnvelopeError('ENVELOPE_INVALID')
    unknown = sorted(set(payload) - set(ENVELOPE_FIELDS))
    if unknown:
        raise EnvelopeError('ENVELOPE_UNKNOWN_FIELDS')
    if any(key not in payload for key in ENVELOPE_FIELDS):
        raise EnvelopeError('ENVELOPE_INVALID')
    operation_id = payload['operationId']
    actor = payload['actor']
    action = payload['action']
    body = payload['body']
    if not isinstance(operation_id, str) or not isinstance(actor, str):
        raise EnvelopeError('ENVELOPE_INVALID')
    if not isinstance(action, str) or action not in commands:
        raise EnvelopeError('UNKNOWN_ACTION')
    if not isinstance(body, dict):
        raise EnvelopeError('OBJECT_BODY_REQUIRED')
    found = problems(body, commands[action], 'body')
    if found:
        raise EnvelopeError('SCHEMA_REJECTED', '; '.join(found))
    return operation_id, actor, action, body


def _type_matches(value, declared):
    if declared is None:
        return False
    names = declared if isinstance(declared, list) else [declared]
    for name in names:
        if name == 'object' and isinstance(value, dict):
            return True
        if name == 'array' and isinstance(value, list):
            return True
        if name == 'string' and isinstance(value, str):
            return True
        if name == 'boolean' and isinstance(value, bool):
            return True
        if name == 'integer' and type(value) is int:
            return True
        if name == 'null' and value is None:
            return True
    return False


def _type_label(declared):
    if isinstance(declared, list):
        return ' or '.join(str(item) for item in declared)
    return str(declared)


def _clip(name):
    text = str(name)
    if len(text) > 64:
        return text[:64]
    return text
