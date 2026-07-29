# B-C7 · Swap at fork S & aftermath

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2028-06 → 2028-08 (3 months) |
| **Migration phase** | Phase 6 — Swap & Aftermath |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Activate **fork `S` (= I\*)**, making PBT the canonical state commitment, and land
the aftermath cleanly. The swap changes the state commitment **only** — no gas or
opcode semantics move with it (`EXTCODEHASH` stays byte-identical since
`code_hash = keccak256(bytecode)` is independent of the tree hash). After
activation, keep the MPT until finality, then sunset the snapshot and dispose of
the MPT, and restore fresh-node sync onto the PBT.

## Scope — what ships
- **Fork `S` activation**: at the fork block, PBT becomes canonical; the block's
  PBT root is the consensus state commitment going forward.
- **Dual-tree window to finality**: the MPT is retained and kept in sync until the
  activation block is finalized, preserving full recoverability up to that point.
- **MPT disposal & snapshot sunset**: once finalized, dispose of the MPT and
  retire the distributed snapshot artifact.
- **Fresh-node sync restored**: new nodes sync directly onto the PBT (no longer
  via the migration snapshot).
- **Unvalidated-flip-input hardening**: apply the mitigation chosen in
  [B-S2](B-S2-readiness-gate-activation-params.md) — either hard-enforce the **shadow
  root** for the final blocks before `S` (the one narrow case where enforcement is on
  the table; routine shadow-root publication stays out of consensus), or document
  reliance on the sustained cross-client agreement accumulated over the shadow period.
- **Builder / relay PBT capability at the fork boundary**: from the first post-fork
  slot, whoever builds a block computes the PBT root as consensus, so every builder and
  relay in the block-production path must be PBT-capable *before* `S` — an MPT-only
  builder produces invalid blocks. Readiness is driven by
  [B-O3](B-O3-shadow-root-ecosystem-readiness.md) and confirmed at the gate.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section). Every
  client flips its canonical commitment to PBT at `S` and must agree on the
  post-swap root; MPT-disposal mechanics differ by DB model.

## Dependencies
- **Upstream (blocks this):** [B-C6](B-C6-mainnet-window.md) (block `N`, snapshot, replay, readiness gate passed), [B-S2](B-S2-readiness-gate-activation-params.md) (activation params for `S`)
- **Downstream (this blocks):** — (terminal deliverable; PBT is canonical)

## Exit criteria (definition of done)
- [ ] Fork `S` activates: PBT is the canonical state commitment and blocks
      finalize on the PBT root, with cross-client agreement.
- [ ] The commitment-only nature is confirmed: gas/opcode semantics unchanged;
      `EXTCODEHASH` byte-identical across `S`.
- [ ] MPT retained until the activation block finalizes, then disposed; snapshot
      artifact sunset.
- [ ] Fresh-node sync onto the PBT works without the migration snapshot.
- [ ] The unvalidated-flip-input weak point is closed by the mitigation chosen in
      [B-S2](B-S2-readiness-gate-activation-params.md) — a hard-enforced shadow root for
      the final pre-`S` blocks, or documented reliance on sustained cross-client agreement.
- [ ] Builders and relays in the block-production path are **PBT-capable** at the fork
      boundary, so post-fork blocks are valid from the first slot.

## Risks & open questions
- **Unvalidated flip input.** `S` activates the pre-fork block's PBT root *without
  consensus validation*. Mitigation: hard-enforce the shadow root for the final
  blocks before `S` (or accept it given sustained cross-client agreement — a
  correlated all-client bug would be similarly undetectable). This is the one narrow
  case where enforcing a shadow root is on the table; routine publication during the
  shadow period stays out of consensus, since enforcing it generally would put PBT
  construction back on the consensus-critical path.
- **Builder / relay PBT capability.** Post-swap the PBT root is consensus for whoever
  builds the block, so an MPT-only builder or relay produces invalid blocks from the
  first post-fork slot. This readiness must be confirmed before `S`
  ([B-O3](B-O3-shadow-root-ecosystem-readiness.md)) and is independent of shadow-root
  coverage, which is sourced from attesters.
- **Post-swap MPT disposal timing (§14)** is open — dispose too early and
  recoverability is lost; too late and disk cost lingers.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
