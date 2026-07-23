# B-O3 · Shadow roots & ecosystem readiness

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Ecosystem outreach |
| **Timeline** | 2027-09 → 2028-04 (8 months) |
| **Migration phase** | Phase 4 → 5 — Rehearsals through Mainnet Window |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Drive the **shadow-commitment period** in the ecosystem: get **builders and relays
computing and publishing per-block PBT shadow roots** while consensus still runs on the
MPT, and bring builder/relay and supporting infrastructure to the state needed to pass
the **readiness gate**. Shadow commitment makes conversion correctness visible per block,
publicly and attributably — omissions count against **coverage** metrics rather than
divergence, preserving interpretability.

## Scope — what ships
- Builder/relay integration so **per-block PBT shadow roots are published** during the
  pre-swap period, on the carrier mechanism defined by
  [B-S2](B-S2-readiness-gate-activation-params.md).
- Ecosystem drive toward the **readiness-gate thresholds**: cross-client agreement **≥ X%**
  sustained over **D** days, coverage **≥ Y%**, and builder/relay ecosystem readiness.
- Public **coverage / cross-client-agreement dashboards** so the gate status is
  transparent and shadow-root omissions are attributed to producers.
- A designed **proposer-signed post-import sidecar** fallback path, socialized with
  validating node operators to close the validator-observability gap.

## Stakeholders
- **Block builders** and **relays** (the parties that publish shadow roots).
- **Node operators / validators** (for the proposer-signed sidecar fallback).
- Infrastructure and tooling providers hosting the dashboards and carrier plumbing.
- Client teams whose PBT roots must agree cross-client.

## Dependencies
- **Upstream (blocks this):** [B-S2](B-S2-readiness-gate-activation-params.md) (readiness-gate
  thresholds X/Y/D and the shadow-root carrier mechanism),
  [B-C5](B-C5-testnet-migrations-shadow-fork.md) (testnet migrations / shadow fork that
  exercise shadow-root production first).
- **Downstream (this blocks):** feeds [B-C6](B-C6-mainnet-window.md) (the mainnet window
  cannot pass its readiness gate without ecosystem shadow-root coverage).

## Exit criteria (definition of done)
- [ ] Builders/relays covering **≥ Y%** of blocks publish per-block PBT shadow roots.
- [ ] Cross-client agreement **≥ X%** sustained for **D** days (thresholds from
      [B-S2](B-S2-readiness-gate-activation-params.md)) — the readiness gate passes.
- [ ] Public coverage / agreement dashboard live; omissions attributed to producers and
      counted against coverage, not divergence.
- [ ] Proposer-signed sidecar fallback specified and available to validating node operators.

## Risks & open questions
- **Validator observability gap** (04-migration.md weak points): the builder stream
  measures block *producers*, not the validating majority, so coverage can look healthy
  while validators are unobserved. Mitigation: pre-swap divergence is harmless and
  self-detectable, and the **proposer-signed post-import sidecar** is the designed fallback.
- **Unvalidated flip input:** `S` activates the pre-fork block's PBT root without consensus
  validation; strong shadow-root coverage and sustained cross-client agreement are what
  make that flip trustworthy, so low coverage directly weakens the swap's safety.
- **§14 open — shadow-root carrier mechanism:** the exact carrier is still open in
  [B-S2](B-S2-readiness-gate-activation-params.md); builder/relay integration cannot finalize
  until it is fixed.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md) (Shadow commitment & observability; Readiness gates; Known weak points)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md) (Shadow root / shadow commitment glossary)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
