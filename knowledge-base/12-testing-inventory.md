# PBT testing inventory

This is a **dated evidence snapshot**, not a live test dashboard. Reference and client tests were counted in September 2026; the Hive artifact draft was reviewed on **2026-09-23**. Counts below are test functions unless stated otherwise. Reported client passes were not re-run for this inventory. See [sources](07-sources.md) before relying on current status.

## Coverage at a glance

| Surface | Evidence in the September snapshot | Main gap |
|---|---|---|
| Tree and EVM state rules | `execution-specs@projects/binary-trie` at `09d2088`: 168 binary-trie unit tests and 56 EIP-8297 filler functions producing 70 blockchain fixtures. Client suites also exist. | A shared release and runner for the 70 fixtures; separate spec rules from provider-specific assumptions. |
| Conversion and artifacts | geth converter tests; draft [Hive PR #1614](https://github.com/ethereum/hive/pull/1614) tests canonical preimages and snapshots. | Full converter-pipeline vectors, a second snapshot producer, and a CI gate. |
| BAL replay | geth tests and a migration devnet. | Shared vectors across clients, including deletion and reorg cases. |
| Swap and recovery | Engine-level geth tests; a four-client migration devnet tests activation and straddle reorgs. | Populated-state end-to-end runs and recovery under extended non-finality. |
| Scale and sync | No accepted mainnet-scale conversion or independent full-size dual-check in this snapshot. | Throughput, memory, disk, fresh-node verification, and PBT-native sync. |
| Shadow roots | EL debug feeds and devnet root comparisons. | CL telemetry transport, validator coverage, and adversarial report tests. |

The reference count is **224 functions** (168 + 56), not 224 independently released blockchain fixtures. The 70 fixtures come from the 56 fillers. Client reports of geth green and Erigon 67/70 were produced in separate client workflows, so they are not a common conformance result.

## Artifact conformance

[Hive PR #1614](https://github.com/ethereum/hive/pull/1614) was open and draft at review commit `b8703d2`. Its `ethereum/pbt-artifacts` suite includes **58 mutation cases**: 14 preimage rejects, 43 snapshot rejects, and one unscored empty-snapshot case. It also checks valid pairs, anchor-root binding, and producer agreement. The PR reports geth passing scored cases, Nethermind crashing on three, and geth/Erigon producing byte-identical preimages. Snapshot producer agreement remained inconclusive because geth was the only producer. These are PR-reported results, not independently re-run here.

This suite checks EIP-8347 artifacts. It does **not** run the 70 EIP-8297 blockchain fixtures, prove a full conversion pipeline, or test BAL replay.

## Devnet evidence

The accepted **M1 gate on 2026-08-27** ran on empty state and one execution-client implementation. Its verifier checked canonical blocks before activation, transaction load, healed partitions and reorgs, agreement across the boundary, progress, shadow-root samples, genesis-state pins, and artifact digests. Equal artifact digests across four geth nodes prove reproducibility of that producer, not cross-producer equality.

By the 2026-09-17 snapshot, the tree-at-genesis devnet had seven nodes from four client implementations. The migration devnet also exercised four clients with different migration mechanisms and judged fork-boundary behavior. That shows cross-client execution of a small migration scenario; it does not establish populated-state artifact production or mainnet-scale conversion. Besu exposed less migration introspection than the other clients in that snapshot.

A root mismatch must compare reports for the **same block hash**, including across reorgs. Test harnesses should deliberately inject wrong roots and malformed artifacts to prove that a green result can fail for the right reason.

## Highest-priority gaps

1. **Release the EIP-8297 fixtures and run them together.** The reference branch's fixture-release workflow lacked a `binary_tree` feature, so client self-reports were not reproducible as one cross-client result. Resolve provider-specific fixture assumptions before treating it as a normative oracle.
2. **Finish artifact conformance.** Land the Hive draft, fix consumer crashes, add another snapshot producer, then test full conversion and replay against shared vectors.
3. **Run populated-state rehearsals.** Measure independent conversion, byte agreement, fresh-node dual-check, BAL catch-up, and transport failures on realistic state.
4. **Exercise the transition window.** Test deep reorgs in both directions, delayed finality, rollback, restart, and a fresh node joining after activation.
5. **Specify and test telemetry.** Measure validator coverage, wrong signed roots, equivocation, rate limits, and the eventual readiness rule once the carrier is specified.
6. **Pin the tree hash before root-bearing fixtures become final.** The reference BLAKE3 roots are provisional while `H` is open in EIP-8297.

## Planned test ownership

| Roadmap area | Evidence needed |
|---|---|
| [A-T1](../roadmap/deliverables/A-T1-eest-test-suite-port.md), [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md) | Published tree, key, and EVM-rule fixtures consumed by multiple clients. |
| [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md) | Sustained root agreement and native state-sync convergence. |
| [A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md) | Performance and adversarial-cost measurements for gas decisions. |
| [B-T1](../roadmap/deliverables/B-T1-conversion-replay-vectors.md) | Canonical conversion and BAL-replay vectors. |
| [B-T2](../roadmap/deliverables/B-T2-full-cycle-devnet-swap.md) | Multi-client convert-through-swap lifecycle, including fresh join and reorgs. |
| [B-T3](../roadmap/deliverables/B-T3-dual-check-verification-scale.md) | Mainnet-scale verification with bad artifacts and transport faults. |

## Provenance and limits

The test-function inventory came from `execution-specs@projects/binary-trie` at `09d2088` (2026-08-13), `CPerezz/go-ethereum@pbt`, and `CPerezz/pbt-devnet`; roadmap requests came from its test deliverables and August 2026 meeting notes. The implementation sweep was last checked 2026-09-17; fixture workflow findings were checked 2026-09-18; the targeted Hive review was 2026-09-23. Re-enumerate source trees and re-run clients before making a current pass/fail claim.
