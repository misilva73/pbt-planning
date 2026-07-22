# B-S1 · Offline-migration EIP (new)

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2026-07 → 2026-10 (4 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Author a **new EIP** that specifies PBT's **offline-conversion** migration from the MPT to the
binary tree. The roadmap explicitly rejects the online/overlay family (Verkle-era
[EIP-7748](../../knowledge-base/07-sources.md), in-consensus state conversion, and
[EIP-7612](../../knowledge-base/07-sources.md), the overlay/fork transition mechanism) in favour of
converting the full state at a fixed anchor block, distributing a verifiable snapshot, and swapping
at a single fork. Rather than re-editing EIP-7748 to fit that model, this deliverable produces a
**standalone specification** — with EIP-7748/7612 cited as prior art — that defines anchor block
`N`, fork `S`, and the shadow-root concept, and that all downstream migration machinery specs build
on.

## Scope — what ships
- A new EIP (draft) specifying **offline** (not in-consensus) MPT→PBT conversion — conversion runs off the consensus-critical path.
- Definition of **anchor block `N`** (finalized, identified by hash) and its `stateRoot` as the conversion source and the consensus-anchoring target.
- Definition of **fork `S`** semantics: the EL+CL hard fork where PBT becomes canonical; the swap changes the state commitment *only* — no gas or opcode semantics move with it (`EXTCODEHASH` stays byte-identical because `code_hash = keccak256(bytecode)`).
- The **shadow-root** concept: per-block PBT roots published while consensus still runs on the MPT, making conversion correctness observable pre-swap.
- A **prior-art / rationale** section stating precisely what is borrowed from EIP-7748 (leaf-by-leaf conversion semantics) and EIP-7612 (frozen base tree + fresh tree that starts empty and takes new writes), and what is deliberately discarded (the live overlay iterator / in-consensus conversion-boundary machinery) — and why the offline model is preferred.
- Transition-window model: both trees maintained until finality after `S`.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — the PBT tree spec (key derivation, node types) must be converged before conversion semantics can be pinned.
- **Co-developed in parallel:** [B-S2](B-S2-preimage-snapshot-manifest-spec.md) — runs the same window (2026-07→2026-10); anchor `N` / conversion semantics are aligned jointly rather than sequentially.
- **Downstream (this blocks):** [B-S3](B-S3-bal-replay-spec.md), [B-C1](B-C1-converter-prototype.md).

## Owners / teams
- PBT / migration spec authors (EIP-8297 editors and the new-EIP authors).
- EF protocol support (fork-mechanism review, `N`/`S` semantics, EIP editorial process).
- EL client migration leads (geth, Nethermind, Besu, Reth, Erigon) as spec reviewers.

## Exit criteria (definition of done)
- [ ] New EIP assigned a number and merged as a draft, with the offline-conversion model and the rejection of the online overlay documented in the rationale.
- [ ] `N` and `S` semantics precisely defined (finalization requirement, hash identification, commitment-only swap).
- [ ] Shadow-root concept specified sufficiently for the carrier-mechanism work in [B-S4](B-S4-readiness-gate-activation-params.md).
- [ ] Reviewed and signed off by all EL client teams as the basis for the converter prototype.

## Risks & open questions
- Shadow-root **carrier mechanism** (how per-block PBT roots are published) is an open §14 parameter — see [04-migration.md §Parameters](../../knowledge-base/04-migration.md) and [06-open-questions.md](../../knowledge-base/06-open-questions.md); this deliverable defines the *concept*, its wire mechanism is fixed in B-S4.
- **Unvalidated-flip** weak point: `S` activates the pre-fork block's PBT root without consensus validation ([04-migration.md §Known weak points](../../knowledge-base/04-migration.md)); mitigation is specified downstream in B-S4.
- Tree-constant drift: the roadmap is design-agnostic but specific constants may lag EIP-8297; must re-sync if A-S1 changes header-stem constants.
- **EIP-process lead time:** a new EIP must clear number assignment and editor review; starting authoring early (month 2) de-risks the draft-merge exit criterion.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
