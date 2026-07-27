# B-S1 · Offline-migration EIP (new)

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2026-07 → 2026-12 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | In progress — **EIP-8347** drafted and opened as [PR #12006](https://github.com/ethereum/EIPs/pull/12006) (2026-07-23, awaiting editor consensus; not yet merged) |

← [Back to roadmap](../README.md)

> **Update (2026-07).** This EIP now exists as a draft: **EIP-8347 — Offline State Migration
> to the PBT** ([PR #12006](https://github.com/ethereum/EIPs/pull/12006), authors Perez /
> Silva / Wedderburn; `requires: 7928, 8297`). The draft already specifies the conversion
> model (`ANCHOR_BLOCK` / `SWAP_FORK`), the preimage and snapshot byte formats, BAL-replay,
> the dual-check, and the shadow-root concept. **One scope divergence to reconcile:** this
> deliverable assumed the EIP would freeze a fixed-size stem-aligned **chunk encoding** and a
> **release-anchored manifest** as the verification anchor. EIP-8347 instead leaves transport
> chunking to the distribution layer, makes the chunk-hash index **optional / non-normative**,
> and makes the **dual-check against `ANCHOR_BLOCK`'s `stateRoot`** the root of trust (a
> release-pinned `pbtRoot` is optional hardening only). The chunk/manifest exit criteria below
> are updated accordingly. See
> [04-migration.md § Source discrepancies](../../knowledge-base/04-migration.md#source-discrepancies-to-reconcile).

## Objective
Author a **single new EIP** that specifies PBT's **offline-conversion** migration from the MPT to
the binary tree, end to end. The roadmap explicitly rejects the online/overlay family (Verkle-era
[EIP-7748](../../knowledge-base/07-sources.md), in-consensus state conversion, and
[EIP-7612](../../knowledge-base/07-sources.md), the overlay/fork transition mechanism) in favour of
converting the full state at a fixed anchor block, distributing a verifiable snapshot, and swapping
at a single fork. Rather than re-editing EIP-7748 to fit that model, this deliverable produces a
**standalone specification** — with EIP-7748/7612 cited as prior art — that binds together, in one
document, the conversion model (anchor block `N`, fork `S`, shadow-root concept), the byte-canonical
snapshot/preimage/manifest formats, the BAL-replay catch-up mechanism, and the dual-check
verification procedure.

> **Scope note.** This deliverable was previously tracked as three separate specs (offline-migration
> EIP, preimage/snapshot-manifest, BAL-replay). They are authored as **one EIP**, so they are now a
> single deliverable.

## Scope — what ships
A new EIP (draft) specifying **offline** (not in-consensus) MPT→PBT conversion, covering:

- **Conversion model** — conversion runs off the consensus-critical path; **anchor block `N`**
  (finalized, identified by hash) and its `stateRoot` are the conversion source and consensus-anchoring
  target; **fork `S`** semantics where PBT becomes canonical and the swap changes the state commitment
  *only* (no gas/opcode semantics move; `EXTCODEHASH` stays byte-identical because
  `code_hash = keccak256(bytecode)`); a **transition window** keeping both trees until finality after `S`.
- **Shadow-root** concept — per-block PBT roots published while consensus still runs on the MPT,
  making conversion correctness observable pre-swap.
- **Preimage file byte-level format** — the layout of MPT-key preimages required by (a) self-converters
  on hash-keyed clients (geth, Nethermind, Besu) and (b) verifiers doing the consensus-anchoring check.
- **Snapshot serialization** — byte-canonical (bit-identical across independent producers), sorted in
  **PBT-key order**. The artifact is a header (`pbtRoot | leafCount`) plus a self-delimiting leaf-record
  stream (zone byte fixes key length); it carries **only leaves**, no inner nodes. **Transport chunking
  is left to the distribution layer** (snap-sync-style P2P, era files, CDNs, torrents), not frozen in the
  EIP — a change from this deliverable's original assumption (see the update note above).
- **Manifest / chunk index** — **optional, non-normative** download accelerator only. The root of trust is
  the **dual-check against `ANCHOR_BLOCK`'s `stateRoot`**, not a release-anchored manifest; a client release
  MAY additionally pin the swap anchor's `pbtRoot` as optional hardening, but that cannot cover the
  after-release re-anchor snapshots.
- **BAL-replay** — per-entry translation rules ([EIP-7928](../../knowledge-base/07-sources.md) →
  PBT leaf mutations), zero-writes-delete-leaves / no-deletion-marker semantics, batching bounds, and
  the **`(E, N]` BAL-completion** procedure that closes the preimage-completeness gap and catches a
  snapshot up to tip without re-execution.
- **Dual-check verification** — internal PBT-consistency rebuild plus consensus-anchoring against `N`'s
  `stateRoot`, so any node (including a fresh one) can reject a bad artifact without trusting the source.
- A **prior-art / rationale** section stating what is borrowed from EIP-7748 (leaf-by-leaf conversion
  semantics) and EIP-7612 (frozen base tree + fresh tree taking new writes), what is discarded (the live
  overlay iterator / in-consensus conversion-boundary machinery), and why the offline model is preferred.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — the PBT tree spec (key derivation, node types) must be converged before conversion semantics can be pinned. Consumes **EIP-7928 (BAL)**, which ships in Glamsterdam (≈ 2026-09) and is assumed mainnet-live (out of scope here).
- **Downstream (this blocks):** [B-C1](B-C1-converter-prototype.md) (converter), [B-C2](B-C2-bal-replay-engine.md) (BAL-replay engine), [B-C3](B-C3-snapshot-production-pipeline.md) / [A-C4](A-C4-snapshot-serving-verification.md) (snapshot production & serving/verification), [B-T1](B-T1-conversion-replay-vectors.md) (conversion/replay vectors).

## Owners / teams
- PBT / migration spec authors (EIP-8297 editors and the new-EIP authors; serialization/manifest and BAL-replay editors).
- EF protocol support (fork-mechanism review, `N`/`S` semantics, EIP editorial process).
- EIP-7928 authors for BAL-format alignment (BAL already shipped in Glamsterdam).
- EL client migration leads (geth, Nethermind, Besu, Reth, Erigon) as spec + format reviewers.
- EF DevOps / distribution (torrent + mirror packaging) for manifest-anchoring review.

## Exit criteria (definition of done)
- [x] New EIP assigned a number and drafted, with the offline-conversion model and the rejection of the online overlay documented in the rationale — **EIP-8347, [PR #12006](https://github.com/ethereum/EIPs/pull/12006)** (draft open; merge pending editor consensus).
- [x] `ANCHOR_BLOCK` (`N`) and `SWAP_FORK` (`S`) semantics precisely defined (finalization requirement, hash identification, commitment-only swap) — in the draft.
- [ ] Preimage byte-level format and snapshot **artifact** serialization specified and frozen — **drafted** (preimage record + `pbtRoot | leafCount | leafRecord*` layouts); transport chunk encoding intentionally **out of scope** (distribution layer), so the §14 chunk-encoding item is *narrowed*, not closed here.
- [ ] Two independent implementations produce a **bit-identical** small-scale snapshot from the byte-canonical serialization. *(Manifest/chunk index is optional and non-normative — no longer an exit criterion; the dual-check is the verification anchor.)*
- [ ] BAL-replay translation rules for all four entry types, zero-write/no-marker semantics, batching bounds, and the `(E, N]` BAL-completion procedure specified and reviewed.
- [ ] Dual-check verification (internal consistency + consensus anchoring) specified.
- [ ] Shadow-root concept specified sufficiently for the carrier-mechanism work in [B-S2](B-S2-readiness-gate-activation-params.md).
- [ ] Reviewed and signed off by all EL client teams as the basis for the converter prototype.

## Risks & open questions
- Shadow-root **carrier mechanism** (how per-block PBT roots are published) is an open §14 parameter — see [04-migration.md §Parameters](../../knowledge-base/04-migration.md) and [open-questions.md](../../open-questions.md); this deliverable defines the *concept*, its wire mechanism is fixed in [B-S2](B-S2-readiness-gate-activation-params.md).
- **Unvalidated-flip** weak point: `S` activates the pre-fork block's PBT root without consensus validation ([04-migration.md §Known weak points](../../knowledge-base/04-migration.md)); mitigation is specified downstream in [B-S2](B-S2-readiness-gate-activation-params.md).
- **Preimage byte-level format** and **snapshot chunk encoding** are §14 parameters this EIP must close; chunk sizing trades verification granularity against overhead at ~100+ GB scale and must be validated at scale by [A-C4](A-C4-snapshot-serving-verification.md) and [B-T3](B-T3-dual-check-verification-scale.md).
- **External dependency on EIP-7928** — any late change to the shipped BAL format would ripple into the translation rules; replay correctness depends on BALs recording *all* writes needed for state transition, validated by [B-T1](B-T1-conversion-replay-vectors.md) vectors.
- Tree-constant drift: the roadmap is design-agnostic but specific constants may lag EIP-8297; must re-sync if [A-S1](A-S1-eip8297-spec-convergence.md) changes header-stem constants.
- **EIP-process lead time:** a new EIP must clear number assignment and editor review; starting authoring early (month 2) de-risks the draft-merge exit criterion.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [open-questions.md](../../open-questions.md)
