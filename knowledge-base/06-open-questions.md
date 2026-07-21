# 06 — Open Questions & Security Considerations

## Security considerations (current, PR #11978)

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

## Open questions — the tree (EIP-8297)

- **Hash function selection** *(dominant open parameter).* Candidates:
  - **BLAKE3** — good native perf, reasonable in-circuit, well-studied, used in the
    reference impl.
  - **Poseidon2** — SNARK-friendly; needs extra spec for field encoding; under EF
    cryptography-initiative review.
  - **Keccak** — native ubiquity, weaker in-circuit.
- **Witness gas recalibration** — `WITNESS_BRANCH_COST` (EIP-4762's 1900) must be
  recalibrated for PBT's deeper branches; **values not yet fixed**.
- **State expiry & resurrection** — per-account (header stem) and per-bucket
  (`key_hash(address)` bucket) expiry is natural on the zone topology (record the
  subtree hash, prune below it). Open issues: content-addressed **code needs reference
  counting** (shared leaves) or deferral to a state sweep; **resurrection** must
  re-attach a subtree consistent with the recorded commitment. Mechanism deferred to a
  separate EIP.
- **Multi-proof compression** — compact formats that exploit shared proof branches when
  proving both account headers and storage for the same account.
- **Reserved zones** `0x02–0xFE` — future categories (e.g. nullifiers) must stay
  mutually prefix-free.

### Older open questions (pre-#11978, may be resolved by full-digest design)

Several open questions from the rendered spec site are **superseded** by PR #11978's
full-digest keys — kept here for historical context:
- Prefix length `P` (was 60 bits → ~43 colliding pairs @10¹⁰ accounts); full digest now.
- Bucket-collision handling (joint vs independent expiry) — largely moot at full width.
- Header stem constants (`0x40` storage onset, `0x80` code onset) — still
  protocol-embedded; changing them requires migrating all header stems.

## Open questions — the migration (§14 of the roadmap)

- Readiness thresholds: cross-client agreement **X%**, coverage **Y%**, sustained **D** days.
- Preimage file byte-level format.
- Snapshot chunk encoding details.
- Shadow-root carrier mechanism (how per-block PBT roots are published).
- Post-swap MPT disposal timing.
- `N′` re-anchoring cadence for late joiners.
- Proof-consumer dependencies: verification precompiles, `eth_getProof` successors.

## Privacy note — "wormholes" (from the spec site)

EIP-7503 (ZK wormholes) suffers from 160-bit Ethereum addresses giving only `2^80`
birthday collisions. PBT's full-width account keys raise the birthday bound far beyond
feasibility, providing the *structural precondition* for protocol-level burn addresses
(e.g. a burn identity `H(H("worm" || secret))`). PBT does **not** implement wormholes;
this is only noted as an enabling property.
