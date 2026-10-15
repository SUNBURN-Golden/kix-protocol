"""RS-4 staged-load workload generator (kix-rs4-l1-load-v1 / kix-rs4-l2-load-v1).

Emits the deterministic step list the `client/load-l1.mjs` driver executes on a
disposable one-validator localnet, plus the expected end-state the summarizer
checks. Three paths are generated separately and must be reported separately
(docs/blueprints/rights-scale-v1/README.md section 7 and the RS-4 node scope):

  public     RS-1 path: creation staging, uniform fill of all stage slots,
             paid-issuance subset, holder/issuer operations, concurrency probes,
             cancel of the full show.
  private    RS-2 path: `private_seated` issued tickets, `shield_count` real
             Groth16 shields (default 1,024 = the depth-10 leaf-capacity
             boundary), private consumptions, root-history eviction, one
             revocation and the proofs it invalidates, concurrent revocation,
             event-source witness reconstruction.
  delegated  RS-3a path: two grants on the last two pages, delegated issuance
             (bundle, single, paid), grant-shared concurrency probe, EDelegated
             rejects, the one-write revocation cut and its post-cut refusals,
             page reclaim, and a stranded pre-cut reservation left
             un-reclaimable.

`--stage l1` (default) is the 1,024-slot L1 workload; its expansion is pinned
byte-identical to the rs-4-l1 record. `--stage l2` is the 16,384-slot L2
workload: public and delegated run full 16,384-seat shows (256 pages of 64),
while the private path is contract-capped at `2^ZK_DEPTH` = 1,024 slots —
`claim_zk` asserts `seated + ga <= 2^ZK_DEPTH` (rights_scale.move). The L2
private leg therefore runs the same 1,024-slot workload as a regression plus a
`probe.zk_capacity` boundary prefix: `claim_zk` on auxiliary 1,025- and
16,384-seat shows must abort ERange. The private path at 16,384 seats is not
measured: it needs a deeper circuit, a new fixture ceremony and a profile
change, all outside this node. The public leg also probes the page boundary:
`claim_pages` one past `page_count` aborts ERange and a re-claim of an already
claimed page aborts inside `derived_object::claim` (RS-C15).

This is a measurement workload, not a performance model and not a product
statement. The fixture values (stage seats, page 64, payment shards 4, depth
10, K=4) come from model.py and are Astra-owned/test-only (profile section
13). Everything is closed-loop (arrival_rate 0): sequential steps with fixed-k
concurrency probes on top, never a rate claim.

  --expand OUT.json [--stage {l1,l2}] [--seed N] [--shield-count N]
                          write the expanded workload document.
"""
import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import model  # noqa: E402

VERSION = 'kix-rs4-l1-load-v1'
VERSIONS = {'l1': 'kix-rs4-l1-load-v1', 'l2': 'kix-rs4-l2-load-v1'}
STAGES = {'l1': model.LOCALNET_SHOW_SLOTS, 'l2': 16384}
DEFAULT_SEED = 20261014
SEATS = model.LOCALNET_SHOW_SLOTS        # 1024; L1 stage size (fixture, not policy)
PAGE_SIZE = model.LOCALNET_PAGE_SLOTS    # 64
MAX_BUNDLE = model.MAX_BUNDLE_CHAIN      # 8
MAX_CLAIM = 8      # driver-side batching bound: a 16-page claim exceeded the local gas budget (RS-1 replay)
PUBLIC_SHARDS = model.LOCALNET_PAYMENT_SHARDS   # 4
PRIVATE_SHARDS = 1
DELEGATED_SHARDS = model.LOCALNET_PAYMENT_SHARDS
PAID_PER_PAGE = 8
PROBE_PAGE = 8
PROBE_BASE = PROBE_PAGE * PAGE_SIZE      # slots 512..521 form the probe region
ZK_LEAF_CAP = 1 << model.ZK_DEPTH        # private-path contract cap on seated+ga

# Abort codes from sui/sources/rights_scale.move, used in `expect` only.
E_CLOSED = 1
E_STALE = 3
E_INVENTORY = 9
E_RANGE = 17
E_ROOT = 19
E_DELEGATED = 23
E_GRANT_CLOSED = 24
ZK_GATE_REJECT = 'zk_gate:2'


class Slots:
    """Generator-side occupancy model used only to emit correct steps and the
    expected end-state. One slot is 'free', 'reserved', 'issued' or 'retired';
    `gen` tracks the chain-side page generation: it bumps on every successful
    mint (issue/issue_paid/bundle_issue) and on every revoke; refund and
    cancel_issuance leave it unchanged, so a reissued slot carries gen >= 1."""

    def __init__(self, count):
        self.state = ['free'] * count
        self.gen = [0] * count
        self.holder = [None] * count

    def issue(self, slot, holder):
        assert self.state[slot] == 'free', ('issue on non-free slot', slot, self.state[slot])
        self.state[slot] = 'issued'
        self.holder[slot] = holder
        self.gen[slot] += 1

    def reserve(self, slot):
        assert self.state[slot] == 'free', ('reserve on non-free slot', slot, self.state[slot])
        self.state[slot] = 'reserved'

    def complete(self, slot, holder):
        assert self.state[slot] == 'reserved', ('complete on non-reserved slot', slot)
        self.state[slot] = 'issued'
        self.holder[slot] = holder
        self.gen[slot] += 1

    def refund(self, slot):
        assert self.state[slot] == 'issued'
        self.state[slot] = 'free'

    def release(self, slot):
        assert self.state[slot] == 'reserved'
        self.state[slot] = 'free'

    def revoke(self, slot):
        assert self.state[slot] in ('issued', 'reserved')
        self.state[slot] = 'retired'
        self.gen[slot] += 1

    def force_issued(self, slot):
        # Post-probe marker: the probe design guarantees the slot ends occupied
        # by exactly one submission regardless of which branch won.
        assert self.state[slot] in ('free', 'issued')
        self.state[slot] = 'issued'
        self.gen[slot] = max(1, self.gen[slot])

    def page_totals(self):
        totals = {}
        for index in range(len(self.state) // PAGE_SIZE + (1 if len(self.state) % PAGE_SIZE else 0)):
            part = self.state[index * PAGE_SIZE:(index + 1) * PAGE_SIZE]
            totals[index] = {'free': part.count('free'), 'reserved': part.count('reserved'),
                             'issued': part.count('issued'), 'retired': part.count('retired')}
        return totals


def _chunks(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def _claim_steps(pages, shards, zk=False, boundary_probe=False):
    steps = []
    for run in _chunks(list(range(pages)), MAX_CLAIM):
        steps.append({'op': 'claim_pages', 'from': run[0], 'count': len(run)})
    if boundary_probe:
        # Page boundary probes (still inside stage.create, before seal): one
        # index past page_count aborts ERange; re-claiming a claimed page
        # aborts inside derived_object::claim (RS-C15) — `any`, the exact
        # abort is runtime characterization data.
        steps.append({'op': 'claim_pages', 'from': pages, 'count': 1,
                      'expect': {'abort': E_RANGE},
                      'comment': 'page_index_past_page_count'})
        steps.append({'op': 'claim_pages', 'from': 0, 'count': 1,
                      'expect': 'any',
                      'comment': 'reclaim_already_claimed_page'})
    if zk:
        steps.append({'op': 'claim_zk', 'verifier': 'v1'})
    steps.append({'op': 'claim_shards', 'from': 0, 'count': shards})
    steps.append({'op': 'seal'})
    return steps


def _paid_steps(slots, slot_state, buyer, amount, ref_counter, delegate_grant=None):
    """attest + issue_paid pairs. Delegated variant when delegate_grant is set."""
    steps = []
    att = 'attest_issuance' if delegate_grant is None else 'attest_issuance_delegated'
    paid = 'issue_paid' if delegate_grant is None else 'issue_paid_delegated'
    for slot in slots:
        step = {'op': att, 'slot': slot, 'gen': slot_state.gen[slot], 'buyer': buyer,
                'amount': amount, 'ref': ref_counter[0]}
        if delegate_grant is not None:
            step['grant'] = delegate_grant
        steps.append(step)
        slot_state.reserve(slot)
        step = {'op': paid, 'slot': slot}
        if delegate_grant is not None:
            step['grant'] = delegate_grant
        steps.append(step)
        slot_state.complete(slot, buyer)
        ref_counter[0] += 1
    return steps


def public_path(settings, rng):
    """Public path on one show (no ZK, domain 0); stage-sized seat count."""
    seats = settings['show']['seated']
    slot_state = Slots(seats)
    paid_offsets = set(range(PAGE_SIZE - PAID_PER_PAGE, PAGE_SIZE))
    probe_slots = list(range(PROBE_BASE, PROBE_BASE + 10))  # 512..521
    ref_counter = [1]
    steps = [{'op': 'create_show', 'seated': seats, 'ga': 0, 'page_size': PAGE_SIZE,
              'shards': PUBLIC_SHARDS, 'verifier': None}]
    steps += _claim_steps(seats // PAGE_SIZE, PUBLIC_SHARDS,
                          boundary_probe=seats > SEATS)

    # ---- concurrency probes on the still-free probe region -----------------
    p = probe_slots
    probes = [
        # IssuerCap shared-read serialization re-observed: two issuer-signed
        # issues on different slots of the same page.
        {'op': 'parallel', 'name': 'same_page_issues',
         'of': [{'op': 'issue', 'slot': p[0], 'gen': 0, 'holder': 'a'},
                {'op': 'issue', 'slot': p[1], 'gen': 0, 'holder': 'b'}], 'expect': 'any'},
        # Same slot twice: exactly one lands, the loser aborts EStale.
        {'op': 'parallel', 'name': 'duplicate_slot_race',
         'of': [{'op': 'issue', 'slot': p[2], 'gen': 0, 'holder': 'a'},
                {'op': 'issue', 'slot': p[2], 'gen': 0, 'holder': 'a'}], 'expect': 'one_wins'},
        # Two attestations on different slots routed to the SAME shard.
        {'op': 'parallel', 'name': 'same_shard_attests',
         'of': [{'op': 'attest_issuance', 'slot': p[3], 'gen': 0, 'buyer': 'a',
                 'amount': 1000, 'ref_shard': 0},
                {'op': 'attest_issuance', 'slot': p[4], 'gen': 0, 'buyer': 'b',
                 'amount': 1000, 'ref_shard': 0}], 'expect': 'any'},
        # Two attestations routed to DIFFERENT shards.
        {'op': 'parallel', 'name': 'cross_shard_attests',
         'of': [{'op': 'attest_issuance', 'slot': p[5], 'gen': 0, 'buyer': 'a',
                 'amount': 1000, 'ref_shard': 1},
                {'op': 'attest_issuance', 'slot': p[6], 'gen': 0, 'buyer': 'b',
                 'amount': 1000, 'ref_shard': 2}], 'expect': 'any'},
        # Overlapping bundles: one wins atomically, the loser's unique slot stays free.
        {'op': 'parallel', 'name': 'bundle_race',
         'of': [{'op': 'bundle', 'slots': [p[7], p[8]], 'holder': 'a'},
                {'op': 'bundle', 'slots': [p[8], p[9]], 'holder': 'a'}], 'expect': 'one_wins'},
    ]
    steps += probes
    # Probe-completion steps bring the region to a deterministic end state:
    # every probe slot ends issued no matter which branch won.
    for slot in p[3:7]:
        steps.append({'op': 'issue_paid', 'slot': slot, 'expect': 'any'})
        steps.append({'op': 'issue', 'slot': slot, 'gen': 0, 'holder': 'a', 'expect': 'any'})
    for slot in (p[0], p[1], p[2], p[7], p[8], p[9]):
        steps.append({'op': 'issue', 'slot': slot, 'gen': 0, 'holder': 'a', 'expect': 'any'})
    for slot in probe_slots:
        slot_state.force_issued(slot)

    # ---- uniform fill of the remaining slots -------------------------------
    for page in range(seats // PAGE_SIZE):
        base = page * PAGE_SIZE
        free_runs, run = [], []
        for off in range(PAGE_SIZE):
            slot = base + off
            if off in paid_offsets or slot in probe_slots or slot_state.state[slot] != 'free':
                if run:
                    free_runs.append(run)
                run = []
            else:
                run.append(slot)
        if run:
            free_runs.append(run)
        for slots in sum((_chunks(r, MAX_BUNDLE) for r in free_runs), []):
            holder = 'a' if slots[0] % 2 == 0 else 'b'
            steps.append({'op': 'bundle' if len(slots) > 1 else 'issue', 'slots': slots,
                          'slot': slots[0], 'gen': 0, 'holder': holder})
            for slot in slots:
                slot_state.issue(slot, holder)
        paid_slots = [base + off for off in sorted(paid_offsets)]
        steps += _paid_steps(paid_slots, slot_state, 'a', 150000, ref_counter)

    # ---- hot-slot rejections -----------------------------------------------
    issued = [s for s in range(seats) if slot_state.state[s] == 'issued']
    for slot in rng.sample(issued, 4):
        steps.append({'op': 'issue', 'slot': slot, 'gen': 0, 'holder': 'a',
                      'expect': {'abort': E_STALE}})
    for slot in rng.sample(issued, 2):
        steps.append({'op': 'issue', 'slot': slot, 'gen': 1, 'holder': 'a',
                      'expect': {'abort': E_INVENTORY}})
    for slot in rng.sample(issued, 2):
        steps.append({'op': 'attest_issuance', 'slot': slot, 'gen': 0, 'buyer': 'a',
                      'amount': 1000, 'ref': ref_counter[0], 'expect': {'abort': E_STALE}})
        ref_counter[0] += 1

    # ---- holder/issuer operation subsets on disjoint seeded slots ----------
    pool = rng.sample(issued, settings['transfers'] + settings['admissions']
                      + settings['reservations'] + settings['refunds']
                      + settings['reissues'] + settings['revokes'])
    it = iter(pool)
    for _ in range(settings['reservations']):
        slot = next(it)
        ref = ref_counter[0]
        ref_counter[0] += 1
        steps.append({'op': 'refund', 'slot': slot, 'version': 1})
        slot_state.refund(slot)
        steps.append({'op': 'attest_issuance', 'slot': slot, 'gen': slot_state.gen[slot],
                      'buyer': 'b', 'amount': 7000, 'ref': ref})
        slot_state.reserve(slot)
        steps.append({'op': 'cancel_issuance', 'slot': slot})
        slot_state.release(slot)
        # The same payment ref was removed from its shard and may be reused.
        steps.append({'op': 'attest_issuance', 'slot': slot, 'gen': slot_state.gen[slot],
                      'buyer': 'b', 'amount': 7000, 'ref': ref, 'comment': 'ref_reuse'})
        slot_state.reserve(slot)
        steps.append({'op': 'issue_paid', 'slot': slot})
        slot_state.complete(slot, 'b')
    for _ in range(settings['reissues']):
        slot = next(it)
        steps.append({'op': 'refund', 'slot': slot, 'version': 1})
        slot_state.refund(slot)
        steps.append({'op': 'issue', 'slot': slot, 'gen': slot_state.gen[slot], 'holder': 'b',
                      'comment': 'reissue_after_refund'})
        slot_state.issue(slot, 'b')
    for _ in range(settings['transfers']):
        slot = next(it)
        other = 'b' if slot_state.holder[slot] == 'a' else 'a'
        steps.append({'op': 'offer', 'slot': slot, 'version': 1, 'to': other, 'amount': 0,
                      'ttl_ms': 600000})
        steps.append({'op': 'accept_gift', 'slot': slot})
        slot_state.holder[slot] = other
    for _ in range(settings['admissions']):
        slot = next(it)
        steps.append({'op': 'authorize', 'slot': slot, 'version': 1, 'gate': 'gate',
                      'ttl_ms': 90000})
        steps.append({'op': 'consume', 'slot': slot, 'version': 1})
    for _ in range(settings['refunds']):
        slot = next(it)
        steps.append({'op': 'refund', 'slot': slot, 'version': 1})
        slot_state.refund(slot)
    for _ in range(settings['revokes']):
        slot = next(it)
        steps.append({'op': 'revoke', 'slot': slot})
        slot_state.revoke(slot)

    # ---- cancel of the full show and post-cancel refusals ------------------
    steps.append({'op': 'cancel_show'})
    free_after = next(s for s in range(seats) if slot_state.state[s] == 'free')
    live_after = next(s for s in range(seats) if slot_state.state[s] == 'issued')
    steps.append({'op': 'issue', 'slot': free_after, 'gen': slot_state.gen[free_after],
                  'holder': 'a', 'expect': {'abort': E_CLOSED}})
    steps.append({'op': 'attest_issuance', 'slot': free_after, 'gen': slot_state.gen[free_after],
                  'buyer': 'a', 'amount': 1000, 'ref': ref_counter[0], 'expect': {'abort': E_CLOSED}})
    ref_counter[0] += 1
    # IM-08: the refund obligation is off-chain once the show is cancelled.
    steps.append({'op': 'refund', 'slot': live_after, 'version': 1, 'expect': {'abort': E_CLOSED},
                  'comment': 'post_cancel_refund_is_off_chain'})
    # revoke carries no open check: it still retires a slot on a cancelled show.
    steps.append({'op': 'revoke', 'slot': live_after, 'comment': 'post_cancel_revoke_allowed'})
    slot_state.revoke(live_after)

    expected = {'pages': slot_state.page_totals()}
    return steps, expected


def private_path(settings, rng):
    """Private path with the depth-10 fixture trees. `private_seated` caps the
    real show at the `claim_zk` contract bound (2^ZK_DEPTH); when the stage is
    larger, a `probe.zk_capacity` prefix first proves the bound on auxiliary
    shows and the capped leg runs unchanged as the regression workload."""
    seated = settings['show']['seated']
    private_seated = settings['show'].get('private_seated', seated)
    shield_count = settings['shield_count']
    # Notes 0 and 1 are pinned to the boundary probe; the revocation,
    # invalidation, race and consume subsets must fit inside the rest.
    budget = shield_count - 5
    invalidation_count = min(settings['invalidation_count'], max(1, budget // 4))
    consume_count = min(settings['consume_count'], budget - invalidation_count)
    if consume_count < 1:
        raise ValueError('shield_count leaves no notes for the consume subset')
    prefix = min(8, shield_count)
    boundary = min(4, shield_count - prefix)
    if shield_count < 12:
        raise ValueError('shield_count below 12 cannot express the K-boundary probe')
    slot_state = Slots(private_seated)
    ref_counter = [500]
    steps = []
    if private_seated < seated:
        # probe.zk_capacity: the private path is contract-capped at
        # 2^ZK_DEPTH seats. Auxiliary shows are created only to be refused by
        # claim_zk — no slot ops are emitted for them and the last create_show
        # below initializes the real measured show.
        for aux_seats in (private_seated + 1, seated):
            steps.append({'op': 'create_show', 'seated': aux_seats, 'ga': 0,
                          'page_size': PAGE_SIZE, 'shards': PRIVATE_SHARDS,
                          'verifier': 'v1', 'phase': 'probe.zk_capacity',
                          'comment': 'zk_capacity_aux_show'})
            steps.append({'op': 'claim_zk', 'verifier': 'v1',
                          'phase': 'probe.zk_capacity',
                          'expect': {'abort': E_RANGE},
                          'comment': 'claim_zk_over_depth_cap'})
    steps.append({'op': 'create_show', 'seated': private_seated, 'ga': 0,
                  'page_size': PAGE_SIZE, 'shards': PRIVATE_SHARDS,
                  'verifier': 'v1'})
    steps += _claim_steps(private_seated // PAGE_SIZE, PRIVATE_SHARDS, zk=True)

    # Every slot gets a ticket; holder 'a' signs all shields.
    for chunk in _chunks(list(range(private_seated)), MAX_BUNDLE):
        steps.append({'op': 'bundle', 'slots': chunk, 'slot': chunk[0], 'gen': 0, 'holder': 'a'})
        for slot in chunk:
            slot_state.issue(slot, 'a')

    # Shield a prefix so the K=4 root-history eviction probe has a known root.
    note_of_slot = {}
    for slot in range(prefix):
        note_of_slot[slot] = len(note_of_slot)
        steps.append({'op': 'shield', 'slot': slot})
    # Boundary: two proofs bound to root@prefix. After 3 more shields the root
    # is still inside the last-K window (ok); after the 4th it is evicted (19).
    steps.append({'op': 'preprove', 'note': 0, 'label': 'bp0'})
    steps.append({'op': 'preprove', 'note': 1, 'label': 'bp1'})
    for i in range(boundary - 1):
        slot = prefix + i
        note_of_slot[slot] = len(note_of_slot)
        steps.append({'op': 'shield', 'slot': slot})
    steps.append({'op': 'consume_private', 'proof': 'bp0'})
    slot = prefix + boundary - 1
    note_of_slot[slot] = len(note_of_slot)
    steps.append({'op': 'shield', 'slot': slot})
    steps.append({'op': 'consume_private', 'proof': 'bp1', 'expect': {'abort': E_ROOT},
                  'comment': 'root_evicted_after_k_writes'})

    shielded = prefix + boundary
    for slot in range(shielded, shield_count):
        note_of_slot[slot] = len(note_of_slot)
        steps.append({'op': 'shield', 'slot': slot})

    # RR-6: proofs generated before a revocation are invalid after it.
    free_notes = [n for n in range(shield_count) if n not in (0, 1)]
    chosen = rng.sample(free_notes, invalidation_count + 1 + 2 + consume_count)
    it = iter(chosen)
    invalid_notes = [next(it) for _ in range(invalidation_count)]
    revoked_note = next(it)
    race_notes = [next(it), next(it)]
    consume_notes = [next(it) for _ in range(consume_count)]
    for i, note in enumerate(invalid_notes):
        steps.append({'op': 'preprove', 'note': note, 'label': f'inv{i}'})
    slot_of_note = {n: s for s, n in note_of_slot.items()}
    steps.append({'op': 'revoke_with_root', 'slot': slot_of_note[revoked_note]})
    slot_state.revoke(slot_of_note[revoked_note])
    for i in range(invalidation_count):
        steps.append({'op': 'consume_private', 'proof': f'inv{i}', 'expect': {'abort': ZK_GATE_REJECT},
                      'comment': 'invalidated_by_revocation'})
    # Re-proving the same note against the new roots restores admissibility.
    steps.append({'op': 'consume_private', 'note': invalid_notes[0],
                  'comment': 'reproof_after_revocation'})
    steps.append({'op': 'consume_private', 'note': revoked_note,
                  'expect': {'client': 'PRIVATE_NOTE_REVOKED'},
                  'comment': 'prover_refuses_revoked_note'})
    steps.append({'op': 'consume_private', 'note': revoked_note, 'allow_revoked': True,
                  'expect': {'client': '*'}, 'comment': 'circuit_rejects_revoked_note'})

    # Two revocations built on the same root: exactly one lands (RR-2(b)).
    ra, rb = slot_of_note[race_notes[0]], slot_of_note[race_notes[1]]
    steps.append({'op': 'parallel', 'name': 'concurrent_revokes', 'expect': 'one_wins',
                  'of': [{'op': 'revoke_with_root', 'slot': ra},
                         {'op': 'revoke_with_root', 'slot': rb}]})
    # Rebuilt-witness retries: the loser lands on the second attempt, the
    # already-revoked slot aborts EStale. Which is which is runtime data.
    steps.append({'op': 'revoke_with_root', 'slot': ra, 'expect': 'any'})
    steps.append({'op': 'revoke_with_root', 'slot': rb, 'expect': 'any'})
    slot_state.revoke(ra)
    slot_state.revoke(rb)

    # Fresh consumptions, then shielded-ticket public-op refusals (RS-C10).
    for note in consume_notes:
        steps.append({'op': 'consume_private', 'note': note})
    shielded_slot = slot_of_note[consume_notes[0]]
    steps.append({'op': 'refund', 'slot': shielded_slot, 'version': 2,
                  'expect': {'abort': E_CLOSED}, 'comment': 'shielded_refuses_public_ops'})
    steps.append({'op': 'offer', 'slot': shielded_slot, 'version': 2, 'to': 'b', 'amount': 0,
                  'ttl_ms': 60000, 'expect': {'abort': E_CLOSED}})

    # Witness rebuild at the full L1 leaf count, once per independent source.
    steps.append({'op': 'reconstruct', 'source': 'jsonrpc'})
    steps.append({'op': 'reconstruct', 'source': 'grpc'})

    expected = {
        'pages': slot_state.page_totals(),
        'leaf_count': shield_count,
        'nullifiers': 2 + consume_count,   # bp0 + reproof + fresh consumptions
        'challenges': 2 + consume_count,
        'revocations': 3,
        'invalidation_count': invalidation_count,
        'consume_count': consume_count,
    }
    return steps, expected


def delegated_path(settings, rng):
    """Delegated path: two grants on the two last pages of a stage-sized show."""
    seats = settings['show']['seated']
    slot_state = Slots(seats)
    ref_counter = [300]
    pages = seats // PAGE_SIZE
    g1_page, g2_page = pages - 2, pages - 1    # L1: 14, 15; L2: 254, 255
    steps = [{'op': 'create_show', 'seated': seats, 'ga': 0, 'page_size': PAGE_SIZE,
              'shards': DELEGATED_SHARDS, 'verifier': None}]
    steps += _claim_steps(pages, DELEGATED_SHARDS)
    steps.append({'op': 'create_grant', 'label': 'g1', 'delegate': 'delegate'})
    steps.append({'op': 'create_grant', 'label': 'g2', 'delegate': 'delegate'})
    steps.append({'op': 'delegate_page', 'grant': 'g1', 'page': g1_page})
    steps.append({'op': 'delegate_page', 'grant': 'g2', 'page': g2_page})

    b1 = g1_page * PAGE_SIZE
    for chunk in _chunks(list(range(b1, b1 + PAGE_SIZE)), MAX_BUNDLE):
        holder = 'a' if chunk[0] % 16 == 0 else 'b'
        steps.append({'op': 'bundle_delegated', 'slots': chunk, 'slot': chunk[0], 'gen': 0,
                      'holder': holder, 'grant': 'g1'})
        for slot in chunk:
            slot_state.issue(slot, holder)
    b2 = g2_page * PAGE_SIZE
    for slot in range(b2, b2 + 16):
        steps.append({'op': 'issue_delegated', 'slot': slot, 'gen': 0, 'holder': 'a',
                      'grant': 'g2'})
        slot_state.issue(slot, 'a')
    steps += _paid_steps(list(range(b2 + 16, b2 + 24)), slot_state, 'a', 9000,
                         ref_counter, delegate_grant='g2')

    # One shared GrantControl as read-only input of two concurrent delegated calls.
    steps.append({'op': 'parallel', 'name': 'shared_grant_reads', 'expect': 'any',
                  'of': [{'op': 'issue_delegated', 'slot': b2 + 24, 'gen': 0, 'holder': 'a',
                          'grant': 'g2'},
                         {'op': 'issue_delegated', 'slot': b2 + 25, 'gen': 0, 'holder': 'b',
                          'grant': 'g2'}]})
    for slot in (b2 + 24, b2 + 25):
        steps.append({'op': 'issue_delegated', 'slot': slot, 'gen': 0, 'holder': 'a',
                      'grant': 'g2', 'expect': 'any'})
        slot_state.force_issued(slot)

    # Direct calls on a delegated page are refused (EDelegated) at any occupancy.
    steps.append({'op': 'issue', 'slot': b1, 'gen': 1, 'holder': 'a', 'expect': {'abort': E_DELEGATED}})
    steps.append({'op': 'attest_issuance', 'slot': b1 + 1, 'gen': 1, 'buyer': 'a', 'amount': 500,
                  'ref': ref_counter[0], 'expect': {'abort': E_DELEGATED}})
    ref_counter[0] += 1
    steps.append({'op': 'refund', 'slot': b1 + 2, 'version': 1, 'expect': {'abort': E_DELEGATED}})

    # Holder-signed delegated refunds before the cut.
    refund_slots = [b1 + 3, b1 + 4, b1 + 5, b1 + 6]
    for slot in refund_slots:
        steps.append({'op': 'refund_delegated', 'slot': slot, 'version': 1, 'grant': 'g1'})
        slot_state.refund(slot)

    # The revocation cut: one write on the grant, then post-cut refusals.
    steps.append({'op': 'revoke_grant', 'grant': 'g1'})
    steps.append({'op': 'issue_delegated', 'slot': b1 + 7, 'gen': 0, 'holder': 'a',
                  'grant': 'g1', 'expect': {'abort': E_GRANT_CLOSED},
                  'comment': 'first_call_after_cut'})
    steps.append({'op': 'attest_issuance_delegated', 'slot': b1 + 8, 'gen': 0, 'buyer': 'a',
                  'amount': 500, 'ref': ref_counter[0], 'grant': 'g1',
                  'expect': {'abort': E_GRANT_CLOSED}})
    ref_counter[0] += 1
    steps.append({'op': 'refund_delegated', 'slot': b1 + 9, 'version': 1, 'grant': 'g1',
                  'expect': {'abort': E_GRANT_CLOSED}, 'comment': 'post_cut_release_is_off_chain'})
    # The other grant is unaffected (grant independence).
    steps.append({'op': 'issue_delegated', 'slot': b2 + 26, 'gen': 0, 'holder': 'a',
                  'grant': 'g2', 'comment': 'grant_independence'})
    slot_state.issue(b2 + 26, 'a')
    # Reclaim the page, then the direct path serves it again (holder refund).
    steps.append({'op': 'undelegate_page', 'grant': 'g1', 'page': g1_page})
    steps.append({'op': 'refund', 'slot': b1 + 10, 'version': 1, 'comment': 'direct_resume'})
    slot_state.refund(b1 + 10)

    # A stranded pre-cut reservation makes the page un-reclaimable (RS-C07b).
    steps.append({'op': 'attest_issuance_delegated', 'slot': b2 + 27, 'gen': 0, 'buyer': 'a',
                  'amount': 500, 'ref': ref_counter[0], 'grant': 'g2',
                  'comment': 'stranded_reservation'})
    ref_counter[0] += 1
    slot_state.reserve(b2 + 27)
    steps.append({'op': 'revoke_grant', 'grant': 'g2'})
    steps.append({'op': 'issue_delegated', 'slot': b2 + 28, 'gen': 0, 'holder': 'a',
                  'grant': 'g2', 'expect': {'abort': E_GRANT_CLOSED}})
    steps.append({'op': 'undelegate_page', 'grant': 'g2', 'page': g2_page,
                  'expect': {'abort': E_DELEGATED}, 'comment': 'unreclaimable_reserved_page'})
    steps.append({'op': 'issue', 'slot': b2 + 28, 'gen': 0, 'holder': 'a',
                  'expect': {'abort': E_DELEGATED}, 'comment': 'page_still_bound'})
    steps.append({'op': 'cancel_issuance_delegated', 'slot': b2 + 27, 'grant': 'g2',
                  'expect': {'abort': E_GRANT_CLOSED}, 'comment': 'stranded_payment_uncleanable'})

    expected = {
        'pages': slot_state.page_totals(),
        'grants': {'g1': {'open': False, 'generation': 2}, 'g2': {'open': False, 'generation': 2}},
        'page_delegated_to': {g1_page: None, g2_page: 'g2'},
    }
    return steps, expected


DEFAULT_SETTINGS = {
    'seed': DEFAULT_SEED,
    'show': {'seated': SEATS, 'ga': 0, 'page_size': PAGE_SIZE},
    'shards': {'public': PUBLIC_SHARDS, 'private': PRIVATE_SHARDS,
               'delegated': DELEGATED_SHARDS},
    'zk': {'depth': model.ZK_DEPTH, 'root_history_k': model.LOCALNET_ROOT_HISTORY_K,
           'nullifier_shards': model.LOCALNET_NULLIFIER_SHARDS,
           'challenge_shards': model.LOCALNET_CHALLENGE_SHARDS},
    'closed_loop': True,
    'arrival_rate': 0,
    'shield_count': SEATS,          # the depth-10 leaf-capacity boundary
    'consume_count': 32,
    'invalidation_count': 8,
    'transfers': 8,
    'admissions': 8,
    'refunds': 16,
    'revokes': 16,
    'reissues': 2,
    'reservations': 2,
}


def expand(settings=None, stage='l1'):
    if stage not in STAGES:
        raise ValueError('unknown stage: ' + str(stage))
    cfg = dict(DEFAULT_SETTINGS)
    if settings:
        cfg.update(settings)
    if stage != 'l1':
        # The private leg is contract-capped at 2^ZK_DEPTH seats; the stage's
        # public/delegated shows run at full size. `private_seated` records
        # the cap in the scenario document.
        cfg['show'] = dict(cfg['show'], seated=STAGES[stage],
                           private_seated=min(STAGES[stage], ZK_LEAF_CAP))
    rng = random.Random(cfg['seed'])
    paths = {}
    expected = {}
    for name, build in (('public', public_path), ('private', private_path),
                        ('delegated', delegated_path)):
        steps, exp = build(cfg, random.Random(rng.randrange(2 ** 32)))
        paths[name] = steps
        expected[name] = exp
    seq = 0
    probes = []
    for name, steps in paths.items():
        for step in steps:
            step.setdefault('expect', 'ok')
            step['seq'] = seq
            seq += 1
            if step['op'] == 'parallel':
                probes.append({'path': name, 'name': step.get('name'), 'k': len(step['of']),
                               'expect': step['expect']})
    cfg['concurrency_probes'] = probes
    zk_capacity = any(s.get('phase') == 'probe.zk_capacity'
                      for s in paths['private'])
    return {
        'version': VERSIONS[stage],
        'settings': cfg,
        'requested': {
            **({'stage': stage,
                'private_seated': cfg['show']['private_seated']}
               if stage != 'l1' else {}),
            'seats_per_show': cfg['show']['seated'],
            'shield_count': cfg['shield_count'],
            'consume_count': cfg['consume_count'],
            'invalidation_count': cfg['invalidation_count'],
        },
        'phases': {
            'public': ['stage.create', 'probe.concurrent', 'stage.fill', 'probe.hot_slot',
                       'stage.ops', 'stage.cancel'],
            'private': (['probe.zk_capacity'] if zk_capacity else [])
                       + ['stage.create', 'stage.issue', 'stage.shield_prefix',
                          'probe.boundary', 'stage.shield_rest', 'stage.revocation',
                          'probe.concurrent_revokes', 'stage.consume', 'stage.negative',
                          'stage.reconstruct'],
            'delegated': ['stage.create', 'stage.delegate', 'stage.fill', 'probe.delegated',
                          'stage.cut', 'stage.stranded'],
        },
        'expected': expected,
        'paths': paths,
    }


def _phase_of(step):
    explicit = step.get('phase')
    if explicit:
        return explicit
    return 'unphased'


def assign_phases(doc):
    """Attach `phase` labels to every step, in doc order."""
    bounds = {}
    seq = 0
    for name in ('public', 'private', 'delegated'):
        steps = doc['paths'][name]
        bounds[name] = _phase_bounds(name, steps)
        for step in steps:
            for i, (label, count) in enumerate(bounds[name]):
                if count:
                    step['phase'] = label
                    bounds[name][i] = (label, count - 1)
                    break
    return doc


def _phase_bounds(path, steps):
    """Split a path's steps into phases matching `phases` above, by content."""
    labels = [s['op'] for s in steps]
    if path == 'public':
        i_probe = next(i for i, s in enumerate(steps) if s['op'] == 'parallel')
        i_fill = next(i for i, s in enumerate(steps) if i > i_probe
                      and s['op'] == 'bundle' and s['slot'] < PROBE_BASE)
        i_hot = next(i for i, s in enumerate(steps) if i > i_fill
                     and s['expect'] != 'ok' and s['expect'] != 'any')
        i_cancel = next(i for i, s in enumerate(steps) if s['op'] == 'cancel_show')
        i_ops = next(i for i, s in enumerate(steps) if i > i_hot
                     and s.get('expect') == 'ok' and s['op'] == 'refund')
        return [('stage.create', i_probe), ('probe.concurrent', i_fill - i_probe),
                ('stage.fill', i_hot - i_fill), ('probe.hot_slot', i_ops - i_hot),
                ('stage.ops', i_cancel - i_ops), ('stage.cancel', len(steps) - i_cancel)]
    if path == 'private':
        aux = sum(1 for s in steps if s.get('phase') == 'probe.zk_capacity')
        i_issue = next(i for i, s in enumerate(steps) if s['op'] == 'bundle')
        i_prefix = next(i for i, s in enumerate(steps) if s['op'] == 'shield')
        i_rest = i_prefix + 8 + 2 + 3 + 1 + 1 + 1   # prefix + preproves + 3 shields + consume + shield + consume
        i_rev = next(i for i, s in enumerate(steps) if s['op'] == 'preprove' and s['label'].startswith('inv'))
        i_race = next(i for i, s in enumerate(steps) if s.get('name') == 'concurrent_revokes')
        i_cons = i_race + 3
        i_neg = next(i for i, s in enumerate(steps) if s['op'] == 'refund')
        return ([('probe.zk_capacity', aux)] if aux else []) + [
                ('stage.create', i_issue - aux), ('stage.issue', i_prefix - i_issue),
                ('stage.shield_prefix', 8), ('probe.boundary', i_rest - i_prefix - 8),
                ('stage.shield_rest', i_rev - i_rest), ('stage.revocation', i_race - i_rev),
                ('probe.concurrent_revokes', i_cons - i_race),
                ('stage.consume', i_neg - i_cons), ('stage.negative', len(steps) - 2 - i_neg),
                ('stage.reconstruct', 2)]
    if path == 'delegated':
        i_delegate = next(i for i, s in enumerate(steps) if s['op'] == 'create_grant')
        i_fill = next(i for i, s in enumerate(steps) if s['op'] == 'bundle_delegated')
        i_probe = next(i for i, s in enumerate(steps) if s['op'] == 'parallel')
        i_cut = next(i for i, s in enumerate(steps) if s['op'] == 'revoke_grant')
        i_stranded = next(i for i, s in enumerate(steps)
                          if s.get('comment') == 'stranded_reservation')
        return [('stage.create', i_delegate), ('stage.delegate', i_fill - i_delegate),
                ('stage.fill', i_probe - i_fill), ('probe.delegated', i_cut - i_probe),
                ('stage.cut', i_stranded - i_cut), ('stage.stranded', len(steps) - i_stranded)]
    raise ValueError(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--expand', metavar='OUT')
    parser.add_argument('--stage', choices=sorted(STAGES), default='l1')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--shield-count', type=int)
    parser.add_argument('--consume-count', type=int)
    args = parser.parse_args()
    settings = {}
    if args.seed is not None:
        settings['seed'] = args.seed
    if args.shield_count is not None:
        settings['shield_count'] = args.shield_count
    if args.consume_count is not None:
        settings['consume_count'] = args.consume_count
    doc = assign_phases(expand(settings, stage=args.stage))
    if args.expand:
        Path(args.expand).write_text(json.dumps(doc, indent=1) + '\n')
        counts = {k: len(v) for k, v in doc['paths'].items()}
        print(f'expanded {doc["version"]} -> {args.expand} steps={counts}')
        return
    parser.error('--expand is required')


if __name__ == '__main__':
    main()
