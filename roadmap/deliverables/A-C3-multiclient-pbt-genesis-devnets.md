# A-C3 · Multi-client PBT-genesis devnets

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2027-01 → 2027-06 (5 months) |
| **Migration phase** | Phase 2 — Devnets |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Bring up multi-client devnets that start from a **PBT genesis** — the tree is
canonical from block 0, with no MPT and no migration in the picture — and
demonstrate that all execution clients advance the chain in lockstep with
byte-identical PBT roots. This is the first cross-client integration of the
A-C1 implementations under live block production and the primary evidence that
feeds the H\* milestone.

## Scope — what ships
- A PBT-genesis specification and genesis-state generator producing an initial
  tree and root usable unchanged by every EL client.
- Standing multi-client devnets (all five ELs paired with CLs) producing and
  importing blocks over a PBT canonical state.
- Cross-client **root agreement** harness: per-block PBT roots collected across
  clients and diffed automatically, with divergence flagged and attributable to
  a client.
- EVM-invisibility validation: `SLOAD`/`SSTORE` and `EXTCODEHASH` behave
  identically to MPT-era execution (key derivation runs below the EVM;
  `code_hash` stays `keccak256(bytecode)`).
- Devnet tooling and configs contributed back so B-thread and test deliverables
  can reuse the networks.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (+ CL where relevant)

## Dependencies
- **Upstream (blocks this):** [A-C1](A-C1-client-tree-implementations.md) (client tree implementations)
- **Downstream (this blocks):** [B-T2](B-T2-full-cycle-devnet-swap.md), [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md); **feeds H\*** (2027-06)

## Exit criteria (definition of done)
- [ ] A multi-client devnet runs from PBT genesis with **all five ELs in
      per-block root agreement** over a sustained run.
- [ ] Any injected divergence is detected by the agreement harness and
      attributed to the responsible client.
- [ ] Execution semantics (`SLOAD`/`SSTORE`, `EXTCODEHASH`, gas for standard
      ops) match MPT-era behavior.
- [ ] Genesis generator output is reproducible and consumed unchanged by every
      client.

## Risks & open questions
- Cross-client agreement is the H\* readiness signal, but a **correlated
  all-client bug** would pass agreement undetected — conformance vectors (A-T3)
  must backstop it. See [open-questions.md](../../open-questions.md).
- Not-yet-final PBT gas constants could surface as subtle cross-client gas
  divergences under adversarial blocks.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
