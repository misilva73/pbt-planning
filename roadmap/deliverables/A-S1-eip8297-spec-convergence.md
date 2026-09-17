# A-S1 · EIP-8297 Spec Convergence

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2026-07 → 2026-09 (3 months) |
| **Migration phase** | Phase 0 — Spec Convergence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight** (as of 2026-09-17) — the EIP text has now been stable for six weeks (unchanged since 2026-08-06) and **four** clients are implementing against it; the formal sign-off record is still missing |

← [Back to roadmap](../README.md)

## Objective
Converge every client team and researcher on the current [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) design as the agreed base for the Partitioned Binary Tree, and resolve all outstanding client-team design contention so implementation starts from a stable, single source of truth. The current EIP-8297 design uses variable-length prefix-free keys, two node types, and full-256-bit-digest keys (an earlier draft had fixed 32-byte keys, four node types, and truncated hashes). Getting everyone to converge on this base is the gate that unblocks the entire Trie Design thread; without it, prototypes, test vectors, and gas work would target a moving spec.

## Scope — what ships
- Sign-off on the current EIP-8297 base design:
  - **Variable-length, prefix-free keys** (≤ `MAX_KEY_LENGTH = 8192` bytes), one fixed length per zone (accounts/code 34 bytes, storage 66 bytes) to keep keys prefix-free and the tree canonical.
  - **Two node types**: `LeafNode` (commits the complete key + 32-byte value, position-independent) and `BranchNode` (compressed bit `prefix` + two non-empty children; extension/path compression folded into the prefix). No `StemNode`, `InternalNode`, or `EmptyNode`; an absent child is `None` and hashes to 32 zero bytes.
  - **Full-256-bit-digest keys**: `key_hash(address)`, `key_hash(address || tree_index)`, `key_hash(code_hash || tree_index)` are all full digests (≈2¹²⁸ birthday work), removing the old truncated-width collision analysis.
  - **Tagged merkelization**: `LEAF_TAG = 0x00`, `BRANCH_TAG = 0x01`; `leaf_hash = H(LEAF_TAG || key || value)`, `branch_hash = H(BRANCH_TAG || encode_bit_prefix(prefix) || left_hash || right_hash)`.
  - **First-byte zone identifier**: `0x00` accounts, `0x01` code overflow, `0x02`–`0xFE` reserved, `0xFF` storage.
  - **BASIC_DATA** change: `code_size` widened to 4 bytes at offset 4.
- Redrawn stem-node diagram (`assets/eip-8297/diagram.png`) if it still depicts the superseded stem-node model rather than the two-node `LeafNode`/`BranchNode` model.
- Confirmation of the EIP `requires:` header. **It is now empty** — EIP-8297 carries *no* `requires` field. An earlier draft required **`7612`** (the Verkle-era overlay-tree transition mechanism); that dependency was dropped when the migration was pointed at EIP-8347 instead (2026-07-31), and this deliverable's original exit criterion asking to confirm `7612` is therefore obsolete. PBT's gas repricing is a separate benchmark-based EIP and is not part of the base spec's `requires` either.
- A written record of resolved client-team design objections, so downstream work does not re-litigate settled points.

## Dependencies
- **Upstream (blocks this):** none (this is the Phase 0 root of Thread A).
- **Downstream (this blocks):** [A-S2](A-S2-gas-cost-recalibration.md), [A-S3](A-S3-eip8297-spec-freeze.md), [A-C1](A-C1-client-tree-implementations.md), [B-S1](B-S1-offline-migration-eip.md), [A-T1](A-T1-eest-test-suite-port.md), [A-T2](A-T2-tree-key-derivation-vectors.md). Paired closely with [A-O1](A-O1-tree-spec-socialization.md), which drives the same content through ACDE/ACDC.

## Owners / teams
- EIP-8297 authors / spec editors.
- EL client teams (geth, Nethermind, Besu, Reth, Erigon) providing design review and sign-off.
- Ethereum Foundation research (tree design), coordinating with the [A-O1](A-O1-tree-spec-socialization.md) outreach effort.

## Exit criteria (definition of done)
- [ ] Client teams and researchers confirm the current EIP-8297 design (variable-length prefix-free keys, two node types, full-digest keys, tagged merkelization) as the convergence base.
- [x] `requires:` confirmed — **no `requires` field**; the former `7612` dependency is gone (2026-07-31, [PR #12027](https://github.com/ethereum/EIPs/pull/12027)).
- [ ] Stem-node diagram redrawn to the `LeafNode`/`BranchNode` model (if not already).
- [ ] All client-team design objections logged and resolved (no open blocking review comments).
- [ ] Reference implementation (`insert`, `merkelize`, `encode_bit_prefix`, key derivation) matches the merged text.

## Risks & open questions
- The third-party rendered spec site (cperezz.github.io/pbt-spec) may still describe the earlier draft (fixed 32-byte keys, 4-bit/3-bit zone prefixes, `StemNode`); reviewers may cite stale specifics. See [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md).
- The **hash function `H`** (== `key_hash`) is intentionally left open here and resolved by the [hash-function dependency](../README.md) (external, due end 2026); convergence must not accidentally pin BLAKE3 as final just because it is the reference-impl choice. **This risk is now live, not hypothetical, and grew with the field:** all **four** devnet clients hardcode or default to BLAKE3 and the devnet's genesis pins roots computed with it, so BLAKE3 is accumulating de-facto status through shipped code and fixtures — each new implementation raises the cost of choosing anything else. See [open-questions.md](../../open-questions.md#hash-function-selection--the-dominant-open-parameter).
- **Convergence is being tested by implementation rather than by sign-off, and it is finding real disagreement.** Erigon's [PR #22942](https://github.com/erigontech/erigon/pull/22942) passes 67 of 70 EIP-8297 fixtures and *deliberately* diverges on the rest: it keeps zero-valued leaves as distinct from absent keys (against the current text, which requires deletion), refuses account removal outright on the grounds that "EIP-8297 defines no removal", and retains code chunks above a shortened redeploy's length — making the tree a function of history rather than of current state. The reference itself is described as having two providers that disagree on removal. Whatever this deliverable's sign-off record ends up saying, **account deletion and zeroization semantics are where it has to be unambiguous**, and today they are not.
- **Gas costs** are out of scope for the base design and are owned by the separate PBT gas repricing EIP ([A-S2](A-S2-gas-cost-recalibration.md)); the base EIP text should not pin state-access or code-chunk costs.
- Reserved zones `0x02`–`0xFE` must be documented as requiring mutual prefix-freedom for any future category.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md)
- [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) — no `requires` field.
