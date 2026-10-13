"""Replays the shared operation scripts (vectors/public_path.json) against model.py.

The localnet driver (client/localnet.mjs) replays the same scripts against the published
package and then compares chain state with `Show.snapshot()` of this model.
"""
import json
from pathlib import Path

import model
from model import Abort, Show

VECTORS = Path(__file__).resolve().parent / 'vectors' / 'public_path.json'
DEFAULT_SENDER = {
    'attest_issuance': 'attester', 'attest_payment': 'attester', 'consume': 'gate',
}


def load():
    return json.loads(VECTORS.read_text())


def ref(tag):
    return bytes([tag]) * 32


def new_show(create, show_id=None):
    kwargs = {} if show_id is None else {'show_id': show_id}
    return Show('issuer', create['seated'], create['ga'], create['page_size'], create['shards'],
                gates=['gate'], payment_attesters=['attester'], **kwargs)


def run_step(show, step, labels):
    op = step['op']
    sender = step.get('sender') or DEFAULT_SENDER.get(op, 'issuer')
    page = step.get('page')
    if op == 'claim_pages':
        return show.claim_pages(sender, step['from'], step['count'])
    if op == 'claim_shards':
        return show.claim_shards(sender, step['from'], step['count'])
    if op == 'seal':
        return show.seal(sender)
    if op == 'cancel_show':
        return show.cancel_show(sender)
    if op == 'issue':
        t = show.issue(sender, step['slot'], step['gen'], step['holder'], page_index=page)
        if 'label' in step:
            labels[step['label']] = t.id
        return t
    if op == 'bundle':
        return show.bundle(sender, step['first'], step['declared'], step['issues'], step['holder'])
    if op == 'attest_issuance':
        return show.attest_issuance(sender, step['slot'], step['gen'], step['buyer'], step['amount'], ref(step['ref']))
    if op == 'issue_paid':
        t = show.issue_paid(sender, step['slot'])
        if 'label' in step:
            labels[step['label']] = t.id
        return t
    if op == 'cancel_issuance':
        return show.cancel_issuance(sender, step['slot'])
    ticket = labels[step['ticket']] if 'ticket' in step else None
    if op == 'offer':
        return show.offer(sender, ticket, step['version'], step['recipient'], step['amount'], step['ttl_ms'])
    if op == 'accept_gift':
        return show.accept_gift(sender, ticket)
    if op == 'attest_payment':
        return show.attest_payment(sender, ticket, ref(step['ref']))
    if op == 'accept_sale':
        return show.accept_sale(sender, ticket)
    if op == 'authorize':
        return show.authorize_admission(sender, ticket, step['version'], 'gate', ref(1), step['ttl_ms'])
    if op == 'consume':
        return show.consume(sender, ticket, step['version'], ref(1))
    if op == 'refund':
        return show.refund(sender, ticket, step['version'])
    if op == 'revoke':
        return show.revoke(sender, ticket)
    raise ValueError(f'unknown op {op}')


def run_scenario(scenario, show_id=None, observe=None):
    """Runs every step, asserting the scripted outcome. Returns (show, labels, outcomes)."""
    show = new_show(scenario['create'], show_id)
    labels, outcomes = {}, []
    for number, step in enumerate(scenario['steps']):
        expected = step.get('expect', 'ok')
        try:
            run_step(show, step, labels)
            actual = 'ok'
        except Abort as abort:
            actual = {'abort': abort.code}
        want = 'ok' if expected == 'ok' else expected
        assert actual == want, f'{scenario["name"]} step {number} {step}: got {actual}, wanted {want}'
        show.check_invariants()
        outcomes.append(actual)
        if observe:
            observe(number, step, actual, show)
    return show, labels, outcomes


def matrix_scenario(case):
    """The edge-slot scenario of a matrix case (same construction as the localnet driver)."""
    n, p = case['seated'] + case['ga'], case['page_size']
    pages = -(-case['seated'] // p) + -(-case['ga'] // p)
    steps = []
    # 8 pages of 64 slots per claim transaction: the measured localnet cost of a
    # larger batch exceeds the journey's gas budget (InsufficientGas, observed on
    # the 16-page claim). This is a driver batching bound, not a protocol value.
    for start in range(0, pages, 8):
        steps.append({'op': 'claim_pages', 'from': start, 'count': min(8, pages - start)})
    steps.append({'op': 'claim_shards', 'from': 0, 'count': case['shards']})
    steps.append({'op': 'seal'})
    edges = []
    for slot in (0, n - 1, p - 1, p, p + 1, 2 * p - 1, 2 * p, 2 * p + 1):
        if 0 <= slot < n and slot not in edges:
            edges.append(slot)
    for slot in edges:
        steps.append({'op': 'issue', 'slot': slot, 'gen': 0, 'holder': 'a', 'label': f's{slot}'})
    for slot in edges:
        steps.append({'op': 'refund', 'ticket': f's{slot}', 'sender': 'a', 'version': 1})
    for slot in edges:
        steps.append({'op': 'issue', 'slot': slot, 'gen': 1, 'holder': 'b'})
    steps.append({'op': 'issue', 'slot': n, 'gen': 0, 'holder': 'a', 'expect': {'abort': model.EInventory}})
    name = f'matrix_{case["seated"]}_{case["ga"]}_p{p}_s{case["shards"]}'
    return {'name': name, 'create': case, 'steps': steps, 'edges': edges}
