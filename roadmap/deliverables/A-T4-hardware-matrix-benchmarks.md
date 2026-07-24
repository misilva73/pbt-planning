# A-T4 · Hardware-matrix benchmarks

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Tests |
| **Timeline** | 2027-07 → 2027-12 (6 months) |
| **Migration phase** | Phase 4 — Rehearsals |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Benchmark the client PBT tree implementations across the EIP-7870 hardware requirements matrix,
measuring tree-operation throughput, branch-depth profile, witness sizes and verification cost,
and memory/disk footprint on representative hardware tiers. The measured witness-branch costs
and depth profile feed the gas recalibration ([A-S2](A-S2-gas-cost-recalibration.md)), and
the throughput/resource numbers size the production rehearsals ([B-C4](B-C4-production-rehearsals.md)).

## Scope — what ships
- A benchmark harness driving the client implementations ([A-C1](A-C1-client-tree-implementations.md))
  across EIP-7870 hardware tiers, with reproducible workloads sourced from the PBT-genesis
  devnets ([A-C3](A-C3-multiclient-pbt-genesis-devnets.md)).
- Tree-operation metrics: insertion/update and merkelization throughput, observed branch-depth
  distribution (PBT's branches are deeper than Verkle's), and effect of prefix compression on
  grinded/pathological key sets.
- Witness metrics: witness sizes and actual branch-opening cost against the EIP-4762
  `WITNESS_BRANCH_COST = 1900` baseline, isolating content-addressed overflow-code chunks
  (charged once per block, single witness copy) from per-account header chunks.
- Resource metrics: memory, disk and I/O per tier, reported as inputs to A-S2 recalibration and
  B-C4 rehearsal sizing.

## Dependencies
- **Upstream (blocks this):** [A-C1](A-C1-client-tree-implementations.md) (implementations to
  benchmark), [A-C3](A-C3-multiclient-pbt-genesis-devnets.md) (representative devnet workloads).
- **Downstream (this blocks):** [A-S2](A-S2-gas-cost-recalibration.md) (recalibrated witness
  gas constants from measured depth/cost), [B-C4](B-C4-production-rehearsals.md) (rehearsal
  hardware sizing).

## Owners / teams
- Client test leads / client performance engineers
- EEST maintainers (harness, workload fixtures)
- Migration rehearsal owners ([B-C4](B-C4-production-rehearsals.md)) as consumers

## Exit criteria (definition of done)
- [ ] Reproducible benchmark results published for every EIP-7870 hardware tier across
      participating clients.
- [ ] Measured branch-depth profile and witness-branch cost delivered to
      [A-S2](A-S2-gas-cost-recalibration.md) in a form usable for recalibration.
- [ ] Resource/throughput envelopes delivered to [B-C4](B-C4-production-rehearsals.md) for
      rehearsal sizing.
- [ ] Content-addressed vs per-account code-chunk costs reported separately.

## Risks & open questions
- The hash function is unresolved and directly drives native performance — BLAKE3 (good native
  perf) vs Poseidon2 (SNARK-friendly, slower native) vs Keccak; benchmarks may need re-running
  once the [hash-function dependency](../README.md) resolves. See
  [open-questions.md](../../open-questions.md).
- Witness-gas constants are not yet fixed; these benchmarks are the evidence that fixes them via
  [A-S2](A-S2-gas-cost-recalibration.md) — see
  [open-questions.md](../../open-questions.md).

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [open-questions.md](../../open-questions.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
