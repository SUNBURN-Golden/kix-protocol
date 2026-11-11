"""Test-owned literals for the existing synthetic fixture representation.

MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY; Analog, NOT Toss. Source-informed,
independently specified expectations, not clean-room authorship, provider
conformance, an operational encoding or a domain/schema assignment.
See validation/2026-10-28-plan-provider-normalization-golden-vectors/README.md
for derivation. No implementation or fixture imports belong in this module.
item_position selects a fixture item only; it is never event identity.
"""

GOLDEN_VECTORS = (
    {
        "case": "paid_payment",
        "fixture": "PAID",
        "item_position": 0,
        "expected_fact": {
            "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
            "payment_ref": {
                "provider": "toss-synthetic",
                "account": "mid_synthetic_001",
                "environment": "test-synthetic",
                "payment_key": "pay_synthetic_001",
                "order_id": "order_synthetic_001",
            },
            "item": {
                "kind": "payment",
                "amount": 15000,
                "currency": "KRW",
                "status_text": "DONE",
                "occurred": {
                    "text": "2026-10-01T12:00:00+09:00",
                    "offset": "+09:00",
                    "status": "OFFSET_RECORDED",
                },
                "detail": {
                    "method_text": "카드",
                    "last_transaction_key_text": "txkey_synthetic_001",
                    "timestamps": {
                        "requestedAt": {
                            "text": "2026-10-01T11:59:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                        "approvedAt": {
                            "text": "2026-10-01T12:00:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                    },
                },
            },
        },
        "canonical_utf8": (
            b'{"item":{"amount":15000,"currency":"KRW","detail":{'
            b'"last_transaction_key_text":"txkey_synthetic_001","method_text":"\xec\xb9\xb4\xeb\x93\x9c",'
            b'"timestamps":{"approvedAt":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"requestedAt":{"offset":"+09:00",'
            b'"status":"OFFSET_RECORDED","text":"2026-10-01T11:59:00+09:00"}}},'
            b'"kind":"payment","occurred":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"status_text":"DONE"},'
            b'"payment_ref":{"account":"mid_synthetic_001","environment":"test-synthetic",'
            b'"order_id":"order_synthetic_001","payment_key":"pay_synthetic_001",'
            b'"provider":"toss-synthetic"},"provenance":"MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"}'
        ),
        "sha256_hex": "623bb1ed3e35ec4c7ad5908a774089661b968eac38d29106d4afb3d99ca3cd23",
    },
    {
        "case": "partial_cancel_payment",
        "fixture": "PARTIAL_CANCEL",
        "item_position": 0,
        "expected_fact": {
            "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
            "payment_ref": {
                "provider": "toss-synthetic",
                "account": "mid_synthetic_001",
                "environment": "test-synthetic",
                "payment_key": "pay_synthetic_001",
                "order_id": "order_synthetic_001",
            },
            "item": {
                "kind": "payment",
                "amount": 15000,
                "currency": "KRW",
                "status_text": "PARTIAL_CANCELED",
                "occurred": {
                    "text": "2026-10-01T12:00:00+09:00",
                    "offset": "+09:00",
                    "status": "OFFSET_RECORDED",
                },
                "detail": {
                    "method_text": "카드",
                    "last_transaction_key_text": "txkey_synthetic_001",
                    "timestamps": {
                        "requestedAt": {
                            "text": "2026-10-01T11:59:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                        "approvedAt": {
                            "text": "2026-10-01T12:00:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                    },
                },
            },
        },
        "canonical_utf8": (
            b'{"item":{"amount":15000,"currency":"KRW","detail":{'
            b'"last_transaction_key_text":"txkey_synthetic_001","method_text":"\xec\xb9\xb4\xeb\x93\x9c",'
            b'"timestamps":{"approvedAt":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"requestedAt":{"offset":"+09:00",'
            b'"status":"OFFSET_RECORDED","text":"2026-10-01T11:59:00+09:00"}}},'
            b'"kind":"payment","occurred":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"status_text":"PARTIAL_CANCELED"},'
            b'"payment_ref":{"account":"mid_synthetic_001","environment":"test-synthetic",'
            b'"order_id":"order_synthetic_001","payment_key":"pay_synthetic_001",'
            b'"provider":"toss-synthetic"},"provenance":"MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"}'
        ),
        "sha256_hex": "4be77e0249d636616dbe884114b0e2e8cfd690a2b02a7fe41d2385b19de4b76f",
    },
    {
        "case": "partial_cancel_item",
        "fixture": "PARTIAL_CANCEL",
        "item_position": 1,
        "expected_fact": {
            "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
            "payment_ref": {
                "provider": "toss-synthetic",
                "account": "mid_synthetic_001",
                "environment": "test-synthetic",
                "payment_key": "pay_synthetic_001",
                "order_id": "order_synthetic_001",
            },
            "item": {
                "kind": "cancel",
                "amount": 5000,
                "currency": "KRW",
                "status_text": "DONE",
                "occurred": {
                    "text": "2026-10-02T09:00:00+09:00",
                    "offset": "+09:00",
                    "status": "OFFSET_RECORDED",
                },
                "detail": {
                    "reason_text": "synthetic partial cancel",
                    "transaction_key_text": "txkey_synthetic_cancel_001",
                },
            },
        },
        "canonical_utf8": (
            b'{"item":{"amount":5000,"currency":"KRW","detail":{'
            b'"reason_text":"synthetic partial cancel","transaction_key_text":"txkey_synthetic_cancel_001"},'
            b'"kind":"cancel","occurred":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-02T09:00:00+09:00"},"status_text":"DONE"},'
            b'"payment_ref":{"account":"mid_synthetic_001","environment":"test-synthetic",'
            b'"order_id":"order_synthetic_001","payment_key":"pay_synthetic_001",'
            b'"provider":"toss-synthetic"},"provenance":"MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"}'
        ),
        "sha256_hex": "0113104c22549a824251cdcaeb1722ff24c451a87c31e2af2a2b8b8f3ba64edd",
    },
    {
        "case": "offsetless_created_at_payment",
        "fixture": "OFFSET_LESS_CREATED_AT",
        "item_position": 0,
        "expected_fact": {
            "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
            "payment_ref": {
                "provider": "toss-synthetic",
                "account": "mid_synthetic_001",
                "environment": "test-synthetic",
                "payment_key": "pay_synthetic_001",
                "order_id": "order_synthetic_001",
            },
            "item": {
                "kind": "payment",
                "amount": 15000,
                "currency": "KRW",
                "status_text": "DONE",
                "occurred": {
                    "text": "2026-10-01T12:00:00+09:00",
                    "offset": "+09:00",
                    "status": "OFFSET_RECORDED",
                },
                "detail": {
                    "method_text": "카드",
                    "last_transaction_key_text": "txkey_synthetic_001",
                    "timestamps": {
                        "requestedAt": {
                            "text": "2026-10-01T11:59:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                        "approvedAt": {
                            "text": "2026-10-01T12:00:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                        "createdAt": {
                            "text": "2026-10-01T12:00:01",
                            "offset": None,
                            "status": "AMBIGUOUS_UNRESOLVED",
                        },
                    },
                },
            },
        },
        "canonical_utf8": (
            b'{"item":{"amount":15000,"currency":"KRW","detail":{'
            b'"last_transaction_key_text":"txkey_synthetic_001","method_text":"\xec\xb9\xb4\xeb\x93\x9c",'
            b'"timestamps":{"approvedAt":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"createdAt":{"offset":null,'
            b'"status":"AMBIGUOUS_UNRESOLVED","text":"2026-10-01T12:00:01"},'
            b'"requestedAt":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T11:59:00+09:00"}}},'
            b'"kind":"payment","occurred":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"status_text":"DONE"},'
            b'"payment_ref":{"account":"mid_synthetic_001","environment":"test-synthetic",'
            b'"order_id":"order_synthetic_001","payment_key":"pay_synthetic_001",'
            b'"provider":"toss-synthetic"},"provenance":"MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"}'
        ),
        "sha256_hex": "41b8a0483d7cf03913c97c4ddb8667d6b30a42e925532e547c70f0bebeda6d7c",
    },
    {
        "case": "u128_max_payment",
        "fixture": "MAX_KRW_AMOUNT",
        "item_position": 0,
        "expected_fact": {
            "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
            "payment_ref": {
                "provider": "toss-synthetic",
                "account": "mid_synthetic_001",
                "environment": "test-synthetic",
                "payment_key": "pay_synthetic_001",
                "order_id": "order_synthetic_001",
            },
            "item": {
                "kind": "payment",
                "amount": 340282366920938463463374607431768211455,
                "currency": "KRW",
                "status_text": "DONE",
                "occurred": {
                    "text": "2026-10-01T12:00:00+09:00",
                    "offset": "+09:00",
                    "status": "OFFSET_RECORDED",
                },
                "detail": {
                    "method_text": "카드",
                    "last_transaction_key_text": "txkey_synthetic_001",
                    "timestamps": {
                        "requestedAt": {
                            "text": "2026-10-01T11:59:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                        "approvedAt": {
                            "text": "2026-10-01T12:00:00+09:00",
                            "offset": "+09:00",
                            "status": "OFFSET_RECORDED",
                        },
                    },
                },
            },
        },
        "canonical_utf8": (
            b'{"item":{"amount":340282366920938463463374607431768211455,"currency":"KRW","detail":{'
            b'"last_transaction_key_text":"txkey_synthetic_001","method_text":"\xec\xb9\xb4\xeb\x93\x9c",'
            b'"timestamps":{"approvedAt":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"requestedAt":{"offset":"+09:00",'
            b'"status":"OFFSET_RECORDED","text":"2026-10-01T11:59:00+09:00"}}},'
            b'"kind":"payment","occurred":{"offset":"+09:00","status":"OFFSET_RECORDED",'
            b'"text":"2026-10-01T12:00:00+09:00"},"status_text":"DONE"},'
            b'"payment_ref":{"account":"mid_synthetic_001","environment":"test-synthetic",'
            b'"order_id":"order_synthetic_001","payment_key":"pay_synthetic_001",'
            b'"provider":"toss-synthetic"},"provenance":"MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"}'
        ),
        "sha256_hex": "52c826ba3ca35303a08a8ac2a5432666a87a06151b56754cecaa9e0cb6f993cd",
    },
)
