"""Replays the shared private-path scripts (vectors/private_path.json) against model.py.

The localnet driver (client/private-localnet.mjs) replays the same scripts against the published
package; compare_private.py then compares the recorded outcomes and chain state with this model.

A `Prover` stands where the real prover and verifier are: it refuses a note the circuit cannot
prove (revoked, absent from the chosen root) and records the public values a proof commits to.
Whether the chain accepts a submitted proof is then decided in model.Show.consume_private by
comparing those values with the ones the chain feeds the Groth16 verifier. No hash is computed.
"""
import json
from pathlib import Path

import model
import replay
from model import Abort, Show

VECTORS = Path(__file__).resolve().parent / 'vectors' / 'private_path.json'
DEFAULT_TTL_MS = 90000


class ClientRefusal(Exception):
    """The prover refuses before any transaction (e.g. a revoked note has no witness)."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def load():
    return json.loads(VECTORS.read_text())


class World:
    """The shows of one scenario plus the notes and proofs the script names."""

    def __init__(self, scenario, vectors, show_ids=None):
        self.vectors = vectors
        self.shows, self.labels = {}, {}
        for index, (name, cfg) in enumerate(scenario['shows'].items()):
            show_id = (show_ids or {}).get(name, b'\x00' * 31 + bytes([index + 1]))
            self.shows[name] = Show('issuer', cfg['seated'], cfg['ga'], cfg['page_size'], cfg['shards'],
                                    gates=vectors['gates'], payment_attesters=['attester'], show_id=show_id,
                                    verifier=cfg['verifier'])
            self.labels[name] = {}
        self.first = next(iter(scenario['shows']))
        self.notes, self.proofs = {}, {}
        self._challenges = 0

    def manifest_of(self, verifier):
        return self.vectors['verifiers'][verifier]['manifest']

    def fresh_challenge(self):
        self._challenges += 1
        return ('challenge', self._challenges)


def prove(world, step):
    note = world.notes.get(step['note'])
    if note is None:
        raise ClientRefusal('NOTE_NOT_ON_CHAIN')
    show = world.shows[note['show']]
    if show.revoked.get(note['slot'], 0) >= note['generation']:
        raise ClientRefusal('PRIVATE_NOTE_REVOKED')
    count = len(show.leaves)
    root = step.get('root')
    if root is not None:
        count = root['count'] if 'count' in root else count - root['age']
    index = show.leaves.index(note['commitment'])
    if index >= count:
        raise ClientRefusal('NOTE_NOT_ON_CHAIN')
    challenge = step.get('challenge')
    world.proofs[step['label']] = dict(
        note=step['note'], show_name=note['show'], nullifier=('nf', note['commitment']),
        challenge=world.fresh_challenge() if challenge is None else ('challenge', challenge),
        domain=show.domain, show=show.show_id, note_count=count, revocations=show.revocations,
        gate=step.get('gate', 'gate'), ttl_ms=step.get('ttl_ms', DEFAULT_TTL_MS))


def run_step(world, step):
    op = step['op']
    proof = world.proofs.get(step.get('proof')) if op == 'consume_private' else None
    name = step.get('show') or (proof['show_name'] if proof else world.first)
    if op == 'prove':
        name = world.notes[step['note']]['show'] if step['note'] in world.notes else world.first
        return prove(world, step)
    if op == 'reconstruct':
        return None
    show, labels = world.shows[name], world.labels[name]
    sender = step.get('sender')
    if op == 'claim_zk':
        verifier = step.get('verifier', show.verifier)
        return show.claim_zk('issuer', verifier, world.manifest_of(verifier))
    if op == 'revoke_plain':
        return show.revoke('issuer', labels[step['ticket']])
    if op == 'revoke':
        return show.revoke_with_root('issuer', labels[step['ticket']], stale_witness=step.get('witness') == 'stale')
    if op == 'shield':
        ticket = labels[step['ticket']]
        bad = step.get('bad')
        show.shield(sender, ticket, step['version'], step['note'],
                    proof_domain=('foreign',) if bad == 'foreign_domain' else None,
                    proof_commitment='other' if bad == 'wrong_commitment' else None)
        t = show.tickets[ticket]
        world.notes[step['note']] = dict(show=name, slot=t.slot, generation=t.generation, commitment=step['note'])
        return None
    if op == 'consume_private':
        root = step.get('note_root')
        count = None if root is None else (len(show.leaves) if root.get('current') else root['count'])
        return show.consume_private(sender or 'gate', proof, note_root=count, ttl_ms=step.get('ttl_ms'),
                                    verifier=step.get('verifier'), wrong_shard=step.get('wrong_shard'))
    return replay.run_step(show, step, labels)


def outcome_of(world, step):
    try:
        run_step(world, step)
        return 'ok'
    except Abort as abort:
        return {'abort': abort.code}
    except ClientRefusal as refusal:
        return {'client': refusal.code}


def run_scenario(scenario, vectors=None, show_ids=None, observe=None):
    """Runs every step, asserting the scripted outcome. Returns (world, outcomes)."""
    vectors = vectors or load()
    world = World(scenario, vectors, show_ids)
    outcomes = []
    for number, step in enumerate(scenario['steps']):
        want = step.get('expect', 'ok')
        actual = outcome_of(world, step)
        assert actual == want, f'{scenario["name"]} step {number} {step}: got {actual}, wanted {want}'
        for show in world.shows.values():
            show.check_invariants()
        outcomes.append(actual)
        if observe:
            observe(number, step, actual, world)
    return world, outcomes


def observer_candidates(scenario, vectors=None):
    """RS-C13: what an observer of PUBLIC data can narrow an accepted private admission down to.

    Shield records the holder, slot and commitment together, so the only thing left hidden is
    WHICH shielded note a later admission spends. The observer sees the note root the proof used
    (so only notes inserted up to that root can be the one), every earlier nullifier (those notes
    are spent) and every revocation (those slots are known). The count of notes left is the
    candidate set: the anonymity set of that admission, before any timing or network correlation.
    """
    vectors = vectors or load()
    rows = []

    def observe(number, step, actual, world):
        if step['op'] != 'consume_private' or actual != 'ok':
            return
        proof = world.proofs[step['proof']]
        show = world.shows[proof['show_name']]
        spent = {nf[1] for nf in show.spent_nullifiers}
        in_window = show.leaves[:proof['note_count']]
        revoked = {n for n, note in world.notes.items()
                   if note['show'] == proof['show_name'] and show.revoked.get(note['slot'], 0) >= note['generation']}
        # The note being spent was unspent a moment ago; the observer counts it among the candidates.
        candidates = [n for n in in_window if (n not in spent or n == proof['note']) and n not in revoked]
        rows.append({'step': number, 'show': proof['show_name'], 'noteCount': proof['note_count'],
                     'notesInTree': len(show.leaves), 'rootAge': len(show.leaves) - proof['note_count'],
                     'candidates': len(candidates)})

    run_scenario(scenario, vectors, observe=observe)
    return rows
