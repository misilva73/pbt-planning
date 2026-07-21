# A-S2 · Hash Function Selection

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2026-07 → 2027-02 (8 months) |
| **Migration phase** | Phase 0-1 |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Choose the tree's hash function `H` — which is the *same* function used both for merkelization and for `key_hash` (key derivation) — from among **BLAKE3**, **Poseidon2**, and **Keccak**. This is the **dominant open parameter** of EIP-8297: it trades native performance against in-circuit / SNARK proving cost against cryptographic maturity, and it blocks every merkelization-dependent implementation and all pinned test vectors (key derivation, merkelization roots) that must be byte-exact across clients.

## Scope — what ships
- A decision and rationale selecting `H` (== `key_hash`) for EIP-8297, with the chosen function written into the spec.
- Comparative evaluation across the three candidates:
  - **BLAKE3** — good native performance, reasonable in-circuit cost, well-studied; already the reference-implementation choice.
  - **Poseidon2** — SNARK-friendly (cheap in-circuit), but requires an additional **field-encoding specification** and review by the EF cryptography initiative before it can be pinned.
  - **Keccak** — native ubiquity and existing hardware/tooling, but weaker in-circuit performance.
- If Poseidon2 is selected: a field-encoding spec (how 32-byte tags/keys/values and digests map to/from field elements) reviewed and signed off by the EF cryptography initiative.
- Benchmark data comparing native hashing throughput vs in-circuit constraint counts for the tree's `leaf_hash`/`branch_hash` shapes.
- Confirmation that the choice of `H` does **not** affect `EXTCODEHASH`: `code_hash` remains `keccak256(bytecode)` independent of `H`.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) (stable node/merkelization shape to hash over).
- **Downstream (this blocks):** [A-T2](A-T2-tree-key-derivation-vectors.md) (golden vectors need the final hash), [A-C1](A-C1-client-tree-implementations.md), [A-C3](A-C3-multiclient-pbt-genesis-devnets.md), [B-C3](B-C3-snapshot-production-pipeline.md) (byte-canonical snapshots depend on the root hash), [A-S4](A-S4-eip8297-spec-freeze.md).

## Owners / teams
- EIP-8297 authors (spec editors).
- **EF cryptography initiative** — leads candidate evaluation and, for Poseidon2, the field-encoding spec and security review.
- EL client teams — provide native performance benchmarks; ZK/proving teams provide in-circuit cost figures.

## Exit criteria (definition of done)
- [ ] A single `H` selected and justified against native perf, in-circuit cost, and maturity.
- [ ] If Poseidon2: field-encoding spec written and reviewed/approved by the EF cryptography initiative.
- [ ] Benchmark results (native throughput + in-circuit constraints) published for the decision record.
- [ ] Spec text updated so `H` == `key_hash` is named (no longer "BLAKE3 in the reference impl").
- [ ] Downstream owners ([A-T2](A-T2-tree-key-derivation-vectors.md), [A-C1](A-C1-client-tree-implementations.md)) confirm they can pin cross-client vectors against the choice.

## Risks & open questions
- **This is explicitly the dominant open parameter** — until it is fixed, all hash outputs in the KB are unpinned and no merkelization root or key-derivation vector is final. See [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- Poseidon2's field encoding adds spec surface and review latency; a late switch to Poseidon2 after clients build against BLAKE3 would invalidate vectors and prototypes.
- Post-quantum posture: all three are hash-only (no elliptic curves), preserving PBT's post-quantum property; selection should not reintroduce curve dependence.
- Timing risk: this window (through 2027-02) must close before the spec freeze [A-S4](A-S4-eip8297-spec-freeze.md) and comfortably before H\* (2027-06).

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md) (SNARK-friendliness, post-quantum rationale)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md) (merkelization / tagged hashing)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md) (`key_hash` == `H`)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md) (hash function selection)
- EIP-8297; EF cryptography initiative (Poseidon2 review).
