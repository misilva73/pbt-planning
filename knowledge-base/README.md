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
| [09-online-vs-offline-migration.md](09-online-vs-offline-migration.md) | Deep-dive comparison of the **online overlay** vs the chosen **offline snapshot** migration, argued through the live objections and re-decided for the post-H\* world (BALs, ePBS, zkEVM proofs, 400M gas). |
| [05-design-evolution.md](05-design-evolution.md) | How the design got here: EIP-7864 → early EIP-8297 draft → current EIP-8297. **Read this to avoid citing stale details.** |
| [10-zero-value-leaves-and-deletion.md](10-zero-value-leaves-and-deletion.md) | The **zero-value leaf vs. delete-on-zeroization** decision record — **resolved**: EIP-8297 was revised to require deletion, matching EIP-8347. Read this for why, and where the earlier no-deletion rule came from. |
| [11-attester-telemetry-transport.md](11-attester-telemetry-transport.md) | **How attester shadow-root reports travel during the transition period**: the CL carrier design space (rate-limited global gossip topic vs subnets, req/resp, ENR, state field, attestations), the bandwidth arithmetic, the spam/signature-DoS risk, and why this is an Ethereum networking protocol rather than a libp2p change. |
| [06-open-questions.md](06-open-questions.md) | Settled **security considerations** (collision resistance, grinding, preimage injectivity) and superseded/historical questions. **Live open questions moved to [../open-questions.md](../open-questions.md).** |
| [08-gas-and-access-events.md](08-gas-and-access-events.md) | PBT's gas model: benchmark-based state-access repricing (EIP-8038 lineage) plus chunk-based code access (EIP-2926), grounded in measured PBT read/write performance. |
| [07-sources.md](07-sources.md) | Primary sources, related EIPs, and how to re-fetch them. |

## Status & provenance (important)

- **PBT is an active, evolving draft.** EIP-8297 is `Draft`, Standards Track: Core, with
  **no `requires` field** (an earlier dependency on EIP-7612 has been dropped).
- The design has changed materially over time. This knowledge base documents the
  **current design as specified in [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297)**
  as the source of truth, and flags where the third-party rendered spec site
  (cperezz.github.io/pbt-spec) may still describe an **earlier** design.
  See [05-design-evolution.md](05-design-evolution.md) before trusting any specific
  numeric detail (key widths, node types, storage prefix bits) you find elsewhere — this
  now includes three post-key-rework changes: code is **uniformly content-addressed** (no
  per-account header chunks), **zero-writes delete leaves** (the earlier contradiction
  with EIP-8347 is resolved), and **EIP-7702 delegation indicators live in a
  `DELEGATION_LEAF_KEY` header leaf**, not `CODE_ZONE` (merged 2026-08-06).
- The **migration EIP, [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347)** ("Offline
  State Migration to the PBT"), is likewise `Draft`, now **published** (formerly tracked
  only as [PR #12006](https://github.com/ethereum/EIPs/pull/12006)), and `requires: 7928,
  8159, 8297`. **Where EIP-8347 and EIP-8297 disagree, treat EIP-8297 (the tree spec) as
  correct** — this KB's standing convention for resolving cross-EIP conflicts.
- The **hash function is not final.** Reference implementations use BLAKE3; Poseidon2
  and Keccak are candidates. Treat all hash outputs as unpinned.

Last synced from sources: **2026-08-12**. Re-verify against the live EIPs before relying
on exact constants.

The migration file also situates the chosen offline conversion against the earlier
Verkle-era survey of transition options (overlay, conversion-node, local bulk, state
expiry); see [04-migration.md](04-migration.md) and [07-sources.md](07-sources.md).

## Related EIPs at a glance

| EIP | Role |
|-----|------|
| EIP-8297 | **Partitioned Binary Tree** — the tree spec this KB documents |
| EIP-8347 | **Offline State Migration to the PBT** — the migration spec this KB documents; `requires: 7928, 8159, 8297` |
| EIP-7864 | Flat unified binary tree — PBT's immediate predecessor design |
| EIP-2926 | Chunk-based code merkleization — code-chunk access pricing PBT adopts |
| EIP-8038 | Benchmark-based state-access gas repricing — the model PBT's gas EIP follows |
| EIP-7928 | Block-Level Access Lists (BAL) — the data BAL-replay consumes |
| EIP-8159 | `eth/71` wire-protocol extension — how BALs are exchanged during migration |
| EIP-7612 / EIP-7748 | The Verkle-era **online overlay** transition and its adaptation — the approach EIP-8347's offline conversion was chosen *over*; no longer an EIP-8297 dependency |
| EIP-7954 | 64 KiB contract code size limit |
| EIP-2929 / EIP-2930 | Cold/warm access and access-list gas costs (motivation baseline) |
