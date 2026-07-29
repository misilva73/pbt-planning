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
Drive the **shadow-commitment period** in the ecosystem: get **CL clients shipping the
attester telemetry sidecar enabled by default**, so that **attesters compute and publish
the PBT root of each block's post-state, signed with their validator key**, while
consensus still runs on the MPT — and bring builders, relays and supporting infrastructure
to the state needed to pass the **readiness gate**. Shadow commitment makes conversion
correctness visible per block, publicly and attributably: signing makes each report
attributable and verifiable, and a missing or late root counts against **coverage**
metrics rather than as a divergence, preserving interpretability. Publication is **out of
consensus** and never a block-validity condition, so the observability signal never puts
PBT construction back on the consensus-critical path.

## Scope — what ships
- **CL client adoption of the companion specification**: the **out-of-consensus telemetry
  sidecar** that carries shadow roots, **shipped enabled by default**, so coverage comes
  from ordinary validator operation rather than an opt-in program. Default-on is an
  operational commitment, not a protocol requirement. The sidecar's wire format,
  aggregation scheme, publication timing and any EL→CL plumbing are **out of scope here**
  and fixed in the companion specification pointed at by
  [B-S2](B-S2-readiness-gate-activation-params.md).
- Ecosystem drive toward the **readiness-gate thresholds**: cross-client agreement **≥ X%**
  sustained over **D** days, coverage **≥ Y%**, and builder/relay PBT readiness.
- **Builder / relay PBT capability before `S`** — a hard prerequisite, independent of the
  observability signal: post-swap, whoever builds a block computes the PBT root as
  consensus, so an MPT-only builder produces invalid blocks from the first post-fork slot.
- Public **coverage / cross-client-agreement dashboards** so the gate status is
  transparent and shadow-root reports are attributable to the validator keys that signed
  them.
- Operator-facing guidance for validators and staking providers: what the sidecar does,
  why it is on by default, and why leaving it enabled is what produces the coverage the
  gate is measured against.

## Stakeholders
- **CL client teams** (implement the companion specification and ship the telemetry
  sidecar enabled by default).
- **Node operators / validators** and staking providers — the attesters whose ordinary
  operation produces the signed shadow-root stream.
- **Block builders** and **relays** (must be PBT-capable before `S`; they no longer carry
  the observability signal).
- Infrastructure and tooling providers hosting the dashboards.
- Client teams whose PBT roots must agree cross-client.

## Dependencies
- **Upstream (blocks this):** [B-S2](B-S2-readiness-gate-activation-params.md) (readiness-gate
  thresholds X/Y/D and the pointer to the companion telemetry specification),
  [B-C5](B-C5-testnet-migrations-shadow-fork.md) (testnet migrations / shadow fork that
  exercise attester shadow-root publication first).
- **Downstream (this blocks):** feeds [B-C6](B-C6-mainnet-window.md) (the mainnet window
  cannot pass its readiness gate without ecosystem shadow-root coverage).

## Exit criteria (definition of done)
- [ ] CL clients implementing the companion specification ship the telemetry sidecar
      **enabled by default**, so no opt-in is required of the operator.
- [ ] Attesters representing **≥ Y%** coverage publish per-block PBT shadow roots signed
      with their validator key; missing or late roots count against coverage, not divergence.
- [ ] Cross-client agreement **≥ X%** sustained for **D** days (thresholds from
      [B-S2](B-S2-readiness-gate-activation-params.md)) — the readiness gate passes.
- [ ] Public coverage / agreement dashboard live; reports attributable to the validator
      keys that signed them.
- [ ] Builders and relays covering the bulk of block production confirm **PBT capability**
      ahead of `S`, since they compute the PBT root as consensus from the first post-fork slot.

## Risks & open questions
- **Coverage rests on default-on adoption, not enforcement:** publication stays a `SHOULD`
  out of consensus, so coverage is a metric over voluntary reports. If clients ship the
  sidecar off by default or operators disable it, coverage can fall short of **Y%** even
  with a correct conversion. Mitigation: default-on in CL clients is the commitment this
  deliverable tracks, and pre-swap divergence is harmless and self-detectable.
- **Companion-specification timing:** the sidecar's wire format, aggregation scheme,
  publication timing and EL→CL plumbing are fixed in a companion specification rather than
  in the migration EIP; CL implementation cannot finalize until it lands, which is a
  schedule risk for the shadow period opening at H\*.
- **Unvalidated flip input:** `S` activates the pre-fork block's PBT root without consensus
  validation; strong shadow-root coverage and sustained cross-client agreement are what
  make that flip trustworthy, so low coverage directly weakens the swap's safety.
- **Builder / relay readiness is a separate failure mode:** it is a hard `S` prerequisite
  (an MPT-only builder produces invalid blocks post-fork) and must be confirmed
  independently of shadow-root coverage, which no longer depends on builders at all.
- **Validator observability gap — closed by design:** sourcing roots from attesters rather
  than from whoever builds the block is what makes the measurement cover the validating
  majority; earlier framing that measured only block producers no longer applies.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md) (Shadow commitment & observability; Readiness gates; Known weak points)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md) (Shadow root / shadow commitment glossary)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
