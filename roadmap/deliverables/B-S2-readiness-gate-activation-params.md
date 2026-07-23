# B-S2 · Readiness gate & activation params

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2027-09 → 2028-02 (6 months) |
| **Migration phase** | Phase 5 — Mainnet Window |
| **Milestone alignment** | gates fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Fix the numeric and procedural parameters that gate activation: the **readiness thresholds**
(cross-client agreement, coverage, sustained duration), the **shadow-root carrier mechanism**, the
**`N′` re-anchoring cadence**, **post-swap MPT disposal timing**, and the **select-`N` / activate-`S`
procedure**. These parameters convert the observability produced during the shadow-commitment period
into a go/no-go decision for the swap, and they encode the mitigation for the unvalidated-flip weak
point.

## Scope — what ships
- **Readiness thresholds:** cross-client agreement **≥ X%**, coverage **≥ Y%**, sustained **D** days — concrete values fixed and justified.
- **Shadow-root carrier mechanism:** the concrete wire/publication mechanism for per-block PBT roots (the concept comes from [B-S1](B-S1-offline-migration-eip.md)).
- **`N′` re-anchoring cadence** for late joiners.
- **Post-swap MPT disposal timing** (retain until finality, then sunset).
- **Select-`N` / activate-`S` procedure:** how the finalized anchor block is chosen and how the fork is scheduled.
- **Unvalidated-flip mitigation:** specify hard-enforcing the shadow root for the final blocks before `S`, or the documented conditions under which sustained cross-client agreement is accepted instead.

## Dependencies
- **Upstream (blocks this):** informed by [B-C4](B-C4-production-rehearsals.md) and [B-C5](B-C5-testnet-migrations-shadow-fork.md) — thresholds must be calibrated against real rehearsal/shadow-fork data.
- **Downstream (this blocks):** [B-C6](B-C6-mainnet-window.md), [B-O4](B-O4-activation-comms.md).

## Owners / teams
- Migration spec authors (activation-parameter editors).
- EF protocol support + client teams (readiness-gate sign-off).
- Builder / relay liaisons (shadow-root coverage and ecosystem readiness input).

## Exit criteria (definition of done)
- [ ] X, Y, D thresholds fixed with rationale tied to rehearsal data, resolving the §14 open parameter.
- [ ] Shadow-root carrier mechanism specified, resolving the §14 open parameter.
- [ ] `N′` re-anchoring cadence fixed, resolving the §14 open parameter.
- [ ] Post-swap MPT disposal timing fixed, resolving the §14 open parameter.
- [ ] Select-`N` / activate-`S` procedure documented and unvalidated-flip mitigation chosen and specified.

## Risks & open questions
- This deliverable closes multiple §14 open parameters at once (readiness thresholds X/Y/D, shadow-root carrier, `N′` cadence, MPT disposal timing) — see [04-migration.md §Parameters](../../knowledge-base/04-migration.md) and [06-open-questions.md](../../knowledge-base/06-open-questions.md).
- **Unvalidated flip:** `S` activates the pre-fork block's PBT root without consensus validation; a correlated all-client bug would be undetectable either way ([04-migration.md §Known weak points](../../knowledge-base/04-migration.md)).
- **Validator observability gap:** the builder stream measures producers, not the validating majority — coverage thresholds must account for this; proposer-signed post-import sidecar is the designed fallback.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
