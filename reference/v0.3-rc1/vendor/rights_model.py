"""Executable SPECIFICATION MODEL. Not a blockchain or a ZK implementation.

The verifier receives plaintext witnesses to evaluate the proposed relation.
AES-GCM and Ed25519 are real library primitives. Keys/nonces are deterministically
derived from PUBLIC fixture seeds: NEVER use this module for real tickets.
Atomic execution, authentic final roots, honest issuers and durable controllers
are assumptions. No performance, formal security, or patentability claim.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
import hashlib
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature, InvalidTag


def enc(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(*items):
    return hashlib.sha256(enc(items)).hexdigest()


class Rejected(Exception):
    pass


def require(ok, reason):
    if not ok:
        raise Rejected(reason)


@dataclass(frozen=True)
class Note:
    domain: str
    event: str
    ticket: str
    version: int
    owner: str
    policy: str
    salt: str
    mode: str = 'ACTIVE'
    epoch: int = 0
    session: str = ''
    controller: str = ''
    expiry: int = 0

    @property
    def cm(self):
        return digest('note-v1', asdict(self))


class Wallet:
    def __init__(self, label):
        # This label is a PUBLIC FIXTURE SEED, not a production key derivation.
        self.seed = hashlib.sha256(('fixture-spend:' + label).encode()).digest()
        self.signer = Ed25519PrivateKey.from_private_bytes(self.seed)
        self.view_key = hashlib.sha256(('fixture-view:' + label).encode()).digest()
        self.owner = digest('owner', self.signer.public_key().public_bytes_raw().hex())
        self.cache = {}

    def nf(self, note, kind=None):
        require(note.owner == self.owner, 'WRONG_OWNER')
        parts = ['consume-right', note.domain, self.seed.hex(), note.ticket,
                 note.version, note.salt]
        # Including kind is a deliberately selectable BAD variant.
        if kind is not None:
            parts.append(kind)
        return digest(*parts)

    def capsule(self, note):
        require(note.owner == self.owner, 'WRONG_OUTPUT_OWNER')
        nonce = bytes.fromhex(digest('fixture-nonce', note.cm)[:24])
        ciphertext = AESGCM(self.view_key).encrypt(nonce, enc(asdict(note)), note.cm.encode())
        return nonce + ciphertext

    def open(self, cm, payload):
        try:
            body = AESGCM(self.view_key).decrypt(payload[:12], payload[12:], cm.encode())
            note = Note(**json.loads(body))
        except (InvalidTag, ValueError, TypeError, KeyError, UnicodeError):
            raise Rejected('UNREADABLE_CAPSULE')
        require(note.cm == cm and note.owner == self.owner, 'WRONG_CAPSULE')
        return note

    def acknowledge(self, command):
        require(command.output is not None, 'NO_OUTPUT')
        note = self.open(command.output.cm, command.payload)
        # A signature cannot prove disk persistence. Honest-wallet behavior only.
        self.cache[note.cm] = note
        return self.signer.sign(command.receipt_message())

    def present(self, note, request):
        require(note.owner == self.owner, 'WRONG_PRESENTATION_OWNER')
        msg = enc(['admission-presentation-v1', note.domain, note.cm, note.session,
                   note.epoch, note.controller, request])
        return (self.signer.public_key().public_bytes_raw(), self.signer.sign(msg))


def merkle_root(leaves):
    if not leaves:
        return digest('empty')
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [digest('branch', level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0]


def merkle_path(leaves, index):
    path = []
    level = list(leaves)
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        path.append((index % 2, level[index ^ 1]))
        level = [digest('branch', level[i], level[i + 1]) for i in range(0, len(level), 2)]
        index //= 2
    return path


def verify_path(cm, path, root):
    cur = cm
    for side, sibling in path:
        require(side in (0, 1), 'BAD_PATH')
        cur = digest('branch', sibling, cur) if side else digest('branch', cur, sibling)
    return cur == root


@dataclass(frozen=True)
class Guards:
    common_nf: bool = True
    check_spent: bool = True
    check_mode: bool = True
    require_ack: bool = True
    bind_ack_payload: bool = True
    bind_ack_finance: bool = True
    require_close: bool = True
    bind_close_epoch: bool = True
    use_close_result: bool = True


@dataclass(frozen=True)
class Closure:
    domain: str
    session: str
    epoch: int
    sequence: int
    head: str
    used: bool
    signature: bytes

    def message(self):
        return enc({k: v for k, v in asdict(self).items() if k != 'signature'})


@dataclass
class Command:
    kind: str
    request: str
    input: Note
    wallet: Wallet                    # PLAINTEXT witness, NOT a ZK proof.
    root: str
    path: list
    output: Note | None = None
    payload: bytes = b''
    recipient: Wallet | None = None
    ack: bytes = b''
    finance: str = ''
    closure: Closure | None = None
    guard: Guards = Guards()

    def receipt_message(self, verifier_guards=None):
        g = self.guard if verifier_guards is None else verifier_guards
        return enc({
            'domain': self.input.domain, 'request': self.request, 'kind': self.kind,
            'input_nf': self.wallet.nf(self.input),
            'output_cm': self.output.cm if self.output else '',
            'cipher_hash': digest(self.payload.hex()) if g.bind_ack_payload else '',
            'finance_commitment': self.finance if g.bind_ack_finance else '',
        })


class Controller:
    def __init__(self, name, event):
        self.name, self.event = name, event
        self.signer = Ed25519PrivateKey.from_private_bytes(
            hashlib.sha256(('fixture-controller:' + name).encode()).digest())
        self.sessions = {}
        self.available = True

    def install(self, note, finalized):
        require(finalized and note.mode == 'DELEGATED', 'UNCONFIRMED_GRANT')
        require(note.controller == self.name and note.event == self.event, 'WRONG_CONTROLLER')
        require(note.session not in self.sessions, 'DUPLICATE_INSTALL')
        self.sessions[note.session] = {
            'note': note, 'used': False, 'closed': False, 'seq': 0,
            'head': digest('start', note.domain, note.session, note.epoch),
            'last_time': 0, 'requests': {},
        }

    def admit(self, session, request, now, presentation):
        require(self.available, 'CONTROLLER_UNAVAILABLE')
        s = self.sessions[session]
        # Concrete signature baseline. A privacy-preserving presentation proof
        # replacing this signature/public-key exchange is NOT implemented here.
        pk, sig = presentation
        note = s['note']
        require(digest('owner', pk.hex()) == note.owner, 'WRONG_PRESENTATION_OWNER')
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        msg = enc(['admission-presentation-v1', note.domain, note.cm, note.session,
                   note.epoch, note.controller, request])
        try:
            Ed25519PublicKey.from_public_bytes(pk).verify(sig, msg)
        except (InvalidSignature, ValueError):
            raise Rejected('BAD_PRESENTATION')
        if request in s['requests']:
            return 'REPLAY'             # Do not open a physical gate again.
        require(not s['closed'] and not s['used'], 'LOCAL_RIGHT_CLOSED_OR_USED')
        require(now >= s['last_time'], 'CLOCK_ROLLBACK')
        require(now < s['note'].expiry, 'GRANT_EXPIRED')
        s['last_time'] = now
        s['seq'] += 1
        s['head'] = digest(s['head'], request, s['seq'], 'ADMIT')
        s['used'] = True
        s['requests'][request] = True
        # In-memory atomic journal stands in for durable storage, explicitly.
        return 'OPEN_ONCE'

    def close(self, session):
        require(self.available, 'CONTROLLER_UNAVAILABLE')
        s = self.sessions[session]
        if not s['closed']:
            s['seq'] += 1
            s['head'] = digest(s['head'], s['seq'], 'CLOSE')
            s['closed'] = True          # Must durably precede release of receipt.
        note = s['note']
        c = Closure(note.domain, session, note.epoch, s['seq'], s['head'], s['used'], b'')
        return replace(c, signature=self.signer.sign(c.message()))


class Ledger:
    def __init__(self, domain='kix:test:1', guards=Guards()):
        self.domain, self.guards = domain, guards
        self.leaves, self.roots, self.events = [], [], []
        self.spent, self.requests = set(), set()
        self.controllers = {}
        self.live = True

    def register(self, controller):
        self.controllers[controller.name] = controller

    def issue_fixture(self, note, payload):
        # AUTHORIZED ISSUANCE is assumed, not implemented or bypassable in a product.
        require(note.domain == self.domain and note.cm not in self.leaves, 'BAD_ISSUE')
        self.leaves.append(note.cm)
        self.roots.append(merkle_root(self.leaves))
        self.events.append({'kind': 'ISSUE', 'out_cm': note.cm,
                            'cipher_hash': digest(payload.hex()), 'ciphertext': payload.hex()})

    def prepare(self, kind, request, note, wallet, output=None, recipient=None,
                finance='', closure=None, anchor_size=None):
        leaves = self.leaves if anchor_size is None else self.leaves[:anchor_size]
        require(note.cm in leaves, 'NOTE_NOT_INCLUDED')
        payload = recipient.capsule(output) if output and recipient else b''
        c = Command(kind, request, note, wallet, merkle_root(leaves),
                    merkle_path(leaves, leaves.index(note.cm)), output, payload,
                    recipient, b'', finance, closure, self.guards)
        if output and recipient:
            c.ack = recipient.acknowledge(c)
        return c

    def execute(self, c):
        g = self.guards
        require(self.live, 'NO_FRESH_FINAL_STATE')
        require(c.input.domain == self.domain, 'WRONG_DOMAIN')
        require(c.request not in self.requests, 'REQUEST_REPLAY')
        require(c.root in self.roots and verify_path(c.input.cm, c.path, c.root), 'BAD_INCLUSION')
        nf = c.wallet.nf(c.input, None if g.common_nf else c.kind)
        if g.check_spent:
            require(nf not in self.spent, 'RIGHT_ALREADY_CONSUMED')
        require(c.kind in ('TRANSFER', 'ADMIT', 'REFUND', 'DELEGATE', 'CLOSE'), 'BAD_KIND')
        n, out = c.input, c.output
        if c.kind != 'CLOSE' and g.check_mode:
            require(n.mode == 'ACTIVE', 'ACTIVE_DELEGATION')
        if c.kind in ('TRANSFER', 'DELEGATE'):
            require(out is not None, 'MISSING_OUTPUT')
        if c.kind in ('ADMIT', 'REFUND'):
            require(out is None, 'TERMINAL_HAS_OUTPUT')
        if c.kind == 'TRANSFER':
            require(out.mode == 'ACTIVE' and out.epoch == n.epoch, 'BAD_TRANSFER_STATE')
        if c.kind == 'DELEGATE':
            require(out.mode == 'DELEGATED' and out.epoch == n.epoch + 1, 'BAD_DELEGATION')
            require(out.owner == n.owner and bool(out.session), 'BAD_DELEGATE_OWNER')
            ctl = self.controllers.get(out.controller)
            require(ctl is not None and ctl.event == out.event, 'UNAUTHORIZED_CONTROLLER')
            require(out.expiry > 0, 'BAD_EXPIRY')
            require(out.session == digest('grant-session-v1', n.domain, nf,
                                          out.epoch, out.controller), 'BAD_SESSION_BINDING')
        if c.kind == 'CLOSE':
            require(n.mode == 'DELEGATED', 'NOT_DELEGATED')
            if g.require_close:
                require(c.closure is not None, 'NO_FINAL_USE_RESULT')
            if c.closure:
                cl = c.closure
                require(cl.domain == n.domain and cl.session == n.session, 'WRONG_CLOSE_SCOPE')
                if g.bind_close_epoch:
                    require(cl.epoch == n.epoch, 'WRONG_CLOSE_EPOCH')
                ctl = self.controllers[n.controller]
                try:
                    ctl.signer.public_key().verify(cl.signature, cl.message())
                except InvalidSignature:
                    raise Rejected('BAD_CLOSE_SIGNATURE')
                require(cl.sequence > 0 and len(cl.head) == 64, 'BAD_CLOSE_LOG')
                used = cl.used if g.use_close_result else False
                require((out is None) if used else (out is not None), 'WRONG_CLOSE_RESULT')
            if out:
                require(out.mode == 'ACTIVE' and out.owner == n.owner and out.epoch == n.epoch,
                        'BAD_RESTORE')
        if out:
            require((out.domain, out.event, out.ticket, out.policy) ==
                    (n.domain, n.event, n.ticket, n.policy), 'RIGHT_ID_CHANGED')
            require(out.version == n.version + 1 and out.salt != n.salt, 'BAD_VERSION')
            require(out.cm not in self.leaves, 'DUPLICATE_OUTPUT')
            require(c.recipient is not None and c.recipient.owner == out.owner, 'WRONG_RECIPIENT')
            if g.require_ack:
                try:
                    c.recipient.signer.public_key().verify(c.ack, c.receipt_message(g))
                except (InvalidSignature, ValueError):
                    raise Rejected('BAD_RECOVERY_ACK')
        # Nothing mutates before ALL conditions pass. This is an ideal atomic step.
        self.spent.add(nf)
        self.requests.add(c.request)
        event = {'kind': c.kind, 'request': c.request, 'input_nf': nf,
                 'finance_commitment': c.finance}
        if out:
            self.leaves.append(out.cm)
            self.roots.append(merkle_root(self.leaves))
            event.update(out_cm=out.cm, cipher_hash=digest(c.payload.hex()),
                         ciphertext=c.payload.hex())
        self.events.append(event)
        return event


class Replica:
    def __init__(self, ledger, available=True, corrupt=False):
        self.records = {e['out_cm']: bytes.fromhex(e['ciphertext'])
                        for e in ledger.events if 'out_cm' in e}
        self.available, self.corrupt = available, corrupt

    def get(self, cm):
        if not self.available or cm not in self.records:
            return None
        b = self.records[cm]
        return b[:-1] + bytes([b[-1] ^ 1]) if self.corrupt else b


def recover(wallet, cm, expected_cipher_hash, replicas):
    # expected hash must come from an authenticated finalized ledger event.
    # Finding that event/Merkle path is part of the DA assumption, not this API.
    for r in replicas:
        b = r.get(cm)
        if b is not None and digest(b.hex()) == expected_cipher_hash:
            try:
                n = wallet.open(cm, b)
                wallet.cache[cm] = n
                return n
            except Rejected:
                continue
    raise Rejected('RECOVERY_DATA_UNAVAILABLE')


def new_note(old, owner, request, **changes):
    return replace(old, owner=owner.owner, version=old.version + 1,
                   salt=digest('fixture-salt', request), **changes)


def fixture(guards=Guards()):
    a, b = Wallet('Alice'), Wallet('Bob')
    l = Ledger(guards=guards)
    n = Note(l.domain, 'synthetic-event', 'T104', 7, a.owner,
             digest('policy-fixed-at-purchase'), digest('fixture-initial-salt'))
    l.issue_fixture(n, a.capsule(n))
    ctl = Controller('venue-controller', n.event)
    l.register(ctl)
    return l, a, b, n, ctl
