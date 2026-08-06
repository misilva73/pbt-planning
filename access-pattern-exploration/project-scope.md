# Project Scope — Empirical Sizing of Account-Header Allocation

**Status:** Scoping draft (not started). Not yet linked into [open-questions.md](../open-questions.md)
or the [roadmap](../roadmap/README.md) as a tracked deliverable — see [Fit with the roadmap](#fit-with-the-roadmap-and-open-questions)
before starting.

## The question

Every account header uses a one-byte sub-index, giving 256 possible values. In the
**current EIP-8297 design**, `BASIC_DATA` (0) and `CODE_HASH` (1) are fixed and storage
slots 0..63 occupy sub-indices 64..127. No code chunk lives in the header: all code
chunks, including chunk 0, are content-addressed in `CODE_ZONE`. See
[knowledge-base/03-key-derivation.md](../knowledge-base/03-key-derivation.md) and the
[design-evolution note](../knowledge-base/05-design-evolution.md#further-rework-code-is-now-uniformly-content-addressed-post-july-2026).
The current header therefore assigns 66 sub-indices and leaves 190 unassigned.

This project deliberately evaluates **counterfactual header layouts**, including the
older design that placed early code chunks in the account header. It evaluate these four layout
families:

1. **Metadata only:** no storage slots and no code chunks in the header (`S=0, C=0`).
2. **Storage only:** the current family, including the current `S=64, C=0` design.
3. **Code only:** early code chunks in the header, but no storage slots.
4. **Mixed:** both early storage slots and early code chunks in the header, including
   the historical `S=64, C=128` design as a labelled comparison point.

Here `S` and `C` are logical window sizes, not necessarily literal offsets. Within the
existing one-byte header key, candidates must reserve two values for `BASIC_DATA` and
`CODE_HASH`, so `S + C <= 254`. The placement of those values is a separate encoding
choice from their sizes.

The project asks two nested questions:

1. **The allocation.** For a fixed header capacity, what storage/code allocation performs
   best for reads and for writes? Read locality affects witnesses and proof generation;
   write locality affects commitment-tree mutation and root recomputation. Does
   metadata-only, storage-only, code-only, or a mixed layout perform best in each channel,
   and do the two channels prefer different allocations?
2. **The capacity and encoding.** How much locality is gained as `S + C` grows within the
   existing byte, and is there enough additional value to justify an encoding larger than
   one byte? This is distinct from changing the global `STEM_SUBTREE_WIDTH`, which also
   controls grouping in the storage and code zones.

The central output is a pair of read and write frontiers, a joint Pareto view that keeps
both axes visible, and explicit comparisons against the **current** (`S=64, C=0`) and
**metadata-only** (`S=0, C=0`) layouts. The historical `S=64, C=128` layout is a
counterfactual benchmark, not the current baseline.

### What header co-location can save

A stem is `zone_byte || tree_position`. Moving a field into an account's header can reduce
two different costs, which this project must measure and report separately:

- **Read/proof channel.** Stateful clients commonly serve execution reads from flat state,
  so PBT layout need not affect their ordinary lookup path. Layout still affects the tree
  branches and proof material needed for witnesses, stateless execution, validity proofs,
  and proof generation. Measure distinct read stems and actual branch/sibling material,
  deduplicated at the transaction and block-witness levels. Separate read-only events from
  reads coupled to writes so the same state transition is not silently counted twice.
- **Write/commitment channel.** A net state mutation changes the committed entry set and
  requires tree updates and root recomputation. Measure distinct mutated leaves and stems,
  shared paths, and resulting hash/node work per block (the natural commitment batch), with
  a per-transaction sensitivity for clients that update incrementally.

In both channels the benefit is conditional: co-location helps only when the relevant
header and storage/code fields for the same account occur in the same proof or commitment
batch. The analysis must therefore measure **same-account joint locality**, not merely
whether a low-index field is touched.

Do not model the header as a fixed, complete 256-leaf binary subtree. PBT is path-compressed:
unused suffix values do not create branches, and reserving part of the byte does not by
itself reduce proof depth. Different stems may also share part of their trie path. The
primary proxies are therefore distinct read stems for the proof channel and distinct
mutated stems for the commitment channel. Construct candidate keys in an actual PBT and
measure resulting branch/sibling counts or update paths rather than substituting
`log2(window size)`.

### Capacity and encoding are asymmetric

The current header sub-index is one byte (`ACCOUNT_KEY_LENGTH = 1 + 32 + 1 = 34`):

- **Using fewer than 254 allocatable values** changes which fields live in the header but
  does not shorten keys or automatically reduce proof depth. Its cost/benefit comes from
  the observed changes in read proofs, mutation work, and measured tree shape.
- **Using more than 254 allocatable values** requires a different account-header encoding,
  such as a wider account-zone suffix or additional header stems. A wider suffix would
  increase `ACCOUNT_KEY_LENGTH`; it does **not necessarily** require widening code- and
  storage-zone keys, because key lengths are fixed independently by zone. Each concrete
  encoding must state which keys, vectors, expiry units, and proofs it changes.
- **Changing global `STEM_SUBTREE_WIDTH`** is a broader proposal than changing header
  capacity: it also changes code/storage grouping and key derivation. Analyze it only as
  a separately specified structural variant, not as a free numeric sweep.

## Research questions

1. **Storage-slot read and write locality.** Across historical mainnet transactions, what
   fraction of storage reads and writes touch slot indices `< N` for
   `N ∈ {8, 16, 32, 64, 96, 128}`? Report separate curves for read-only events,
   write-coupled reads, and net mutations; do not combine them into one access count. How
   do the read and write distributions differ, and how do they vary between EOA-adjacent
   simple contracts (few slots) and high-slot-count contracts (proxies, AMM pools,
   mapping-heavy DeFi)?
2. **Counterfactual code-chunk read and write locality.** Although current EIP-8297 keeps
   every code chunk in `CODE_ZONE`, ask separately what would happen if chunks `< M` lived
   in the account header. For reads, across historical execution traces, what fraction of
   PC-touched (and `PUSH`-data-spanned, and `CODECOPY`-range) 31-byte chunks fall within
   chunk id `< M` for `M ∈ {32, 64, 96, 128, 160, 192}`? For writes, across contract
   creation, replacement, and deletion events, how many chunks are newly materialized,
   retained through content-addressed sharing, or removed, and how would a per-account
   header prefix change write work and duplication? Report the read result as an
   **event-weighted replay** and the write result as a **deployment/mutation-weighted
   replay**. Also report per-distinct-bytecode and per-deployment sensitivity views. The
   two channels must separately show the loss of current cross-account sharing when a
   counterfactual moves chunks into per-account header stems.
3. **Header capacity and allocation frontier.** Using the separate storage- and
   code-locality results, for each total allocatable header capacity `K` from 0 through the
   one-byte limit of 254, which allocation between storage slots and code chunks performs
   best for (a) read proofs/witnesses and (b) commitment updates? Sweep `S` and `C` subject
   to `S + C <= K`, including metadata-only, storage-only, code-only, and mixed candidates.
   Plot separate read and write frontiers, then a joint Pareto view; do not collapse them
   into one score without explicit, justified weights. Mark both the current `S=64, C=0`
   design and historical `S=64, C=128` counterfactual. Do the channels prefer different
   allocations, and is any candidate better on both? If gains remain substantial at 254,
   are they large enough to justify a concrete beyond-one-byte encoding and its additional
   costs? Do not assume unused values impose proof depth, and do not
   change global `STEM_SUBTREE_WIDTH` unless the analysis explicitly includes its effects
   on code/storage-zone grouping. Read-stem and mutated-stem counts depend on `S` and `C`,
   while exact PBT proof and update shapes can also depend on where those windows are placed
   in the suffix byte; evaluate placement explicitly.
4. **Sensitivity to account/contract type.** Does one allocation serve both cost channels
   and most contract categories reasonably well, or do reads, writes, or categories
   (ERC-20, proxies, AMM pools, plain EOAs) want different splits badly enough that a
   single global constant is a poor fit
   regardless of where it's set? (This bears on whether the fix is "move the boundary"
   or "the fixed-boundary design itself is the wrong shape" — the latter is out of scope
   for a constant-tuning project and should be flagged, not chased, if it emerges.)
5. **Locality under idealized reordering (adaptation upper bounds).** Contracts today
   don't optimize slot/chunk placement for locality — Solidity assigns storage slots in
   declaration order and the compiler emits code layout with no regard to which functions
   are hot, because there's currently no incentive to do otherwise. If cheaper low-index
   access created that incentive, contracts would presumably adapt their layout. Repeat
   the read and write analyses from questions 1–2 under explicitly idealized bounds:
   - **Storage:** report separate read- and write-frequency ranking ceilings, then narrower
     low-index-capable bounds only where the data can defensibly distinguish declared slots
     from hash-derived mapping/array entries. Do not claim that key width alone perfectly
     classifies reorderability.
   - **Code reads:** aggregate access frequency by `code_hash`, not by deployed account,
     because identical bytecode has one layout. Packing the hottest chunks first is a mathematical
     capacity ceiling, not a valid compiler transformation: arbitrary chunk movement can
     break jumps, fallthrough, `PUSH` data, and metadata. If feasible, add a constrained
     basic-block/function-layout sensitivity analysis; otherwise stop at the labelled ceiling.
   - **Code writes:** code ordering does not reduce the number of chunks created during a
     deployment. Do not reuse the hot-chunk read ceiling for writes; instead report the
     attainable deduplication/sharing bound separately.
   Report the gap from the as-assigned curve at every window size, but do not present any
   oracle curve as an achievable forecast.

## Background motivation (2026-07-30 mainnet-state snapshot)

A state-snapshot report (`file:///Users/maria/Telegram/mainnet-state.html`, built from
Erigon `integration state_stats` on `mainnet-min-hc`, collated step 9,443, dated
2026-07-30) helped motivate this project. It is background only, not an input to the
analysis: it describes current state rather than historical access patterns. Its findings
suggest a direction:

- **Storage locality saturates fast, well before slot 64.** Cumulative share of *all*
  1.62B storage slots by slot-key value: `0–15` → 3.65%, `0–63` → 3.87%, `0–255` → 4.00%,
  `0–1023` → 4.07%, `0–4095` → 4.12%, `0–65535` → 4.24%. Going from a 64-wide window to a
  **1024×-wider** 65536 window buys only **+0.37 percentage points**. The current
  `HEADER_STORAGE_SLOTS = 64` window is already deep in the flat part of this curve — on this
  standing-state view, a *smaller* storage window would capture nearly all of the
  achievable benefit, and a *larger* one would not capture meaningfully more.
- **Why it saturates: most storage isn't low-index at all.** Slot-key width breakdown:
  94.9% of all 1.62B slots (1.543B) have a full 32-byte (keccak-image) key — mapping and
  dynamic-array entries, whose slot number is a hash and therefore is overwhelmingly
  unlikely to be small regardless
  of window size. Only the remaining ~5% (declared, low-index variables) can possibly
  benefit from a low-index header window at all. This bounds *any* header-window design
  to a low single-digit percentage of raw slot count, independent of how wide the window.
  This motivates research question 4's "is the fixed-boundary shape even the right lever"
  check.
- **Slots-per-contract is heavily skewed.** Median is 1 slot/contract (54.2% of the
  27.54M contracts with storage hold exactly one slot); mean is 58.9, carried by a long
  tail (log2 histogram running out past 2^24). Most contracts need almost no header
  storage window at all; a small number of outliers (AMM pools, large DeFi protocols —
  the largest single contract holds 161M slots) will overflow any window PBT could
  reasonably afford.
- **Code is dominated by tiny, heavily-duplicated templates.** 85.31M code records but
  only 2.58M distinct bytecodes (33× average duplication; 64% of all bytecode bytes are
  duplicates). Record counts are dominated by two "teeth": 45-byte EIP-1167 minimal
  proxies (49.18M records) and 23-byte EIP-7702 designators — both far under the
  historical 128-chunk (~4 KB) header window. The current EIP has no header code
  window. The snapshot's own "deployed vs. distinct" cumulative-size comparison is
  directionally relevant to research question 2's per-deployment-vs-per-distinct-bytecode
  distinction, but does not replace access-weighted execution data.
- **Caveats on this snapshot specifically:** it excludes anything written after the last
  collated step (lives in MDBX only, outside the scan) and a key deleted after that step
  can still appear with a stale value — treat exact percentages as approximate, and
  do not use these approximate figures as results in the final report.

## Data & methodology

**Primary data source — ethpandaops ClickHouse**, for historical access patterns. Verified
2026-08-05 against the live
`clickhouse.xatu.ethpandaops.io` cluster (`default` database) — see
[open items](#open-items-before-starting) for the query used:

- **Storage-slot read/write locality (research question 1) — directly answerable.**
  `default.canonical_execution_storage_reads` (`block_number`, `transaction_hash`,
  `internal_index`, `contract_address`, `slot`, `value`; mainnet blocks 46402–25687406,
  ~21.4B rows) and `default.canonical_execution_storage_diffs` (same shape, `address` /
  `from_value` / `to_value`; ~9.9B rows) provide the read and net-mutation series. Keep
  them separate. Classify reads joined to a diff for the same transaction, account, and
  slot as write-coupled; retain the remaining reads as a read-only series. `slot` is a hex
  string; convert it to an integer for the `N ∈ {8, 16, ...}` windows. Use block-level
  final mutations for the primary commitment-update metric and per-transaction diffs as
  an incremental-update sensitivity.
- **Code-chunk reads (research question 2) — not directly answerable; needs a fresh
  ingestion job.** No table on this cluster carries a program-counter or bytecode-offset
  column per executed opcode. `canonical_execution_transaction_structlog` has the right
  shape (per-step `operation`, `gas`, `depth`, `call_frame_id`) but **no `pc` column**
  and is empty on this cluster (block range came back `(0, 0, 0)`).
  `canonical_execution_transaction_structlog_agg` (mainnet blocks 21313920–25531362,
  ~173B rows) aggregates to (call frame × opcode) — `operation`, `opcode_count`, `gas`,
  `gas_cumulative`, `cold_access_count` — which is enough for gas-recalibration work
  ([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) but loses positional
  information entirely, so it **cannot** answer "which chunk id was touched." This
  confirms the fallback flagged below: research question 2 needs the
  `debug_traceBlock`-style ingestion job (`structLogs[].pc`) over a sampled block range,
  not a table that already exists at ethpandaops.
  `default.canonical_execution_contracts` (`contract_address`, `code`, `code_hash`,
  `n_code_bytes`, `deployer`, `factory`; ~104.9M rows) gives runtime bytecode and
  distinct-bytecode-by-`code_hash`, enabling the per-distinct-bytecode sensitivity view
  in research question 2 — but only once PC coverage is ingested separately; bytecode
  alone doesn't say what was *executed*.
- **Code-chunk writes (research question 2) — separate from the PC-trace gap.** Use
  `canonical_execution_contracts` and historical creation/replacement/deletion events to
  reconstruct code mutations by block. For each event, derive its 31-byte chunks and
  determine which content-addressed `(code_hash, chunk_id)` leaves are newly inserted,
  remain referenced, or become removable. Validate the available deletion and historical
  code-hash coverage before treating this side as fully answerable.
- **Joint locality (required to measure co-location benefit)** —
  `canonical_execution_balance_reads` /
  `canonical_execution_nonce_reads` (and their `_diffs` counterparts) exist per-tx and can
  proxy "was `BASIC_DATA` read in this tx" (nonce+balance are the MPT-era analogs of the
  packed `BASIC_DATA` field); join against `storage_reads` on `(block_number,
  transaction_hash, normalized account address)` for the read/proof channel. Separately,
  join balance/nonce diffs, storage diffs, and code mutations by block and normalized
  account for the write/commitment channel. A join without account identity would pair
  unrelated accesses. For code, retain `DELEGATECALL`/`CALLCODE` code-source versus storage
  context and distinguish per-transaction read proofs from block-level mutations.
- **Contract classification** (proxy / ERC-20 / AMM / EOA-like) if research question 4
  is pursued — likely needs a bytecode-signature heuristic (e.g., known selectors, proxy
  patterns) rather than a ready-made label; scope this as best-effort, not exhaustive.

### Comparison metric

For every candidate `(S, C)` layout, run two replays over disjointly reported event sets.

**Read/proof replay:**

- Count distinct pre-state leaves and stems, plus measured PBT branch/sibling material, at
  both per-transaction and block-witness granularity. Deduplicate repeated reads within the
  relevant unit.
- Report read-only accesses separately from reads coupled to a mutation. Stateful flat-state
  lookup time is out of scope; these metrics estimate proof/witness work.
- Add header reads implied by execution and account-inspection operations, including the
  account whose `CODE_HASH` is resolved for code execution. State the mapping assumptions.
- For code, deduplicate content-addressed code-zone keys per block and report how many shared
  reads become per-account reads under a counterfactual header code window.

**Write/commitment replay:**

- Compute the block's net post-state mutations, then count distinct changed leaves and
  stems, affected branch paths, hashes/nodes recomputed, and insertions versus deletions.
  Report per-transaction updates only as an implementation sensitivity.
- Model code leaves by reference: distinguish an existing shared chunk from a newly inserted
  chunk and remove it only when the resulting state has no remaining reference. A
  counterfactual header code window instead creates per-account mutations and duplication.
- Compare write work against both `S=0, C=0` and the current `S=64, C=0` layout without
  adding read-proof counts to write-update counts.

In both replays, header and storage/code events share a stem only when they resolve to the
same account and occur in the same measurement unit. Raw index-locality curves, unique
accounts affected, per-distinct-bytecode views, and measured tree shape are secondary
diagnostics. Any combined read/write ranking must expose its weighting assumptions.

### Sampling plan

Start with a bounded, recent block range (e.g., last ~1M blocks, or a period comparable to
the existing code-chunk study) to keep query cost and turnaround manageable; only widen the
range if early results are sensitive to the window chosen. Use the same sampled range for
storage and code analysis. State this bound explicitly in the writeup rather than presenting
a sample as exhaustive (no silent truncation).

### Code-chunk read locality — data request draft (research question 2)

Note: the current EIP-8297 text has already removed the header code-chunk window this
research question was originally sized against (see
[knowledge-base/05-design-evolution.md](../knowledge-base/05-design-evolution.md#further-rework-code-is-now-uniformly-content-addressed-post-july-2026)) —
confirmed against the live spec text 2026-08-05. This data still has value independent of
that because this project explicitly evaluates counterfactual code-only and mixed header
layouts, including whether reinstating a header code window would improve read-proof
locality. Code-write analysis uses deployment and mutation data and does not require `pc`.

**The ask, framed to be cheap.** `default.canonical_execution_transaction_structlog` is
already schema-ready for most of this (`operation`, `gas`, `depth`, `call_frame_id`,
`call_frame_path`, `call_to_address`) but is (a) empty on the ethpandaops cluster today —
`(min, max, count)` came back `(0, 0, 0)` — and (b) missing the one field that actually
blocks this research question: **program counter (`pc`)**. The concrete ask is: backfill
this table for a sampled block range and retain `pc`, executing code address/hash, and the
minimal `CODECOPY`/`EXTCODECOPY` target/range operands described below — rather than
requesting a net-new trace pipeline.

**Exact fields needed, per opcode-execution step (one row per `structLogs[]` entry):**

- `block_number`, `transaction_hash`, `transaction_index` — already present.
- `call_frame_id`, `call_frame_path`, `depth` — already present; needed because
  `DELEGATECALL`/`CALLCODE` execute another contract's code under the caller's storage
  identity, so the call frame alone doesn't tell you which bytecode is running.
- **`executing_code_address` — new.** The historical address that owns the bytecode being
  executed. For `DELEGATECALL`/`CALLCODE`, this is the code-source address rather than the
  storage-context address. It identifies which account header would hold the chunks in the
  counterfactual layout; `executing_code_hash` alone cannot do that.
- **`executing_code_hash` — new, and the second-most-critical field after `pc`.** The
  `code_hash` of whichever contract's bytecode is actually executing at this frame — for
  `CALL`/`STATICCALL`/`CREATE`/`CREATE2` that's the target address's own code, but for
  `DELEGATECALL`/`CALLCODE` it's the *code-source* address, not the storage-context
  target. `CODE_ZONE` chunks are content-addressed by `code_hash`, not caller address, so
  this is the correct join key for current content-addressed-code identity and the
  distinct-bytecode sensitivity view. It also needs to reflect the code live **at that
  historical block** — a
  `CREATE2`-redeployed or subsequently-self-destructed contract can have a different
  `code_hash` today than when the transaction executed.
- **`pc` — new, the single missing column.** Program-counter byte offset of the opcode
  within the executing bytecode.
- `operation` — already present; used to detect `PUSH1`..`PUSH32` (immediate-data span)
  and `CODECOPY`/`EXTCODECOPY` (dynamic range, below).
- **For `CODECOPY`/`EXTCODECOPY` steps only — new: the `offset` and `length` operands**
  consumed by the opcode (i.e. the relevant top-of-stack values at that step, not the
  full stack). `EXTCODECOPY` additionally needs the target address and that address's
  historical `code_hash` — distinct from `executing_code_address` and
  `executing_code_hash` — since it copies another contract's code.

**Derivation logic (ours to run once the columns above exist):**

- Chunk id: `chunk_id = pc // 31` (31-byte chunks, per current `chunkify_code` in
  [knowledge-base/03-key-derivation.md](../knowledge-base/03-key-derivation.md#code)).
- Baseline PC touch: every `(pc, operation)` row marks `chunk_id = pc // 31` touched.
- `PUSH`-data span: for `operation ∈ {PUSH1..PUSH32}` with immediate-data width `w`
  (decodable from the opcode name itself, no extra column needed), mark the full byte
  range `[pc, pc + w + 1)` touched — this can span more than one chunk.
- `CODECOPY` range: mark byte range `[offset, offset + length)` of `executing_code_hash`'s
  own code touched.
- `EXTCODECOPY` range: same, but against the target's `code_hash` — track as a separate
  series; the original research-question wording doesn't require this, treat as optional.
- Preserve `(block_number, transaction_hash, call_frame_id, executing_code_address,
  executing_code_hash, chunk_id)` through the replay stage. Then produce both event counts
  and deduplicated transaction/block aggregates. A global `(code_hash, chunk_id)` aggregate
  alone would lose the information needed to measure header co-occurrence and current
  cross-account sharing.

**Scope.** Same sampled block range as the rest of the project (the ~1M-block window, or
whatever is chosen in the [sampling plan](#sampling-plan)) — not full mainnet history.
`canonical_execution_transaction_structlog_agg` already holds ~173B rows over a ~4.2M
block span; a raw per-PC dump over full history would be materially more expensive to
produce and store than that aggregate, so bound the ask explicitly rather than requesting
"all of it."

**Two ways to get it, in order of preference:**

1. **Ask ethpandaops** to backfill `canonical_execution_transaction_structlog` for the
   agreed block range with the `pc` / `executing_code_address` / `executing_code_hash` /
   `CODECOPY`-operand fields
   above — cheaper than it sounds since most of the table's shape already exists and is
   already wired into their pipeline; this is a schema extension and backfill, not a new
   collector.
2. **Self-collect** if that's not feasible on their timeline: run `debug_traceTransaction`
   (standard `structLogger`, `disableMemory: true`, `disableStorage: true` — storage is
   already covered by `canonical_execution_storage_reads`/`_diffs` — `disableStack: false`
   since `CODECOPY`/`EXTCODECOPY` operands need it) against an archive node over the same
   sampled range, keeping only `pc`/`op`/`depth`/`call_frame_id` plus the top-of-stack
   values on `CODECOPY`/`EXTCODECOPY` steps. Preserve the transaction, call-frame,
   code-address, and code-hash dimensions required by the replay rather than collapsing
   immediately to global touch counts. Comparable in scope
   to the ~1M-tx code-chunk study already cited in
   [knowledge-base/08](../knowledge-base/08-gas-and-access-events.md).

### Analysis steps

1. Pull and classify storage and code events for the sampled range. Produce separate
   storage read-only, write-coupled-read, and net-mutation sets; separately produce executed
   code-chunk reads and code creation/replacement/deletion mutations. Build cumulative
   locality curves for every series using as-assigned slot/chunk indices.
2. Build same-account event sets at the appropriate unit: transactions and block witnesses
   for reads, blocks for net writes, and transactions as an incremental-write sensitivity.
   Derive `BASIC_DATA`/`CODE_HASH`, storage, and code identities; retain code-source versus
   storage-context identities through `DELEGATECALL`/`CALLCODE`.
3. Replay the four layout families — metadata-only, storage-only, code-only, and mixed —
   across capacities up to `S + C = 254`. For each `(S, C)`, run the read/proof and
   write/commitment replays separately according to [Comparison metric](#comparison-metric).
   Mark current `S=64, C=0` and historical `S=64, C=128` explicitly. Instantiate explicit
   suffix placements (including the current offsets and a compact allocation starting at
   sub-index 2) in the PBT implementation to measure proof material and update paths.
4. Compute the idealized bounds from research question 5 separately: read- and write-ranked
   storage ceilings, a per-`code_hash` hot-chunk read ceiling, and a code-write sharing/
   deduplication ceiling. Label each as a mathematical bound; add a semantics-preserving
   code-layout read sensitivity only if the required control-flow analysis is available.
5. If the capacity curve is still materially rising at 254, specify at least one concrete
   wider-account-suffix or multi-header-stem encoding and evaluate its affected key lengths,
   vectors, expiry unit, measured tree shape, and datastore cost. Keep any change to global
   `STEM_SUBTREE_WIDTH` as a separate structural experiment.
6. If pursued, segment by contract category (research question 4) and re-run the locality
   and replay analyses in steps 1–4 per segment.
7. Translate the read-proof and commitment-update deltas into separate approximate costs
   using whatever PBT benchmark figures are available at the time (provisional
   [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)
   numbers if benchmarks haven't landed yet, clearly labeled as provisional) — the
   deliverable should state qualitative directions and rough magnitudes, not a
   false-precision combined score or gas number ahead of A-S2/A-T4.
8. Package and verify the complete reproduction workflow: data acquisition, transformation,
   replay, chart/table generation, and report assembly. Run it from a clean environment
   using the documented commands before considering the project complete.

## Deliverable

The deliverable is a reproducible analysis package in `access-pattern-exploration/`, not
only a final report. It must include:

- **Final report:** a markdown report structured as: problem statement and
  current-versus-counterfactual layouts → data and methodology → comparison metric →
  separate read/proof and write/commitment locality curves → separate and joint-Pareto
  frontiers for metadata-only, storage-only, code-only, and mixed layouts → explicitly
  labelled idealized bounds → comparisons against current `S=64, C=0`, metadata-only
  `S=0, C=0`, and historical `S=64, C=128` → recommendations and limitations. Never
  present an unlabeled aggregate that mixes read and write costs.
- **Notebooks:** all exploratory and final-analysis notebooks needed to reproduce the
  reported results, organized so they can be run in a documented order from top to bottom.
- **Reusable code:** scripts or modules for data extraction, normalization, chunk/slot
  aggregation, layout replay, metrics, and figure/table generation. Shared logic must live
  in reusable code rather than being duplicated across notebooks.
- **Queries and data manifest:** the exact ClickHouse queries and trace-collection commands,
  plus the sampled block range, source-table versions or retrieval dates, row counts, and
  checksums or stable identifiers for every external input. Large or restricted raw data
  need not be committed, but its acquisition and expected local layout must be documented.
- **Reproduction environment:** a dependency lockfile or equivalent pinned environment,
  configuration examples with no credentials, and a README containing the exact commands
  required to acquire inputs and regenerate every reported table, figure, and result.
- **Generated artifacts:** machine-generated tables and figures used by the report, with
  clear provenance back to the producing notebook or script. Do not hand-edit reported
  numbers or charts.

Definition of done: from a clean checkout and with documented access to the external data,
a second researcher can follow the README to regenerate the report's tables, figures, and
headline results without undocumented manual steps. Secrets and large raw datasets remain
outside version control.

Recommendations should separately cover header allocation/capacity and any beyond-one-byte
encoding. If a structural change is recommended, open a tracked item in
[open-questions.md](../open-questions.md) under *Trie design (EIP-8297)* referencing this
report; it must land before
[A-S3](../roadmap/deliverables/A-S3-eip8297-spec-freeze.md). State exactly which per-zone
key lengths and vectors the proposed encoding changes rather than implying that every tree
key necessarily grows.

## Limitations to state up front

- **Backward-looking bias.** Current mainnet access patterns were shaped by *MPT-era*
  gas costs (flat per-slot `SSTORE`, no chunk-based code pricing). PBT's own repricing
  ([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) may itself change how
  contracts are written once live — this analysis can only say "the current design
  serves current behavior well/poorly," not predict post-repricing behavior. Research
  question 5's oracle-reordered curve gives a partial, best-case answer to "how much
  could adaptation close the gap," but it is a ceiling, not a forecast: it assumes free,
  perfect relayout, ignores migration cost for already-deployed contracts, and doesn't
  model how devs would *actually* respond to a locality incentive. State both — the
  backward-looking bias and the oracle bound's own limits — explicitly in the report
  rather than presenting the recommendation as future-proof.
- **Read-cost boundary.** Stateful clients may serve ordinary execution reads from flat
  state, so the read channel estimates proof/witness work rather than flat-database lookup
  latency. It must not claim that header co-location accelerates all stateful-client reads.
  Stateless execution, validity proving, and witness generation remain in scope.
- **Benchmark dependency.** Turning fewer proof branches or commitment updates into hard
  gas/performance numbers depends on PBT read/write benchmarks that don't exist yet
  ([A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md), due 2027-07→2027-12).
  This project should produce the separate read/write locality evidence now (it doesn't
  need the benchmark) and leave the final gas translation to A-S2 once benchmark data lands.
- **Counterfactual header code loses sharing.** In the current design, every code chunk is
  content-addressed and shared across contracts with identical bytecode (see
  [knowledge-base/03-key-derivation.md](../knowledge-base/03-key-derivation.md#code)). A
  counterfactual per-account header code window gives up that sharing for its resident
  chunks. Both the block-deduplicated read replay and the code-mutation replay must report
  this; otherwise the header-code benefit will be overstated.
- **Sample bias.** A block-range sample skews toward whatever contracts are active in
  that window (bots, popular DeFi protocols); note this rather than treating the sample
  as representative of "all Ethereum contracts."
- **Allocation and encoding changes are not equally cheap.** Reallocating values within
  the existing account-header byte is a same-length relayout. Exceeding 254 allocatable
  values requires a specified encoding change, while changing global
  `STEM_SUBTREE_WIDTH` also affects code/storage-zone grouping. Do not collapse these into
  one numeric "width" recommendation.

## Open items before starting

- ~~Confirm exact ethpandaops ClickHouse table names/schemas for EL traces and state~~ —
  **done 2026-08-05**, verified live via `DESCRIBE TABLE` against
  `clickhouse.xatu.ethpandaops.io` (`default` db, credentials in the gitignored
  `secrets.json`, connection pattern matches
  `repricing-impact/src/repricing_impact/clickhouse.py`). Findings folded into
  [Data & methodology](#data--methodology) above. Net result: storage reads and mutations
  (research question 1) are covered by existing tables. Code reads (research question 2)
  are **not** — no table retains a program-counter/bytecode-offset column, so that channel
  still needs a fresh `debug_traceBlock`-style ingestion job. Code-write coverage depends
  on validating historical creation/replacement/deletion and code-reference data.
- Decide the sample block range (recency vs. size trade-off) before running the first
  query, and record it in the eventual report. Full mainnet history is available for
  `storage_reads`/`storage_diffs` (blocks 46402–25687406), so the "last ~1M blocks"
  default from the sampling plan is a genuine choice, not a data-availability constraint.
- Scope the code-chunk PC-tracing ingestion job described above. Executed chunks require
  runtime `pc` data, and dynamic `CODECOPY`/`EXTCODECOPY` ranges require the relevant stack
  operands. Static bytecode plus call input may validate chunkification or enrich traced
  rows, but it cannot replace execution tracing for dynamic control flow.
- Validate the code-write event model: confirm how contract creation, `CREATE2`
  replacement, deletion, and surviving `code_hash` references can be reconstructed for the
  sample before claiming exact insertion/removal counts for content-addressed code leaves.
- Decide whether contract-category segmentation (research question 4) is in scope for a
  first pass or deferred to a follow-up if the aggregate frontier already gives a clear
  answer.
