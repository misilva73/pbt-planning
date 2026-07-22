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
- **Unvalidated-flip-input hardening**: hard-enforce the **shadow root** for the
  final blocks before `S`, so `S` does not activate the pre-fork block's PBT root
  without a validated commitment.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section). Every
  client flips its canonical commitment to PBT at `S` and must agree on the
  post-swap root; MPT-disposal mechanics differ by DB model.

## Dependencies
- **Upstream (blocks this):** [B-C6](B-C6-mainnet-window.md) (block `N`, snapshot, replay, readiness gate passed), [B-S4](B-S4-readiness-gate-activation-params.md) (activation params for `S`)
- **Downstream (this blocks):** — (terminal deliverable; PBT is canonical)

## Exit criteria (definition of done)
- [ ] Fork `S` activates: PBT is the canonical state commitment and blocks
      finalize on the PBT root, with cross-client agreement.
- [ ] The commitment-only nature is confirmed: gas/opcode semantics unchanged;
      `EXTCODEHASH` byte-identical across `S`.
- [ ] MPT retained until the activation block finalizes, then disposed; snapshot
      artifact sunset.
- [ ] Fresh-node sync onto the PBT works without the migration snapshot.
- [ ] The final pre-`S` blocks have a **hard-enforced shadow root**, closing the
      unvalidated-flip-input weak point.

## Risks & open questions
- **Unvalidated flip input.** `S` activates the pre-fork block's PBT root *without
  consensus validation*. Mitigation: hard-enforce the shadow root for the final
  blocks before `S` (or accept it given sustained cross-client agreement — a
  correlated all-client bug would be similarly undetectable).
- **Validator observability gap.** The builder stream measures block *producers*,
  not the validating majority; the designed fallback is a proposer-signed
  post-import sidecar. Pre-swap divergence is harmless and self-detectable.
- **Post-swap MPT disposal timing (§14)** is open — dispose too early and
  recoverability is lost; too late and disk cost lingers.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
