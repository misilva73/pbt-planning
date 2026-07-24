# 04 — MPT → PBT Migration Roadmap

> Source: **"MPT → PBT: Ethereum State Migration Roadmap"**
> ([hackmd.io/@CPerezz/H1Q2zt8NMe](https://hackmd.io/@CPerezz/H1Q2zt8NMe)).
> This is a *strategy* document; specific tree constants may lag the latest EIP design
> (see [05-design-evolution.md](05-design-evolution.md)). The migration approach itself
> is largely design-agnostic.

## The core decision: offline conversion (not online overlay)

The roadmap explicitly chooses **offline conversion** over an online overlay approach.

The shape of it:
1. Convert the full state at a **fixed anchor block `N`**.
2. Distribute the result as a **verifiable snapshot**.
3. Maintain **both trees** during a transition window.
4. Activate the PBT at **fork `S`**, making it canonical.

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
([notes.ethereum.org/@parithosh/verkle-transition](https://notes.ethereum.org/@parithosh/verkle-transition),
Parithosh Jayanthi). It predates PBT and targeted the Verkle tree, but the transition
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

## Six-phase timeline

| Phase | Name | Key work |
|-------|------|----------|
| **0** | Spec Convergence *(in flight)* | Finalize the PBT spec with all client teams; remove design contention before implementation. |
| **1** | Prototypes & Evidence | Client PBT implementations; test-suite ports (EEST); conversion/replay vector suites; preimage format & generation pipeline; state-op benchmarks; begin ecosystem outreach. |
| **2** | Devnets | Multi-client PBT-genesis networks; PBT-native state sync; snapshot serving & verification; end-to-end distribution plumbing. |
| **3** | Migration Machinery | Converter across clients; BAL-replay engine; snapshot production pipeline; full-cycle devnet including the swap. |
| **4** | Rehearsals | Production runs on mainnet state; hardware-matrix testing (EIP-7870); public testnet migrations with swaps; mainnet shadow fork; performance metrics. |
| **5** | Mainnet Window | Select finalized block `N`; produce & cross-verify snapshot; distribute via torrent + mirrors; BAL-replay to chain tip; shadow commitment period (builders publish roots); pass readiness gate. |
| **6** | Swap & Aftermath | Fork `S` makes PBT canonical; keep MPT until finality; sunset snapshot & dispose MPT; restore fresh-node sync. |

## Key machinery

### The Converter

A deterministic function translating MPT state to PBT:
1. Scan source (MPT) leaves.
2. Validate `keccak(preimage)` matches trie paths.
3. Derive PBT keys.
4. **External merge-sort** by PBT key order.
5. Sequential **bottom-up** tree construction.

Includes security checkpoints and resumability markers. The PBT-key sort order lets
ingestion be a sequential **bulk-load** rather than random inserts.

### BAL-replay

**Block-Level Access Lists (EIP-7928)** enable state transition **without
re-execution**. It applies per-block state writes using translation rules per entry
type (balance/nonce changes, storage writes, code deployments):
- **Zero-writes delete leaves** (zeros encoded as absence, in the migration context).
- **Account deletion needs no special BAL marker.**
- Batching bounds replay cost while keeping convergence below steady-state block
  production rate.

Used to catch a converted snapshot up from anchor `N` to chain tip, and to close the
gap when preimages are extracted at an earlier height `E`: BAL-completion over `(E, N]`
ensures completeness.

### Snapshot distribution

- Artifact is **~100+ GB**, **byte-canonical** serialization → bit-identical output
  across independent producers.
- Chunked distribution with **release-anchored manifest hashes** → per-chunk
  verification.
- Sorted in **PBT-key order** for bulk ingestion.

### Preimages — why they're needed

MPT state **cannot be iterated backward into raw keys** (it's hash-keyed). Preimages
serve (a) self-converters on hash-keyed clients (geth, Nethermind, Besu) and
(b) verifiers doing the consensus-anchoring check. Extraction at height `E` from
raw-keyed nodes + BAL-completion over `(E, N]` gives completeness.

## Verification — dual-check authentication

Any node — **including a fresh one with no prior state** — can verify a downloaded
snapshot without trusting the distribution source:

1. **Internal PBT consistency** — rebuild the PBT from snapshot leaves, derive keys,
   hash bottom-up, verify the claimed PBT root.
2. **Consensus anchoring** — rehash snapshot leaves under the **MPT schema** using
   distributed preimages, verify against block `N`'s header `stateRoot`.

## Shadow commitment & observability

During the pre-swap period, **builders compute and publish per-block PBT roots** while
consensus still runs on the MPT. Conversion correctness thus becomes visible per block,
publicly and attributably. Omissions count against **coverage** metrics rather than
divergence (preserving interpretability).

**Readiness gates** before the activation release:
- Cross-client agreement **≥ X%** sustained **D** days.
- Coverage **≥ Y%**.
- Builder / relay ecosystem readiness.

## Parameters

| Symbol | Meaning | When fixed |
|--------|---------|-----------|
| `N` | Anchor block whose state is converted (finalized, identified by hash) | Chosen after Phase 4 |
| `S` | EL+CL hard fork where PBT becomes canonical | Post-shadow period |
| `M` | A node's local conversion height (any block it has finalized) | Per-node |
| `N′` | Re-anchoring cadence for late joiners | Open (§14) |

**Open parameters (§14):** readiness thresholds (X, Y, D); preimage byte-level format;
snapshot chunk encoding; shadow-root carrier mechanism; post-swap MPT disposal timing;
`N′` re-anchoring cadence; proof-consumer dependencies (verification precompiles,
`eth_getProof` successors).

## Known weak points & mitigations

- **Unvalidated flip input.** `S` activates the pre-fork block's PBT root *without
  consensus validation*. Mitigation: hard-enforce the shadow root for the final blocks
  before `S`, or accept it given sustained cross-client agreement (a correlated
  all-client bug would be similarly undetectable anyway).
- **Validator observability gap.** The builder stream measures block *producers*, not
  the validating majority. Mitigation: pre-swap divergence is harmless and
  self-detectable; a proposer-signed post-import sidecar is the designed fallback.

## Ecosystem impact

- **Contracts:** none — standard operations unchanged.
- **On-chain proof consumers:** significant — the eliminated `storage_root` in account
  headers and the new tree hash mean these systems need coordinated upgrades. Tracked
  in the outreach workstream (longest lead time → started in Phase 1).
- **Post-swap gas:** PBT-native gas improvements (chunk-granular code access, stem
  warm/cold semantics) are previewed separately and **deliberately decoupled** from the
  state-commitment fork `S`.
