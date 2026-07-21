# 05 — Design Evolution (read this before citing numbers)

PBT's design has changed materially across versions. Numeric details you find in older
renderings (key widths, node types, storage prefix bits) are frequently **stale**. This
file records what changed so agents don't propagate outdated specifics.

## Lineage

```
EIP-7864 (flat unified binary tree)
   │  add zones, content-addressed code, per-account storage buckets
   ▼
EIP-8297 — published draft   ← the eips.ethereum.org page & pbt-spec site render THIS
   │  PR #11978: rework keys & node types
   ▼
EIP-8297 — PR #11978 design  ← CURRENT source of truth in this KB
```

## From EIP-7864 → EIP-8297

EIP-7864 is a **flat** unified binary tree: every key is
`key_hash(address || tree_index)[:31] || sub_index`, with a dedicated `StemNode`
committing a fixed 256-leaf subtree; no zones — all of an account's data is scattered
across the tree by `tree_index`.

EIP-8297 adds:
- **Zones** — a zone prefix per key; each state category (headers, code, storage) gets
  its own region rather than being scattered uniformly.
- **Content-addressed overflow code** (chunks ≥128) keyed by `code_hash` → dedup.
- **Per-account storage buckets** for overflow storage (slots ≥64).
- Removed `MAIN_STORAGE_OFFSET` (EIP-7864 offset main storage by `256**31`); the
  storage zone separates storage structurally, so no numeric offset is needed.

The account header layout, code chunkification, and (originally) the four node types
were kept from EIP-7864.

## From published EIP-8297 → PR #11978 (the big one)

⚠️ **The eips.ethereum.org EIP-8297 page and the rendered spec site
(cperezz.github.io/pbt-spec) still describe the pre-#11978 design.** PR #11978 changes
the key scheme *and* the node types. Do not mix the two.

| Aspect | Published EIP-8297 (OLD) | PR #11978 (CURRENT) |
|--------|--------------------------|---------------------|
| Keys | Fixed **32-byte** (31-byte stem + 1 sub-index) | **Variable-length, prefix-free** (≤ `MAX_KEY_LENGTH = 8192`) |
| Zone identifier | High **4 bits** of the stem | The **first byte** of the key |
| Zone values | `0x0` acct, `0x1` code, `0x2–0x7` reserved, `0x8–0xF` storage (storage = upper half, rooted at depth 1) | `0x00` acct, `0x01` code, `0x02–0xFE` reserved, `0xFF` storage |
| Node types | **Four**: `InternalNode`, `StemNode` (fixed 256-leaf subtree), `LeafNode`, `EmptyNode` | **Two**: `LeafNode` (full key + value), `BranchNode` (compressed bit prefix + 2 children) |
| Path compression | Minimal internal nodes; no extension nodes | `BranchNode.prefix` **is** the compression (path/extension folded in) |
| Leaf position | Value indexed by sub-index within a stem subtree | Leaf commits its **complete key** → position-independent |
| Non-storage stem | 4-bit zone + **244-bit** truncated hash | zone byte + **full 256-bit** digest (`key_hash(address)`) + sub-index → 34-byte key |
| Storage stem | 1 storage bit + **60-bit** address prefix + **187-bit** suffix (`H(addr\|\|tree_index)`) | `0xFF` + **full** `key_hash(address)` + **full** `key_hash(address\|\|tree_index)` + sub-index → 66-byte key |
| `code_size` | 3 bytes at offset 5 | **4 bytes at offset 4** |
| Merkelization | `stem \|\| 0x00 \|\| hash(l\|\|r)`; leaf = `hash(value)` | tagged: `H(LEAF_TAG\|\|key\|\|value)` / `H(BRANCH_TAG\|\|encode_bit_prefix(prefix)\|\|l\|\|r)` |
| Structural boundaries | Fixed **depths** (storage@1, zones@4, bucket@61, stem@248, leaf@256) | Fixed **key-space regions** (prefix compression means no fixed depth, but the region a boundary owns is exact) |
| Security bounds | Truncated widths: acct 244-bit (2¹²²), storage prefix 60-bit (~43 colliding pairs @10¹⁰ accts), suffix 187-bit (2⁹³·⁵) | **Full 256-bit** digests everywhere → ~2¹²⁸ birthday work; storage bucket collisions negligible |

### Why the rework (per the PR)

- **Full digests** remove the truncated-width collision analysis and the ~43
  colliding-pairs storage caveat: every hash-derived component is a full 256-bit digest
  (~2¹²⁸ birthday work).
- **Position-independent leaves** mean splitting/merging branches elsewhere never
  changes an unrelated leaf's hash.
- **Prefix compression** collapses the long single-child chains that storage buckets
  would otherwise manufacture (every overflow group shares `key_hash(address)`), and
  bounds the proof-size cost of grinding.
- **Variable-length + prefix-free** keys with one fixed length per zone keep the tree
  canonical (exactly one valid tree per key/value set).

### PR #11978 metadata

- Updates `requires:` from `7612` to **`4762, 7612`**.
- Notes the diagram (`assets/eip-8297/diagram.png`) still depicts the old stem-node
  model and needs redrawing.
- Marked **Draft**; still under assessment at time of sync.

## Even-earlier variant note

The rendered spec site summary (cperezz.github.io/pbt-spec) additionally describes a
**3-bit** zone prefix variant (zones `000` accounts, `001` code, `1` storage) with a
248-bit key structure. Treat the 3-bit and 4-bit descriptions as **superseded** by the
first-byte (1-byte) zone identifier in PR #11978.

**Bottom line for agents:** cite [02-tree-structure.md](02-tree-structure.md) and
[03-key-derivation.md](03-key-derivation.md) (PR #11978 design) for current specifics.
If you read the live EIP page or spec site and it disagrees, the page is likely
pre-#11978 — verify against the PR.
