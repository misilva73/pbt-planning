# A-T2 · Tree & key-derivation vectors

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Tests |
| **Timeline** | 2026-07 → 2026-12 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Produce canonical, machine-checkable test vectors for PBT's tree structure and key
derivation per PR #11978: merkelization, insertion/split into canonical form, bit-prefix
encoding, and the full zone/stem/sub-index embedding of Ethereum state. These vectors are
the first concrete evidence artifact and the reference clients ([A-C1](A-C1-client-tree-implementations.md))
check their tree code against. Because the tree hash function is not yet chosen, the initial
vectors are **structure-only** — they pin key bytes, node shapes and preimage layouts, and
defer digest/root values until the hash is fixed by [A-S2](A-S2-hash-function-selection.md).

## Scope — what ships
- **Key-derivation vectors** covering the worked examples in the key-derivation spec:
  account `BASIC_DATA` (`0x00 || H(A) || 0x00`, 34 bytes), header-resident storage slot 5,
  storage-zone slot 1000 (`0xFF || H(A) || H(A||3) || 0xE8`, 66 bytes), header code chunk 5,
  and overflow code chunk 300 (`0x01 || H(C||0) || 0xAC`), including per-zone length asserts.
- **Embedding vectors** for the zone map (`0x00` account, `0x01` code, `0xFF` storage), the
  header stem offsets (`HEADER_STORAGE_OFFSET=64`, `CODE_OFFSET=128`, `STEM_SUBTREE_WIDTH=256`),
  storage buckets (`key_hash(address)` prefix + `key_hash(address||tree_index)` suffix), and
  content-addressed code stems, with the group-0 exception (storage-zone slots 64..255 only).
- **Tree-operation vectors:** insertion, leaf split, and branch split producing the single
  canonical tree for a key/value set; two-non-empty-children invariant; zero-value leaf
  distinct from an absent key.
- **Encoding vectors:** `encode_bit_prefix` (2-byte big-endian bit count + MSB-first padded
  bits), `LEAF_TAG`/`BRANCH_TAG` preimage layouts, and prefix-freedom / length-bound rejection
  cases (`MAX_KEY_LENGTH = 8192`).
- Structure-only now; a hash-parameterized layer that fills in `H(...)` digests and roots once
  A-S2 lands.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — vectors track the
  converged PR #11978 constants and algorithms. Hash outputs additionally need
  [A-S2](A-S2-hash-function-selection.md) before they can be pinned.
- **Downstream (this blocks):** [A-C1](A-C1-client-tree-implementations.md) — client tree
  implementations validate key derivation and merkelization against these vectors.

## Owners / teams
- EEST maintainers / spec authors (vector generation from the reference implementation)
- Client test leads (per-client consumption)

## Exit criteria (definition of done)
- [ ] Structure-only vectors published for all key-derivation cases, tree operations, prefix
      encoding, and rejection paths, each independently checkable.
- [ ] Reference implementation and at least one client agree on every structure-only vector.
- [ ] Hash-parameterized layer defined so digest/root values drop in mechanically once
      [A-S2](A-S2-hash-function-selection.md) fixes the hash.
- [ ] Vectors are versioned against the PR #11978 constant set and flagged if constants change.

## Risks & open questions
- Hash function not final — the dominant open parameter. Digests and roots stay unpinned
  until [A-S2](A-S2-hash-function-selection.md); see
  [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
  (hash-function selection: BLAKE3 / Poseidon2 / Keccak).
- Header stem constants (`0x40` storage onset, `0x80` code onset) remain protocol-embedded;
  a change would require regenerating all embedding vectors — see the older open questions in
  [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
