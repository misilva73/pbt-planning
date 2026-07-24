# 08 — Gas & State-Access Pricing

> **Status: to be fixed by benchmark.** PBT's gas repricing is a **dedicated,
> benchmark-based EIP** (tracked by [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)).
> PBT is **not** designed for statelessness, so its gas schedule is not built around the
> cost of shipping a witness; it is built around the **measured read and write performance
> of the PBT trie** on client prototypes. The costs below are described by role and marked
> **pending** until the repricing EIP fixes them from
> [A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md) benchmark data. See
> [03-key-derivation.md](03-key-derivation.md#L138) (§ Access events) and
> [../open-questions.md](../open-questions.md).

## What PBT gas repricing does, in one paragraph

Moving state from the hexary MPT into the PBT changes the real cost of touching state:
leaves accessed together are co-located under one stem, the `storage_root` no longer sits
inside the account leaf, and contract code lives in the tree as chunks. Gas must reflect
those new costs. PBT's repricing has **two components**: (1) a **benchmark-based repricing
of state-access opcodes** — the cold/warm read and write costs for accounts and storage —
in the spirit of [EIP-8038](https://eips.ethereum.org/EIPS/eip-8038), which realigns
state-access gas from empirical measurement rather than first principles; and (2)
**chunk-based code access pricing** from
[EIP-2926](https://eips.ethereum.org/EIPS/eip-2926), which charges code by the chunks an
execution actually touches instead of a flat per-byte cost. Both are grounded in measured
PBT prototype performance, not estimates.

## 1 · Benchmark-based state-access repricing (EIP-8038 lineage)

PBT keeps the familiar **cold/warm access model** (a slot or account is charged a higher
cost on first touch in a transaction, then a cheap warm cost on subsequent touches). What
changes is the *numbers*: they are re-derived from how fast the PBT trie actually reads and
writes on representative hardware — the same empirical approach EIP-8038 takes to realign
state-access gas with today's grown state.

Costs repriced from PBT read/write benchmarks, by role:

- **Cold account access** — first-touch read of an account header (`BASIC_DATA`,
  `CODE_HASH`), reached via `*CALL`, `BALANCE`, `EXTCODEHASH`, etc.
- **Cold storage access** — first-touch `SLOAD` of a slot.
- **Storage write** — `SSTORE`, including the one-time cost of filling a previously-empty
  slot (a tree key goes `None → not-None` exactly once and never returns; see
  [02-tree-structure.md](02-tree-structure.md#L148)).
- **Code-metadata reads** — `EXTCODESIZE` / `EXTCODECOPY` need a header read *plus* a code
  read, so they price above a plain account read (an explicit EIP-8038 refinement).

Because state accessed together shares a stem, PBT makes **same-stem** follow-up accesses
(adjacent storage slots, header fields) genuinely cheap to serve — the repricing is where
that is turned into gas. The concrete values are **pending** the repricing EIP
([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) and must be conservative
enough to stay safe while provisional.

## 2 · Chunk-based code access (EIP-2926)

Contract code is split into fixed-size chunks and committed in the tree. Chunk `i` stores a
32-byte value: bytes 1..31 are the i'th 31-byte slice of code, and byte 0 marks how many
leading bytes fall inside a PUSH data region (`chunkify_code`, per EIP-2926 — see
[03-key-derivation.md](03-key-derivation.md#L84)). Code access is then charged **per chunk
touched**, not by a flat per-byte code cost:

- Executing at `PC` touches chunk `PC // CHUNK_SIZE`.
- `PUSH{n}` touches every chunk its immediate data spans.
- A non-empty `CODECOPY` / `EXTCODECOPY` touches the chunks overlapping the copied range.
- Contract creation touches every chunk of the deployed code.

Each chunk is charged once per transaction on first access, warm afterwards.

### Content-addressed code accounting

Overflow code chunks (`chunk_id ≥ 128`) live in `CODE_ZONE`, content-addressed by
`code_hash`, so contracts with identical bytecode **share** the same leaves (see
[03-key-derivation.md](03-key-derivation.md#L84)). Their access events MUST therefore be
keyed by the `(zone, tree_position, sub-index)` **tree-key**, *not* by `(address, chunk)`:
a shared chunk is charged **once per block** regardless of which contract triggers it.
Header chunks (0..127) stay per-account. This accounting is spec'd alongside the repricing
in [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md).

## Co-location is a read-performance property

PBT co-locates a stem's 256 leaves so reading many leaves of one stem is a single seek, and
keeps the commitment tree separate from the data store so no tree traversal is needed to
find a state element. This is what makes same-stem accesses cheap to serve, and it is
exactly what the benchmark-based repricing measures and turns into gas — a **performance**
property of the PBT layout, not a witness-size concern.

## Empirical evidence for the code-chunk cost

> An analysis of ~1M mainnet txs (Jun 2024, via a Geth live-tracer over PC traces) measured
> code-access gas overhead averaging **~32.6% of the current tx receipt gas** (95% of txs
> under 800k gas) once code is charged per chunk, and found a **32-byte** code chunker used
> ≈1.5% less total gas than a **31-byte** chunker while adding far less contract-size
> overhead (+0.6% vs +3.7%). It suggests mitigations (lower per-chunk charge, a free-chunk
> allowance, multi-dimensional gas). Design-agnostic evidence for PBT's code-chunk pricing
> and the chunk-size trade-off — see [07-sources.md](07-sources.md) #7.

## Status & pending constants

- **State-access costs** (cold/warm account and storage access, storage write, code-metadata
  reads) — **pending**, derived from PBT read/write benchmarks.
- **Code-chunk access cost and chunk size** — **pending**; the 31- vs 32-byte chunker
  trade-off (source #7) is an open input.
- **Content-addressed shared-chunk accounting** — overflow chunks keyed by tree-key and
  charged once per block; spec'd by A-S2.

All of the above are fixed by the benchmark-based gas repricing EIP
([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)), which is deliberately
**decoupled** from the spec freeze and the swap and previewed for a later gas-focused fork.
The published EIP text (allowed host `eips.ethereum.org`) is authoritative for
[EIP-2926](https://eips.ethereum.org/EIPS/eip-2926) and
[EIP-8038](https://eips.ethereum.org/EIPS/eip-8038); PBT's tree-key embedding lives in
EIP-8297. See [07-sources.md](07-sources.md) to re-fetch and
[../open-questions.md](../open-questions.md) for what is still open.
