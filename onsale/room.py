"""Waiting-room facade: route, enqueue, admit, reissue, expire, observe.

The waiting room is load-control and GA routing only; it creates no inventory
authority (contract intro, §3). Waiting users get a queue token and the coarse
versioned artifact; admitted buyers get a bounded session view. Every write
goes through AdmissionUnit's single-writer commit. When no shard is routable
the facade reports capacity and writes nothing. No public endpoint exists:
this is a local Python API over the adopted non-production backend.
"""

from __future__ import annotations

from onsale.model import AdmitRequest, EnqueueRequest, ReissueRequest
from onsale.router import HintRouter
from onsale.unit import AdmissionUnit


class WaitingRoom:
    def __init__(self, unit, router):
        if not isinstance(unit, AdmissionUnit):
            raise ValueError('unit must be an AdmissionUnit')
        if not isinstance(router, HintRouter):
            raise ValueError('router must be a HintRouter')
        self.unit = unit
        self.router = router

    def enter(self, *, show_id, inventory_epoch, inventory_mode, principal,
              client_command_id, nonce, now_ms):
        """Route a waiting user to a shard and issue the queue token."""
        observations = self.unit.shard_hints(show_id, inventory_epoch, now_ms)
        shard_id = self.router.route(
            observations, inventory_epoch=inventory_epoch, now_ms=now_ms,
        )
        if shard_id is None:
            result = self.unit.flags()
            result.update({
                'outcome': 'capacity', 'first_result': '', 'reason': None,
                'budget_class': None, 'capacity_reason': 'no_routable_shard',
                'sold_hint': None,
            })
            return result
        return self.unit.enqueue(EnqueueRequest(
            show_id=show_id, inventory_epoch=inventory_epoch,
            inventory_mode=inventory_mode, principal=principal,
            client_command_id=client_command_id, nonce=nonce, shard_id=shard_id,
        ), now_ms)

    def admit(self, *, show_id, inventory_epoch, inventory_mode, principal,
              client_command_id, token, now_ms):
        return self.unit.admit(AdmitRequest(
            show_id=show_id, inventory_epoch=inventory_epoch,
            inventory_mode=inventory_mode, principal=principal,
            client_command_id=client_command_id, token=token,
        ), now_ms)

    def reissue(self, *, show_id, inventory_epoch, inventory_mode, principal,
                client_command_id, queue_ticket_id, old_nonce, new_nonce, now_ms):
        """Queue-position-preserving reissue; the new shard is routed, the
        ticket and position identity are carried unchanged by the unit."""
        observations = self.unit.shard_hints(show_id, inventory_epoch, now_ms)
        new_shard_id = self.router.route(
            observations, inventory_epoch=inventory_epoch, now_ms=now_ms,
        )
        if new_shard_id is None:
            result = self.unit.flags()
            result.update({
                'outcome': 'capacity', 'first_result': '', 'reason': None,
                'budget_class': None, 'capacity_reason': 'no_routable_shard',
                'sold_hint': None,
            })
            return result
        return self.unit.reissue(ReissueRequest(
            show_id=show_id, inventory_epoch=inventory_epoch,
            inventory_mode=inventory_mode, principal=principal,
            client_command_id=client_command_id, queue_ticket_id=queue_ticket_id,
            old_nonce=old_nonce, new_nonce=new_nonce, new_shard_id=new_shard_id,
        ), now_ms)

    def expire(self, now_ms, max_count):
        return self.unit.expire_sweep(now_ms, max_count)

    def artifact(self, show_id, inventory_epoch, now_ms):
        return self.unit.queue_artifact(show_id, inventory_epoch, now_ms)

    def session(self, session_id, principal):
        return self.unit.session_view(session_id, principal)


__all__ = ['WaitingRoom']
