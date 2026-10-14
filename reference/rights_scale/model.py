"""In-memory reference model of the extended-profile public path (RS-1) and private path (RS-2).

Mirrors `sui/sources/rights_scale.move` operation by operation, including the order of
the checks, so a failing operation reports the same abort code the Move package does.
It is a model for differential tests and for reading, not an implementation of anything
and not a performance model. Every constant marked "localnet default" is Astra-owned and
is not a protocol value (docs/contracts/RIGHTS_SCALE_PROFILE.md section 13).

Scope: the public path (RS-1) and the private path (RS-2: claim_zk, shield,
consume_private, revoke_with_root). GrantControl and delegation (RS-3a) and GA
redistribution (RS-C02 sentence 2, DECISION_REQUIRED for Astra) are deliberately absent.

The private path is modelled WITHOUT hashes or proofs. A note root is the number of leaves
the tree had when the root was made (the tree is append-only, so that number identifies the
root); the revocation root is the number of revocations so far (every revoke adds a leaf, so
the set only grows). The Groth16 verifier is replaced by what the spend circuit proves: the
proof's domain, note root, revocation root, gate and expiry must equal the values the chain
feeds the verifier, and a revoked note has no proof at all. Root equality with the real
Poseidon trees is asserted by the localnet driver against circomlibjs, not here.
"""
import copy
import hashlib
import struct
from dataclasses import dataclass, field

# Error codes: same numbers as the Move package.
EClosed, ENotHolder, EStale, EAuthority, ELocked, EPolicy, EPayment = 1, 2, 3, 4, 5, 6, 7
EProof = 8
EInventory = 9
EBundleTooLarge, EBundleIncomplete, EBundleMismatch = 10, 11, 12
ESealed, ENotComplete, EPage, EShard, ERange = 13, 14, 15, 16, 17
EZk, ERoot, ETreeFull, ERootRequired, EVerifier = 18, 19, 20, 21, 22
# A proof Groth16 rejects aborts with code 2 inside kix_rights_scale::zk_gate.
EBadProof = 'zk_gate:2'
# sui::derived_object::EObjectAlreadyExists: a second claim of the same (parent, key).
EObjectAlreadyExists = 'EObjectAlreadyExists'

ACTIVE, CONSUMED, VOID, SHIELDED = 0, 1, 2, 3
DIRECT, PAID = 0, 1
SEATED, GA = 0, 1
REF_PRIMARY, REF_SECONDARY = 1, 2

# Localnet defaults; Astra-owned; not protocol values.
PROFILE_VERSION = 1
MAX_BUNDLE_CHAIN = 8
LOCALNET_SHOW_SLOTS = 1024
LOCALNET_PAGE_SLOTS = 64
LOCALNET_PAYMENT_SHARDS = 4
# RS-2 localnet fixture values; Astra-owned; none is a protocol value or an operational default.
ZK_DEPTH = 10
LOCALNET_ROOT_HISTORY_K = 4
LOCALNET_NULLIFIER_SHARDS = 4
LOCALNET_CHALLENGE_SHARDS = 4

MAX_OFFER_MS = 900000
MAX_ADMISSION_MS = 120000


class Abort(Exception):
    """A Move abort. `code` is the abort code (or EObjectAlreadyExists for a re-claim)."""

    def __init__(self, code):
        super().__init__(f'abort {code}')
        self.code = code


def check(condition, code):
    if not condition:
        raise Abort(code)


def route(show_id: bytes, payment_ref: bytes, profile_version: int, shard_count: int) -> int:
    """blake2b256(show id || reference || profile_version LE u64); first 8 bytes LE; mod shards."""
    digest = hashlib.blake2b(show_id + payment_ref + struct.pack('<Q', profile_version), digest_size=32).digest()
    return struct.unpack('<Q', digest[:8])[0] % shard_count


def ceil_div(n, d):
    return 0 if n == 0 else (n - 1) // d + 1


@dataclass
class Page:
    index: int
    start: int
    end: int
    mode: int
    generations: list
    occupied: list
    issuances: int = 0
    free: int = 0
    reserved: int = 0
    issued: int = 0
    retired: int = 0
    delegated_to: object = None  # always None in RS-1

    def conserved(self):
        return self.free + self.reserved + self.issued + self.retired == self.end - self.start


@dataclass
class Shard:
    index: int
    refs: dict = field(default_factory=dict)  # reference bytes -> kind


@dataclass
class Ticket:
    id: str
    slot: int
    generation: int
    holder: str
    version: int = 1
    state: int = ACTIVE
    offer: dict = None
    admission: dict = None
    last_payment: bytes = b''
    last_amount: int = 0
    last_payer: str = ''


@dataclass
class Payment:  # IssuancePayment
    slot: int
    expected_generation: int
    buyer: str
    amount: int
    payment_ref: bytes


@dataclass
class Evidence:  # PaymentEvidence
    ticket: str
    version: int
    buyer: str
    seller: str
    amount: int
    terms: tuple
    payment_ref: bytes


def atomic(method):
    """A PTB is all-or-nothing: an abort leaves no state behind."""

    def wrapper(self, *args, **kwargs):
        saved = copy.deepcopy(self.__dict__)
        try:
            return method(self, *args, **kwargs)
        except Abort:
            self.__dict__.clear()
            self.__dict__.update(saved)
            raise

    wrapper.__name__ = method.__name__
    wrapper.__doc__ = method.__doc__
    return wrapper


class Show:
    """ShowControl + its pages, shards and the tickets minted under it."""

    def __init__(self, issuer, seated_capacity, ga_capacity, page_size, shard_count, gates,
                 payment_attesters, resale_cap=150000, organizer_bps=200, platform_bps=300,
                 show_id: bytes = b'\x00' * 31 + b'\x01', verifier=None):
        check(page_size > 0 and shard_count > 0 and seated_capacity + ga_capacity > 0 and len(gates) > 0, EPolicy)
        check(organizer_bps <= 10000 and platform_bps <= 10000 and organizer_bps + platform_bps <= 10000, EPolicy)
        self.show_id = show_id
        self.issuer = issuer
        self.profile_version = PROFILE_VERSION
        self.open = False
        self.sealed = False
        self.cancel_generation = 0
        self.gates = list(gates)
        self.attesters = list(payment_attesters)
        self.resale_cap, self.organizer_bps, self.platform_bps = resale_cap, organizer_bps, platform_bps
        self.page_size, self.seated_capacity, self.ga_capacity = page_size, seated_capacity, ga_capacity
        self.seated_pages = ceil_div(seated_capacity, page_size)
        self.page_count = self.seated_pages + ceil_div(ga_capacity, page_size)
        self.shard_count = shard_count
        self.claimed_pages = self.claimed_shards = self.claim_sequence = 0
        self.pages = {}    # index -> Page
        self.shards = {}   # index -> Shard
        self.tickets = {}  # id -> Ticket
        self.payments = {}  # slot -> Payment (the IssuancePayment the issuer holds)
        self.evidence = {}  # ticket id -> Evidence (the PaymentEvidence the buyer holds)
        self.now_ms = 0
        self.events = []  # (kind, ...) in emission order
        self._ticket_seq = 0
        # RS-2. `verifier` is an opaque label for the Verifier object pinned at creation.
        self.verifier = verifier
        self.domain = None       # set by claim_zk: (show id, profile version, manifest label)
        self.leaves = []         # note commitments (labels) in insertion order
        self.revoked = {}        # slot -> highest revoked generation (revocation tree leaf)
        self.revocations = 0     # one per revoke_with_root: identifies the revocation root
        self.spent_nullifiers = set()
        self.spent_challenges = set()

    # ------------------------------------------------------------------ helpers
    @property
    def capacity(self):
        return self.seated_capacity + self.ga_capacity

    def range_of(self, index):
        if index < self.seated_pages:
            start = index * self.page_size
            return start, min(start + self.page_size, self.seated_capacity), SEATED
        start = self.seated_capacity + (index - self.seated_pages) * self.page_size
        return start, min(start + self.page_size, self.capacity), GA

    def page_index_of(self, slot):
        check(0 <= slot < self.capacity, EInventory)
        if slot < self.seated_capacity:
            return slot // self.page_size
        return self.seated_pages + (slot - self.seated_capacity) // self.page_size

    def authority(self, sender):
        check(sender == self.issuer, EAuthority)

    def _page(self, index):
        """The page object at a derived address; None when it was never claimed."""
        return self.pages.get(index)

    def offset(self, page_index_given, slot):
        """`page_index_given` stands for the page object the caller passed."""
        index = self.page_index_of(slot)
        check(page_index_given == index and index in self.pages, EPage)
        p = self.pages[index]
        check(p.start <= slot < p.end, EPage)
        return p, slot - p.start

    def routed(self, payment_ref):
        return route(self.show_id, payment_ref, self.profile_version, self.shard_count)

    def check_shard(self, shard_index_given, payment_ref):
        index = self.routed(payment_ref)
        check(shard_index_given == index and index in self.shards, EShard)
        return self.shards[index]

    def live(self, page_index, t, version):
        check(self.open and t.state == ACTIVE, EClosed)
        p, off = self.offset(page_index, t.slot)
        check(t.generation == p.generations[off] and t.version == version, EStale)
        return p, off

    def idle(self, t):
        check(t.offer is None or self.now_ms >= t.offer['expires_ms'], ELocked)
        check(t.admission is None or self.now_ms >= t.admission['expires_ms'], ELocked)

    def _mint(self, p, off, slot, holder, payment_ref, amount, payer, kind):
        p.generations[off] += 1
        p.issuances += 1
        self._ticket_seq += 1
        t = Ticket(f'T{self._ticket_seq}', slot, p.generations[off], holder, last_payment=payment_ref,
                   last_amount=amount, last_payer=payer)
        self.tickets[t.id] = t
        self.events.append(('Issuance', t.id, slot, t.generation, holder, kind, amount, payment_ref))
        self.events.append(('Change', t.id, t.version, t.state, holder, 0))
        return t

    # ------------------------------------------------------------------ creation staging
    @atomic
    def claim_pages(self, sender, start, count):
        self.authority(sender)
        check(not self.sealed and self.cancel_generation == 0, ESealed)
        check(count > 0 and start + count <= self.page_count, ERange)
        for index in range(start, start + count):
            lo, hi, mode = self.range_of(index)
            check(('page', index) not in self._claimed(), EObjectAlreadyExists)
            self._claim(('page', index))
            self.pages[index] = Page(index, lo, hi, mode, [0] * (hi - lo), [False] * (hi - lo), free=hi - lo)
            self.claimed_pages += 1
            self.claim_sequence += 1
            self.events.append(('PageClaimed', index, self.claim_sequence))

    @atomic
    def claim_shards(self, sender, start, count):
        self.authority(sender)
        check(not self.sealed and self.cancel_generation == 0, ESealed)
        check(count > 0 and start + count <= self.shard_count, ERange)
        for index in range(start, start + count):
            check(('shard', index) not in self._claimed(), EObjectAlreadyExists)
            self._claim(('shard', index))
            self.shards[index] = Shard(index)
            self.claimed_shards += 1
            self.claim_sequence += 1
            self.events.append(('ShardClaimed', index, self.claim_sequence))

    def _claimed(self):
        return self.__dict__.setdefault('_claims', set())

    def _claim(self, key):
        self._claimed().add(key)

    @atomic
    def seal(self, sender):
        self.authority(sender)
        check(not self.sealed and self.cancel_generation == 0, ESealed)
        check(self.claimed_pages == self.page_count and self.claimed_shards == self.shard_count, ENotComplete)
        self.sealed = self.open = True
        self.events.append(('ShowSealed',))

    @atomic
    def cancel_show(self, sender):
        self.authority(sender)
        check(self.open, EClosed)
        self.open = False
        self.cancel_generation = 1
        self.events.append(('ShowCancelled', 1))

    # ------------------------------------------------------------------ issuance
    def _issue(self, sender, page_index, slot, expected_generation, holder):
        self.authority(sender)
        check(self.open, EClosed)
        p, off = self.offset(page_index, slot)
        check(p.generations[off] == expected_generation, EStale)
        check(not p.occupied[off], EInventory)
        p.occupied[off] = True
        p.free -= 1
        p.issued += 1
        return self._mint(p, off, slot, holder, b'', 0, holder, DIRECT)

    @atomic
    def issue(self, sender, slot, expected_generation, holder, page_index=None):
        """`page_index` overrides the page the caller passes (cross-page predicates)."""
        return self._issue(sender, self.page_index_of(slot) if page_index is None else page_index, slot,
                           expected_generation, holder)

    @atomic
    def bundle(self, sender, first_slot, declared, issues, holder):
        """begin_bundle(declared), `issues` x bundle_issue(first_slot + i), finish_bundle."""
        check(declared > 0, EPolicy)
        check(declared <= MAX_BUNDLE_CHAIN, EBundleTooLarge)
        check(self.open, EClosed)
        remaining = declared
        tickets = []
        for i in range(issues):
            check(remaining > 0, EBundleMismatch)
            remaining -= 1
            slot = first_slot + i
            tickets.append(self._issue(sender, self.page_index_of(slot), slot, 0, holder))
        check(remaining == 0, EBundleIncomplete)
        return tickets

    @atomic
    def attest_issuance(self, sender, slot, expected_generation, buyer, amount, payment_ref,
                        page_index=None, shard_index=None):
        check(sender in self.attesters, EAuthority)
        check(self.open, EClosed)
        p, off = self.offset(self.page_index_of(slot) if page_index is None else page_index, slot)
        check(p.generations[off] == expected_generation, EStale)
        check(not p.occupied[off], EInventory)
        check(amount > 0 and len(payment_ref) == 32, EPayment)
        shard = self.check_shard(self.routed(payment_ref) if shard_index is None else shard_index, payment_ref)
        check(payment_ref not in shard.refs, EPayment)
        p.occupied[off] = True
        p.free -= 1
        p.reserved += 1
        shard.refs[payment_ref] = REF_PRIMARY
        self.payments[slot] = Payment(slot, expected_generation, buyer, amount, payment_ref)

    @atomic
    def cancel_issuance(self, sender, slot):
        self.authority(sender)
        pay = self.payments[slot]
        p, off = self.offset(self.page_index_of(slot), slot)
        check(p.occupied[off] and p.reserved > 0, EInventory)
        shard = self.check_shard(self.routed(pay.payment_ref), pay.payment_ref)
        check(pay.payment_ref in shard.refs, EPayment)
        del shard.refs[pay.payment_ref]
        del self.payments[slot]
        p.occupied[off] = False
        p.reserved -= 1
        p.free += 1

    @atomic
    def issue_paid(self, sender, slot):
        self.authority(sender)
        pay = self.payments[slot]
        check(self.open, EClosed)
        p, off = self.offset(self.page_index_of(slot), slot)
        check(p.occupied[off] and p.reserved > 0, EInventory)
        check(p.generations[off] == pay.expected_generation, EStale)
        shard = self.check_shard(self.routed(pay.payment_ref), pay.payment_ref)
        check(pay.amount > 0 and len(pay.payment_ref) == 32 and pay.payment_ref in shard.refs, EPayment)
        del self.payments[slot]
        p.reserved -= 1
        p.issued += 1
        return self._mint(p, off, slot, pay.buyer, pay.payment_ref, pay.amount, pay.buyer, PAID)

    # ------------------------------------------------------------------ holder operations
    def _page_of(self, t, page_index):
        return self.page_index_of(t.slot) if page_index is None else page_index

    @atomic
    def offer(self, sender, ticket, version, recipient, amount, expires_ms, page_index=None):
        t = self.tickets[ticket]
        self.live(self._page_of(t, page_index), t, version)
        check(t.holder == sender, ENotHolder)
        self.idle(t)
        check(recipient != t.holder and amount <= self.resale_cap and expires_ms > self.now_ms
              and expires_ms - self.now_ms <= MAX_OFFER_MS, EPolicy)
        terms = (t.id, version, t.holder, recipient, amount, expires_ms, self.organizer_bps, self.platform_bps)
        t.offer = dict(recipient=recipient, amount=amount, expires_ms=expires_ms, version=version, terms=terms)
        t.admission = None

    def _accepted(self, sender, t, page_index):
        self.live(self._page_of(t, page_index), t, t.version)
        check(t.offer is not None, ELocked)
        o = t.offer
        check(o['recipient'] == sender and o['version'] == t.version and self.now_ms < o['expires_ms'], EStale)
        return o

    def _transfer(self, t, recipient):
        t.holder = recipient
        t.version += 1
        t.offer = t.admission = None
        self.events.append(('Change', t.id, t.version, t.state, recipient, 1))

    @atomic
    def accept_gift(self, sender, ticket, page_index=None):
        t = self.tickets[ticket]
        o = self._accepted(sender, t, page_index)
        check(o['amount'] == 0, EPayment)
        self._transfer(t, o['recipient'])

    @atomic
    def attest_payment(self, sender, ticket, payment_ref, page_index=None, shard_index=None):
        t = self.tickets[ticket]
        check(sender in self.attesters, EAuthority)
        self.live(self._page_of(t, page_index), t, t.version)
        check(t.offer is not None, EPayment)
        o = t.offer
        check(o['amount'] > 0 and self.now_ms < o['expires_ms'] and len(payment_ref) == 32, EPayment)
        shard = self.check_shard(self.routed(payment_ref) if shard_index is None else shard_index, payment_ref)
        check(payment_ref not in shard.refs, EPayment)
        shard.refs[payment_ref] = REF_SECONDARY
        self.evidence[ticket] = Evidence(ticket, t.version, o['recipient'], t.holder, o['amount'], o['terms'],
                                         payment_ref)

    @atomic
    def accept_sale(self, sender, ticket, page_index=None):
        t = self.tickets[ticket]
        o = self._accepted(sender, t, page_index)
        ev = self.evidence[ticket]
        check(ev.ticket == t.id and ev.version == t.version and ev.buyer == o['recipient']
              and ev.seller == t.holder and ev.amount == o['amount'] and ev.amount > 0 and ev.terms == o['terms'],
              EPayment)
        del self.evidence[ticket]
        organizer_due = ev.amount * self.organizer_bps // 10000
        platform_due = ev.amount * self.platform_bps // 10000
        self.events.append(('Allocation', t.id, ev.payment_ref, ev.amount, ev.amount - organizer_due - platform_due,
                            organizer_due, platform_due))
        t.last_payment, t.last_amount, t.last_payer = ev.payment_ref, ev.amount, ev.buyer
        self._transfer(t, ev.buyer)

    @atomic
    def authorize_admission(self, sender, ticket, version, gate, request, expires_ms, page_index=None):
        t = self.tickets[ticket]
        self.live(self._page_of(t, page_index), t, version)
        check(sender == t.holder, ENotHolder)
        self.idle(t)
        check(gate in self.gates and len(request) == 32 and expires_ms > self.now_ms
              and expires_ms - self.now_ms <= MAX_ADMISSION_MS, EPolicy)
        t.offer = None
        t.admission = dict(gate=gate, expires_ms=expires_ms, version=version, request=request)

    @atomic
    def consume(self, sender, ticket, version, request, page_index=None):
        t = self.tickets[ticket]
        self.live(self._page_of(t, page_index), t, version)
        check(sender in self.gates and t.admission is not None, EAuthority)
        a = t.admission
        check(a['gate'] == sender and a['version'] == version and a['request'] == request
              and self.now_ms < a['expires_ms'], EStale)
        t.state = CONSUMED
        t.version += 1
        t.admission = t.offer = None
        self.events.append(('Change', t.id, t.version, t.state, t.holder, 2))

    @atomic
    def refund(self, sender, ticket, version, page_index=None):
        t = self.tickets[ticket]
        p, off = self.live(self._page_of(t, page_index), t, version)
        check(sender == t.holder, ENotHolder)
        self.idle(t)
        t.state = VOID
        t.version += 1
        t.offer = t.admission = None
        p.occupied[off] = False
        p.issued -= 1
        p.free += 1
        self.events.append(('RefundDutyRequested', t.id, t.last_payer, t.last_amount, t.last_payment))
        self.events.append(('Change', t.id, t.version, t.state, t.holder, 3))

    @atomic
    def revoke(self, sender, ticket, page_index=None):
        """The plain public-path revoke. A show with a revocation root must use revoke_with_root."""
        check(self.domain is None, ERootRequired)
        self._revoke_ticket(sender, ticket, page_index)

    def _revoke_ticket(self, sender, ticket, page_index=None):
        self.authority(sender)
        t = self.tickets[ticket]
        p, off = self.offset(self._page_of(t, page_index), t.slot)
        check(t.generation == p.generations[off] and p.occupied[off] and t.state != VOID, EStale)
        p.generations[off] += 1
        p.issued -= 1
        p.retired += 1
        t.state = VOID
        t.version += 1
        t.offer = t.admission = None
        self.events.append(('Change', t.id, t.version, t.state, t.holder, 4))
        return t

    # ------------------------------------------------------------------ private path (RS-2)
    @atomic
    def claim_zk(self, sender, verifier, manifest):
        """`verifier` is the Verifier object passed, `manifest` its circuit manifest label."""
        self.authority(sender)
        check(not self.sealed and self.cancel_generation == 0, ESealed)
        check(self.domain is None, EZk)
        check(verifier == self.verifier, EVerifier)
        check(self.capacity <= 2 ** ZK_DEPTH, ERange)
        self.domain = (self.show_id, self.profile_version, manifest)
        # One claim sequence number each: tree, revocation state, nullifier and challenge shards.
        self.claim_sequence += 2 + LOCALNET_NULLIFIER_SHARDS + LOCALNET_CHALLENGE_SHARDS
        self.events.append(('ZkClaimed', self.domain))

    def history(self):
        """Note-root counts the chain accepts: the roots of the last K states, current included."""
        n = len(self.leaves)
        return range(max(0, n - LOCALNET_ROOT_HISTORY_K + 1), n + 1)

    @atomic
    def shield(self, sender, ticket, version, commitment, verifier=None, proof_domain=None,
               proof_commitment=None, page_index=None):
        t = self.tickets[ticket]
        self.live(self._page_of(t, page_index), t, version)
        check(sender == t.holder, ENotHolder)
        self.idle(t)
        check((verifier or self.verifier) == self.verifier, EProof)
        check(self.domain is not None, EZk)
        check(len(self.leaves) < 2 ** ZK_DEPTH, ETreeFull)
        # The mint proof binds (commitment, slot, generation, domain).
        check((proof_domain or self.domain) == self.domain and (proof_commitment or commitment) == commitment,
              EBadProof)
        self.leaves.append(commitment)
        t.state = SHIELDED
        t.version += 1
        t.offer = t.admission = None
        self.events.append(('NoteAdded', len(self.leaves) - 1, commitment))
        self.events.append(('Change', t.id, t.version, t.state, t.holder, 5))

    @atomic
    def consume_private(self, sender, proof, note_root=None, ttl_ms=None, verifier=None, wrong_shard=None):
        """`proof` is what the prover made (see replay.Prover); the other arguments are the call's.

        note_root: the note-root count passed (default: the proof's); ttl_ms: the expiry passed
        relative to now (default: the proof's); wrong_shard: 'nullifier' or 'challenge'.
        """
        check(self.open and sender in self.gates and (verifier or self.verifier) == self.verifier, EAuthority)
        check(self.domain is not None, EZk)
        check(wrong_shard is None, EShard)
        nullifier, challenge = proof['nullifier'], proof['challenge']
        check(nullifier not in self.spent_nullifiers and challenge not in self.spent_challenges, EProof)
        ttl = proof['ttl_ms'] if ttl_ms is None else ttl_ms
        check(0 < ttl <= MAX_ADMISSION_MS, EPolicy)
        count = proof['note_count'] if note_root is None else note_root
        check(count in self.history(), ERoot)
        # What Groth16 checks: the public inputs the chain feeds the verifier equal the proof's.
        check(proof['domain'] == self.domain and proof['show'] == self.show_id and proof['note_count'] == count
              and proof['revocations'] == self.revocations and proof['gate'] == sender
              and proof['ttl_ms'] == ttl, EBadProof)
        self.spent_nullifiers.add(nullifier)
        self.spent_challenges.add(challenge)
        self.events.append(('PrivateAdmission', nullifier, sender, challenge, count))

    @atomic
    def revoke_with_root(self, sender, ticket, stale_witness=False, page_index=None):
        """The issuer supplies the sibling path of the CURRENT tree; `stale_witness` supplies the
        empty tree's path, which only matches while nothing has been revoked."""
        check(self.domain is not None, EZk)
        t = self.tickets[ticket]
        check(t.generation > self.revoked.get(t.slot, 0), ERoot)
        check(not stale_witness or self.revocations == 0, ERoot)
        generation = t.generation
        self._revoke_ticket(sender, ticket, page_index)
        self.revoked[t.slot] = generation
        self.revocations += 1
        self.events.append(('RevocationLeaf', t.slot, generation))

    # ------------------------------------------------------------------ read-only views
    def totals(self):
        """(free, reserved, issued, retired) summed over the claimed pages."""
        return tuple(sum(getattr(p, name) for p in self.pages.values())
                     for name in ('free', 'reserved', 'issued', 'retired'))

    def check_invariants(self):
        """Raises AssertionError when a structural invariant of the profile is violated."""
        covered = 0
        for p in self.pages.values():
            assert p.conserved(), f'page {p.index} does not conserve its range'
            assert sum(p.occupied) == p.reserved + p.issued + p.retired, f'page {p.index} occupancy'
            assert p.delegated_to is None
            covered += p.end - p.start
        if self.sealed:
            assert covered == self.capacity and len(self.pages) == self.page_count
        live = {}
        for t in self.tickets.values():
            if t.state in (ACTIVE, CONSUMED, SHIELDED):
                assert t.slot not in live, f'two live rights on slot {t.slot}'
                live[t.slot] = t
                p = self.pages[self.page_index_of(t.slot)]
                assert p.occupied[t.slot - p.start] and p.generations[t.slot - p.start] == t.generation
        for p in self.pages.values():
            assert p.issued == sum(1 for t in live.values() if p.start <= t.slot < p.end)
        for shard in self.shards.values():
            for ref in shard.refs:
                assert self.routed(ref) == shard.index, 'reference in the wrong shard'
        # RS-2: the private path keeps the right count and the append-only tree consistent.
        shielded = sum(1 for t in self.tickets.values() if t.state == SHIELDED)
        assert shielded <= len(self.leaves) <= 2 ** ZK_DEPTH, 'a SHIELDED ticket without a note'
        assert len(set(self.leaves)) == len(self.leaves), 'a note was added twice'
        if self.domain is None:
            assert not self.leaves and not self.revoked and not self.spent_nullifiers
        assert all(n[0] == 'nf' and n[1] in self.leaves for n in self.spent_nullifiers), 'nullifier without a note'
        assert self.revocations >= len(self.revoked)

    def private_snapshot(self):
        """The private-path state a driver can read from chain objects and events without hashes."""
        return {
            'zk_enabled': self.domain is not None,
            'leaf_count': len(self.leaves),
            'history_len': min(LOCALNET_ROOT_HISTORY_K, len(self.leaves) + 1),
            'revocations': self.revocations,
            'revoked': {str(slot): gen for slot, gen in sorted(self.revoked.items())},
            'nullifiers': len(self.spent_nullifiers),
            'challenges': len(self.spent_challenges),
        }

    def snapshot(self):
        """Plain-data state, comparable with what the localnet driver reads from the chain."""
        return {
            'control': {'open': self.open, 'sealed': self.sealed, 'cancel_generation': self.cancel_generation,
                        'claimed_pages': self.claimed_pages, 'claimed_shards': self.claimed_shards,
                        'claim_sequence': self.claim_sequence},
            'pages': [dict(index=p.index, start=p.start, end=p.end, mode=p.mode, generations=list(p.generations),
                           occupied=list(p.occupied), issuances=p.issuances, free=p.free, reserved=p.reserved,
                           issued=p.issued, retired=p.retired) for _, p in sorted(self.pages.items())],
            'shards': [dict(index=s.index, refs=sorted(r.hex() for r in s.refs)) for _, s in sorted(self.shards.items())],
            'tickets': {t.id: dict(slot=t.slot, generation=t.generation, holder=t.holder, version=t.version,
                                   state=t.state, last_amount=t.last_amount) for t in self.tickets.values()},
        }
