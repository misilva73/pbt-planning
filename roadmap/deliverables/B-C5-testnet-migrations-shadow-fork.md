# B-C5 · Testnet migrations + mainnet shadow fork

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2027-08 → 2028-01 (6 months) |
| **Migration phase** | Phase 4 — Rehearsals |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Take the full migration — including the **swap** — public. Migrate the public
testnets with a real fork that makes PBT canonical, then run a **mainnet shadow
fork** to rehearse the swap against mainnet-derived state and traffic without
touching mainnet consensus. This is the last full dress rehearsal before the
mainnet window: it exercises distribution, ingestion, replay, and activation on
networks with real validators, clients, and tooling.

## Scope — what ships
- **Public testnet migrations with swaps**: on each targeted public testnet,
  select an anchor, distribute the snapshot, replay to tip, and activate a fork
  that makes PBT canonical — the complete offline-conversion lifecycle end to end.
- A **mainnet shadow fork**: fork mainnet state into an isolated network and
  rehearse the entire migration + swap against realistic mainnet-scale conditions.
- Validation that the whole ecosystem loop (converters → snapshot distribution →
  verifying nodes → replay → swap) works with independent operators.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section). All five
  must participate in each public testnet migration and the shadow fork,
  converting or ingesting per their DB model.

## Dependencies
- **Upstream (blocks this):** [B-C4](B-C4-production-rehearsals.md) (mainnet-state rehearsals), [B-T2](B-T2-full-cycle-devnet-swap.md) (full-cycle devnet with swap)
- **Downstream (this blocks):** [B-C6](B-C6-mainnet-window.md)

## Exit criteria (definition of done)
- [ ] At least one public testnet completes a full migration **with a swap** to
      PBT-canonical and continues producing blocks post-swap.
- [ ] A mainnet shadow fork completes the full migration + swap on
      mainnet-derived state with cross-client agreement.
- [ ] Snapshot distribution (chunked, manifest-verified) works with independent
      operators pulling and verifying the artifact.
- [ ] BAL-replay reaches tip on each network and the shadow-commitment /
      activation flow behaves as designed.
- [ ] Any divergence or failure is surfaced pre-consensus (offline-conversion
      safety property) and root-caused before the mainnet window opens.

## Risks & open questions
- Public testnets have smaller, less diverse state than mainnet; the **shadow
  fork** is what closes the realism gap, so its fidelity to mainnet matters.
- Coordinating independent operators and tooling (builders/relays) surfaces
  ecosystem-readiness gaps that outreach (B-O3) must then close before I\*.
- **Shadow-root carrier mechanism (§14)** is exercised here for the first time at
  scale; its final form is still open.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
