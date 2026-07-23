# B-T3 · Dual-check verification at scale

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Tests |
| **Timeline** | 2027-10 → 2028-04 (7 months) |
| **Migration phase** | Phase 4 — Rehearsals |
| **Milestone alignment** | gates fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Validate **dual-check authentication** at mainnet scale: prove that any node — including a **fresh
node with no prior state** — can verify a downloaded snapshot without trusting the distribution
source. The two checks are (1) **internal PBT consistency** and (2) **consensus anchoring**. This is
the test that makes the ~100+ GB distributed artifact trustworthy, and it must hold at full mainnet
state size.

## Scope — what ships
- **Check 1 — internal PBT consistency:** rebuild the PBT from snapshot leaves, derive keys, hash bottom-up, and verify the claimed PBT root — run over a full mainnet-scale snapshot.
- **Check 2 — consensus anchoring:** rehash snapshot leaves under the **MPT schema** using distributed preimages and verify against block `N`'s header `stateRoot`.
- A **fresh-node** verification run: a node with no prior state performs both checks purely from the snapshot + preimages + block `N` header.
- Per-chunk verification against release-anchored manifest hashes, so verification streams chunk-by-chunk at scale.
- Scale/perf metrics: verification wall-clock, memory, and disk footprint at ~100+ GB; failure-injection tests (corrupted chunk, wrong preimage, tampered root) confirming detection.

## Dependencies
- **Upstream (blocks this):** [B-C3](B-C3-snapshot-production-pipeline.md), [B-C4](B-C4-production-rehearsals.md).
- **Downstream (this blocks):** [B-C6](B-C6-mainnet-window.md).

## Owners / teams
- EEST / verification-harness team.
- EL client teams (fresh-node verification implementations).
- EF DevOps (mainnet-scale test infrastructure).

## Exit criteria (definition of done)
- [ ] Both checks pass on a full mainnet-scale snapshot across multiple clients.
- [ ] A fresh node with no prior state independently authenticates the snapshot from snapshot + preimages + block `N` header alone.
- [ ] Failure injection (corrupted chunk / wrong preimage / tampered root) is reliably **detected** by the appropriate check.
- [ ] Verification resource cost (time/memory/disk) measured and shown acceptable per the hardware matrix (EIP-7870).

## Risks & open questions
- Consensus anchoring hinges on **preimage completeness** — the MPT is hash-keyed and can't be walked back to raw keys, so extraction at `E` + `(E, N]` BAL-completion must be exhaustive ([04-migration.md §Preimages](../../knowledge-base/04-migration.md)); gaps would surface as check-2 failures.
- Scale cost of the bottom-up rebuild and MPT-schema rehash at ~220M accounts / 600M slots is unproven until this test — depends on the finalized hash function (open parameter in [06-open-questions.md](../../knowledge-base/06-open-questions.md)).
- Verification depends on frozen preimage/snapshot/manifest formats from [B-S1](B-S1-offline-migration-eip.md) (§14 open params) and on [A-C4](A-C4-snapshot-serving-verification.md) serving infrastructure.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
