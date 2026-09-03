# A-T2 · Tree & key-derivation vectors

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Tests |
| **Timeline** | 2026-07 → 2026-12 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight** (as of 2026-09-02) — conformance vectors are being generated on `execution-specs@projects/binary-trie`; the constant set below needed correcting |

← [Back to roadmap](../README.md)

## Objective
Produce canonical, machine-checkable test vectors for PBT's tree structure and key
derivation per EIP-8297: merkelization, insertion/split into canonical form, bit-prefix
encoding, and the full zone/stem/sub-index embedding of Ethereum state. These vectors are
the first concrete evidence artifact and the reference clients ([A-C1](A-C1-client-tree-implementations.md))
check their tree code against. Because the tree hash function is not yet chosen, the initial
vectors are **structure-only** — they pin key bytes, node shapes and preimage layouts, and
defer digest/root values until the hash is fixed by the [hash-function dependency](../README.md).

## Scope — what ships
- **Key-derivation vectors** covering the worked examples in the key-derivation spec:
  account `BASIC_DATA` (`0x00 || H(A) || 0x00`, 34 bytes), `CODE_HASH_LEAF_KEY`
  (`0x00 || H(A) || 0x01`), the EIP-7702 `DELEGATION_LEAF_KEY`
  (`0x00 || H(A) || 0x02`, value `0xef0100 || target || 0x00 * 9`, mutually exclusive with
  `CODE_HASH_LEAF_KEY`), header-resident storage slot 5,
  storage-zone slot 1000 (`0xFF || H(A) || H(A||3) || 0xE8`, 66 bytes), and code chunk 300
  (`0x01 || H(C||1) || 0x2C`, 34 bytes), including per-zone length asserts.
- **Embedding vectors** for the zone map (`0x00` account, `0x01` code, `0xFF` storage), the
  header stem offsets (`HEADER_STORAGE_OFFSET = 64`, `HEADER_STORAGE_SLOTS = 64`,
  `STEM_SUBTREE_WIDTH = 256`; **`CODE_OFFSET` no longer exists** — EIP-8297 removed it on
  2026-08-04 when all code moved into `CODE_ZONE`, so the header's live sub-indices are
  exactly 0, 1, 2 and 64..127), storage buckets (`key_hash(address)` prefix +
  `key_hash(address||tree_index)` suffix), and content-addressed code stems, with the
  group-0 exception (storage-zone slots 64..255 only).
- **Tree-operation vectors:** insertion, leaf split, and branch split producing the single
  canonical tree for a key/value set; two-non-empty-children invariant; and — **corrected
  from an earlier draft of this deliverable, which asserted the opposite** — zero and absent
  as the *same* state committing to the same root, so a zero write to an absent key is a
  no-op and a zero write to a present leaf deletes it. Plus account deletion: header leaves
  and the storage leaves under the shared prefix go; a `CODE_ZONE` leaf goes only if no
  remaining account shares its `code_hash`.
- **Encoding vectors:** `encode_bit_prefix` (2-byte big-endian bit count + MSB-first padded
  bits), `LEAF_TAG`/`BRANCH_TAG` preimage layouts, and prefix-freedom / length-bound rejection
  cases (`MAX_KEY_LENGTH = 8192`).
- Structure-only now; a hash-parameterized layer that fills in `H(...)` digests and roots once
  the hash-function dependency lands.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — vectors track the
  converged EIP-8297 constants and algorithms. Hash outputs additionally need
  the [hash-function dependency](../README.md) before they can be pinned.
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
      the [hash-function dependency](../README.md) fixes the hash.
- [ ] Vectors are versioned against the EIP-8297 constant set and flagged if constants change.

## Risks & open questions
- Hash function not final — the dominant open parameter. Digests and roots stay unpinned
  until the [hash-function dependency](../README.md) resolves; see
  [open-questions.md](../../open-questions.md)
  (hash-function selection: BLAKE3 / Poseidon2 / Keccak).
- Header stem constants remain protocol-embedded and a change regenerates every embedding
  vector — which is not theoretical: the `0x80` code onset (`CODE_OFFSET`) was **deleted**
  on 2026-08-04 and delegation indicators **moved into** the header at sub-index `0x02` on
  2026-08-06. Any vector set generated before those dates is wrong. See
  [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md) and
  the older open questions in
  [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- **The conformance vectors that exist may encode provider behaviour rather than the spec.**
  `execution-specs@projects/binary-trie` regenerates conformance vectors and carries the
  EIP-8297 suite, but Erigon reports two zero-write fixtures pinning `state_pbt.py`'s
  behaviour and one `CREATE2`-after-EIP-161-clear fixture the reference calls an open
  consensus question. Vectors this deliverable publishes must be traceable to EIP text.

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [open-questions.md](../../open-questions.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [jsign/binary-tree-spec](https://github.com/jsign/binary-tree-spec) — candidate Python reference
  implementation to adapt for vector generation (currently EIP-7864, not yet EIP-8297; `tree.py`
  merkelization + `embedding.py` key derivation with existing `test_*` suites).
