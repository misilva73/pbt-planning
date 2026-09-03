# B-S2 · Readiness gate & activation params

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2027-09 → 2028-02 (6 months) |
| **Migration phase** | Phase 5 — Mainnet Window |
| **Milestone alignment** | gates fork S = I\* (2028-06) |
| **Status** | Not started (re-verified 2026-09-02) |

← [Back to roadmap](../README.md)

## Objective
Fix the numeric and procedural parameters that gate activation: the **readiness thresholds**
(cross-client agreement, coverage, sustained duration), the **`N′` re-anchoring cadence**,
**post-swap MPT disposal timing**, and the **select-`N` / activate-`S` procedure**. These parameters
convert the observability produced during the shadow-commitment period — the signed shadow-root
stream published by attesters — into a go/no-go decision for the swap, and they encode the mitigation
for the unvalidated-flip weak point.

## Scope — what ships
- **Readiness thresholds:** cross-client agreement **≥ X%**, coverage **≥ Y%** of the attester
  shadow-root stream, sustained **D** days — concrete values fixed and justified.
- **Go/no-go gate definition:** the three legs evaluated against the attester stream (agreement,
  coverage, sustained duration) plus **builder/relay PBT capability**, which is a hard prerequisite
  for `S` in its own right (post-swap, whoever builds a block computes the PBT root as consensus).
- **Pointer to the companion telemetry specification:** the shadow-root carrier architecture is
  settled — an out-of-consensus telemetry sidecar carrying attester-signed per-block PBT roots,
  expected to ship enabled by default in CL clients (see [B-S1](B-S1-offline-migration-eip.md)). Its
  wire format, aggregation scheme, publication timing and any EL→CL plumbing are **out of scope for
  this deliverable and for the migration EIP**; this deliverable names the companion specification the
  gate metrics are computed against and tracks its landing.
- **`N′` re-anchoring cadence** for late joiners. The EIP-8347 draft ([PR #12006](https://github.com/ethereum/EIPs/pull/12006)) proposes a starting value **`REANCHOR_CADENCE = 50400` blocks (~1 week)**; this deliverable confirms or refines it against rehearsal data, and must keep it **newer than the BAL expiry window**.
- **Post-swap MPT disposal timing** (retain until finality, then sunset).
- **Select-`N` / activate-`S` procedure:** how the finalized anchor block is chosen and how the fork is scheduled.
- **Unvalidated-flip mitigation:** specify hard-enforcing the shadow root for the final blocks before `S`, or the documented conditions under which sustained cross-client agreement is accepted instead. This is the one narrow case where enforcement is on the table; routine shadow-root publication during the shadow period stays out of consensus.

## Dependencies
- **Upstream (blocks this):** informed by [B-C4](B-C4-production-rehearsals.md) and [B-C5](B-C5-testnet-migrations-shadow-fork.md) — thresholds must be calibrated against real rehearsal/shadow-fork data.
- **Downstream (this blocks):** [B-C6](B-C6-mainnet-window.md), [B-O4](B-O4-activation-comms.md).

## Owners / teams
- Migration spec authors (activation-parameter editors).
- EF protocol support + client teams (readiness-gate sign-off).
- CL client teams (owners of the companion telemetry specification and of shipping the sidecar
  enabled by default — the source of the coverage the gate measures).
- Builder / relay liaisons (PBT-capability readiness input for the gate's builder leg).

## Exit criteria (definition of done)
- [ ] X, Y, D thresholds fixed with rationale tied to rehearsal data, resolving the §14 open parameter.
- [ ] Gate legs defined against the attester shadow-root stream (agreement, coverage, sustained days) plus builder/relay PBT capability.
- [ ] The companion telemetry specification the gate metrics are computed against is named and landed (authored by the CL side; not specified here).
- [ ] `N′` re-anchoring cadence fixed, resolving the §14 open parameter.
- [ ] Post-swap MPT disposal timing fixed, resolving the §14 open parameter.
- [ ] Select-`N` / activate-`S` procedure documented and unvalidated-flip mitigation chosen and specified.

## Risks & open questions
- This deliverable closes multiple §14 open parameters at once (readiness thresholds X/Y/D, `N′` cadence, MPT disposal timing) — see [04-migration.md §Parameters](../../knowledge-base/04-migration.md) and [open-questions.md](../../open-questions.md).
- **Unvalidated flip:** `S` activates the pre-fork block's PBT root without consensus validation; a correlated all-client bug would be undetectable either way ([04-migration.md §Known weak points](../../knowledge-base/04-migration.md)).
- **Coverage is a metric, not a rule:** shadow-root publication stays out of consensus and a `SHOULD`, so the coverage threshold is measured over voluntary reports. It depends on CL clients shipping the sidecar enabled by default; **Y** must be set against realistic default-on adoption, not against enforcement.

## References
- [knowledge-base/11-attester-telemetry-transport.md](../../knowledge-base/11-attester-telemetry-transport.md) — the companion specification's design space. Note the coupling: the publisher-selection period `N` fixes how long a full sweep of the validator set takes, so it cannot be chosen independently of the **D** sustained-observation window this deliverable fixes.
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [open-questions.md](../../open-questions.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
