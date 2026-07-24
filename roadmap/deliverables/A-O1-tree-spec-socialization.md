# A-O1 · Tree Spec Socialization

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Outreach |
| **Timeline** | 2026-07 → 2027-03 (9 months) |
| **Migration phase** | Phase 0-1 |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Drive EIP-8297 through the community governance process — ACDE (All Core Devs Execution) and ACDC (Consensus) calls — build researcher and client-team alignment around the current EIP-8297 design, and get PBT onto the H\*/I\* fork-scoping agenda. This outreach pairs directly with the spec-convergence work in [A-S1](A-S1-eip8297-spec-convergence.md): A-S1 secures the agreed base design, A-O1 secures the social and governance buy-in that makes convergence and eventual freeze real.

## Scope — what ships
- Recurring presentation of the current EIP-8297 design at ACDE/ACDC calls, with tracked follow-ups.
- Researcher alignment on the design rationale: unified binary tree, arity-2 witness minimization, no `storage_root` (parallel root computation), zone partitioning, content-addressed code, and the hash-only post-quantum posture.
- Client-team alignment: a shared understanding of the two-node model and full-digest keys, and a channel for design objections to feed back into [A-S1](A-S1-eip8297-spec-convergence.md).
- **Correcting stale public material**: the third-party rendered spec site (cperezz.github.io/pbt-spec) may still describe the earlier draft (fixed 32-byte keys, 4-bit/3-bit zone prefixes, `StemNode`); outreach must ensure the community reasons about the current EIP-8297 design, not superseded numbers.
- PBT placed on the H\* (and I\*/fork-S) fork-scoping agenda as a candidate.
- Meeting notes / call agenda items, alignment write-ups, and an agreed path to CFI at H\*.

## Dependencies
- **Upstream (blocks this):** none as a hard blocker; runs in parallel with and is paired to [A-S1](A-S1-eip8297-spec-convergence.md).
- **Downstream (this blocks):** [A-S3](A-S3-eip8297-spec-freeze.md) depends on the H\* CFI agenda slot this outreach secures. Successful socialization also de-risks the migration outreach thread ([B-O1](B-O1-proof-consumer-coordination.md)).

## Owners / teams
- EIP-8297 authors and EF research (present and defend the design).
- Protocol-support / governance coordinators (ACDE/ACDC facilitation, agenda placement).
- EL client-team representatives (alignment partners; objection channel back into [A-S1](A-S1-eip8297-spec-convergence.md)).

## Exit criteria (definition of done)
- [ ] EIP-8297 presented at ACDE/ACDC with recorded consensus to proceed.
- [ ] Researcher and client-team alignment on the current EIP-8297 design documented (no unresolved blocking objections carried outside the spec process).
- [ ] Stale public material flagged/corrected or clearly annotated as superseded.
- [ ] PBT explicitly on the H\*/I\* fork-scoping agenda as a CFI candidate.

## Risks & open questions
- Divergence between published material and the current design is a live source of confusion; outreach must actively counter it. See [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md).
- The unresolved hash-function choice (the [hash-function dependency](../README.md)) means outreach cannot promise a fully pinned spec during this window; messaging must frame `H` as an open decision with a clear path, not a gap.
- Fork-scoping competition: H\* is a shared agenda and PBT must win a CFI slot against other candidates. (Its protocol prerequisites — BAL EIP-7928, 64 KiB code EIP-7954 — already ship in Glamsterdam ~2026-09, so they are not competing for H\* scope.)
- Migration-parameter open questions (readiness thresholds, shadow-root carrier) are outreach-adjacent but owned by the B thread; A-O1 scope is the tree spec itself. See [open-questions.md](../../open-questions.md).

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md) (design goals / rationale)
- [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md) (stale-material warning)
- [open-questions.md](../../open-questions.md)
- [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297); ACDE/ACDC process.
