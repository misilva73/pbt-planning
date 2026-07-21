# A-S1 · EIP-8297 Spec Convergence

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2026-07 → 2026-11 (5 months) |
| **Migration phase** | Phase 0 — Spec Convergence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Land [EIP PR #11978](https://github.com/ethereum/EIPs/pull/11978) as the agreed base design for the Partitioned Binary Tree (EIP-8297) and resolve all outstanding client-team design contention so implementation starts from a stable, single source of truth. PR #11978 replaces the published EIP-8297 design (fixed 32-byte keys, four node types, truncated hashes) with variable-length prefix-free keys, two node types, and full-256-bit-digest keys. Getting every client team and researcher to converge on this base is the gate that unblocks the entire Trie Design thread; without it, prototypes, test vectors, and gas work would target a moving spec.

## Scope — what ships
- Merged EIP PR #11978 moving EIP-8297 to the current design:
  - **Variable-length, prefix-free keys** (≤ `MAX_KEY_LENGTH = 8192` bytes), one fixed length per zone (accounts/code 34 bytes, storage 66 bytes) to keep keys prefix-free and the tree canonical.
  - **Two node types**: `LeafNode` (commits the complete key + 32-byte value, position-independent) and `BranchNode` (compressed bit `prefix` + two non-empty children; extension/path compression folded into the prefix). No `StemNode`, `InternalNode`, or `EmptyNode`; an absent child is `None` and hashes to 32 zero bytes.
  - **Full-256-bit-digest keys**: `key_hash(address)`, `key_hash(address || tree_index)`, `key_hash(code_hash || tree_index)` are all full digests (≈2¹²⁸ birthday work), removing the old truncated-width collision analysis.
  - **Tagged merkelization**: `LEAF_TAG = 0x00`, `BRANCH_TAG = 0x01`; `leaf_hash = H(LEAF_TAG || key || value)`, `branch_hash = H(BRANCH_TAG || encode_bit_prefix(prefix) || left_hash || right_hash)`.
  - **First-byte zone identifier**: `0x00` accounts, `0x01` code overflow, `0x02`–`0xFE` reserved, `0xFF` storage.
  - **BASIC_DATA** change: `code_size` widened to 4 bytes at offset 4.
- Redrawn stem-node diagram (`assets/eip-8297/diagram.png`) — the current asset still depicts the superseded stem-node model and must be replaced with the two-node `LeafNode`/`BranchNode` model.
- Updated `requires:` header from `7612` to **`4762, 7612`**.
- A written record of resolved client-team design objections, so downstream work does not re-litigate settled points.

## Dependencies
- **Upstream (blocks this):** none (this is the Phase 0 root of Thread A).
- **Downstream (this blocks):** [A-S2](A-S2-hash-function-selection.md), [A-S3](A-S3-witness-gas-recalibration.md), [A-S4](A-S4-eip8297-spec-freeze.md), [A-C1](A-C1-client-tree-implementations.md), [B-S1](B-S1-eip7748-adaptation.md), [A-T1](A-T1-eest-test-suite-port.md), [A-T2](A-T2-tree-key-derivation-vectors.md). Paired closely with [A-O1](A-O1-tree-spec-socialization.md), which drives the same content through ACDE/ACDC.

## Owners / teams
- EIP-8297 authors (spec editors driving PR #11978).
- EL client teams (geth, Nethermind, Besu, Reth, Erigon) providing design review and sign-off.
- Ethereum Foundation research (tree design), coordinating with the [A-O1](A-O1-tree-spec-socialization.md) outreach effort.

## Exit criteria (definition of done)
- [ ] PR #11978 merged; EIP-8297 page reflects variable-length prefix-free keys, two node types, full-digest keys, and tagged merkelization.
- [ ] `requires:` updated to `4762, 7612`.
- [ ] Stem-node diagram redrawn to the `LeafNode`/`BranchNode` model.
- [ ] All client-team design objections logged and resolved (no open blocking review comments).
- [ ] Reference implementation (`insert`, `merkelize`, `encode_bit_prefix`, key derivation) matches the merged text.

## Risks & open questions
- The published EIP page and rendered spec site (cperezz.github.io/pbt-spec) still describe the pre-#11978 design (fixed 32-byte keys, 4-bit/3-bit zone prefixes, `StemNode`); reviewers may cite stale specifics. See [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md).
- The **hash function `H`** (== `key_hash`) is intentionally left open here and resolved in [A-S2](A-S2-hash-function-selection.md); convergence must not accidentally pin BLAKE3 as final just because it is the reference-impl choice. See [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- **Witness gas constants** remain unfixed at this stage (handled in [A-S3](A-S3-witness-gas-recalibration.md)); the EIP text should mark them as pending recalibration, not final.
- Reserved zones `0x02`–`0xFE` must be documented as requiring mutual prefix-freedom for any future category.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md)
- [EIP PR #11978](https://github.com/ethereum/EIPs/pull/11978); EIP-8297; requires EIP-4762, EIP-7612.
