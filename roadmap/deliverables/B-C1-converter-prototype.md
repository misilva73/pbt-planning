# B-C1 · Converter (prototype)

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2026-10 → 2027-03 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Build the first working prototype of **the Converter** — the deterministic
function that translates a full MPT state at anchor block `N` into a PBT. It
scans MPT leaves, validates that `keccak(preimage)` matches the trie paths,
derives PBT keys, external-merge-sorts by PBT-key order, and constructs the tree
bottom-up in a single sequential pass. The PBT-key sort order is the load-bearing
design choice: it turns snapshot ingestion into a sequential **bulk-load** rather
than billions of random inserts. This prototype proves the algorithm and its
determinism before it hardens into the production pipeline.

## Scope — what ships
- A deterministic converter with the five-stage pipeline: (1) scan MPT source
  leaves, (2) validate `keccak(preimage)` against trie paths, (3) derive PBT
  keys, (4) **external merge-sort** by PBT-key order, (5) sequential **bottom-up**
  tree construction.
- **Security checkpoints** that abort on any preimage/path mismatch or malformed
  leaf, and **resumability markers** so a long conversion can restart from the
  last durable checkpoint rather than from scratch.
- PBT-key-ordered output staged so downstream ingestion is a sequential bulk-load.
- A conversion of a bounded, non-mainnet-scale state (test/dev state) with a
  reproducible PBT root, driven by the B-T1 conversion vectors.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section). MPT state
  cannot be iterated backward into raw keys on hash-keyed clients (geth,
  Nethermind, Besu), so those depend on distributed **preimages**; raw-keyed
  clients (Reth, Erigon) can supply preimages via extraction at height `E`.

## Dependencies
- **Upstream (blocks this):** [B-S1](B-S1-offline-migration-eip.md) (offline-migration EIP: MPT→PBT conversion rules), [A-C1](A-C1-client-tree-implementations.md) (PBT tree + key derivation)
- **Downstream (this blocks):** [B-C3](B-C3-snapshot-production-pipeline.md), [B-C4](B-C4-production-rehearsals.md)

## Exit criteria (definition of done)
- [ ] Converter runs end-to-end on a bounded test state and emits a PBT whose
      root matches the reference / B-T1 vectors bit-for-bit.
- [ ] Preimage validation (`keccak(preimage)` == trie path) is enforced; a
      deliberately corrupted preimage aborts the run at a security checkpoint.
- [ ] External merge-sort produces globally PBT-key-ordered output; bottom-up
      construction is a single sequential pass (no random inserts).
- [ ] A run interrupted mid-conversion resumes from the last resumability marker
      and produces an identical root to an uninterrupted run.
- [ ] Determinism: two independent runs over the same input produce byte-identical
      intermediate sort output and identical PBT root.

## Risks & open questions
- **Preimage availability & format.** Hash-keyed clients cannot recover raw keys
  from the MPT; the byte-level **preimage file format** is still open (§14). A
  gap between extraction height `E` and anchor `N` must be closed by BAL-completion
  over `(E, N]` — coordinate with B-C2.
- **Determinism across DB engines.** hash-keyed vs raw-keyed iteration order
  differs; the external merge-sort must impose a canonical order so all clients
  converge on the same tree regardless of source layout.
- Tree hash `H` and key-derivation constants are not yet frozen (the hash-function dependency), so the
  converter must keep both pluggable.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
