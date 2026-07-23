# A-T1 · EEST test-suite port

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Tests |
| **Timeline** | 2026-08 → 2027-01 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Port the Ethereum Execution Spec Tests (EEST) framework so it can fill and execute
state-transition and access-event tests against PBT (EIP-8297) state commitments instead
of the MPT. This gives every client tree implementation a shared, executable oracle:
fixtures encode the expected PBT state and, once the hash function is pinned, the expected
PBT root. It is the backbone the cyan Tests workstream builds on and the reference all
green client implementations run against.

## Scope — what ships
- EEST state-test and blockchain-test fillers adapted to emit PBT key/value state and PBT
  roots, replacing MPT trie construction with the two-node-type tree (LeafNode/BranchNode,
  canonical prefix-compressed form) from PR #11978.
- Key-embedding hooks so fillers derive tree keys via the zone/stem/sub-index scheme
  (account header stem, storage buckets, content-addressed code overflow).
- Access-event fixtures on the EIP-4762 framework carrying PBT's two required modifications:
  content-addressed overflow-code events keyed by `(zone, tree_position, sub-index)` (charged
  once per block, one witness copy), and a witness-branch-cost value left as a parameter
  until A-S2 fixes it.
- A fixture format that carries the PBT state root (parameterized on the hash function until
  the hash-function dependency lands) and CI wiring so clients consume the ported suite.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — the key/value tree,
  node types and merkelization must be converged before fillers can target them.
- **Downstream (this blocks):** [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md) — the
  cross-client conformance suite executes these fixtures. Runs in parallel with
  [A-C1](A-C1-client-tree-implementations.md), which is validated against the port.

## Owners / teams
- EEST maintainers (framework, fillers, fixture format)
- Client test leads (per-client consumer integration, CI)

## Exit criteria (definition of done)
- [ ] EEST can fill and run PBT state/blockchain tests end to end, producing fixtures with
      PBT state (root parameterized on hash until the hash-function dependency resolves).
- [ ] Access-event tests cover EIP-4762 with PBT's content-addressed-code and
      branch-cost-parameter modifications.
- [ ] At least one client implementation ([A-C1](A-C1-client-tree-implementations.md))
      consumes the ported suite in CI.
- [ ] Fixture format is documented and stable enough for [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md).

## Risks & open questions
- Hash function is not final (BLAKE3 in the reference impl only): root-bearing fixtures must
  stay hash-parameterized until the [hash-function dependency](../README.md) resolves — see
  [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md) (hash-function
  selection).
- `WITNESS_BRANCH_COST` and the rest of the witness-gas constants are not yet fixed for PBT's
  deeper branches; access-event fixtures must treat them as parameters pending
  [A-S2](A-S2-gas-cost-recalibration.md).

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [jsign/binary-tree-spec](https://github.com/jsign/binary-tree-spec) — existing Python binary-tree
  reference impl (EIP-7864, BLAKE3) that the ported fillers can cross-check against once adapted to PBT.
