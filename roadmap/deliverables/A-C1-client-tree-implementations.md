# A-C1 · Client PBT tree implementations

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2026-09 → 2027-03 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight** (as of 2026-09-17) — **four** implementations exist and are differentially tested (Nethermind joined the devnet 2026-09-14); only Reth missing, semantics still not uniform |

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
  4-byte-at-offset-4 `code_size`, CODE_HASH **or** the `DELEGATION_LEAF_KEY`
  EIP-7702 leaf — never both, header storage 0..63), **all** code chunks
  content-addressed in `CODE_ZONE`, and storage buckets/groups (`STORAGE_ZONE`,
  `key_hash(address) || key_hash(address||tree_index)`). Note there are **no**
  per-account header code chunks and no `CODE_OFFSET` — both were removed from
  EIP-8297 on 2026-08-04.
- Zone-aware DB / storage layout: the first key byte partitions accounts
  (`0x00`), code overflow (`0x01`), and storage (`0xFF`) into structural regions
  usable independently by sync, proving, and expiry.
- Parallel bottom-up root recomputation (no `storage_root` cross-reference in
  leaves) and passing the shared EEST-derived test vectors.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (+ CL where relevant)

### Where each client actually is (2026-09-17)

| Client | Branch | State |
|---|---|---|
| **geth** | [`CPerezz/go-ethereum@pbt`](https://github.com/CPerezz/go-ethereum/tree/pbt) | Furthest along; the tree plus proofs, flat state and the whole EIP-8347 migration. Upstream draft [#35436](https://github.com/ethereum/go-ethereum/pull/35436) is this same branch. **Quiet since 2026-09-07** — no longer the fastest-moving branch in the field. |
| **Erigon** | [`erigontech/erigon@binary-trie`](https://github.com/erigontech/erigon/tree/binary-trie) | `PBinPatriciaHashed` commitment engine behind `--experimental.bin-commitment`, off by default, in the **upstream** repo. **67 of 70** EIP-8297 fixtures pass; the three failures and two deletion caveats are deliberate divergences (see risks). Tracking issue [#23389](https://github.com/erigontech/erigon/issues/23389). |
| **Besu** | [`matkt/besu@glamsterdam-devnet-8-pbt`](https://github.com/matkt/besu/tree/glamsterdam-devnet-8-pbt) + [`besu-eth/besu-stateless@feat/partitioned-binary-trie`](https://github.com/besu-eth/besu-stateless/tree/feat/partitioned-binary-trie) | Tree in the `besu-stateless` library ([PR #92](https://github.com/besu-eth/besu-stateless/pull/92)), enabled with `--data-storage-format=BINARY`. Besu has moved org to `besu-eth/besu`. |
| **Nethermind** | [`pbt-state`](https://github.com/NethermindEth/nethermind/tree/pbt-state) | **Changed materially since the last sync.** Draft [#12573](https://github.com/NethermindEth/nethermind/pull/12573) still carries the **"prototype — not for merge"** warning, but the branch is now the **most actively developed in the field** (daily commits through 2026-09-17: parallel trie-updater folds, node groups keyed by zero-padded path + nibble count, RocksDB tuning, and a correctness fix counting delegation leaves as code references on rebuild), and it **joined the devnet on 2026-09-14** — running in *both* the tree-at-genesis and migration profiles via `--Pbt.Enabled=true`. Its storage-layout evidence (depth-4-interleave fastest; root calculation 3 ms → 11 ms) still stands. **Treat the not-for-merge label as stale relative to the branch**, and resolve which it is: the roadmap cannot count a client that disowns its own implementation. |
| **Reth** | — | Still nothing: no branch, issue or PR matching PBT / EIP-8297 as of 2026-09-17. The sole remaining gap against the five-client exit criterion. |

**Cross-client root agreement is already being measured**, ahead of
[A-C3](A-C3-multiclient-pbt-genesis-devnets.md): the
[PBT devnet](https://github.com/CPerezz/pbt-devnet) runs two nodes each of geth, Besu and
Erigon — deliberately configured differently within each pair — plus a single Nethermind node
since 2026-09-14, on an Amsterdam-at-genesis chain, requires every client to agree on every
state root, and forces a reorg every 15–30 blocks. Its genesis pins state root `0x7e16e879…`
and block hash `0x52327d2d…` as the pair geth and Besu both produce, which is the concrete
artifact this deliverable's first exit criterion asks for — now at **four** clients rather
than five. Caveat unchanged and worth repeating: all four compute those roots with **BLAKE3**,
so none of this agreement is evidence about the undecided `H`.

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
- [ ] Zero-value writes **delete** the leaf: zero and absent are the same state and
      commit to the same root (EIP-8297 was revised to require this on 2026-07-31 —
      this criterion previously asserted the opposite). Account deletion removes the
      header leaves and the storage leaves under the shared prefix, and removes
      `CODE_ZONE` leaves only when no remaining account shares the `code_hash`.
- [ ] Root recomputation runs as a single parallelizable bottom-up pass with no
      leaf-embedded `storage_root`.

## Risks & open questions
- PBT gas costs (state-access and code-chunk pricing, fixed by the benchmark-based
  repricing EIP [A-S2](A-S2-gas-cost-recalibration.md)) and the final hash `H` are
  not yet fixed; implementations must keep both pluggable. See
  [open-questions.md](../../open-questions.md).
- Divergent DB engines across clients (hash-keyed vs raw-keyed) make a single
  canonical zone layout non-trivial; a correlated all-client merkelization bug
  would be hard to detect before cross-client agreement testing.
- **Semantics are not uniform across the three existing implementations, and the gaps are
  in deletion — the part hardest to test and most load-bearing for the migration.** Erigon
  keeps zero-valued leaves (against the current EIP), **refuses account removal
  altogether**, and leaves code chunks above a shortened redeploy's length in the tree, so
  its tree is a function of history rather than of current state — which also invalidates
  recompute-from-domains as an oracle for any code-bearing account, and is reachable via an
  EIP-7702 delegation clear. Besu's `binaryTrieDefinition` drops the EIP-7610 `CREATE`
  collision check with the compensating nonce bump unimplemented. Closing these is
  upstream of any credible root-agreement gate.
- **Non-tree divergences will trip the agreement harness first.** Erigon's default Amsterdam
  ships the pre-revision EIP-8038 schedule (8000 / 3000 / 11000 / 12480) against geth-pbt's
  current one (9000 / 2100 / 12000 / 11616), and does not subtract `WARM_ACCESS` from the
  EIP-2930 access-list constants — 100 gas of drift on every access-list transaction. See
  [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md).
- **Two clients are missing and one is disposable.** Reth has no PBT work at all, and
  Nethermind's is labelled throwaway. The five-client exit criterion below is a long way
  from three-plus-a-prototype, and the shortfall is in *production-track* commitments, not
  in code volume.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [open-questions.md](../../open-questions.md)
- [jsign/binary-tree-spec](https://github.com/jsign/binary-tree-spec) — candidate Python reference
  implementation clients can check tree code against (currently EIP-7864 — must be adapted to PBT's
  prefix-free keys, two node types, and zone partitioning before roots match EIP-8297).
