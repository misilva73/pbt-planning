# B-C1 · Converter (prototype)

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2026-10 → 2027-03 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight, ~2 months early** (as of 2026-09-17) — geth's `bintrie convert` implements the full EIP-8347 pipeline; **still the only offline converter**, small-fixture, and its preimage writer **still** lags the spec (re-checked 2026-09-17, unfixed four weeks on). Erigon now lists mainnet PBT state conversion as in progress — watch it as a possible second producer. |

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

> **Update (2026-09-02).** A working converter exists in one client, ahead of this
> deliverable's 2026-10 start: `geth bintrie convert [state-root]`
> ([PR #14](https://github.com/CPerezz/go-ethereum/pull/14), merged 2026-08-09, on
> `CPerezz/go-ethereum@pbt`). It implements the pipeline this deliverable describes —
> one scan derives every leaf, an external merge-sort orders them in tree-key order, the
> tree builds bottom-up in a single pass, flat state is written alongside, both stores are
> verified, and a completion marker is written last. `--snapshot-out` / `--preimages-out`
> emit the EIP-8347 distribution artifacts with their keccak digests computed in the same
> pass; `--memory-limit` / `--tmpdir` control sort spilling; `--delete-source` drops the MPT
> trie nodes once conversion verifies. The consumer side landed a week later as
> `geth bintrie import` ([PR #16](https://github.com/CPerezz/go-ethereum/pull/16)) — see
> [A-C4](A-C4-snapshot-serving-verification.md).
>
> Reported on a 70k-account / 140k-slot / 5.2k-distinct-code fixture (108–115 MB source
> datadir, 458,831 leaves, 290,503 node records) on an M-class laptop:
>
> | Phase | Time |
> |---|---|
> | Scan + derive (leaves, flat state, preimage checks) | 1.78 s |
> | Sort + bottom-up build | 0.81 s |
> | Tree verification (walk + refold) | 1.13 s |
> | Flat-state verification (full re-derivation) | 1.14 s |
> | **Total** | **4.86 s** (~22 source-MB/s, 14.4k accounts/s) |
>
> Read those as **compute costs on a page-cache-resident fixture**, not as migration
> timings: half the total is the two verification passes, and the author's own naive
> extrapolation to ~270 GB of mainnet state puts the compute floor at 3–4 h with real runs
> expected to be I/O-bound past cache. Artifacts came to 29.4 MB against a 114.7 MB datadir,
> since they carry leaves and no inner nodes.
>
> **Three things this does not yet give the deliverable.** (1) It is **one** client — the
> load-bearing claim that independent correct converters emit *bit-identical* output is
> untested, and cannot be tested until a second converter exists. (2) The preimage writer
> still emits **RLP, address-sorted** records, the format EIP-8347 replaced on 2026-08-20
> with fixed-width hashed-key-ordered records; until that is fixed, byte-canonicality is
> claimed against a superseded spec. (3) Resumability: the implementation writes a
> completion marker, which is not the same as restarting from the last durable checkpoint.

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
  from the MPT. The byte-level **preimage file format** is no longer open — EIP-8347
  specifies it — but it has **changed twice**, most recently on 2026-08-20 to fixed-width
  records ordered by `keccak256(address)` / `keccak256(slotKey)`. The current geth
  implementation predates that change and still writes the RLP, address-sorted form, so the
  first task here is closing that drift, not designing a format. The new ordering is not
  cosmetic: it puts the file in MPT iteration order so the scan and the preimage match run
  as a sequential merge, which is what removes the in-memory index from converter step 2.
  A gap between extraction height `E` and anchor `N` must still be closed by BAL-completion
  over `(E, N]` — coordinate with B-C2.
- **"Bit-identical across independent producers" is the design's central claim and nothing
  tests it yet.** One converter exists. A second, independent implementation is worth more
  to this deliverable than any amount of hardening on the first.
- **Determinism across DB engines.** hash-keyed vs raw-keyed iteration order
  differs; the external merge-sort must impose a canonical order so all clients
  converge on the same tree regardless of source layout.
- Tree hash `H` and key-derivation constants are not yet frozen (the hash-function dependency), so the
  converter must keep both pluggable.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
