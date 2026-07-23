# B-O4 · Activation comms & fork-S coordination

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Ecosystem outreach |
| **Timeline** | 2028-03 → 2028-06 (4 months) |
| **Migration phase** | Phase 5 → 6 — Mainnet Window through Swap & Aftermath |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Coordinate the **activation of fork `S` (I\*, 2028-06)** with the ecosystem: align the
activation release and client release timing, publish the public communications around
the state-commitment swap, and give node operators a clear upgrade path. Fork `S` changes
only the state commitment — no gas or opcode semantics move with it (`EXTCODEHASH` stays
byte-identical) — and the comms must set that expectation precisely so operators and
downstream systems know what does and does not change.

## Scope — what ships
- A **coordinated activation-release plan**: client release versions/dates carrying the
  fork-`S` activation, aligned across EL/CL teams.
- **Public communications** for the swap: what changes (state commitment only), what does
  not (gas/opcode semantics, `EXTCODEHASH`), the MPT-until-finality retention behavior,
  and the timeline.
- A **node-operator upgrade path**: instructions and version requirements for the swap,
  including that the MPT is retained until finality and only then sunset.
- Coordination with the mainnet swap execution in [B-C6](B-C6-mainnet-window.md) /
  [B-C7](B-C7-swap-fork-s-aftermath.md) so comms and release timing match the on-chain events.

## Stakeholders
- **EL and CL client teams** (release engineering and version coordination).
- **Node operators / validators** and staking providers who must upgrade for `S`.
- **Exchanges, infra providers, explorers, and dapps** needing advance notice of the fork.
- Ecosystem comms channels (ACD, client release notes, blog/announcements).

## Dependencies
- **Upstream (blocks this):** [B-S2](B-S2-readiness-gate-activation-params.md) (activation
  parameters — the fork `S` definition and activation trigger the comms announce).
- **Downstream (this blocks):** pairs with [B-C6](B-C6-mainnet-window.md) (mainnet window) and
  [B-C7](B-C7-swap-fork-s-aftermath.md) (swap & aftermath) — the on-chain execution these
  comms wrap around.

## Exit criteria (definition of done)
- [ ] Coordinated client release versions/dates for fork `S` published and aligned across teams.
- [ ] Public swap communications published, correctly scoping the change to the state
      commitment only (gas/opcode semantics and `EXTCODEHASH` unchanged).
- [ ] Node-operator upgrade path documented, including MPT-retention-until-finality behavior.
- [ ] Comms and release timing confirmed against the [B-C6](B-C6-mainnet-window.md) /
      [B-C7](B-C7-swap-fork-s-aftermath.md) swap schedule.

## Risks & open questions
- **Unvalidated flip input** (04-migration.md weak points): `S` activates the pre-fork
  block's PBT root without consensus validation; comms must convey that the swap's safety
  rests on the sustained cross-client agreement from the shadow period
  ([B-O3](B-O3-shadow-root-ecosystem-readiness.md)), not on gas/semantic changes.
- **Messaging risk:** because gas/opcode semantics are unchanged and PBT-native gas
  improvements are **deliberately decoupled** from `S`, comms must avoid implying users
  will see behavior or fee changes at the swap.
- **§14 open — post-swap MPT disposal timing:** the sunset schedule is still open; operator
  guidance on when the MPT is disposed must track that decision.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md) (Six-phase timeline — Phases 5-6; Known weak points; Ecosystem impact — post-swap gas decoupled)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md) (`EXTCODEHASH` unchanged; state-commitment-only swap)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
