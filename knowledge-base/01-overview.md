# 01 — PBT Overview

> PBT = **Partitioned Binary Tree**. The name has also appeared as "Partitioned
> Binary Trie"; the current spec calls it a *tree*.

## The problem PBT solves

Ethereum's state today lives in **hexary (arity-16) Merkle Patricia Tries (MPT)**.
This design has several properties that hurt future scaling, especially
**stateless clients and validity (SNARK) proofs**:

1. **Proofs are large.** MPT uses RLP encoding, Keccak hashing, and a
   "tree-of-tries" structure. A single account branch is roughly
   `15 * 32 * 12 = 5760` bytes (15 sibling hashes × 32 bytes × ~12 levels).
   A worst-case block touching one byte of many distinct unchunked codes can need
   `≈ 1.8 GB` of witness data.
2. **Sequential root computation.** Each account leaf embeds a `storage_root` hash,
   so a storage trie must be fully computed before the account trie can be updated.
   Root recomputation is serialized rather than parallel.
3. **Not proving-friendly.** Variable-arity branching, RLP, and Keccak are awkward
   in circuits; code cannot be proven in segments (chunks).
4. **Curve-based alternatives (Verkle) are not post-quantum.** Verkle relies on
   elliptic-curve cryptography, which NIST guidance calls to retire by 2030.

## What PBT does about it

- **One unified binary tree.** Account trie + storage tries + code merged into a
  single key/value tree. One abstraction for DB access, caching, sync, proofs.
- **Arity 2.** Binary branching minimizes average proof branch length. For
  `N = 2^24` elements a branch is ~768 bytes (arity 2) vs ~1152 (arity 4).
- **No `storage_root` inside leaves.** An account's nonce and one of its storage
  slots are *independent* writes. The root recomputes in a single bottom-up pass;
  branches meet near the root — enabling parallelism across zones, accounts, and stems.
- **Zone partitioning.** The first byte of every key labels a category (account
  headers / code / storage). This gives **structural boundaries**: a known key-space
  region is always one category, so a node can sync, prove, or expire one category
  without touching the rest.
- **Content-addressed code.** Code beyond the first chunks is keyed by `code_hash`,
  so thousands of contracts cloned from the same factory bytecode **share** leaves
  (deduplication) instead of each storing a copy.
- **Hash-only ⇒ post-quantum.** The tree depends only on a hash function, not on
  elliptic curves, so it stays secure against quantum adversaries.

## Design goals (why the shape is what it is)

- **Small witnesses** — proof size scales with `siblings × log_arity(N)`, minimized at arity 2.
- **SNARK friendliness** — no RLP, no variable-arity branching; the dominant cost is
  the merkelization hash, chosen to be efficient in and out of circuit.
- **Parallel root computation** — no cross-reference hashing inside leaf values.
- **Structural boundaries** — zones enable state expiry and partial statelessness.
- **EVM-invisibility** — contracts still address storage by 256-bit slot numbers via
  `SLOAD`/`SSTORE`; key derivation runs *inside the client, below the EVM*. No
  contract/Solidity/Yul changes. `EXTCODEHASH` is unchanged (`code_hash` is still
  `keccak256(bytecode)`, independent of the tree's merkelization hash).

## Glossary

- **PBT** — Partitioned Binary Tree; the binary state tree defined by EIP-8297.
- **MPT** — Merkle Patricia Trie; Ethereum's current hexary state structure.
- **Zone** — a category of state identified by the **first byte** of a key
  (`0x00` accounts, `0x01` code overflow, `0xFF` storage; `0x02`–`0xFE` reserved).
- **Stem** — the shared key prefix that groups leaves accessed together (a key's
  zone byte + hash-derived tree position). Up to 256 leaves share a stem, indexed by
  the final **sub-index** byte.
- **Sub-index** — the last byte of a key (0–255); selects a leaf within a stem's group.
- **Leaf node** — holds the complete key + a 32-byte value. Position-independent.
- **Branch node** — an internal node with a compressed bit **prefix** and two children.
- **Prefix-free keys** — no key may be a prefix of another key; enforced so each
  key/value set has exactly one valid tree.
- **`key_hash`** — the tree's hash applied to derive key positions (same hash as
  merkelization `H`); BLAKE3 in the reference implementation.
- **Tree index** — which 256-slot group a storage slot or code chunk falls into
  (`slot // 256`).
- **BASIC_DATA** — the packed header leaf holding version, nonce, balance, code_size.
- **BAL** — Block-Level Access List (EIP-7928); a per-block list of state accesses/writes.
- **Anchor block N / Fork S** — migration parameters: `N` is the block whose state is
  converted; `S` is the hard fork at which PBT becomes canonical.
- **Shadow root / shadow commitment** — a PBT root published per block *before* the
  swap, while consensus still runs on the MPT, to make conversion correctness visible.

See [02-tree-structure.md](02-tree-structure.md) for the data structure and
[03-key-derivation.md](03-key-derivation.md) for how keys are computed.
