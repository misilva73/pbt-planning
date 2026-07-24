# A-C1 · Client PBT tree implementations

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2026-09 → 2027-03 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Stand up a production-track PBT (Partitioned Binary Tree / EIP-8297) tree
implementation inside each major execution client. Each client must model the
unified binary key/value tree — the two node types, canonical insertion,
bottom-up merkelization, and the full key-derivation embedding — and expose a
root that matches the reference implementation bit-for-bit. This is the
foundation every later devnet, sync, and migration deliverable builds on.

## Scope — what ships
- `LeafNode` (complete key + 32-byte value) and `BranchNode` (compressed bit
  `prefix` + two non-empty children); no extension node, no `EmptyNode`
  (`None` → 32 zero bytes).
- Canonical `insert`: big-endian bit traversal, leaf split on first differing
  bit, mid-prefix branch split, in-place value update; asserts enforcing
  prefix-freedom, per-zone key length, 32-byte values, and
  `1 ≤ len(key) ≤ MAX_KEY_LENGTH` (8192).
- `merkelize` with `LEAF_TAG`/`BRANCH_TAG` and `encode_bit_prefix`
  (2-byte big-endian bit count + MSB-first packed bits), driven by the
  hash `H` (selected by the hash-function dependency) used both for merkelization and `key_hash`.
- Full key-derivation embedding: account header stem (BASIC_DATA with the
  4-byte-at-offset-4 `code_size`, CODE_HASH, header storage 0..63, header code
  chunks 0..127), content-addressed code overflow (`CODE_ZONE`), and storage
  buckets/groups (`STORAGE_ZONE`, `key_hash(address) || key_hash(address||tree_index)`).
- Zone-aware DB / storage layout: the first key byte partitions accounts
  (`0x00`), code overflow (`0x01`), and storage (`0xFF`) into structural regions
  usable independently by sync, proving, and expiry.
- Parallel bottom-up root recomputation (no `storage_root` cross-reference in
  leaves) and passing the shared EEST-derived test vectors.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (+ CL where relevant)

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) (spec convergence), the [hash-function dependency](../README.md) (hash function `H` selection)
- **Downstream (this blocks):** [A-C2](A-C2-pbt-native-state-sync.md), [A-C3](A-C3-multiclient-pbt-genesis-devnets.md), [B-C1](B-C1-converter-prototype.md), [A-T4](A-T4-hardware-matrix-benchmarks.md)

## Exit criteria (definition of done)
- [ ] All five EL clients produce **identical PBT roots** on the shared test
      vectors and on a common synthetic state (cross-client root agreement).
- [ ] Insert enforces prefix-freedom, per-zone key length, 32-byte values, and
      the `MAX_KEY_LENGTH` bound, each with a negative test.
- [ ] Key derivation reproduces the worked test vectors for account, storage
      (header + overflow), and code (header + overflow, content-addressed) keys.
- [ ] Zero-value writes are stored as present leaves distinct from absent keys.
- [ ] Root recomputation runs as a single parallelizable bottom-up pass with no
      leaf-embedded `storage_root`.

## Risks & open questions
- Witness gas constants (recalibrated `WITNESS_BRANCH_COST` for PBT's deeper
  branches) and the final hash `H` are not yet fixed; implementations must keep
  both pluggable. See [open-questions.md](../../open-questions.md).
- Divergent DB engines across clients (hash-keyed vs raw-keyed) make a single
  canonical zone layout non-trivial; a correlated all-client merkelization bug
  would be hard to detect before cross-client agreement testing.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [open-questions.md](../../open-questions.md)
- [jsign/binary-tree-spec](https://github.com/jsign/binary-tree-spec) — candidate Python reference
  implementation clients can check tree code against (currently EIP-7864 — must be adapted to PBT's
  prefix-free keys, two node types, and zone partitioning before roots match PR #11978).
