# B-T2 · Full-cycle devnet with swap

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Tests |
| **Timeline** | 2027-03 → 2027-08 (6 months) |
| **Migration phase** | Phase 3 — Migration Machinery |
| **Milestone alignment** | feeds H\* (2027-06) → validates path to fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Exercise the **entire migration pipeline end-to-end** on a devnet: convert → snapshot → distribute →
BAL-replay → **swap at a simulated fork `S`**. This is the first test where every piece of migration
machinery runs together against a live chain, proving the offline-conversion model works as a whole
before rehearsals move to mainnet-scale state.

## Scope — what ships
- A multi-client devnet that runs the full cycle: converter output at an anchor block, byte-canonical chunked snapshot, distribution to fresh nodes, BAL-replay from anchor to tip, and activation at a simulated fork `S`.
- Verification that the swap changes the **state commitment only** — no gas/opcode behaviour changes across `S`; `EXTCODEHASH` byte-identical.
- Exercise of the transition window: both trees maintained until finality after the simulated `S`.
- A repeatable devnet scenario/harness other teams can re-run, including a fresh-node join that ingests the snapshot as a sequential bulk-load.
- Captured metrics: conversion time, replay catch-up rate vs block production, snapshot distribution timing.

## Dependencies
- **Upstream (blocks this):** [A-C3](A-C3-multiclient-pbt-genesis-devnets.md), [B-C1](B-C1-converter-prototype.md), [B-C2](B-C2-bal-replay-engine.md), [B-C3](B-C3-snapshot-production-pipeline.md).
- **Downstream (this blocks):** feeds the rehearsal phase — [B-C4](B-C4-production-rehearsals.md), [B-C5](B-C5-testnet-migrations-shadow-fork.md).

## Owners / teams
- EF DevOps / devnet coordination.
- EL + CL client teams (all participating clients).
- EEST / test team (scenario definition and pass/fail oracle).

## Exit criteria (definition of done)
- [ ] Full convert → snapshot → distribute → BAL-replay → swap cycle completes on a multi-client devnet.
- [ ] Post-swap state root matches across all clients and the swap is confirmed commitment-only (no execution-semantics change).
- [ ] A fresh node with no prior state joins by ingesting the snapshot and reaches consensus post-swap.
- [ ] Metrics (conversion, replay catch-up, distribution) captured and published to inform rehearsals.

## Risks & open questions
- Replay must converge **below the steady-state block-production rate** or catch-up never completes — a core assumption to validate here ([04-migration.md §BAL-replay](../../knowledge-base/04-migration.md)).
- Simulated `S` cannot fully reproduce the **unvalidated-flip** risk of a real swap; mitigation design lives in [B-S2](B-S2-readiness-gate-activation-params.md) and is stress-tested later in [B-C5](B-C5-testnet-migrations-shadow-fork.md).
- Devnet scale is far below mainnet's ~220M accounts / 600M slots and ~100+ GB snapshot; scale behaviour is deferred to [B-C4](B-C4-production-rehearsals.md) / [B-T3](B-T3-dual-check-verification-scale.md).

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
