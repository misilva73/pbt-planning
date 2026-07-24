# A-T3 · Genesis conformance & sync tests

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Tests |
| **Timeline** | 2027-01 → 2027-06 (6 months) |
| **Migration phase** | Phase 2 — Devnets |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Stand up a cross-client conformance suite over PBT-genesis devnets, plus PBT-native state-sync
tests, proving that independent clients agree on PBT state roots block-for-block and can sync
PBT state between each other. This is the readiness evidence that gates the H\* spec freeze:
without demonstrated multi-client agreement and working sync, the tree cannot be declared
implemented and observable at H\*.

## Scope — what ships
- A conformance harness that runs the ported EEST fixtures ([A-T1](A-T1-eest-test-suite-port.md))
  across every participating client on a shared PBT genesis, asserting identical PBT state
  roots after each block.
- Block-processing conformance covering the access-event framework (EIP-4762 with PBT's
  content-addressed-code and recalibrated-branch modifications) and canonical-tree invariants
  (two-non-empty-children branches, prefix-compressed single valid tree per state).
- PBT-native sync tests exercising [A-C2](A-C2-pbt-native-state-sync.md): a joining client
  reconstructs state and converges to the same root as the serving client.
- Devnet-driven scenarios built on [A-C3](A-C3-multiclient-pbt-genesis-devnets.md), including
  root-agreement dashboards and sustained-agreement tracking toward the readiness gate.

## Dependencies
- **Upstream (blocks this):** [A-T1](A-T1-eest-test-suite-port.md) (fixtures to execute),
  [A-C2](A-C2-pbt-native-state-sync.md) (PBT-native sync under test),
  [A-C3](A-C3-multiclient-pbt-genesis-devnets.md) (multi-client PBT-genesis devnets to run on).
- **Downstream (this blocks):** [A-S3](A-S3-eip8297-spec-freeze.md) — conformance and sync
  results are the H\*-readiness evidence for freezing the spec.

## Owners / teams
- Client test leads (per-client conformance and sync integration)
- EEST maintainers (harness, fixture execution)
- Devnet coordinators ([A-C3](A-C3-multiclient-pbt-genesis-devnets.md))

## Exit criteria (definition of done)
- [ ] All participating clients produce identical PBT roots across the conformance fixture set
      on a shared PBT genesis.
- [ ] PBT-native sync succeeds cross-client: a fresh node converges to the serving node's root.
- [ ] Sustained multi-client root agreement demonstrated on a devnet over a defined window.
- [ ] Results packaged as H\*-readiness evidence for [A-S3](A-S3-eip8297-spec-freeze.md).

## Risks & open questions
- Readiness thresholds are undefined — cross-client agreement **X%**, coverage **Y%**, sustained
  **D** days are still placeholders; see the migration open questions in
  [open-questions.md](../../open-questions.md).
- Hash function still not final until the [hash-function dependency](../README.md) resolves; conformance on a
  provisional hash must be re-confirmed if the choice changes — see
  [open-questions.md](../../open-questions.md).

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [open-questions.md](../../open-questions.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
