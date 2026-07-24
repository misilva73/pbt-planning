# PBT Knowledge Base

A working reference for the **Partitioned Binary Tree (PBT)** — Ethereum's proposed
binary state tree — and the **MPT → PBT state migration**.

This knowledge base exists so that any agent (or human) can get up to speed quickly
and build on a shared, accurate picture. Read the file that matches your task; each
file is self-contained but cross-links the others.

## What is PBT, in one paragraph

PBT is a single, unified, **binary** state tree that replaces Ethereum's hexary
Merkle Patricia Tries (MPT). It merges the account trie, storage tries, and contract
code into one key/value tree, partitioned into **zones** (account headers, code,
storage) by the first byte of each key. It is designed to be **proving-friendly**
(small witnesses, hash-only so post-quantum secure, SNARK-amenable), to remove the
sequential `storage_root`-inside-account bottleneck (enabling single-pass parallel
root computation), and to provide structural boundaries that later state-expiry and
partial-statelessness proposals can build on. It is specified in **EIP-8297**.

## Map of this knowledge base

| File | Read it when you need… |
|------|------------------------|
| [01-overview.md](01-overview.md) | The big picture: what PBT is, why, goals, and the glossary of terms. Start here. |
| [02-tree-structure.md](02-tree-structure.md) | The data structure itself: node types, key format, zones, merkelization, insertion. The core spec. |
| [03-key-derivation.md](03-key-derivation.md) | How account / code / storage keys are derived, header layout, constants, worked test vectors. |
| [04-migration.md](04-migration.md) | The MPT → PBT migration roadmap: offline conversion, phases, converter, BAL-replay, snapshot, verification. |
| [05-design-evolution.md](05-design-evolution.md) | How the design got here: EIP-7864 → early EIP-8297 draft → current EIP-8297. **Read this to avoid citing stale details.** |
| [06-open-questions.md](06-open-questions.md) | Settled **security considerations** (collision resistance, grinding, preimage injectivity) and superseded/historical questions. **Live open questions moved to [../open-questions.md](../open-questions.md).** |
| [08-gas-and-access-events.md](08-gas-and-access-events.md) | PBT's gas model: benchmark-based state-access repricing (EIP-8038 lineage) plus chunk-based code access (EIP-2926), grounded in measured PBT read/write performance. |
| [07-sources.md](07-sources.md) | Primary sources, related EIPs, and how to re-fetch them. |

## Status & provenance (important)

- **PBT is an active, evolving draft.** EIP-8297 is `Draft`, Standards Track: Core.
- The design has changed materially over time. This knowledge base documents the
  **current design as specified in [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297)**
  as the source of truth, and flags where the third-party rendered spec site
  (cperezz.github.io/pbt-spec) may still describe an **earlier** design.
  See [05-design-evolution.md](05-design-evolution.md) before trusting any specific
  numeric detail (key widths, node types, storage prefix bits) you find elsewhere.
- The **hash function is not final.** Reference implementations use BLAKE3; Poseidon2
  and Keccak are candidates. Treat all hash outputs as unpinned.

Last synced from sources: **2026-07-21**. Re-verify against the live EIP/PR before
relying on exact constants.

The migration file also situates the chosen offline conversion against the earlier
Verkle-era survey of transition options (overlay, conversion-node, local bulk, state
expiry); see [04-migration.md](04-migration.md) and [07-sources.md](07-sources.md).

## Related EIPs at a glance

| EIP | Role |
|-----|------|
| EIP-8297 | **Partitioned Binary Tree** — the tree spec this KB documents |
| EIP-7864 | Flat unified binary tree — PBT's immediate predecessor design |
| EIP-2926 | Chunk-based code merkleization — code-chunk access pricing PBT adopts |
| EIP-8038 | Benchmark-based state-access gas repricing — the model PBT's gas EIP follows |
| EIP-7612 | Overlay-tree fork mechanism (how the new tree is switched on) |
| EIP-7748 | State conversion (the MPT→tree migration, adapted to PBT) |
| EIP-7928 | Block-Level Access Lists (BAL) — used by BAL-replay and partial statefulness |
| EIP-7954 | 64 KiB contract code size limit |
| EIP-2929 / EIP-2930 | Cold/warm access and access-list gas costs (motivation baseline) |
