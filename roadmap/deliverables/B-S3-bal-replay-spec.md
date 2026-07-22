# B-S3 · BAL-replay spec

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2026-11 → 2026-12 (2 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Specify **BAL-replay**: how [Block-Level Access Lists (EIP-7928)](../../knowledge-base/07-sources.md)
drive a state transition **without re-execution**. Instead of re-running transactions, replay applies
each block's recorded state writes directly to the converted tree via per-entry-type translation
rules. This is what catches a converted snapshot up from anchor `N` to chain tip and closes the
preimage-completeness gap, replacing the ad-hoc "catch-up messages" of the older conversion-node
method with a verifiable, re-execution-free mechanism.

## Scope — what ships
- **Translation rules per BAL entry type:** balance changes, nonce changes, storage writes, and code deployments → PBT leaf mutations.
- **Zero-writes delete leaves** — in the migration context, zeros are encoded as absence (the leaf is removed).
- Rule that **account deletion needs no special BAL marker** — deletion falls out of the write/absence semantics.
- **Batching** rules that bound per-step replay cost while keeping convergence below the steady-state block-production rate (so replay can catch up to a live tip).
- **`(E, N]` BAL-completion:** when preimages are extracted at an earlier height `E`, replaying BALs over the half-open interval `(E, N]` guarantees completeness at anchor `N`.
- Determinism/ordering requirements so replay is reproducible across clients.

## Dependencies
- **Upstream (blocks this):** [B-S1](B-S1-offline-migration-eip.md) — anchor/fork semantics. Consumes **EIP-7928 (BAL)**, which ships in Glamsterdam (≈ 2026-09) and is assumed mainnet-live (out of scope here).
- **Downstream (this blocks):** [B-C2](B-C2-bal-replay-engine.md).

## Owners / teams
- Migration spec authors (BAL-replay editors).
- EIP-7928 authors for BAL-format alignment (BAL already shipped in Glamsterdam).
- EL client migration leads as translation-rule reviewers.

## Exit criteria (definition of done)
- [ ] Translation rules for all four entry types specified and reviewed.
- [ ] Zero-write-deletes-leaf and no-deletion-marker semantics documented with rationale.
- [ ] Batching bounds shown (on paper) to keep replay below steady-state block rate.
- [ ] `(E, N]` BAL-completion procedure specified and cross-checked against the preimage format ([B-S2](B-S2-preimage-snapshot-manifest-spec.md)).
- [ ] Signed off against a frozen-enough EIP-7928 to unblock the [B-C2](B-C2-bal-replay-engine.md) engine.

## Risks & open questions
- **External dependency on EIP-7928** — BAL ships in Glamsterdam (≈ 2026-09), ahead of this work, so it is assumed available; any late change to the shipped BAL format would still ripple into these translation rules.
- BAL is a per-block *access* list; replay correctness depends on it recording *all* writes needed for state transition — completeness must be validated by [B-T1](B-T1-conversion-replay-vectors.md) vectors.
- Batching parameters interact with the ~1-month conversion sizing pressures discussed in [04-migration.md §Historical context](../../knowledge-base/04-migration.md).

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
