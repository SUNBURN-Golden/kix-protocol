"""Pure admission decisions for the on-sale waiting room and GA routing.

No I/O, no psycopg. One command is one atomic unit: identity, payload sha256,
first result, token state transition, shard remaining decrement, append-only
evidence and a budget ledger entry. Replay returns the stored first result and
adds nothing. A conflicting payload for an existing command id is retained as
separate evidence. Capacity writes nothing. The outcome vocabulary is the
stage-5 durable one: replayed / conflict_retained / capacity /
business_rejected / new_success (unknown is added by the unit on CommitUnknown).

CommandIdentity is stable business scope (show + inventory epoch + inventory
mode) + authenticated principal + client_command_id (contract §4, ADR-0001
§3). Routing fields (shardId, nonce, placement version) are never key
components; the payload fingerprint is stored separately. Every limit is a
required caller argument with no default and no product meaning; fixture
numbers live only in test code.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

from readiness.codec import canonical_json

from durable.model import Usage

from onsale import tokens

ISSUED = 'ISSUED'
REPLACED = 'REPLACED'
EXPIRED = 'EXPIRED'
CONSUMED = 'CONSUMED'
TERMINAL_STATES = (REPLACED, EXPIRED, CONSUMED)

OUTCOMES = (
    'replayed', 'conflict_retained', 'capacity', 'business_rejected',
    'new_success', 'unknown',
)

_FLAGS = {
    'localOnsaleFixtureOnly': True,
    'protocolTruth': False,
    'productionConformance': False,
    'productionReadiness': False,
    'productionEndpoint': False,
    'fundsExecuted': False,
    'chainWriter': False,
    'delegatedExecution': False,
}


class GaConfigError(ValueError):
    pass


def _positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError('%s must be a positive integer supplied by the caller' % label)
    return value


def _non_empty_str(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError('%s must be a non-empty string' % label)
    return value


@dataclass(frozen=True)
class OnsaleLimits:
    """Every bound the contract names, required from the caller. No defaults.

    The numbers are DECISION_REQUIRED · Astra (contract §10); this dataclass
    only refuses to run without them.
    """

    token_ttl_ms: int
    hint_ttl_ms: int
    max_queue_wait_ms: int
    max_outstanding_tokens: int
    max_sessions: int
    group_max_count: int
    group_max_bytes: int
    group_max_wait_ms: int

    def __post_init__(self):
        for name in (
            'token_ttl_ms', 'hint_ttl_ms', 'max_queue_wait_ms',
            'max_outstanding_tokens', 'max_sessions', 'group_max_count',
            'group_max_bytes', 'group_max_wait_ms',
        ):
            _positive_int(getattr(self, name), name)

    def document(self):
        return {
            'group_max_bytes': self.group_max_bytes,
            'group_max_count': self.group_max_count,
            'group_max_wait_ms': self.group_max_wait_ms,
            'hint_ttl_ms': self.hint_ttl_ms,
            'max_outstanding_tokens': self.max_outstanding_tokens,
            'max_queue_wait_ms': self.max_queue_wait_ms,
            'max_sessions': self.max_sessions,
            'token_ttl_ms': self.token_ttl_ms,
        }


def validate_ga_config(total_capacity, shard_capacities):
    """Contract §1: sum(initialShardCapacity) == immutableTotalCapacity."""
    _positive_int(total_capacity, 'total_capacity')
    if not isinstance(shard_capacities, dict) or not shard_capacities:
        raise GaConfigError('shard capacities must be a non-empty mapping')
    total = 0
    for shard_id, capacity in shard_capacities.items():
        _non_empty_str(shard_id, 'shard_id')
        _positive_int(capacity, 'shard capacity')
        total += capacity
    if total != total_capacity:
        raise GaConfigError('sum(initialShardCapacity) != immutableTotalCapacity')
    return dict(shard_capacities)


def effective_remaining(observed_remaining, outstanding_unexpired_tokens):
    """Contract §3 routing hint arithmetic; clamped at zero, never authority."""
    for value, label in (
        (observed_remaining, 'observed_remaining'),
        (outstanding_unexpired_tokens, 'outstanding_unexpired_tokens'),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError('%s must be a non-negative integer' % label)
    return max(0, observed_remaining - outstanding_unexpired_tokens)


def command_id(show_id, inventory_epoch, inventory_mode, principal, client_command_id):
    """Stable scope + principal + client_command_id. No routing component."""
    _non_empty_str(show_id, 'show_id')
    if isinstance(inventory_epoch, bool) or not isinstance(inventory_epoch, int) or inventory_epoch < 0:
        raise ValueError('inventory_epoch must be a non-negative integer')
    _non_empty_str(inventory_mode, 'inventory_mode')
    _non_empty_str(principal, 'principal')
    _non_empty_str(client_command_id, 'client_command_id')
    return 'cmd-' + hashlib.sha256(canonical_json(
        [show_id, inventory_epoch, inventory_mode, principal, client_command_id],
    ).encode('utf-8')).hexdigest()[:16]


def queue_ticket_id(show_id, inventory_epoch, principal, client_command_id):
    return 'qt-' + hashlib.sha256(canonical_json(
        ['ticket', show_id, inventory_epoch, principal, client_command_id],
    ).encode('utf-8')).hexdigest()[:16]


def position_identity(show_id, inventory_epoch, ticket_id):
    """Rank identity preserved across reissue; never derived from routing."""
    return 'qpos-' + hashlib.sha256(canonical_json(
        [show_id, inventory_epoch, ticket_id],
    ).encode('utf-8')).hexdigest()[:16]


def payload_sha256(body):
    return hashlib.sha256(canonical_json(body).encode('utf-8')).hexdigest()


def payload_nbytes(body):
    return len(canonical_json(body).encode('utf-8'))


def first_result_canonical(outcome, body):
    document = dict(_FLAGS)
    document['outcome'] = outcome
    document.update(body)
    return canonical_json(document)


def negative_hint_document(*, shard_id, inventory_epoch, version,
                           source_commit_position, expires_at_ms, reason='SOLD_OUT'):
    """Contract §5: a versioned negative view, never a permanent verdict."""
    return {
        'shardId': shard_id,
        'inventoryEpoch': inventory_epoch,
        'version': version,
        'sourceCommitPosition': source_commit_position,
        'expiresAtMs': expires_at_ms,
        'reason': reason,
        'negative': True,
    }


def hint_is_valid(hint, now_ms, inventory_epoch):
    """A hint is usable only inside its epoch and before its expiry."""
    if not isinstance(hint, dict):
        return False
    for name in ('shardId', 'inventoryEpoch', 'version', 'sourceCommitPosition', 'expiresAtMs'):
        if name not in hint:
            return False
    return hint['inventoryEpoch'] == inventory_epoch and hint['expiresAtMs'] > now_ms


def propose_group(entries, *, max_count, max_bytes, max_wait_ms, now_ms):
    """Contract §7 group-commit boundary: first of count / bytes / max wait.

    entries is the ordered pending list, each {'nbytes', 'enqueued_ms'}.
    Returns how many leading entries to commit now. When the oldest entry has
    already waited max_wait_ms, the oldest entry alone is proposed: low load
    never hides behind a large batch. Otherwise the longest prefix within the
    count and byte bounds is proposed, cut at the first boundary reached.
    """
    _positive_int(max_count, 'max_count')
    _positive_int(max_bytes, 'max_bytes')
    _positive_int(max_wait_ms, 'max_wait_ms')
    if not entries:
        return 0
    for entry in entries:
        if isinstance(entry['nbytes'], bool) or not isinstance(entry['nbytes'], int) or entry['nbytes'] < 0:
            raise ValueError('entry nbytes must be a non-negative integer')
        if isinstance(entry['enqueued_ms'], bool) or not isinstance(entry['enqueued_ms'], int):
            raise ValueError('entry enqueued_ms must be an integer')
    if now_ms - entries[0]['enqueued_ms'] >= max_wait_ms:
        return 1
    total = 0
    for count, entry in enumerate(entries, 1):
        total += entry['nbytes']
        if count >= max_count or total >= max_bytes:
            return count
    return len(entries)


@dataclass(frozen=True)
class EnqueueRequest:
    show_id: str
    inventory_epoch: int
    inventory_mode: str
    principal: str
    client_command_id: str
    nonce: str
    shard_id: str

    def __post_init__(self):
        command_id(self.show_id, self.inventory_epoch, self.inventory_mode,
                   self.principal, self.client_command_id)
        _non_empty_str(self.nonce, 'nonce')
        _non_empty_str(self.shard_id, 'shard_id')

    def payload(self):
        return {
            'showId': self.show_id, 'inventoryEpoch': self.inventory_epoch,
            'inventoryMode': self.inventory_mode, 'principal': self.principal,
            'clientCommandId': self.client_command_id, 'nonce': self.nonce,
            'shardId': self.shard_id,
        }


@dataclass(frozen=True)
class AdmitRequest:
    show_id: str
    inventory_epoch: int
    inventory_mode: str
    principal: str
    client_command_id: str
    token: dict

    def __post_init__(self):
        command_id(self.show_id, self.inventory_epoch, self.inventory_mode,
                   self.principal, self.client_command_id)
        if not isinstance(self.token, dict):
            raise ValueError('token must be a document')

    def payload(self):
        return {
            'showId': self.show_id, 'inventoryEpoch': self.inventory_epoch,
            'inventoryMode': self.inventory_mode, 'principal': self.principal,
            'clientCommandId': self.client_command_id,
            'token': {name: self.token.get(name) for name in tokens.TOKEN_FIELDS},
        }


@dataclass(frozen=True)
class ReissueRequest:
    show_id: str
    inventory_epoch: int
    inventory_mode: str
    principal: str
    client_command_id: str
    queue_ticket_id: str
    old_nonce: str
    new_nonce: str
    new_shard_id: str

    def __post_init__(self):
        command_id(self.show_id, self.inventory_epoch, self.inventory_mode,
                   self.principal, self.client_command_id)
        for name in ('queue_ticket_id', 'old_nonce', 'new_nonce', 'new_shard_id'):
            _non_empty_str(getattr(self, name), name)

    def payload(self):
        return {
            'showId': self.show_id, 'inventoryEpoch': self.inventory_epoch,
            'inventoryMode': self.inventory_mode, 'principal': self.principal,
            'clientCommandId': self.client_command_id,
            'queueTicketId': self.queue_ticket_id, 'oldNonce': self.old_nonce,
            'newNonce': self.new_nonce, 'newShardId': self.new_shard_id,
        }


def _usage_of(usage, budget_class):
    return usage.get(budget_class) or Usage()


def _capacity(spec, usage, budget_class, nbytes, now_ms):
    used = _usage_of(usage, budget_class)
    code, why = spec.check(
        budget_class, used_count=used.count, used_bytes=used.nbytes,
        oldest_open_ms=used.oldest_open_ms, now_ms=now_ms, extra_bytes=nbytes,
    )
    if code == 'OK':
        return None
    return Decision(outcome='capacity', budget_class=budget_class, capacity_reason=why)


@dataclass
class Decision:
    outcome: str
    reason: Optional[str] = None
    budget_class: Optional[str] = None
    capacity_reason: Optional[str] = None
    nbytes: int = 0
    first_result: str = ''
    store_command: bool = False
    store_observation: bool = False
    observation_id: Optional[str] = None
    ticket: Optional[dict] = None
    token: Optional[dict] = None
    issue_state: Optional[dict] = None
    terminal: Optional[dict] = None
    shard_decrement: Optional[tuple] = None
    session: Optional[dict] = None
    evidence: Optional[dict] = None
    ledger: Optional[tuple] = None
    ledger_close: Optional[str] = None
    hint: Optional[dict] = None
    sold_hint: Optional[dict] = None

    @property
    def writes(self):
        return (
            self.store_command or self.store_observation or self.ticket is not None
            or self.token is not None or self.terminal is not None
            or self.shard_decrement is not None or self.session is not None
            or self.evidence is not None or self.hint is not None
        )


def _existing_path(snapshot, digest, body, spec, now_ms, command):
    """Replay / conflict handling shared by all three commands (§5)."""
    existing = snapshot.existing
    if existing is None:
        return None
    if existing['payload_sha256'] == digest:
        return Decision(outcome='replayed', first_result=existing['first_result'])
    if snapshot.conflict_retained:
        return Decision(outcome='conflict_retained', first_result=existing['first_result'])
    nbytes = payload_nbytes(body)
    refused = _capacity(spec, snapshot.usage, 'observation', nbytes, now_ms)
    if refused is not None:
        return refused
    return Decision(
        outcome='conflict_retained', budget_class='observation',
        store_observation=True, nbytes=nbytes,
        first_result=existing['first_result'],
        observation_id='obs-' + command + '-' + digest,
    )


def _refusal(command, reason, nbytes, extra=None, budget_class='inflow'):
    body = {'commandId': command, 'reason': reason}
    if extra:
        body.update(extra)
    return Decision(
        outcome='business_rejected', reason=reason, budget_class=budget_class,
        store_command=True, nbytes=nbytes,
        first_result=first_result_canonical('business_rejected', body),
    )


def _token_row(token_document, tid, origin_command, ledger_entry):
    return {
        'token_id': tid,
        'queue_ticket_id': token_document['queueTicketId'],
        'position_identity': token_document['queuePositionIdentity'],
        'show_id': token_document['showId'],
        'epoch': token_document['inventoryEpoch'],
        'mode': token_document['inventoryMode'],
        'placement_version': token_document['authorityPlacementVersion'],
        'shard_id': token_document['shardId'],
        'nonce': token_document['nonce'],
        'issued_at_ms': token_document['issuedAt'],
        'expires_at_ms': token_document['expiresAt'],
        'signature': token_document['signature'],
        'key_version': token_document['keyVersion'],
        'origin_command_id': origin_command,
        'ledger_entry_id': ledger_entry,
    }


def _token_document(row):
    return {
        'showId': row['show_id'], 'queueTicketId': row['queue_ticket_id'],
        'queuePositionIdentity': row['position_identity'],
        'inventoryEpoch': row['epoch'], 'inventoryMode': row['mode'],
        'authorityPlacementVersion': row['placement_version'],
        'shardId': row['shard_id'], 'nonce': row['nonce'],
        'issuedAt': row['issued_at_ms'], 'expiresAt': row['expires_at_ms'],
        'signature': row['signature'], 'keyVersion': row['key_version'],
    }


def _evidence(evidence_id, kind, *, show_id, epoch, ticket_id, position, sequence,
              old_shard, shard, reason, issued_at_ms, expires_at_ms, outcome,
              command, now_ms):
    return {
        'evidence_id': evidence_id, 'kind': kind, 'show_id': show_id, 'epoch': epoch,
        'queue_ticket_id': ticket_id, 'position_identity': position,
        'sequence': sequence, 'old_shard_id': old_shard, 'shard_id': shard,
        'reason': reason, 'issued_at_ms': issued_at_ms, 'expires_at_ms': expires_at_ms,
        'outcome': outcome, 'command_id': command, 'at_ms': now_ms,
    }


@dataclass
class EnqueueSnapshot:
    existing: Optional[dict] = None
    conflict_retained: bool = False
    config: Optional[dict] = None
    shard: Optional[dict] = None
    outstanding: int = 0
    next_seq: int = 1
    usage: dict = field(default_factory=dict)


def decide_enqueue(snapshot, request, limits, spec, key, key_version, now_ms):
    body = request.payload()
    digest = payload_sha256(body)
    command = command_id(request.show_id, request.inventory_epoch,
                         request.inventory_mode, request.principal,
                         request.client_command_id)
    path = _existing_path(snapshot, digest, body, spec, now_ms, command)
    if path is not None:
        return path
    nbytes = payload_nbytes(body)
    refused = _capacity(spec, snapshot.usage, 'inflow', nbytes, now_ms)
    if refused is not None:
        return refused
    if snapshot.outstanding >= limits.max_outstanding_tokens:
        return Decision(outcome='capacity', budget_class='inflow',
                        capacity_reason='outstanding_tokens')
    if snapshot.config is None or snapshot.config['mode'] != request.inventory_mode:
        return _refusal(command, 'CONFIG_UNKNOWN', nbytes)
    if snapshot.shard is None:
        return _refusal(command, 'SHARD_UNKNOWN', nbytes, {'shardId': request.shard_id})
    ticket = queue_ticket_id(request.show_id, request.inventory_epoch,
                             request.principal, request.client_command_id)
    position = position_identity(request.show_id, request.inventory_epoch, ticket)
    expires = now_ms + limits.token_ttl_ms
    document = tokens.sign({
        'showId': request.show_id, 'queueTicketId': ticket,
        'queuePositionIdentity': position, 'inventoryEpoch': request.inventory_epoch,
        'inventoryMode': request.inventory_mode,
        'authorityPlacementVersion': snapshot.config['placement_version'],
        'shardId': request.shard_id, 'nonce': request.nonce,
        'issuedAt': now_ms, 'expiresAt': expires, 'keyVersion': key_version,
    }, key, key_version)
    tid = tokens.token_id(ticket, request.nonce)
    ledger_entry = 'enq:' + command
    return Decision(
        outcome='new_success', budget_class='inflow', store_command=True, nbytes=nbytes,
        first_result=first_result_canonical('new_success', {
            'commandId': command, 'queueTicketId': ticket,
            'queuePositionIdentity': position, 'queueSeq': snapshot.next_seq,
            'token': document,
        }),
        ticket={
            'queue_ticket_id': ticket, 'show_id': request.show_id,
            'epoch': request.inventory_epoch, 'principal': request.principal,
            'position_identity': position, 'seq': snapshot.next_seq, 'created_ms': now_ms,
        },
        token=_token_row(document, tid, command, ledger_entry),
        issue_state={'token_id': tid, 'seq': 0, 'state': ISSUED,
                     'reason': 'issued', 'at_ms': now_ms},
        evidence=_evidence(
            'ev-' + command, 'enqueue', show_id=request.show_id,
            epoch=request.inventory_epoch, ticket_id=ticket, position=position,
            sequence=1, old_shard=None, shard=request.shard_id, reason='issued',
            issued_at_ms=now_ms, expires_at_ms=expires, outcome='new_success',
            command=command, now_ms=now_ms,
        ),
        ledger=(ledger_entry, 'inflow', nbytes, True),
    )


@dataclass
class AdmitSnapshot:
    existing: Optional[dict] = None
    conflict_retained: bool = False
    config: Optional[dict] = None
    shard: Optional[dict] = None
    token: Optional[dict] = None
    token_state: Optional[str] = None
    token_state_seq: int = 0
    ticket: Optional[dict] = None
    ticket_sequence: int = 0
    session_count: int = 0
    hint_version: int = 0
    commit_position: int = 0
    usage: dict = field(default_factory=dict)


def decide_admit(snapshot, request, limits, spec, key, now_ms):
    body = request.payload()
    digest = payload_sha256(body)
    command = command_id(request.show_id, request.inventory_epoch,
                         request.inventory_mode, request.principal,
                         request.client_command_id)
    path = _existing_path(snapshot, digest, body, spec, now_ms, command)
    if path is not None:
        return path
    nbytes = payload_nbytes(body)
    refused = _capacity(spec, snapshot.usage, 'inflow', nbytes, now_ms)
    if refused is not None:
        return refused
    if snapshot.session_count >= limits.max_sessions:
        return Decision(outcome='capacity', budget_class='inflow',
                        capacity_reason='sessions')
    presented = request.token
    if not tokens.verify(presented, key):
        return _refusal(command, 'TOKEN_SIGNATURE', nbytes)
    if snapshot.config is None or snapshot.config['mode'] != request.inventory_mode:
        return _refusal(command, 'CONFIG_UNKNOWN', nbytes)
    if (
        presented.get('showId') != request.show_id
        or presented.get('inventoryEpoch') != request.inventory_epoch
        or presented.get('inventoryMode') != request.inventory_mode
        or presented.get('authorityPlacementVersion') != snapshot.config['placement_version']
    ):
        return _refusal(command, 'TOKEN_BINDING', nbytes)
    ticket = presented.get('queueTicketId')
    nonce = presented.get('nonce')
    if not isinstance(ticket, str) or not ticket or not isinstance(nonce, str) or not nonce:
        return _refusal(command, 'TOKEN_BINDING', nbytes)
    if snapshot.token is None:
        return _refusal(command, 'TOKEN_UNKNOWN', nbytes, {'queueTicketId': ticket})
    if _token_document(snapshot.token) != {name: presented.get(name) for name in tokens.TOKEN_FIELDS}:
        return _refusal(command, 'TOKEN_BINDING', nbytes, {'queueTicketId': ticket})
    if snapshot.ticket is None or snapshot.ticket['principal'] != request.principal:
        return _refusal(command, 'TOKEN_BINDING', nbytes, {'queueTicketId': ticket})
    extra = {'queueTicketId': ticket, 'shardId': snapshot.token['shard_id']}
    if snapshot.token_state == CONSUMED:
        return _refusal(command, 'TOKEN_CONSUMED', nbytes, extra)
    if snapshot.token_state == REPLACED:
        return _refusal(command, 'TOKEN_REPLACED', nbytes, extra)
    if snapshot.token_state == EXPIRED:
        return _refusal(command, 'TOKEN_EXPIRED', nbytes, extra)
    if snapshot.token['expires_at_ms'] <= now_ms:
        return _refusal(command, 'TOKEN_EXPIRED', nbytes, extra)
    if now_ms - snapshot.ticket['created_ms'] > limits.max_queue_wait_ms:
        return _refusal(command, 'QUEUE_WAIT', nbytes, extra)
    if snapshot.shard is None or snapshot.shard['remaining'] <= 0:
        hint = negative_hint_document(
            shard_id=snapshot.token['shard_id'], inventory_epoch=request.inventory_epoch,
            version=snapshot.hint_version + 1, source_commit_position=snapshot.commit_position,
            expires_at_ms=now_ms + limits.hint_ttl_ms,
        )
        decision = _refusal(command, 'SHARD_SOLD_OUT', nbytes, extra)
        decision.hint = {
            'hint_id': 'hint-' + command, 'show_id': request.show_id,
            'epoch': request.inventory_epoch, 'shard_id': snapshot.token['shard_id'],
            'version': hint['version'], 'source_commit_position': hint['sourceCommitPosition'],
            'expires_at_ms': hint['expiresAtMs'], 'reason': hint['reason'], 'created_ms': now_ms,
        }
        decision.sold_hint = hint
        return decision
    session = 'sess-' + command
    position = snapshot.ticket['position_identity']
    return Decision(
        outcome='new_success', budget_class='inflow', store_command=True, nbytes=nbytes,
        first_result=first_result_canonical('new_success', {
            'commandId': command, 'sessionId': session,
            'shardId': snapshot.token['shard_id'], 'queueTicketId': ticket,
            'queuePositionIdentity': position,
        }),
        terminal={
            'token_id': snapshot.token['token_id'], 'seq': snapshot.token_state_seq + 1,
            'state': CONSUMED, 'reason': 'consumed', 'at_ms': now_ms,
            'ledger_entry_id': snapshot.token['ledger_entry_id'],
        },
        shard_decrement=(request.show_id, request.inventory_epoch, snapshot.token['shard_id']),
        session={
            'session_id': session, 'command_id': command, 'principal': request.principal,
            'show_id': request.show_id, 'epoch': request.inventory_epoch,
            'shard_id': snapshot.token['shard_id'], 'created_ms': now_ms,
        },
        evidence=_evidence(
            'ev-' + command, 'admit', show_id=request.show_id,
            epoch=request.inventory_epoch, ticket_id=ticket, position=position,
            sequence=snapshot.ticket_sequence + 1, old_shard=None,
            shard=snapshot.token['shard_id'], reason='consumed',
            issued_at_ms=snapshot.token['issued_at_ms'],
            expires_at_ms=snapshot.token['expires_at_ms'], outcome='new_success',
            command=command, now_ms=now_ms,
        ),
        ledger=('adm:' + command, 'inflow', nbytes, False),
        ledger_close=snapshot.token['ledger_entry_id'],
    )


@dataclass
class ReissueSnapshot:
    existing: Optional[dict] = None
    conflict_retained: bool = False
    config: Optional[dict] = None
    old_token: Optional[dict] = None
    old_state: Optional[str] = None
    old_state_seq: int = 0
    ticket: Optional[dict] = None
    ticket_sequence: int = 0
    new_shard: Optional[dict] = None
    new_token_exists: bool = False
    outstanding: int = 0
    usage: dict = field(default_factory=dict)


def decide_reissue(snapshot, request, limits, spec, key, key_version, now_ms):
    body = request.payload()
    digest = payload_sha256(body)
    command = command_id(request.show_id, request.inventory_epoch,
                         request.inventory_mode, request.principal,
                         request.client_command_id)
    path = _existing_path(snapshot, digest, body, spec, now_ms, command)
    if path is not None:
        return path
    nbytes = payload_nbytes(body)
    refused = _capacity(spec, snapshot.usage, 'recovery', nbytes, now_ms)
    if refused is not None:
        return refused
    if snapshot.outstanding >= limits.max_outstanding_tokens:
        return Decision(outcome='capacity', budget_class='recovery',
                        capacity_reason='outstanding_tokens')
    if snapshot.config is None or snapshot.config['mode'] != request.inventory_mode:
        return _refusal(command, 'CONFIG_UNKNOWN', nbytes, budget_class='recovery')
    if snapshot.ticket is None or snapshot.ticket['principal'] != request.principal:
        return _refusal(command, 'TICKET_UNKNOWN', nbytes,
                        {'queueTicketId': request.queue_ticket_id}, budget_class='recovery')
    extra = {'queueTicketId': request.queue_ticket_id}
    if snapshot.old_token is None:
        return _refusal(command, 'TOKEN_UNKNOWN', nbytes, extra, budget_class='recovery')
    if snapshot.old_state != ISSUED:
        return _refusal(command, 'REISSUE_NOT_ISSUED', nbytes, extra, budget_class='recovery')
    if snapshot.old_token['expires_at_ms'] <= now_ms:
        return _refusal(command, 'TOKEN_EXPIRED', nbytes, extra, budget_class='recovery')
    if snapshot.new_shard is None:
        return _refusal(command, 'SHARD_UNKNOWN', nbytes,
                        dict(extra, shardId=request.new_shard_id), budget_class='recovery')
    if request.new_nonce == request.old_nonce or snapshot.new_token_exists:
        return _refusal(command, 'NONCE_REUSE', nbytes, extra, budget_class='recovery')
    ticket = request.queue_ticket_id
    position = snapshot.ticket['position_identity']
    expires = now_ms + limits.token_ttl_ms
    document = tokens.sign({
        'showId': request.show_id, 'queueTicketId': ticket,
        'queuePositionIdentity': position, 'inventoryEpoch': request.inventory_epoch,
        'inventoryMode': request.inventory_mode,
        'authorityPlacementVersion': snapshot.config['placement_version'],
        'shardId': request.new_shard_id, 'nonce': request.new_nonce,
        'issuedAt': now_ms, 'expiresAt': expires, 'keyVersion': key_version,
    }, key, key_version)
    tid = tokens.token_id(ticket, request.new_nonce)
    ledger_entry = 'rei:' + command
    return Decision(
        outcome='new_success', budget_class='recovery', store_command=True, nbytes=nbytes,
        first_result=first_result_canonical('new_success', {
            'commandId': command, 'replacedTokenId': snapshot.old_token['token_id'],
            'queueTicketId': ticket, 'queuePositionIdentity': position,
            'token': document,
        }),
        terminal={
            'token_id': snapshot.old_token['token_id'], 'seq': snapshot.old_state_seq + 1,
            'state': REPLACED, 'reason': 'reissued', 'at_ms': now_ms,
            'ledger_entry_id': snapshot.old_token['ledger_entry_id'],
        },
        token=_token_row(document, tid, command, ledger_entry),
        issue_state={'token_id': tid, 'seq': 0, 'state': ISSUED,
                     'reason': 'reissued', 'at_ms': now_ms},
        evidence=_evidence(
            'ev-' + command, 'reissue', show_id=request.show_id,
            epoch=request.inventory_epoch, ticket_id=ticket, position=position,
            sequence=snapshot.ticket_sequence + 1,
            old_shard=snapshot.old_token['shard_id'], shard=request.new_shard_id,
            reason='reissued', issued_at_ms=now_ms, expires_at_ms=expires,
            outcome='new_success', command=command, now_ms=now_ms,
        ),
        ledger=(ledger_entry, 'recovery', nbytes, True),
        ledger_close=snapshot.old_token['ledger_entry_id'],
    )
