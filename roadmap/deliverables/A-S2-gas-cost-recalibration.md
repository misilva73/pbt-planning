# A-S2 · Gas Cost Recalibration

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2028-01 → 2028-03 (3 months) |
| **Migration phase** | Deferred — post-benchmark (PBT-native gas decoupled from the swap) |
| **Milestone alignment** | decoupled from H\*/I\*; feeds a later gas-focused fork |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Author a **new gas repricing EIP** for PBT, grounded in the **benchmarked read and write
performance of the PBT trie** on client prototypes. PBT is not designed for statelessness,
so its gas schedule is not about the cost of building a witness — it is about what a state
access actually costs to serve on the new tree. The EIP has two components: a
**benchmark-based repricing of state-access opcodes** (cold/warm account and storage
access, storage writes, code-metadata reads) in the spirit of
[EIP-8038](https://eips.ethereum.org/EIPS/eip-8038), and **chunk-based code access pricing**
from [EIP-2926](https://eips.ethereum.org/EIPS/eip-2926). Both are derived from measured PBT
prototype performance, not estimates.

## Scope — what ships
- A **new PBT gas repricing EIP** covering:
  - **State-access repricing** — cold/warm account access, cold storage access (`SLOAD`),
    storage writes (`SSTORE`, including the one-time empty-slot fill), and the higher
    code-metadata read cost for `EXTCODESIZE` / `EXTCODECOPY`, all recalibrated from measured
    PBT read/write performance (EIP-8038-style empirical estimation).
  - **Chunk-based code access** — code charged per chunk touched (EIP-2926) rather than a
    flat per-byte cost, including the chunk-size choice (the 31- vs 32-byte trade-off is an
    open input; see [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md) #7).
- Spec for **content-addressed code access accounting**: overflow code chunks (chunk_id ≥ 128,
  in `CODE_ZONE`) are shared between contracts with identical bytecode, so their access
  events MUST be keyed by the `(zone, tree_position, sub-index)` **tree-key**, **not** by
  `(address, chunk)`. A shared chunk is charged once per block regardless of which contract
  triggers it. Header chunks (0..127, in the account stem) remain per-account.
- Documentation of how each cost was derived from the benchmark data, so the constants are
  defensible when the EIP goes to a gas-focused fork.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) (stable key scheme and node types) and [A-T4](A-T4-hardware-matrix-benchmarks.md) hardware-matrix benchmarks — this deliverable is **deferred until the benchmark data lands** (2027-12), so the repricing is grounded on measured state-op read/write costs rather than early estimates.
- **Downstream (this blocks):** a **later gas-focused fork**. This does **not** block the [A-S3](A-S3-eip8297-spec-freeze.md) spec freeze (which fixes only the structural parameters — keys, node types, hash `H`); gas costs are out of scope for the freeze and owned here, and PBT-native gas is deliberately decoupled from the swap.

## Owners / teams
- EIP-8297 authors and EL gas/pricing specialists (state-access and code-chunk schedule).
- EL client teams — provide read/write throughput, state-op latency, and code-chunk cost measurements from prototypes ([A-C1](A-C1-client-tree-implementations.md)) and the hardware matrix ([A-T4](A-T4-hardware-matrix-benchmarks.md)).

## Exit criteria (definition of done)
- [ ] New PBT gas repricing EIP drafted, with state-access costs derived from measured PBT read/write performance.
- [ ] Chunk-based code access priced (EIP-2926), with the chunk-size choice settled.
- [ ] Content-addressed code access spec'd: overflow chunks keyed by tree-key, charged once per block; header chunks per-account.
- [ ] Costs validated against representative worst-case and typical-block workloads.
- [ ] EIP packaged for a later gas-focused fork (superseding the provisional costs in place through the swap).

## Risks & open questions
- **The repricing values are not yet fixed** — this deliverable is what fixes them, from benchmark data. Until then, gas costs are provisional. See [knowledge-base/08-gas-and-access-events.md](../../knowledge-base/08-gas-and-access-events.md) and [open-questions.md](../../open-questions.md).
- Because **provisional** gas costs are in place through the swap while this repricing waits on [A-T4](A-T4-hardware-matrix-benchmarks.md) data (2027-07→2027-12), the network runs on provisional pricing until the later gas-focused fork adopts the benchmarked values; the provisional costs must therefore be conservative enough to be safe in the interim.
- The read/write performance the EIP prices depends on the hash function `H` (native speed) and the client DB layout, so benchmarks may need re-running if either shifts. See [open-questions.md](../../open-questions.md).
- Reference-counting for shared code leaves (state-expiry interaction) is deferred to a separate EIP but touches the content-addressed access accounting assumptions.

## References
- [knowledge-base/08-gas-and-access-events.md](../../knowledge-base/08-gas-and-access-events.md) (PBT gas model)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md) (access events / tree-key embedding)
- [open-questions.md](../../open-questions.md) (state-access gas repricing)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md) #7 (code-chunking gas evidence)
- EIP-2926 (chunk-based code merkleization); EIP-8038 (benchmark-based state-access repricing); EIP-8297.
