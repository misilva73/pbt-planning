# B-S1 · EIP-7748 → PBT adaptation

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2026-08 → 2027-02 (7 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Adapt the Verkle-era migration EIPs — [EIP-7748](../../knowledge-base/07-sources.md) (state
conversion to a binary tree) and [EIP-7612](../../knowledge-base/07-sources.md) (overlay/fork
transition mechanism) — to PBT's **offline-conversion** model. The roadmap explicitly rejects the
online/overlay family in favour of converting the full state at a fixed anchor block, distributing a
verifiable snapshot, and swapping at a single fork. This deliverable produces the authoritative spec
text that defines anchor block `N`, fork `S`, and the shadow-root concept, and that all downstream
migration machinery specs build on.

## Scope — what ships
- Spec text repurposing EIP-7748's leaf-by-leaf conversion for **offline** (not in-consensus) execution — conversion runs off the consensus-critical path.
- Definition of **anchor block `N`** (finalized, identified by hash) and its `stateRoot` as the conversion source and the consensus-anchoring target.
- Definition of **fork `S`** semantics: the EL+CL hard fork where PBT becomes canonical; the swap changes the state commitment *only* — no gas or opcode semantics move with it (`EXTCODEHASH` stays byte-identical because `code_hash = keccak256(bytecode)`).
- The **shadow-root** concept: per-block PBT roots published while consensus still runs on the MPT, making conversion correctness observable pre-swap.
- Explicit statement of what is borrowed from EIP-7612 (frozen base tree + fresh tree that starts empty and takes new writes) and what is discarded (the live overlay iterator / conversion-boundary machinery).
- Transition-window model: both trees maintained until finality after `S`.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — the PBT tree spec (key derivation, node types) must be converged before conversion semantics can be pinned.
- **Downstream (this blocks):** [B-S2](B-S2-preimage-snapshot-manifest-spec.md), [B-S3](B-S3-bal-replay-spec.md), [B-C1](B-C1-converter-prototype.md).

## Owners / teams
- PBT / migration spec authors (EIP-8297 and EIP-7748/7612 adaptation editors).
- EF protocol support (fork-mechanism review, `N`/`S` semantics).
- EL client migration leads (geth, Nethermind, Besu, Reth, Erigon) as spec reviewers.

## Exit criteria (definition of done)
- [ ] Adapted spec merged as a draft, with the offline-conversion model and the rejection of the online overlay documented in the rationale.
- [ ] `N` and `S` semantics precisely defined (finalization requirement, hash identification, commitment-only swap).
- [ ] Shadow-root concept specified sufficiently for the carrier-mechanism work in [B-S4](B-S4-readiness-gate-activation-params.md).
- [ ] Reviewed and signed off by all EL client teams as the basis for the converter prototype.

## Risks & open questions
- Shadow-root **carrier mechanism** (how per-block PBT roots are published) is an open §14 parameter — see [04-migration.md §Parameters](../../knowledge-base/04-migration.md) and [06-open-questions.md](../../knowledge-base/06-open-questions.md); this deliverable defines the *concept*, its wire mechanism is fixed in B-S4.
- **Unvalidated-flip** weak point: `S` activates the pre-fork block's PBT root without consensus validation ([04-migration.md §Known weak points](../../knowledge-base/04-migration.md)); mitigation is specified downstream in B-S4.
- Tree-constant drift: the roadmap is design-agnostic but specific constants may lag EIP-8297; must re-sync if A-S1 changes header-stem constants.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
