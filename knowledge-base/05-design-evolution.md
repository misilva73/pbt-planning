# 05 — Design Evolution (read this before citing numbers)

PBT's design has changed materially across versions. Numeric details you find in older
renderings (key widths, node types, storage prefix bits) are frequently **stale**. This
file records what changed so agents don't propagate outdated specifics.

## Lineage

```
EIP-7864 (flat unified binary tree)
   │  add zones, content-addressed code, per-account storage buckets
   ▼
EIP-8297 — early draft   ← the third-party pbt-spec site may still render THIS
   │  rework keys & node types
   ▼
EIP-8297 — current        ← CURRENT source of truth (published at eips.ethereum.org)
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

## From the early EIP-8297 draft → current EIP-8297 (the big one)

⚠️ **The third-party rendered spec site (cperezz.github.io/pbt-spec) may still describe
the early EIP-8297 draft.** The current design reworked the key scheme *and* the node
types; the table below is the diff. Do not mix the two.

| Aspect | Early EIP-8297 draft (OLD) | Current EIP-8297 |
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

### Why the rework

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

### EIP-8297 metadata

- **No `requires:` field** as of the current text. An earlier note here recorded
  `requires: 7612` (the Verkle-era overlay-tree transition mechanism); that dependency
  has since been **dropped** — migration is no longer coupled to the online-overlay
  approach and is instead specified independently in
  [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) (offline conversion), which PBT's
  own "Fork" section points to by name without a formal `requires`. PBT's gas repricing
  remains a separate, not-yet-drafted benchmark-based EIP.
- The diagram (`assets/eip-8297/diagram.png`) may still depict the old stem-node
  model and need redrawing.
- Marked **Draft**, Standards Track: Core.

## Further rework: code is now uniformly content-addressed (post-July-2026)

A design step **after** the key/node-type rework above, so it is not yet reflected in
older renderings of file 05's table: the account header stem no longer holds *any* code
chunks. An earlier version of EIP-8297 (matching [03-key-derivation.md](03-key-derivation.md)'s
older `CODE_OFFSET = 128` split) kept the first 128 chunks (~4 KB) of a contract's code
per-account in the header stem, sub-indices 128–255, and only "overflow" chunks beyond
that were content-addressed by `code_hash` in `CODE_ZONE`. The current text removes that
split entirely: **every** code chunk, from chunk 0, is content-addressed in `CODE_ZONE`
via `get_tree_key_for_code_chunk(code_hash, chunk_id)` — no `address` parameter, no
`CODE_OFFSET` constant. The header's sub-indices in use are now exactly
`BASIC_DATA_LEAF_KEY`, `CODE_HASH_LEAF_KEY`, and the `HEADER_STORAGE_OFFSET` range; no
other sub-index is defined. One consequence: because *all* code is now shared rather than
only an overflow tail, the account/code-hash deletion rule ("remove a `CODE_ZONE` leaf
only if no resulting-state account shares the same `code_hash`") applies universally, not
just to overflow chunks — see
[02-tree-structure.md § Zero values and deletion](02-tree-structure.md#zero-values-and-deletion).

## Further rework: zero-value leaves now delete (post-July-2026)

Also **after** the key/node-type rework: an earlier EIP-8297 text kept a zero-valued leaf
present and distinct from an absent key (inherited from Verkle, motivated by multi-tree
state expiry). This directly contradicted EIP-8347's BAL-replay rules, which require
deletion. EIP-8297 has since been revised to require deletion on zeroization, matching
EIP-8347 and `ethereum.state_pbt`. Full history and the case for this outcome:
[10-zero-value-leaves-and-deletion.md](10-zero-value-leaves-and-deletion.md).

## Further rework: delegation indicators move into the account header (post-August-2026)

Merged 2026-08-06 via [PR #12114](https://github.com/ethereum/EIPs/pull/12114) (EIP-8297)
and [PR #12115](https://github.com/ethereum/EIPs/pull/12115) (EIP-8347). Before this
change, an EIP-7702 delegation indicator (the 23-byte `0xef0100 || target` an EOA's code
is set to) was treated like ordinary code: chunked into `CODE_ZONE` and content-addressed,
shared across every account delegating to the same target. Two problems drove this
rework:

1. **Locality.** Content-addressing a delegation leaf meant deleting it required
   reference-counting against every other account that might share it (the Besu team
   flagged that this can't be determined from block-local data alone, unlike ordinary
   code deletion where the same check at least stays within one converter/replay pass).
2. **Dual-check correctness.** EIP-8347's Check 2 verifies bytecode by reassembling it
   from `CODE_ZONE` chunks and re-hashing to `code_hash`. A 23-byte delegation indicator
   isn't real bytecode in that sense, so the reassembly either fails or needs a special
   case — and because mainnet already has EIP-7702-delegated accounts in every recent
   block, this wasn't a hypothetical: **every anchor-block snapshot would fail
   verification** without a fix.

The fix adds `DELEGATION_LEAF_KEY = 2` as a new header-stem sub-index, mutually exclusive
with `CODE_HASH_LEAF_KEY`: a delegated account holds exactly one of the two leaves, never
both, and never any `CODE_ZONE` chunk leaves. Value-based (rather than key-based)
discriminators between the two leaf types were considered and rejected as vulnerable to
grinding. Full current mechanics: [03-key-derivation.md § Delegation
indicators](03-key-derivation.md#delegation-indicators-eip-7702) (key derivation, value
layout) and [04-migration.md § Delegation
indicators](04-migration.md#delegation-indicators-eip-7702) (converter, dual-check,
BAL-replay).

## Even-earlier variant note

The rendered spec site summary (cperezz.github.io/pbt-spec) additionally describes a
**3-bit** zone prefix variant (zones `000` accounts, `001` code, `1` storage) with a
248-bit key structure. Treat the 3-bit and 4-bit descriptions as **superseded** by the
first-byte (1-byte) zone identifier in the current EIP-8297.

**Bottom line for agents:** cite [02-tree-structure.md](02-tree-structure.md) and
[03-key-derivation.md](03-key-derivation.md) (current EIP-8297 design) for current
specifics. If you read the third-party spec site and it disagrees, it is likely showing
the early draft — verify against [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297).
