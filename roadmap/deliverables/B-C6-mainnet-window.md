# B-C6 · Mainnet window (block N → replay)

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2028-04 → 2028-06 (3 months) |
| **Migration phase** | Phase 5 — Mainnet Window |
| **Milestone alignment** | feeds fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Execute the real migration on mainnet, up to (but not including) the swap. Select
a **finalized anchor block `N` (identified by hash)**, produce and cross-verify
its snapshot, distribute it via **torrent + mirrors**, BAL-replay every node to
the chain tip, and run the **shadow-commitment period** in which builders publish
per-block PBT roots while consensus stays on the MPT. The window closes by
**passing the readiness gate** — the go/no-go for fork `S` at I\*.

## Scope — what ships
- Selection of finalized anchor block **`N`, identified by hash**.
- Snapshot production for `N` and **cross-verification** across independent
  producers (bit-identical chunks + manifest) plus dual-check authentication.
- **Distribution via torrent + mirrors** so any node can fetch and verify the
  artifact without trusting the source.
- **BAL-replay to chain tip** so nodes hold a live PBT alongside the canonical MPT.
- A **shadow-commitment period**: builders compute and publish per-block PBT roots
  while consensus still runs on the MPT, making conversion correctness visible,
  public, and attributable per block.
- **Passing the readiness gate**: cross-client agreement ≥ X% sustained D days,
  coverage ≥ Y%, builder/relay readiness.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section). Hash-keyed
  clients rely on distributed preimages for the consensus-anchoring verification
  against block `N`'s `stateRoot`; all clients must reach the same PBT root.

## Dependencies
- **Upstream (blocks this):** [B-C4](B-C4-production-rehearsals.md) (rehearsed at scale), [B-C5](B-C5-testnet-migrations-shadow-fork.md) (public + shadow-fork rehearsals), [B-S2](B-S2-readiness-gate-activation-params.md) (gate thresholds & activation params), [B-C2](B-C2-bal-replay-engine.md) (replay to tip)
- **Downstream (this blocks):** [B-C7](B-C7-swap-fork-s-aftermath.md)

## Exit criteria (definition of done)
- [ ] Finalized block `N` selected and pinned by hash; snapshot produced and
      cross-verified bit-identically across independent producers.
- [ ] Snapshot distributed via torrent + mirrors; nodes verify it via dual-check
      (internal PBT consistency + consensus-anchoring to `N`'s `stateRoot`).
- [ ] BAL-replay brings nodes to chain tip and holds there.
- [ ] Shadow-commitment period runs: builders publish per-block PBT roots;
      omissions counted against **coverage**, disagreements against **divergence**.
- [ ] Readiness gate **passed**: cross-client agreement ≥ X% sustained D days,
      coverage ≥ Y%, builder/relay ecosystem ready — a documented go decision for S.

## Risks & open questions
- **Readiness thresholds (X, Y, D) are open (§14)** and must be fixed by B-S2
  before the gate can be evaluated.
- **Validator observability gap.** The builder stream measures block *producers*,
  not the validating majority; pre-swap divergence is harmless and self-detectable,
  with a proposer-signed post-import sidecar as the designed fallback.
- **Shadow-root carrier mechanism** and **`N′` re-anchoring cadence** for late
  joiners are still open (§14).

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
