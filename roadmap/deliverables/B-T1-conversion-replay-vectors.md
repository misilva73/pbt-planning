# B-T1 · Conversion/replay vectors

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Tests |
| **Timeline** | 2026-09 → 2027-03 (7 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | Not started (as of 2026-09-17) — the preimage format has now been **stable for four weeks** (unchanged since 2026-08-20), so the "moving format" excuse has expired; meanwhile the one client that shipped ahead of the fixtures still emits the superseded layout, and the reference branch that would host these vectors has not moved since 2026-08-13 |

← [Back to roadmap](../README.md)

## Objective
Produce cross-client **golden fixtures** for the two deterministic engines at the heart of the
migration: the **Converter** (MPT leaf → PBT key/value) and **BAL-replay** translation. These vectors
pin down exact expected outputs so that independent client implementations converge bit-for-bit,
turning the offline-migration EIP (B-S1) into executable conformance checks.

## Scope — what ships
- **Converter vectors:** MPT leaf → PBT key/value fixtures exercising the full pipeline — scan source leaves, validate `keccak(preimage)` ↔ trie path, derive PBT keys, and (at least in miniature) the external merge-sort + bottom-up construction that yields the PBT root.
- **BAL-replay vectors:** fixtures for each translation rule (balance / nonce / storage / code), including zero-write-deletes-leaf and account-deletion-without-marker cases (the `nonce == 0 ∧ balance == 0 ∧ code_size == 0` trigger, exact in both directions only because [EIP-7523](https://eips.ethereum.org/EIPS/eip-7523) leaves no empty account in the MPT — added to EIP-8347's `requires` on 2026-08-25), the EIP-7702 delegation set/clear pair (setting a delegation removes the `code_hash` leaf; clearing one writes it back), and a small `(E, N]` BAL-completion sequence.
- Negative/edge fixtures: mismatched preimage, empty account, shared code leaves (content-addressed dedup), boundary sub-index cases.
- Machine-readable format consumable by EEST and each EL client's test harness; parallels the tree/key-derivation vectors so tooling is shared.

## Dependencies
- **Upstream (blocks this):** [B-S1](B-S1-offline-migration-eip.md).
- **Downstream (this blocks):** parallels [B-C1](B-C1-converter-prototype.md) — the converter prototype is validated against these fixtures; also informs [B-C2](B-C2-bal-replay-engine.md).

## Owners / teams
- EEST / test-vector team.
- Migration spec authors (oracle definition for expected outputs).
- EL client migration leads (per-client harness integration).

## Exit criteria (definition of done)
- [ ] Converter golden fixtures published covering scan → preimage-validation → key-derivation → bottom-up root.
- [ ] BAL-replay fixtures published covering all four entry types plus zero-write/deletion and `(E, N]` completion cases.
- [ ] At least two independent client implementations pass every vector with identical output.
- [ ] Vectors wired into CI as a conformance gate for [B-C1](B-C1-converter-prototype.md).

## Risks & open questions
- Fixture correctness depends on frozen-enough preimage and snapshot formats — blocked on [B-S1](B-S1-offline-migration-eip.md) closing the §14 preimage/chunk-encoding parameters ([04-migration.md §Parameters](../../knowledge-base/04-migration.md)). **This risk has already fired once.** The preimage record format changed on **2026-08-20** ([PR #12215](https://github.com/ethereum/EIPs/pull/12215)) from RLP/address-sorted to fixed-width/hashed-key-ordered, *after* geth had implemented against the earlier form — so the one existing converter now disagrees with the spec. Publishing golden fixtures before that format is explicitly frozen means regenerating them; a freeze gate in B-S1 is the cheaper order of operations.
- **A converter and a BAL-replay engine now exist, ahead of the vectors meant to validate them** (geth [#14](https://github.com/CPerezz/go-ethereum/pull/14), [#31](https://github.com/CPerezz/go-ethereum/pull/31)). Useful as an oracle *candidate*, but the "at least two independent implementations agree" criterion below is what actually matters, and deriving the fixtures from the single existing implementation would quietly convert them into a conformance test for geth's choices. Derive them from EIP text — the same failure mode already visible in `execution-specs`' EIP-8297 suite, where three fixtures pin provider behaviour rather than the spec (see [A-T1](A-T1-eest-test-suite-port.md)).
- BAL-replay vectors depend on the EIP-7928 BAL format (shipped in Glamsterdam ≈ 2026-09); any late churn there forces vector regeneration.
- Miniature fixtures cannot exercise scale behaviour (external merge-sort, ~100+ GB) — that is deferred to [B-T2](B-T2-full-cycle-devnet-swap.md) and [B-T3](B-T3-dual-check-verification-scale.md).

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [open-questions.md](../../open-questions.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
