# Rights scale — public localnet profile

`kix_scale::rights` uses 256-slot independent shared pages, supports configured show capacities from 1 through 65,536, and shards payment references into 16 hash-routed tables. The legacy 16-slot package remains an unchanged regression fixture.

Read [profile contract](../../docs/contracts/RIGHTS_SCALE_PROFILE.md) before integration. This is a new package/type/API, not a compatible upgrade to the existing Show decoder, SDK or Commerce adapter. No deployment has been authorized. Private/ZK, GA, grants and production qualification remain pending.

## Build and test

Use the repository-pinned Sui CLI/framework and local configuration:

```sh
source scripts/env.sh
sui move --client.config "$KIX_SUI_CONFIG" --build-env mainnet test \
  --path reference/rights-scale-v1/sui --gas-limit 1000000000
```

The build environment selects dependency metadata; it does not publish to mainnet. Tests use Sui's in-process Move test scenario, without external funds or RPC. Large-capacity tests construct all pages and issue the last slot; they do not simulate a sold-out concert or measure production capacity.

## Construction and calls

1. Issuer calls `create_show(capacity, gates, attesters, resale_cap, organizer_bps, platform_bps)`.
2. In successive transactions, create each page (`0..page_count-1`) and each payment shard (`0..15`) using IssuerCap.
3. Call `seal`; it refuses incomplete construction. The show is now open. Its capacity/ranges cannot change.
4. Route by `page_id(show, slot/256)` and `shard_id(show, payment_shard(reference))`.
5. Issue takes `(show, page, slot, expected_generation, holder)` signed by the issuer. Read actual current generation before creating a new intent. An ambiguous prior request must be reconciled, not replaced with a new generation.
6. Gift/resale/admission take read-only ShowControl and page plus the mutable ticket. Cancel writes only ShowControl; it cannot reopen. Refund/revoke mutate the ticket and page. Reservation cancellation remains possible after show cancellation.

Capacity is independent from page size, cumulative issue history and single-transaction network limits. No generated production SDK or UI binding is supplied by this package.

## Disposable localnet acceptance

After the normal bootstrap, run `python scripts/run_localnet.py --scale`. It creates its own one-validator local chain, disables zkLogin background key fetches, publishes only there, constructs complete 1,024/16,384/65,536-slot ranges and exercises last-slot issuance, cross-page failed-PTB rollback, refund/generation fencing and show cancellation. It terminates only the process it created. The non-secret receipt is `.local/verification/scale-localnet.json`; no signing keys are exported by the JS driver.
