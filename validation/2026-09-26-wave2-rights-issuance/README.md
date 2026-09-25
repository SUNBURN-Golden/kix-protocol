# Wave 2 — primary issuance on existing rights

Local Move note for the `rights` extension. This is not a charter revision, a
coin module, or a claim that issuance is production-ready.

## What changed

`kix::rights` can mint the same public `Ticket` in two ways:

- `issue` — direct `IssuerCap` grant. No payment. `Issuance.kind = 0`.
- `attest_issuance` then `issue_paid` — a listed payment attester reserves a
  free slot against a 32-byte fiat assertion, and the issuer mints that slot
  to the buyer. `Issuance.kind = 1`.

`cancel_issuance` drops a reservation, including after `cancel_show`, and does
not mint. The reserved slot cannot be direct-issued. The payment ref shares
the show's existing ref list with resale `attest_payment`.

The minted object is the existing `Ticket`. Gift, resale, admission, refund
and a later holder `shield` (`zk_gate::mint`) / `consume_private` are the same
functions as before. `Show` and `Ticket` field layouts are unchanged.
`zk_gate` is unchanged. There is no new coin module and no `tix` module.

## Contract-undefined

The Move `Show` has no primary price and no primary fee. Paid issuance stores
the attester's amount on the ticket and does not emit `Allocation`. Resale
`organizer_bps` / `platform_bps` are not applied here. The Python model uses a
separate `primaryPrice` and `primaryFeeBps`; this change does not copy that
split onto the chain.

An attester assertion is still not proof of bank funds. No localnet journey,
Groth16 proof, or settlement path was executed for this note.

## Command

```bash
python3 scripts/configure_local.py
export PATH="$PWD/.local/bin:$PATH"
export KIX_SUI_CONFIG="$PWD/.local/sui-config/client.yaml"
sui move --client.config "$KIX_SUI_CONFIG" --build-env mainnet test --path reference/v0.3-rc1/sui
```

Sui CLI `1.79.1-808640d9b49a` (pinned `mainnet-v1.79.1`). Result: 19 tests
passed, 0 failed. That count is this local run only. It is not CI for the
commit that records this note, and it is not a mainnet or funds result.

Branch base at session start: `729a106add049ad1a75b90f99c00b6e0ccb8a67d`.
This note does not rebase onto later `origin/main`.
