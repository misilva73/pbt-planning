# B-T1 · Conversion/replay vectors

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Tests |
| **Timeline** | 2026-09 → 2027-03 (7 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Produce cross-client **golden fixtures** for the two deterministic engines at the heart of the
migration: the **Converter** (MPT leaf → PBT key/value) and **BAL-replay** translation. These vectors
pin down exact expected outputs so that independent client implementations converge bit-for-bit,
turning the offline-migration EIP (B-S1) into executable conformance checks.

## Scope — what ships
- **Converter vectors:** MPT leaf → PBT key/value fixtures exercising the full pipeline — scan source leaves, validate `keccak(preimage)` ↔ trie path, derive PBT keys, and (at least in miniature) the external merge-sort + bottom-up construction that yields the PBT root.
- **BAL-replay vectors:** fixtures for each translation rule (balance / nonce / storage / code), including zero-write-deletes-leaf and account-deletion-without-marker cases, and a small `(E, N]` BAL-completion sequence.
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
- Fixture correctness depends on frozen-enough preimage and snapshot formats — blocked on [B-S1](B-S1-offline-migration-eip.md) closing the §14 preimage/chunk-encoding parameters ([04-migration.md §Parameters](../../knowledge-base/04-migration.md)).
- BAL-replay vectors depend on the EIP-7928 BAL format (shipped in Glamsterdam ≈ 2026-09); any late churn there forces vector regeneration.
- Miniature fixtures cannot exercise scale behaviour (external merge-sort, ~100+ GB) — that is deferred to [B-T2](B-T2-full-cycle-devnet-swap.md) and [B-T3](B-T3-dual-check-verification-scale.md).

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
