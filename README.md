# PBT Planning

Planning, specification, and coordination materials for shipping the **Partitioned
Binary Tree (PBT)** — Ethereum's proposed binary state commitment — and for **migrating
mainnet state from the MPT to PBT**.

PBT is a single, unified binary state tree that replaces Ethereum's hexary Merkle
Patricia Tries (MPT). It merges the account trie, storage tries, and contract code into
one key/value tree, designed to be proving-friendly (small, hash-only, post-quantum-secure
witnesses), to remove the sequential `storage_root` bottleneck, and to provide structural
boundaries for later state-expiry and statelessness work.

This repo is the working home for the *what*, *why*, *when*, and *who* of that effort. It
does not hold client implementations or the canonical specs themselves — those live in the
EIP and execution-spec repositories linked below.

## What's here

| Directory | Contents |
|-----------|----------|
| [knowledge-base/](knowledge-base/README.md) | A working reference for PBT and the migration — the *what* and *why*: tree structure, key derivation, migration design, open questions, and sources. **Start here.** |
| [roadmap/](roadmap/README.md) | The month-by-month delivery plan — the *when* and *who*: threads, workstreams, deliverables, and a clickable Gantt chart. |
| [open-questions.md](open-questions.md) | The **key unresolved design questions** for the trie and the migration — what is still not decided, and which deliverable closes each. |

## Key resources

*Verified against live sources on **2026-09-02**. Re-verify before relying on exact
constants or implementation status — see
[knowledge-base/07-sources.md](knowledge-base/07-sources.md#how-to-re-fetch--re-verify).*

### EIPs

| EIP | Status | Link |
|-----|--------|------|
| **Trie (PBT)** — EIP-8297 | Draft (last revised 2026-08-06) | https://eips.ethereum.org/EIPS/eip-8297 |
| **Migration** — EIP-8347, offline MPT→PBT conversion | Draft (last revised 2026-08-25; `requires: 7523, 7928, 8159, 8297`) | https://eips.ethereum.org/EIPS/eip-8347 |
| **State pricing** — PBT gas repricing (benchmark-based; EIP-2926 + EIP-8038 lineage) | TBD | *to be drafted* |

### Specs & tests

| Suite | Link |
|-------|------|
| **Trie specs and tests** | [`execution-specs@projects/binary-trie`](https://github.com/ethereum/execution-specs/tree/projects/binary-trie) — implementation + EIP-8297 test suite; proposed upstream as draft [PR #3207](https://github.com/ethereum/execution-specs/pull/3207) into `forks/amsterdam` |
| **Migration specs and tests** | *TBD* — no EIP-8347 converter/preimage code on the `projects/binary-trie` branch as of 2026-09-02 |
| **PBT devnet** | [CPerezz/pbt-devnet](https://github.com/CPerezz/pbt-devnet) — differential devnet, **geth + Besu + Erigon** (two nodes each) on an Amsterdam-at-genesis chain under Lighthouse; migration devnet on the `migration-*` branches |

### Client implementations

The devnet pins these exact checkouts
([`scripts/sources.sh`](https://github.com/CPerezz/pbt-devnet/blob/main/scripts/sources.sh)):

| Client | Branch under test | Upstreaming |
|--------|-------------------|-------------|
| **geth** | [`CPerezz/go-ethereum@pbt`](https://github.com/CPerezz/go-ethereum/tree/pbt) | draft [ethereum/go-ethereum#35436](https://github.com/ethereum/go-ethereum/pull/35436) — *the same branch*, opened for discussion |
| **Erigon** | [`erigontech/erigon@binary-trie`](https://github.com/erigontech/erigon/tree/binary-trie) | draft [erigontech/erigon#22942](https://github.com/erigontech/erigon/pull/22942) (`PBinPatriciaHashed` commitment engine); tracking issue [#23389](https://github.com/erigontech/erigon/issues/23389) |
| **Besu** | [`CPerezz/besu@fix/pbt-fcu-null-trie-node`](https://github.com/CPerezz/besu/tree/fix/pbt-fcu-null-trie-node) over [`matkt/besu@glamsterdam-devnet-8-pbt`](https://github.com/matkt/besu/tree/glamsterdam-devnet-8-pbt), plus the [`besu-eth/besu-stateless@feat/partitioned-binary-trie`](https://github.com/besu-eth/besu-stateless/tree/feat/partitioned-binary-trie) library ([PR #92](https://github.com/besu-eth/besu-stateless/pull/92)) | Besu now lives at `besu-eth/besu` |
| **Nethermind** | [`NethermindEth/nethermind@pbt-state`](https://github.com/NethermindEth/nethermind/tree/pbt-state) | draft [NethermindEth/nethermind#12573](https://github.com/NethermindEth/nethermind/pull/12573) — explicitly a **prototype, not for merge**; not in the devnet |
| **Reth** | *none found* | — |
| Genesis generator | [`CPerezz/ethereum-genesis-generator@pbt`](https://github.com/CPerezz/ethereum-genesis-generator/tree/pbt) | emits `binaryTrieTime` |
