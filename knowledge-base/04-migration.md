# 04 — MPT → PBT Migration Roadmap

> **Primary source (this doc):** *"MPT → PBT: Ethereum State Migration Roadmap"*
> ([hackmd.io/@CPerezz/H1Q2zt8NMe](https://hackmd.io/@CPerezz/H1Q2zt8NMe)) — the
> strategy-and-operator roadmap, and the document with the most context (program phases,
> node-operator playbook, trust tiers, testing).
>
> **Formal write-up:** **EIP-8347 — Offline State Migration to the PBT**
> ([PR #12006](https://github.com/ethereum/EIPs/pull/12006), Draft;
> `requires: 7928, 8297`). The EIP is the normative rendering of this
> roadmap: it pins the byte-level artifact formats, the parameter values, and the
> RFC-2119 requirements. Where this doc needs an exact format or a concrete constant, it
> cites the EIP.
>
> This is a *strategy* document; specific tree constants may lag the latest EIP design
> (see [05-design-evolution.md](05-design-evolution.md)). The migration approach itself
> is largely design-agnostic.

## Source discrepancies to reconcile

The roadmap and its formal EIP write-up do **not yet agree** on the following. They are
flagged here rather than silently resolved; the fix lands when the EIP and roadmap are
re-synced. Downstream trackers: [../open-questions.md](../open-questions.md).

| # | Point | HackMD roadmap | EIP-8347 (PR #12006) | Note |
| --- | --- | --- | --- | --- |
| D1 | **Re-anchor cadence / dual-state window** | Targets a **2–3 week** per-node dual-state holding window; re-anchor cadence `N′` left generic. | `REANCHOR_CADENCE = 50400` blocks (**~1 week**). Its "transition window" is a *distinct* concept: `SWAP_FORK` activation → finality, **not** the dual-state holding period. | Two different clocks are being conflated across the docs. Reconcile the terminology: is the "2–3 week" figure the re-anchor cadence, the catch-up budget, or the hold window? |
| D2 | **Hash domains** | Names **BLAKE3** explicitly for PBT key derivation and internal-node hashing (and BLAKE3/keccak256 for artifact hashing). | Defers entirely to [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) for key derivation; never names a hash. | The hash `H` is still an **open parameter** (BLAKE3 / Poseidon2 / Keccak candidates — see [../open-questions.md](../open-questions.md#hash-function-selection--the-dominant-open-parameter)). The EIP's deferral is the safer framing; the roadmap's BLAKE3 naming is ahead of the decision. |
| D3 | **Phase model** | **Six** program phases (P0–P6): a project schedule from spec convergence to aftermath. | **Five** lifecycle phases: conversion → distribution/verification → catch-up → shadow → swap+window. | Not a contradiction (program schedule vs protocol lifecycle) but the two "phase" numberings must not be conflated. |
| D4 | **Disk figure** | **300–500 GB** headroom for the PBT database (self-migrators). | Snapshot artifact is **~100+ GB**; ~300–500 GB is what MPT disposal *reclaims* after finality. | Three different quantities (PBT DB, snapshot file, extra-tree overhead ≈300 GB in [09](09-online-vs-offline-migration.md)). Pin a single definition. |

## The core decision: offline conversion (not online overlay)

The roadmap explicitly chooses **offline conversion** over an online overlay approach.

> For the full argued comparison — the online/offline debate worked through point by point
> and re-decided for the post-H\* world (BALs, ePBS, zkEVM proofs, 400M gas limit), including
> the conversion-pointer / two-tree-read question — see
> [09-online-vs-offline-migration.md](09-online-vs-offline-migration.md).

The shape of it:
1. Convert the full state at a **fixed anchor block `ANCHOR_BLOCK`** (`N`).
2. Distribute the result as a **verifiable snapshot**.
3. Maintain **both trees** during a transition window.
4. Activate the PBT at **fork `SWAP_FORK`** (`S`), making it canonical.

**Why offline wins** (the document acknowledges online's advantages — inherent
observability, gentler disk usage, no distribution event — but judges those "engineering
costs with known tools" against offline's safety):
- **Failures surface before consensus depends on the new tree** (no live chain split).
- A single, small consensus fork.
- Execution semantics preserved until activation.
- Full recoverability until the activation release deploys.
- Comprehensive rehearsal is possible.

The swap **changes the state commitment only** — no gas or opcode semantics move with
it. `EXTCODEHASH` and similar stay byte-identical across `S` because
`code_hash = keccak256(bytecode)` is independent of the tree hash.

## Historical context: the four Verkle-transition options

The "offline conversion" choice is best understood against the **earlier Verkle-era
survey** of migration options
([notes.ethereum.org/@parithosh/verkle-transition](https://notes.ethereum.org/@parithosh/verkle-transition)).
It predates PBT and targeted the Verkle tree, but the transition
problem — moving live mainnet state from the MPT to a new commitment without splitting
the chain — is the same, so it's the direct ancestor of today's roadmap. It compared
four approaches:

1. **Overlay (live) conversion.** Base MPT is frozen read-only; an initially-empty
   overlay tree takes all writes. A per-block iterator advances a "conversion boundary"
   (N keys/block); reads check overlay then MPT. Minimal disk, reorg-resilient,
   verification folded into consensus — but every client's DB differs (custom work per
   client), snapshot sync gets complex, and MPT↔new-tree gas discrepancies open attack
   vectors. Sizing: ~220M accounts + 600M slots in one month needs **N ≥ 4,873** keys
   per block (~3× a typical block's state touches). *Most developed of the four.*
2. **Conversion-node method.** Dedicated nodes go offline at `fork_begin`, convert the
   whole state, and distribute it (torrent/CDN) before `fork_end`; regular nodes keep
   running and replay accumulated payloads to catch up. Uses specialized hardware, low
   network-wide CPU (fewer missed slots) — but needs **2× disk** during conversion,
   complex reorg handling, and nodes offline at `fork_begin` lack replay messages.
3. **Local bulk conversion.** Every node converts its own state locally at `fork_begin`,
   then replays payloads to the tip; all switch at `fork_end`. Ideologically clean and
   easy to test — but **>2× disk**, heavy live-conversion overhead risking missed
   validator slots, hard reorg handling, and it may not even be feasible on some client
   DBs / low-powered machines.
4. **State-expiry method.** Freeze the MPT, start a fresh "era" on the new tree; reads
   fall back to the frozen MPT; an offline conversion runs in the background over
   months. "No transition needed" and no per-node transition work — but adds a long
   research dependency, state keeps growing meanwhile, and **all** MPT data plus
   preimages must be retained throughout.

| Aspect | Overlay | Conversion nodes | Local bulk | State expiry |
| --- | --- | --- | --- | --- |
| Disk overhead | Minimal | 2× | >2× | Minimal |
| Client complexity | High | Medium | Very High | Medium |
| Network resilience | High | Medium | Medium | High |
| Conversion duration | ~1 month | Flexible | Variable | Months OK |
| Research maturity | Advanced | Moderate | Moderate | Preliminary |

### How these compare with the PBT offline migration

The PBT roadmap is **not** any one of these four — it's closest to the
**conversion-node method** (convert once off the live path, distribute a snapshot,
replay to catch up), refined with modern tooling and a safety-first framing:

- **vs Overlay (the Verkle front-runner).** The PBT roadmap deliberately rejects the
  online/overlay family. Overlay's headline wins — no distribution event, gentle disk,
  consensus-integrated verification — are exactly what the roadmap concedes online does
  better, but it judges them "engineering costs with known tools" and prefers offline's
  safety: **no consensus-critical conversion code**, failures surface *before* consensus
  depends on the new tree, and full recoverability until activation. It also sidesteps
  overlay's live MPT↔new-tree **gas-discrepancy attack surface**, since both trees are
  never simultaneously consensus-live.
- **vs Conversion-node method.** Same skeleton (offline convert → distribute → replay),
  but the roadmap hardens the weak points the original flagged: **BAL-replay**
  (EIP-7928) replaces ad-hoc "catch-up messages" and needs no re-execution; a
  **byte-canonical, chunked, PBT-key-sorted snapshot** with release-anchored manifest
  hashes makes distribution verifiable rather than trust-based; and **dual-check
  verification** (internal PBT consistency + consensus-anchoring against block `N`'s
  MPT `stateRoot`) lets even a fresh node trust the artifact. The "2× disk during
  conversion" cost is accepted but confined to converters, not every validator.
- **vs Local bulk.** The roadmap explicitly avoids forcing **every node** to convert
  live — the ">2× disk + missed-slots" failure mode of local bulk. Only converters pay
  that; everyone else ingests a snapshot as a sequential bulk-load.
- **vs State expiry.** State expiry is really a *deferral* (freeze + convert lazily over
  months). The PBT design borrows its best structural idea — a frozen MPT plus a fresh
  tree that starts empty and takes only new writes (this is literally how EIP-8297's
  tree begins; see [05-design-evolution.md](05-design-evolution.md)) — but commits to a
  bounded, anchored conversion at block `N` and a definite fork `S`, rather than an
  open-ended research dependency. State expiry proper is left to a **separate future
  EIP** ([../open-questions.md](../open-questions.md)).

**Net:** the four options traded off disk, client complexity, network resilience, and
duration; the PBT roadmap picks the offline/snapshot branch and spends engineering
effort (BAL-replay, canonical snapshots, dual verification, shadow-root observability)
to neutralize that branch's classic downsides — distribution trust and catch-up
correctness — in exchange for keeping conversion entirely off the consensus-critical path.

## Six-phase program timeline

The roadmap's project schedule (P0–P6). This is a *program* view; do not conflate it
with the EIP's five-phase protocol lifecycle (discrepancy [D3](#source-discrepancies-to-reconcile),
and the lifecycle is summarized under [Migration lifecycle](#migration-lifecycle-the-eip-view) below).

| Phase | Name | Key work |
|-------|------|----------|
| **0** | Spec Convergence *(in flight)* | Finalize the PBT spec with all client teams; remove design contention before implementation. |
| **1** | Prototypes & Evidence | Client PBT implementations; test-suite ports (EEST); conversion/replay vector suites; preimage format & generation pipeline; state-op benchmarks; begin ecosystem outreach. |
| **2** | Devnets | Multi-client PBT-genesis networks; PBT-native state sync; snapshot serving & verification; end-to-end distribution plumbing. |
| **3** | Migration Machinery | Converter across clients; BAL-replay engine; snapshot production pipeline; full-cycle devnet including the swap. |
| **4** | Rehearsals | Production runs on mainnet state; hardware-matrix testing (EIP-7870); public testnet migrations with swaps; mainnet shadow fork; performance metrics. |
| **5** | Mainnet Window | Select finalized block `N`; produce & cross-verify snapshot; distribute via torrent + mirrors; BAL-replay to chain tip; shadow commitment period (attesters publish signed roots); pass readiness gate. `N` is announced **only after Phase 4** completes. |
| **6** | Swap & Aftermath | Fork `S` makes PBT canonical; keep MPT until finality; sunset snapshot & dispose MPT; restore fresh-node sync. |

### Migration lifecycle (the EIP view)

The EIP frames the same process as **five protocol-lifecycle phases**, each a pure
function of the state committed by `ANCHOR_BLOCK`'s `stateRoot`, none touching the
consensus-critical path:

1. **Conversion (off-chain)** — extract [preimages](#preimages--why-theyre-needed) at `ANCHOR_BLOCK`, then
   run the [converter](#the-converter) to produce the [PBT snapshot](#snapshot-distribution).
2. **Distribution and verification** — publish artifacts; every node runs the
   [dual-check](#verification--dual-check-authentication).
3. **Catch-up** — [BAL-replay](#bal-replay) from `ANCHOR_BLOCK` to the tip; distributors
   [re-anchor](#re-anchoring--late-joiners) on a fixed cadence to bound the replay gap.
4. **Shadow-commitment period** — attesters publish signed
   [shadow roots](#shadow-commitment--observability) while consensus still runs on the MPT.
5. **Swap and transition window** — at `SWAP_FORK` the PBT becomes canonical; both trees
   are held until finality, after which the MPT may be disposed.

## Two migration paths for node operators

Every node reaches a verified, tip-tracking PBT by one of two paths. Most operators take
Option B; expert operators and distribution sources take Option A.

### Option A — Self-migrate (expert path)

**Prerequisites:** a client release with passing vector suites; **300–500 GB** disk
headroom for the PBT DB (discrepancy [D4](#source-discrepancies-to-reconcile)); the
keccak-preimage file (**hash-keyed clients only** — geth/Nethermind/Besu; reth/erigon
skip it); BAL retention from the conversion base through the swap plus margin; and a
recent locally finalized block to anchor on.

**Two modes:**
- **STOPPED** — node offline; fastest conversion (hours to days).
- **ALONGSIDE** — live node keeps following the chain; considerably slower under IO/CPU
  contention. Hardware that can only just keep up (`k ≤ 1`) **cannot** use this mode.

**Procedure (12 steps):** choose a finalized starting point → pin the state view →
create an isolated PBT store → assemble preimage coverage (hash-keyed only) → scan and
bind (`keccak256(preimage) == path` for every leaf) → derive PBT keys → zone-sharded
external merge-sort → single sequential bottom-up build → seal with an atomic watermark →
resume node operation → BAL-replay from the watermark → checkpoint-compare against
published roots.

### Option B — Download snapshot (majority path)

Distribution at scale: **~10⁴ nodes × ~150 GB ≈ 1–2 PB** to move within the
release-adoption window.

**Both dual-checks are mandatory** (see [Verification](#verification--dual-check-authentication)).
**Procedure (9 steps):** obtain release-baked expectations (`N` hash, PBT root, manifest
digest) → anchor `N` in the local canonical header chain → fetch and verify the manifest
digest → chunked download with per-chunk hash verification on arrival → assemble/stream
verified chunks → run Check 1 while ingesting → run Check 2 (MPT rebuild from the same
stream) → diagnostic report on any failure → BAL-replay from `N` to tip.

**Trust tiers** (decreasing artifact trust, increasing cost):

| Tier | What it trusts | Cost |
|------|----------------|------|
| **Full verification** (Checks 1+2) | Nothing beyond `N`'s `stateRoot` from its own header chain | ~one full conversion |
| **Manifest tier** | Release-baked root; skips Check 2 | Requires explicit opt-out flag |
| **Self-convert at `M`** | Nothing (own state) | Conversion cost |
| **Archive audit-at-`N`** | Nothing (independent rebuild from own history) | Archive rebuild |

## Key machinery

### The Converter

A deterministic function translating MPT state to PBT. Given the state at `ANCHOR_BLOCK`
(MPT snapshot + preimages), it:
1. Scans source (MPT) leaves.
2. Validates `keccak256(preimage)` matches trie paths.
3. Derives PBT keys per [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297).
4. For each account with code, fetches bytecode by `code_hash`, chunks it, and emits the
   code leaves (the `0x01` code zone).
5. **External merge-sort** by PBT key order.
6. Sequential **bottom-up** tree construction (single pass).

Independent, correct converters on the same `ANCHOR_BLOCK` state **MUST produce a
bit-identical PBT root and snapshot**. The PBT-key sort order lets ingestion be a
sequential **bulk-load** rather than random inserts. A self-converter's input needs no
separate provenance check — its correctness is already established by having executed the
chain to `ANCHOR_BLOCK` and matched the header `stateRoot`.

### BAL-replay

**Block-Level Access Lists (EIP-7928)** enable state transition **without
re-execution**. Per-entry translation rules apply each block's writes to the PBT
(balance/nonce changes, storage writes, code deployments):
- **Zero-writes delete leaves** — a value of zero is encoded as leaf *absence*, so a
  replayed zero-write deletes an existing leaf or is a no-op, never inserts. This matches
  MPT semantics and keeps independently converged PBTs bit-identical.
- **Account deletion needs no special BAL marker.**
- Batching bounds replay cost while keeping the replay rate **below** steady-state block
  production, so the snapshot converges to and then tracks the tip.

The EIP distinguishes **two regimes**: *finalized-only* (installation → shadow period; no
journal, batching unconstrained) and *tip-following* (shadow period on; a pre-value
journal ~2 epochs deep handles reorgs within the journal horizon). A **batch-boundary
alignment rule** applies when comparing at a checkpoint height `h` (a re-anchor or a
shadow-covered block): close the batch exactly at `h` before continuing to `h+1`.

Used to catch a converted snapshot up from anchor `N` to chain tip, and to close the gap
when preimages are extracted at an earlier height `E`: BAL-completion over `(E, N]`
ensures completeness.

### Snapshot distribution

- Artifact is **~100+ GB**, **byte-canonical** serialization → bit-identical output
  across independent producers.
- Formal layout (EIP-8347): a small header `pbtRoot[32] | leafCount[8, big-endian]`
  followed by the sorted `leafRecord` stream. Each leaf record is `key[keyLen] |
  value[32]`, self-delimiting because the leading **zone byte** of the key fixes `keyLen`
  (`0x00` account header → 34, `0x01` code → 34, `0xFF` storage → 66).
- The snapshot carries **only leaves — no intermediate nodes**. Every node reconstructs
  the inner nodes locally during verification; the only inner value shipped is the single
  claimed `pbtRoot`, which is recomputed and checked, never trusted.
- Sorted in **PBT-key order** for bulk ingestion. How the artifact is split for transport
  is left to the distribution layer (snap-sync-style P2P, era files, CDNs, torrents),
  which already provide partial-download integrity and resumption; a chunk-hash index is
  an optional, non-normative accelerator.

### Preimages — why they're needed

MPT state **cannot be iterated backward into raw keys** (it's hash-keyed, and most
clients don't persist plain addresses/slot keys). Preimages serve (a) self-converters on
hash-keyed clients (geth, Nethermind, Besu) and (b) verifiers doing the consensus-anchoring
check. They **MUST** be extracted at `ANCHOR_BLOCK`. Extraction at an earlier height `E`
from raw-keyed nodes + BAL-completion over `(E, N]` gives completeness.

Formal file layout (EIP-8347): a concatenation of self-delimiting per-account records,
`address[20] | slotCount[4, big-endian] | slotKey[32] * slotCount`, sorted by `address`
ascending (byte-lexicographic, each address once) and slot keys sorted ascending within a
record (no duplicates). A verifier recovers MPT paths as `keccak256(address)` and
`keccak256(slotKey)`.

## Verification — dual-check authentication

Any node — **including a fresh one with no prior state** — can verify a downloaded
snapshot without trusting the distribution source. Both checks are mandatory; a snapshot
failing either **MUST** be rejected:

1. **Internal PBT consistency** — rebuild the PBT from snapshot leaves, derive keys,
   hash bottom-up, verify the claimed PBT root. (This step is also where each node
   *derives the full tree for itself*, since inner nodes are not shipped.)
2. **Consensus anchoring** — rehash snapshot leaves under the **MPT schema** using
   distributed preimages, verify against block `N`'s header `stateRoot` (taken from the
   node's own header chain). A fabricated but internally self-consistent package still
   fails here.

## Hash domains

Which hash function operates in each domain. **Caveat:** the roadmap names BLAKE3, but the
hash `H` is still an **open parameter** (BLAKE3 / Poseidon2 / Keccak) and the EIP defers
to EIP-8297 rather than naming it — see discrepancy
[D2](#source-discrepancies-to-reconcile) and
[../open-questions.md](../open-questions.md#hash-function-selection--the-dominant-open-parameter).
Treat the BLAKE3 entries below as *reference-implementation, not final*.

| Domain | Hash function |
|--------|--------------|
| MPT paths, `codeHash` | Keccak256 (unchanged forever) |
| PBT key derivation, internal-node hashing | BLAKE3 *(unpinned — see caveat)* |
| Artifact / preimage / manifest hashes | BLAKE3 (snapshots) or keccak256 (self-migration) |

Raw keys (addresses, storage slots) are the **shared preimage of both tree domains**.

## Shadow commitment & observability

During the pre-swap period, **attesters compute the PBT root of each block's post-state and
publish it, signed with their validator key** (shadow roots), while consensus still runs on
the MPT. Conversion correctness thus becomes visible per block, publicly and attributably:
signing makes every report attributable and verifiable, and sourcing reports from
*attesters* rather than from block producers measures the **validating majority**. A missing
or late root counts against a **coverage** metric, never as a divergence (preserving
interpretability).

The carrier is an **out-of-consensus telemetry sidecar**. Publication stays a `SHOULD` and
is **never a block-validity condition** — enforcing it would force every validator to
compute the PBT post-state root per block, putting PBT construction back on the
consensus-critical path, the exact property the offline design exists to avoid. The sidecar
is **expected to ship enabled by default in CL clients**, so coverage comes from ordinary
validator operation rather than an opt-in program; that default-on posture is an
*operational commitment* of the client teams, not a protocol requirement. The wire format,
aggregation scheme, publication timing, and any EL→CL plumbing are **out of scope here and
fixed in a companion specification** (see
[../open-questions.md](../open-questions.md#shadow-root-publication--the-companion-specification)).
This architecture is **settled and agreed** across the roadmap, EIP-8347, and this
knowledge base.

**Readiness gates** before the activation release (the thresholds themselves remain open
parameters):
- Cross-client agreement **≥ X%** sustained **D** days.
- Coverage **≥ Y%**.
- Builder / relay ecosystem readiness — PBT capability is a **hard prerequisite for
  `SWAP_FORK`**, since post-swap an MPT-only builder produces invalid blocks. This is a
  separate readiness concern from observability, not a publication role.

## Testing framework (EEST coverage)

The roadmap enumerates the test surface (built out in Phase 1):
- Ported execution-spec-tests (root representation only).
- PBT-structural unit tests (zones, stems, key derivation).
- Adversarial / structural-cost suites (spam patterns, chunk floods).
- Code-chunking suite (chunk boundaries, padding, dedup).
- BAL-replay vector suite (pre-state + BAL → expected post-root).
- State-op benchmarks (PBT vs MPT under current gas).
- Dual-DB performance suites (concurrent MPT load; batched / per-block).
- Devnet adversarial workloads (sustained hostile traffic).
- Rehearsal acceptance runs (byte-identical snapshots; convergence `k > 1`).

## Parameters

| Symbol | Meaning | When fixed |
|--------|---------|-----------|
| `ANCHOR_BLOCK` (`N`) | Anchor block whose state is converted (finalized, identified by hash) | Chosen after Phase 4 |
| `SWAP_FORK` (`S`) | EL+CL hard fork where PBT becomes canonical | Post-shadow period |
| `M` | A node's local conversion height (any block it has finalized) | Per-node |
| `REANCHOR_CADENCE` (`N′`) | Re-anchoring cadence for late joiners | EIP proposes **50400 blocks (~1 week)**; roadmap leaves generic ([D1](#source-discrepancies-to-reconcile)) |

**Open parameters (§14):** readiness thresholds (X, Y, D); preimage byte-level format
*(now specified in the EIP-8347 draft)*; snapshot chunk/transport encoding; the shadow-root
**companion specification** *(the carrier architecture is settled — only its wire format,
aggregation, timing and EL→CL plumbing remain)*; post-swap MPT disposal timing; `N′`
re-anchoring cadence;
proof-consumer dependencies (verification precompiles, `eth_getProof` successors).

### Re-anchoring & late joiners

The BAL-replay gap grows without bound as the chain advances, so a distributor re-runs
conversion at successive finalized anchors `ANCHOR_BLOCK + n · REANCHOR_CADENCE` and
publishes a fresh snapshot + preimage set for each. Each re-anchored snapshot is
self-contained (anchored to its own `stateRoot`, verified by the same dual-check, no
dependency on earlier anchors). A late joiner selects the most recent re-anchor at or
below finality and BAL-replays only from there. Re-anchor cadence **must** stay newer than
the BAL expiry window, or a late joiner won't have the BALs to replay from the chosen
anchor (see [../open-questions.md](../open-questions.md#re-anchor-cadence--bal-expiry)).

## Known weak points & mitigations

- **Unvalidated flip input.** `S` activates the pre-fork block's PBT root *without
  consensus validation*. Mitigation: hard-enforce the shadow root for the final blocks
  before `S`, or accept it given sustained cross-client agreement (a correlated
  all-client bug would be similarly undetectable anyway). Note the first option sits in
  tension with publication being out of consensus
  ([above](#shadow-commitment--observability)) and would need its own justification.
- **Fork-boundary reorg procedure.** A post-`S` head reorging to a pre-`S` fork point
  needs a concrete step-by-step specification before the swap EIP is finalized. Open in
  both the roadmap and the EIP (see
  [../open-questions.md](../open-questions.md#reorg-behavior-around-the-swap)).
- **Coverage rests on adoption, not enforcement.** Sourcing shadow roots from attesters
  means the signal already reflects the validating majority — there is no
  producers-only sampling gap. What remains is narrower: because publication is never a
  validity condition, the coverage metric is only as good as CL clients shipping the
  telemetry sidecar **enabled by default**. Mitigation: pre-swap divergence is harmless and
  self-detectable, and the coverage **≥ Y%** gate makes under-reporting hold back the
  activation release rather than pass unnoticed.
- **Distribution trust.** The ~100+ GB artifact is served off-chain. Neutralized by the
  dual-check: consensus anchoring against `ANCHOR_BLOCK`'s `stateRoot` means a fabricated
  package fails even if internally self-consistent. Transport-level integrity (torrent
  piece hashes, TLS, CDN checksums) drops bad segments on arrival.
- **Recoverability.** Both trees are held until `SWAP_FORK` is finalized; a fault at or
  just after the swap recovers by falling back to the MPT until the activation release
  deploys.

## Ecosystem impact

- **Contracts:** none — standard operations unchanged. Contracts still address storage by
  256-bit slot via `SLOAD`/`SSTORE`; PBT key derivation runs below the EVM.
- **Execution semantics / gas:** `SWAP_FORK` changes the state commitment **only** — gas,
  opcodes, tx validity unchanged across the swap. PBT-native gas repricing (chunk-granular
  code access, stem warm/cold semantics) is a **separate gas-repricing EIP**, deliberately
  decoupled from `S`. Direction matters for timing: a **price *increase*** (if PBT access
  is costlier) **MUST** activate at a fork *before* `S` to close the DoS window; a **price
  *decrease*** may activate *after* `S` (overcharging carries no DoS risk).
- **On-chain proof consumers:** significant — the eliminated `storage_root` in account
  headers and the new tree hash mean bridges, light-client verifiers, and `eth_getProof`
  consumers need coordinated upgrades. Longest lead time → started in Phase 1; tracked in
  the outreach workstream.
- **Fresh sync (interim):** `N′` snapshot + BAL-replay until PBT-native snap-sync ships.
