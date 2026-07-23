# B-C4 · Production rehearsals (mainnet state)

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2027-07 → 2027-12 (6 months) |
| **Migration phase** | Phase 4 — Rehearsals |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Run the full converter on **real mainnet state** across the EIP-7870 hardware
matrix, at production scale, before any public-facing migration. This is where
the machinery meets reality: it must complete within the **2× disk** budget
(confined to converters), produce **cross-client snapshot equality** on genuine
mainnet state, and yield the performance metrics that inform anchor-block
selection and the readiness gate.

## Scope — what ships
- Full converter runs on real mainnet state, executed across the **EIP-7870
  hardware matrix** (representative validator/node hardware tiers).
- Demonstration that conversion fits within **2× disk during conversion**, and
  that this overhead is **confined to converters** (not imposed on every node).
- **Cross-client snapshot equality**: snapshots produced by different clients over
  the same mainnet anchor are bit-identical (chunk hashes + manifest match).
- A **performance metrics** report: wall-clock conversion time, replay
  convergence rate, disk/IO/memory profiles per hardware tier.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section).
  Hash-keyed clients exercise the preimage-driven path; raw-keyed clients exercise
  preimage extraction — all must converge on the same snapshot.

## Dependencies
- **Upstream (blocks this):** [B-C3](B-C3-snapshot-production-pipeline.md) (snapshot pipeline), [B-C2](B-C2-bal-replay-engine.md) (BAL-replay to tip), [A-T4](A-T4-hardware-matrix-benchmarks.md) (EIP-7870 hardware matrix)
- **Downstream (this blocks):** [B-C5](B-C5-testnet-migrations-shadow-fork.md), [B-C6](B-C6-mainnet-window.md), [B-S2](B-S2-readiness-gate-activation-params.md)

## Exit criteria (definition of done)
- [ ] Converter completes on full mainnet state on every hardware tier in the
      EIP-7870 matrix, within the 2× disk budget.
- [ ] All five clients produce **bit-identical snapshots** from the same mainnet
      anchor block.
- [ ] BAL-replay catches the converted snapshot up to chain tip and holds there
      (convergence below block-production rate) on mainnet-scale data.
- [ ] Performance metrics (time, disk, IO, memory, convergence rate) are captured
      per tier and published to inform B-S2 readiness thresholds.
- [ ] 2× disk overhead is confirmed confined to converters; non-converting nodes
      are unaffected.

## Risks & open questions
- **2× disk during conversion** is real and could exclude low-tier hardware;
  rehearsals must establish which tiers can self-convert vs must ingest a snapshot.
- Mainnet state size keeps growing; metrics have a shelf life and may need a
  refresh close to the mainnet window.
- Readiness thresholds (X, Y, D) are open (§14) and are partly derived from these
  metrics — a chicken/egg loop with B-S2 to resolve.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
