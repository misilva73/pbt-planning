# B-O1 · Proof-consumer coordination

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Ecosystem outreach |
| **Timeline** | 2026-08 → 2028-04 (21 months) |
| **Migration phase** | Phase 1 → 5 — Prototypes & Evidence through Mainnet Window |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Coordinate the upgrade of **on-chain proof consumers** ahead of the state-commitment
swap. Contracts themselves need no changes — standard EVM operations are unchanged
across `S` — but systems that *read Ethereum state proofs* are significantly affected:
the PBT eliminates the `storage_root` field inside account headers and changes the tree
hash, so any verifier that reconstructs or checks an MPT proof breaks at the swap. This
is the **longest-lead** outreach track — it must start in Phase 1 and reach coordinated
readiness before the [B-C7](B-C7-swap-fork-s-aftermath.md) swap, or dependent protocols
break at fork `S`.

## Scope — what ships
- A published **inventory of affected proof consumers**: state-proof verifier contracts,
  cross-chain bridges that verify Ethereum state proofs, L2s anchoring to L1 state, and
  services/dapps built on `eth_getProof`.
- A **migration guide** documenting the header-shape change (no `storage_root` in leaves;
  independent nonce/balance/slot writes) and the new tree hash / merkelization so
  consumers can update their verification logic.
- Coordinated tracking of the **verification-precompile** direction and the
  **`eth_getProof` successor** RPC (both flagged open in §14 — proof-consumer
  dependencies), so consumers migrate onto a stable replacement rather than a moving one.
- A readiness register mapping each major consumer to its upgrade status ahead of `S`.

## Stakeholders
- Cross-chain **bridge** operators and light-client / state-proof verifier teams.
- **L2** teams whose settlement or fraud/validity proofs read L1 state.
- **Indexers, RPC providers, and dapps** relying on `eth_getProof`.
- EIP editors and client RPC maintainers defining the verification precompile and the
  `eth_getProof` successor.

## Dependencies
- **Upstream (blocks this):** none — this starts at the front of Phase 1 (longest lead).
- **Downstream (this blocks):** [B-C7](B-C7-swap-fork-s-aftermath.md) (proof consumers must be
  ready before the swap makes PBT canonical).

## Exit criteria (definition of done)
- [ ] Published inventory of affected on-chain proof consumers, kept current through Phase 5.
- [ ] Migration guide covering the eliminated `storage_root` and the new tree hash is
      published and acknowledged by the major consumer classes.
- [ ] Verification-precompile / `eth_getProof`-successor direction is decided and
      communicated (§14 open item closed for outreach purposes).
- [ ] Major identified proof consumers report an upgrade path (or explicit N/A) before
      the [B-C7](B-C7-swap-fork-s-aftermath.md) swap window.

## Risks & open questions
- Per 04-migration.md **Ecosystem impact**: proof consumers are the one class with
  *significant* impact — the eliminated `storage_root` and new tree hash mean
  uncoordinated verifiers break at `S`. This is why the track has the longest lead time.
- **§14 open — proof-consumer dependencies:** verification precompiles and `eth_getProof`
  successors are not yet specified; consumers cannot fully finalize migration until these
  land, so the track must track that spec work, not just socialize the change.
- Discovery risk: some proof consumers are off-radar (private bridges, bespoke verifiers)
  and may not surface until late; the inventory must be treated as never-complete.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md) (Ecosystem impact; Parameters — §14 open parameters)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md) (no `storage_root` in leaves; EVM-invisibility)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
