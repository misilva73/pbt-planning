# B-C5 · Testnet migrations + mainnet shadow fork

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2028-01 → 2028-03 (3 months) |
| **Migration phase** | Phase 4 — Rehearsals |
| **Milestone alignment** | feeds fork S = I\* (2028-06) |
| **Status** | Not started (re-verified 2026-09-02) |

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
      activation flow behaves as designed — attesters publish signed per-block PBT
      roots via the telemetry sidecar, and coverage / agreement metrics are computed
      from that stream.
- [ ] Any divergence or failure is surfaced pre-consensus (offline-conversion
      safety property) and root-caused before the mainnet window opens.

## Risks & open questions
- Public testnets have smaller, less diverse state than mainnet; the **shadow
  fork** is what closes the realism gap, so its fidelity to mainnet matters.
- Coordinating independent operators and tooling (including builder/relay PBT
  capability, a hard prerequisite for a post-swap network) surfaces
  ecosystem-readiness gaps that outreach (B-O3) must then close before I\*.
- The **attester telemetry sidecar** carrying shadow roots is exercised here for the
  first time at scale: this is where default-on behaviour, coverage measurement and
  cross-client agreement reporting are validated on networks with real validators
  ([B-O3](B-O3-shadow-root-ecosystem-readiness.md)). Publication is out of consensus,
  so a shortfall shows up as low coverage rather than as consensus failure — which is
  exactly the signal the readiness thresholds in
  [B-S2](B-S2-readiness-gate-activation-params.md) are calibrated against here.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
