# Project Scope — Empirical Sizing of Account-Header Allocation

**Status:** Approved for a storage-first implementation. The code-chunk and joint-allocation
work is intentionally deferred to later parts. This is not yet linked into
[open-questions.md](../open-questions.md) or the [roadmap](../roadmap/README.md) as a
tracked deliverable; see [Fit with the roadmap and open questions](#fit-with-the-roadmap-and-open-questions).

## The question

Every account header uses a one-byte sub-index, giving 256 possible values. In the
**current EIP-8297 design**, `BASIC_DATA` (0), `CODE_HASH` (1), and `DELEGATION` (2) have
fixed suffixes. `CODE_HASH` and `DELEGATION` are mutually exclusive leaves, but both
suffixes are reserved encoding values. Storage slots 0..63 occupy sub-indices 64..127.
No code chunk lives in the header: all code
chunks, including chunk 0, are content-addressed in `CODE_ZONE`. See
[knowledge-base/03-key-derivation.md](../knowledge-base/03-key-derivation.md) and the
[design-evolution note](../knowledge-base/05-design-evolution.md#further-rework-code-is-now-uniformly-content-addressed-post-july-2026).
The current header therefore assigns or reserves 67 sub-indices and leaves 189
unassigned.

This project deliberately evaluates **counterfactual header layouts**, including the
older design that placed early code chunks in the account header. It evaluates these four
layout families:

1. **Metadata only:** no storage slots and no code chunks in the header (`S=0, C=0`).
2. **Storage only:** the current family, including the current `S=64, C=0` design.
3. **Code only:** early code chunks in the header, but no storage slots.
4. **Mixed:** both early storage slots and early code chunks in the header, including
   the historical `S=64, C=128` design as a labelled comparison point.

Here `S` and `C` are logical window sizes, not necessarily literal offsets. Within the
existing one-byte header key, candidates must reserve three values for `BASIC_DATA`,
`CODE_HASH`, and `DELEGATION`, so `S + C <= 253`. Mutual exclusion of the latter two
leaves does not make either suffix available to storage or code. The placement of the
windows is a separate encoding choice from their sizes.

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

The eventual central output is a pair of read and write frontiers, a joint Pareto view
that keeps both axes visible, and explicit comparisons against the **current**
(`S=64, C=0`) and **metadata-only** (`S=0, C=0`) layouts. The historical
`S=64, C=128` layout is a counterfactual benchmark, not the current baseline. Part 1 is
narrower: with `C=0`, it produces storage-capacity curves rather than a storage-versus-code
allocation frontier.

## Parts and decision gates

The work is split so that the directly answerable storage question produces a useful,
reproducible result without waiting for code traces or a full PBT state image.

### Part 1 — Storage-window locality and stem replay (first deliverable)

Part 1 sweeps `S = 0..253` with `C=0`, emphasizing
`S ∈ {0, 8, 16, 32, 64, 96, 128, 192, 253}`. It compares metadata-only (`S=0`) with
the current storage window (`S=64`) and answers:

- how much of each storage read/write series falls below `S`;
- how many distinct leaves and stems each `S` produces at transaction and block
  granularity;
- how often a low-index storage access shares an account header stem with an observed
  `BASIC_DATA` access or mutation for the same account and measurement unit;
- how the current suffix placement (`64..127` for `S=64`) compares with a compact window
  beginning at suffix `3`; and
- how the as-assigned curves compare with separately ranked read and write ceilings.

Part 1 reports exact event, leaf, and stem counts. It reports exact proof siblings,
witness bytes, affected internal nodes, and hashes only if the prerequisites in
[PBT measurement tiers](#pbt-measurement-tiers) become available. Otherwise those metrics
are explicitly deferred rather than approximated from an access-only tree.

Contract-category segmentation is not part of the first deliverable. The aggregate result
will determine whether the extra classification work is likely to affect the decision.

### Part 2 — Code-chunk locality and mutation replay

Part 2 collects the missing per-PC execution data and performs the counterfactual code-only
analysis. It includes PC/PUSH/CODECOPY read coverage, deployment and mutation writes,
per-`code_hash` and per-deployment views, and the loss of current cross-account sharing.
It should use the same immutable block range as Part 1 when the required trace coverage can
be produced for that range; any unavoidable mismatch must be disclosed and must not be
silently joined into a common replay.

### Part 3 — Joint allocation frontier and encoding extensions

Part 3 combines the validated Part 1 and Part 2 event sets, sweeps `(S, C)` subject to
`S + C <= 253`, and produces separate read and write frontiers plus a joint Pareto view.
It evaluates suffix placement explicitly, marks current `S=64, C=0` and historical
`S=64, C=128`, and considers a concrete beyond-one-byte encoding only if the measured
capacity curve is still materially rising at 253.

### Part 4 — Optional segmentation and implementation-cost translation

Part 4 is conditional. It adds contract-category segmentation only if aggregate results
hide material heterogeneity, and translates structural deltas into performance or gas
only when suitable PBT benchmarks exist. Categories must have documented, reproducible,
non-overlapping rules (or be explicitly multi-label); an unclassified group and heuristic
precision checks are mandatory.

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
primary Part 1 metrics are therefore distinct read stems and distinct mutated stems.
Exact branch/sibling counts or update paths require the Tier 2 inputs defined below;
never substitute `log2(window size)` or construct an access-only tree and call its output
a mainnet proof measurement.

### Capacity and encoding are asymmetric

The current header sub-index is one byte (`ACCOUNT_KEY_LENGTH = 1 + 32 + 1 = 34`):

- **Using no more than 253 allocatable values** changes which fields live in the header but
  does not shorten keys or automatically reduce proof depth. Its cost/benefit comes from
  the observed changes in read proofs, mutation work, and measured tree shape.
- **Using more than 253 allocatable values** requires a different account-header encoding,
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
   `N ∈ {8, 16, 32, 64, 96, 128}` and across the full `S=0..253` sweep? Report separate
   curves for read-only events, write-coupled reads, and net mutations; do not combine them
   into one access count. How do the read and write distributions differ? Part 1 answers
   this in aggregate. Part 4 may add category sensitivity if the aggregate result warrants it.
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
3. **Header capacity and allocation frontier (Part 3).** Using the separate storage- and
   code-locality results, for each total allocatable header capacity `K` from 0 through the
   one-byte limit of 253, which allocation between storage slots and code chunks performs
   best for (a) read proofs/witnesses and (b) commitment updates? Sweep `S` and `C` subject
   to `S + C <= K`, including metadata-only, storage-only, code-only, and mixed candidates.
   Plot separate read and write frontiers, then a joint Pareto view; do not collapse them
   into one score without explicit, justified weights. Mark both the current `S=64, C=0`
   design and historical `S=64, C=128` counterfactual. Do the channels prefer different
   allocations, and is any candidate better on both? If gains remain substantial at 253,
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
[Part 1 start conditions](#part-1-start-conditions) for the required live revalidation:

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

### Part 1 data contract and event definitions

Part 1 must encode the following rules in shared, tested code and in the query manifest:

- Normalize addresses to lowercase fixed-width 20-byte values and slots to unsigned
  256-bit values before any join. Reject malformed or out-of-range values and report their
  count; do not coerce them to zero.
- A **storage-read event** is one source-table row. It is **write-coupled** when a
  non-no-op storage diff exists for the same `(block_number, transaction_hash, address,
  slot)`; otherwise it is **read-only**. These two row-weighted series are disjoint. Also
  publish transaction-distinct `(transaction, address, slot)` counts so repeated reads do
  not leak into the proof replay.
- The extraction may aggregate those rows server-side to
  `(block, transaction, address, slot, read_count)`. `read_count` preserves the row-weighted
  denominator while the grouped key preserves every dimension required by classification
  and transaction/block deduplication; raw billions-row downloads are not required.
- A **transaction mutation** is formed by ordering diffs for a
  `(block, transaction, address, slot)`, taking the earliest `from_value` and latest
  `to_value`, and dropping the key if those values are equal. It is the incremental-client
  sensitivity series.
- A **block-final net mutation** is formed by ordering all diffs for a
  `(block, address, slot)`, taking the earliest `from_value` and latest `to_value`, and
  dropping the key if those values are equal. This is the primary commitment series.
  Transaction order must come from a canonical transaction-index source and
  `internal_index` breaks ties within a transaction. If that ordering cannot be recovered
  and validated, block-final mutation results are blocked; transaction diffs must not be
  relabelled as block-final mutations.
- Treat zero→nonzero, nonzero→nonzero, and nonzero→zero separately as insertions,
  updates, and deletions in mutation diagnostics, while keeping their union as the net
  mutation denominator.
- For a window `S`, slot `x` is in the header iff `x < S`. Overflow storage keeps the
  current key derivation, including `tree_index = x // STEM_SUBTREE_WIDTH`; changing `S`
  does not renumber overflow slots.
- The primary locality fraction for each series is `events with slot < S / all events in
  that series`. The proof/update replay separately deduplicates concrete leaf and stem keys
  within each transaction or block, as appropriate. Raw row counts must never be presented
  as witness or commitment counts.

For same-account metadata locality, Part 1 uses the union of observed balance and nonce
reads as a `BASIC_DATA`-read proxy, and the block-final union of balance and nonce diffs as
a `BASIC_DATA`-mutation proxy. It joins only on normalized account identity in the same
transaction (reads) or block (writes). This is an **observed-metadata lower bound** because
it excludes code-hash resolution, account-existence checks, and other implied header reads
not captured by those tables. Part 1 must publish storage-only results independently so the
proxy does not become a hidden prerequisite.

### Candidate placements in Part 1

Stem counts do not depend on the suffix chosen inside a header, but exact path-compressed
subtree shapes can. Part 1 therefore records these encodings even when only Tier 1 metrics
are available:

- **Compact:** storage slot `x < S` uses suffix `3 + x`, valid for `0 <= S <= 253`.
- **Current-anchored:** storage slot `x < S` uses suffix `64 + x`, valid only for
  `0 <= S <= 192`. `S=64` exactly matches the current layout.

Unused suffix gaps create no leaves. No current-anchored result above `S=192` may be
invented; such a layout requires another placement or a wider/multi-stem encoding.

### Idealized storage bounds

The unconstrained ceiling ranks distinct storage keys separately for each account by read
frequency for the read ceiling and by net-mutation frequency for the write ceiling, then
places the top `S` keys into that account's hypothetical window. It is a mathematical
oracle and not an achievable Solidity transformation. A narrower "low-index-capable"
bound may be added only with a documented classifier and validation sample that can
distinguish declared/static slots from hash-derived mapping or array entries; byte width
alone is insufficient. If that classifier is not defensible, omit the narrower bound and
state why.

### PBT measurement tiers

- **Tier 1 — required for Part 1:** exact event, distinct-leaf, distinct-stem, and
  same-account co-location counts derived from canonical access data and symbolic key
  identities `(zone, account/code identity, tree_index, suffix)`. These counts do not
  depend on the still-unpinned hash function except for the standard collision-resistance
  assumption. If serialized keys are emitted, pin and record the chosen reference hash.
  Tier 1 is sufficient for the first deliverable.
- **Tier 2 — deferred unless prerequisites are supplied:** exact sibling/branch material,
  witness bytes, affected internal nodes, and hashes recomputed. Tier 2 requires (a) a
  pinned EIP-8297-compatible PBT implementation and hash configuration, (b) a complete PBT
  pre-state at the block before the sample, and (c) specified proof and block-update APIs.
  The manifest must identify all three. An access-only tree is not a substitute because
  unaccessed state changes branch occupancy and sibling material.

Tier 2 may augment Part 1 later without changing its event sets or Tier 1 outputs.

### Additional data sources and later-part enrichments

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

For every candidate layout, run two replays over disjointly reported event sets. Part 1
sets `C=0`; the full `(S, C)` replay begins in Part 3.

**Read/proof replay:**

- Count distinct pre-state leaves and stems at both per-transaction and block-witness
  granularity. Deduplicate repeated reads within the relevant unit. Add measured PBT
  branch/sibling material only at Tier 2.
- Report read-only accesses separately from reads coupled to a mutation. Stateful flat-state
  lookup time is out of scope; these metrics estimate proof/witness work.
- In Part 1, publish the observed-`BASIC_DATA` lower bound defined above and do not infer
  uncaptured `CODE_HASH` or account-existence reads. Part 2 must add executing-code header
  reads using its call-frame/code-source data before Part 3.
- For code, deduplicate content-addressed code-zone keys per block and report how many shared
  reads become per-account reads under a counterfactual header code window.

**Write/commitment replay:**

- Compute the block's net post-state mutations, then count distinct changed leaves and
  stems and insertions versus updates versus deletions. Count affected branch paths and
  hashes/nodes recomputed only at Tier 2. Report per-transaction updates only as an
  implementation sensitivity.
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

Part 1 uses an immutable one-million-block inclusive range. Before extraction, query the
coverage and ingestion status of every required storage, balance, nonce, and canonical
transaction-index table. Set `end_block` to the latest finalized block for which all
required tables are demonstrably complete, and set `start_block = end_block - 999,999`.
Completeness must be checked against a canonical block/transaction source rather than
inferred only from each event table's `max(block_number)`, because a block can legitimately
contain no event of a given type. Record the selection query, retrieval timestamp, table
schemas, endpoints, row counts, and checksums in the manifest before analysis.

Run a temporal sensitivity check by splitting the range into ten consecutive 100,000-block
buckets and plotting the headline locality values per bucket. The default materiality
threshold is an absolute spread above 1 percentage point in the captured-event fraction at
any emphasized `S`, or a change in which emphasized `S` retains at least 99% of the `S=253`
captured-event fraction. Freeze that threshold in configuration before computing results.
Widen or add an earlier comparison range if either condition is met.

Part 2 should use the same range. If PC traces cannot cover it, freeze and disclose the
Part 2 range separately and do not produce a joint Part 3 replay until overlap or an
explicitly matched comparison sample exists. Never present a bounded range as exhaustive
mainnet history.

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

**Scope.** Use Part 1's frozen one-million-block range when feasible, following the mismatch
rule in the [sampling plan](#sampling-plan) — not full mainnet history.
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

### Analysis steps and gates

#### Part 1

1. Scaffold the pinned environment, configuration schema, query directory, data manifest,
   reusable package, tests, report, and generated-artifact directories. Implement a local
   ClickHouse client; do not rely on the currently absent `repricing-impact` module.
2. Validate live table schemas and canonical transaction ordering, select and freeze the
   one-million-block range using the sampling rule, then extract storage and observed
   metadata inputs. Queries must be resumable and aggregate server-side wherever this does
   not discard a dimension required by the replay.
3. Normalize and validate inputs, construct the disjoint read-only/write-coupled series,
   transaction mutations, and block-final net mutations, and emit reconciliation checks.
   At minimum: source rows = accepted + rejected; read-only + write-coupled = all reads;
   block-net keys are unique; and every reported fraction has a non-hidden denominator.
4. Sweep `S=0..253`, generating event-locality curves and Tier 1 transaction/block leaf and
   stem replays. Mark emphasized values, metadata-only, and current `S=64`. Record compact
   and current-anchored placements; compare placement-dependent metrics only if Tier 2 is
   available.
5. Generate the observed-`BASIC_DATA` lower-bound views, temporal sensitivity buckets, and
   separate read-ranked and write-ranked oracle ceilings.
6. Assemble the Part 1 report and generated tables/figures, then reproduce them from a
   clean environment using only documented commands and externally supplied credentials.
   Freeze input/output checksums and run automated tests before marking Part 1 complete.

**Gate to Part 2:** Part 1 is complete and its immutable event schema is documented. Code
work may begin independently, but Part 1 results must not be held open for it.

#### Part 2

1. Validate code creation/replacement/deletion coverage and obtain the PC/code-source trace
   fields specified above for a matching range.
2. Build code read and mutation event sets, current sharing/reference-count behavior, and
   counterfactual per-account header behavior.
3. Produce code-only locality curves, mutation replays, sharing-loss diagnostics, and
   labelled read/write oracle bounds; package and reproduce the Part 2 report.

**Gate to Part 3:** Parts 1 and 2 have a common or explicitly matched sample, compatible
measurement units, and reconciled account/code identities. Without that, report them
separately and do not synthesize an allocation frontier.

#### Parts 3 and 4

1. Replay all four layout families across `S + C <= 253`, producing separate read and write
   frontiers and a joint Pareto view. Mark current and historical layouts explicitly.
2. If the curve remains materially rising at 253, specify and evaluate at least one
   concrete wider-suffix or multi-header-stem encoding. A global `STEM_SUBTREE_WIDTH`
   change remains a separate structural experiment.
3. Add category segmentation only under Part 4's classification rules and translate
   structural deltas into approximate costs only when benchmark provenance is sufficient.

## Deliverables

Every part is a reproducible analysis package in `access-pattern-exploration/`, not only a
report. Shared infrastructure is extended rather than duplicated between parts.

### Part 1 definition of done

The first deliverable includes:

- a storage-focused report with methodology, data-quality checks, separately reported
  read-only/write-coupled/transaction-mutation/block-net-mutation curves, Tier 1 leaf/stem
  replays, observed-metadata lower bounds, temporal sensitivity, oracle ceilings,
  comparisons against `S=0` and current `S=64`, recommendations, and limitations;
- machine-generated tables and figures for every reported number, including the full
  `S=0..253` sweep and emphasized-window summary;
- exact ClickHouse queries, frozen block range and schemas, row counts, rejects,
  retrieval timestamps, and checksums or stable identifiers in a data manifest;
- reusable, tested code for extraction, normalization, event classification, key/stem
  construction, replay, metrics, and artifact generation;
- notebooks for exploration and presentation where they add value, runnable top-to-bottom;
  all result-producing logic shared with scripts must call the reusable package rather than
  duplicate it in notebook cells;
- a pinned dependency environment, credential-free configuration example, and exact clean
  reproduction commands; and
- a clear Tier 2 status stating either the pinned PBT implementation/pre-state/proof API
  used or that exact proof/update-shape measurements remain deferred.

Part 1 is done when a second researcher with documented data access can regenerate all
storage tables, figures, and headline results from a clean checkout without undocumented
manual steps. It does not require PC traces, code-mutation history, contract classification,
a mixed allocation frontier, PBT benchmarks, or Tier 2 inputs.

### Later-part deliverables

Parts 2–4 extend the package with:

- **Final integrated report:** a markdown report structured as: problem statement and
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
encoding. 

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
  the existing account-header byte is a same-length relayout. Exceeding 253 allocatable
  values requires a specified encoding change, while changing global
  `STEM_SUBTREE_WIDTH` also affects code/storage-zone grouping. Do not collapse these into
  one numeric "width" recommendation.

## Prerequisites and deferred open items

### Part 1 start conditions

No unresolved research-data dependency prevents Part 1 from starting. Credentials for the
ethpandaops ClickHouse cluster are available locally and remain gitignored. The first
implementation run must still perform and record these validation checks before the large
extract:

- `DESCRIBE TABLE` every storage, balance, nonce, block, and transaction-ordering input;
- identify the canonical source of `transaction_index` and verify a deterministic
  `(transaction_index, internal_index)` diff order;
- verify coverage/completeness and freeze the range by the sampling rule; and
- run small-range reconciliation queries before scaling to one million blocks.

A failed schema or ordering check is a normal explicit gate, not permission to weaken the
event definitions silently. The repository currently has no analysis dependency file or
ClickHouse client module, so Part 1 creates and pins its own environment and implementation.

### Deferred to Part 2 or later

- Scope and obtain the code-chunk PC-tracing ingestion described above. Executed chunks
  require runtime `pc`; dynamic `CODECOPY`/`EXTCODECOPY` ranges require the relevant stack
  operands. Static bytecode cannot replace dynamic execution traces.
- Validate how creation, `CREATE2` replacement, deletion, and surviving `code_hash`
  references are reconstructed before claiming exact content-addressed code-leaf insertions
  or removals.
- Obtain a pinned current PBT implementation and full sample pre-state before enabling Tier
  2 proof/update-shape metrics.
- Trigger contract-category work only if Part 1 or Part 3 exposes material heterogeneity;
  freeze the taxonomy and validation method before computing category results.

## Fit with the roadmap and open questions

Part 1 is an evidence-producing precursor to gas-cost recalibration
([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) and informs whether the
current `HEADER_STORAGE_SLOTS = 64` constant should remain a spec assumption. It does not
set gas values, modify EIP-8297, or block client implementation work. Tier 2 depends on a
current tree implementation and benchmark maturity associated with
[A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md) and
[A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md), but Tier 1 does not.

Before implementation results are treated as a roadmap recommendation, add a tracked link
from [open-questions.md](../open-questions.md) for account-header storage-window sizing and
link the resulting Part 1 report from the relevant roadmap deliverable. That bookkeeping is
separate from starting the reproducible analysis and should not be presented as a data
dependency.
