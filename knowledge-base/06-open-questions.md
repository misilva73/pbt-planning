# 06 — Security Considerations & Historical Notes

> **Live open questions moved out.** The tracker of unresolved trie and migration design
> questions now lives at [../open-questions.md](../open-questions.md) (outside the
> knowledge base). This file keeps the **settled security analysis** and the older,
> **superseded** questions for historical context.

## Security considerations (current EIP-8297)

A **collision** = two distinct items deriving the same key. Keys contain three
hash-derived components, each a **full 256-bit digest** (≈ `2^128` birthday work — far
beyond reach):

- `key_hash(address)` — the account stem **and** the storage bucket.
- `key_hash(address || tree_index)` — the storage suffix (spreads groups).
- `key_hash(code_hash || tree_index)` — the code stem.

Keys of different zones differ in their first byte and cannot collide at all.

- **Content-addressed code** — two contracts with identical bytecode sharing code-zone
  leaves is *deduplication, not a collision*. Two distinct bytecodes colliding would
  need a 256-bit collision on Keccak (`code_hash`) or on `key_hash(code_hash||tree_index)`.
- **Sub-index** — a direct `% 256` mapping, not a hash. Two distinct keys share a
  sub-index only if they share a stem, in which case they are the same item.
- **Grinding** — an attacker picks slot numbers freely (own contract, or mapping keys
  in any contract that hashes them into slots), so they can grind digests that share
  `k` leading bits to deepen the tree. Without compression a `k`-node chain costs
  ~`2^(k/2)` work. **Compression** folds the run into one `BranchNode` prefix (~`k/8`
  bytes), and `d` *real* extra nodes cost ~`2^d` work. Binding the suffix to the
  **address** stops cross-contract reuse: a slot set grinded for one contract is random
  in every other.
- **Preimage injectivity** — every node preimage starts with a one-byte tag; branch
  prefixes carry an explicit bit count → the logical-node→preimage mapping is injective.

## Superseded / historical open questions (early EIP-8297 draft)

Several open questions from the rendered spec site are **superseded** by the current
EIP-8297 full-digest keys — kept here for historical context:
- Prefix length `P` (was 60 bits → ~43 colliding pairs @10¹⁰ accounts); full digest now.
- Bucket-collision handling (joint vs independent expiry) — largely moot at full width.
- Header stem constants (`0x40` storage onset, `0x80` code onset) — still
  protocol-embedded; changing them requires migrating all header stems.

The **live** trie and migration open questions (hash-function selection, witness-gas
recalibration, state expiry, readiness thresholds, artifact formats, shadow-root carrier,
etc.) now live in [../open-questions.md](../open-questions.md).

## Privacy note — "wormholes" (from the spec site)

EIP-7503 (ZK wormholes) suffers from 160-bit Ethereum addresses giving only `2^80`
birthday collisions. PBT's full-width account keys raise the birthday bound far beyond
feasibility, providing the *structural precondition* for protocol-level burn addresses
(e.g. a burn identity `H(H("worm" || secret))`). PBT does **not** implement wormholes;
this is only noted as an enabling property.
