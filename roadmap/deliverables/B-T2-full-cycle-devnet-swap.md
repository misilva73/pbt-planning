# B-T2 · Full-cycle devnet with swap

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Tests |
| **Timeline** | 2027-03 → 2027-08 (6 months) |
| **Migration phase** | Phase 3 — Migration Machinery |
| **Milestone alignment** | feeds H\* (2027-06) → validates path to fork S = I\* (2028-06) |
| **Status** | **Seeded** (as of 2026-09-02) — a migration devnet exists and passed an M1 gate, but on **empty state** and one client |

← [Back to roadmap](../README.md)

## Objective
Exercise the **entire migration pipeline end-to-end** on a devnet: convert → snapshot → distribute →
BAL-replay → **swap at a simulated fork `S`**. This is the first test where every piece of migration
machinery runs together against a live chain, proving the offline-conversion model works as a whole
before rehearsals move to mainnet-scale state.

> **Update (2026-09-02).** A migration devnet exists on
> [pbt-devnet](https://github.com/CPerezz/pbt-devnet)'s `migration-devnet` /
> `migration-m1` / `migration-m1-tooling` branches: a **merkle genesis with the tree fork
> ahead**, geth built from `CPerezz/go-ethereum@pbt` with the EIP-8347 migration shim, and
> purpose-built tooling — a migration monitor, a migration chaos driver (stake-weighted deep
> victims, healable deep windows, schedule-relative backstop heals) and a `verify-migration`
> checker with a pinned genesis fixture. **M1 is accepted**: *"the empty-state migration
> devnet is accepted"* (2026-08-27).
>
> Note what was pinned and why, because it is a useful pattern for this deliverable's
> harness: only the **genesis state root** (`0x1a20cc79…`) is asserted, not the genesis
> hash, because kurtosis renders a fresh timestamp every run — the alloc is the invariant
> worth defending. `TestPBTGenesisPins` in
> [go-ethereum#32](https://github.com/CPerezz/go-ethereum/pull/32) cross-references it,
> proving one binary computes both tree kinds from one alloc.
>
> **The gap between this and the deliverable is the whole point of the deliverable.** M1 ran
> on **empty state**, on **one execution client**, and does not exercise convert → snapshot →
> distribute at all. The `code-sole` / `code-shared` / `delegate` / `storage-*` scenarios and
> the reorg-across-activation case ([go-ethereum#33](https://github.com/CPerezz/go-ethereum/pull/33),
> a 41-block rewind across the format swap on four nodes) are real evidence, but they are
> evidence about the swap mechanism, not about migrating a populated state multi-client.

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
- **The first migration-devnet gate passed on empty state, which is a weaker signal than it looks.** Empty state exercises the lifecycle machinery (replay, swap, window, reboot, finality close) while exercising *none* of the converter, the artifacts, the dual-check, or code and storage translation. The obvious next gate is a populated-state single-client run, then a second client — in that order, since bit-identical artifacts across producers is the claim with no evidence behind it at all.
- **Only one EL can do the migration today.** Besu started migration code on 2026-08-31 and Erigon lists mainnet conversion as in progress; until a second client lands, "multi-client devnet running the full cycle" is gated on other teams' work, not on this harness.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
