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

### EIPs

| EIP | Status | Link |
|-----|--------|------|
| **Trie (PBT)** — EIP-8297 | Draft | https://eips.ethereum.org/EIPS/eip-8297 |
| **Migration** — offline MPT→PBT conversion | Draft PR | https://github.com/ethereum/EIPs/pull/12006 |
| **State pricing** — PBT gas repricing (benchmark-based; EIP-2926 + EIP-8038 lineage) | TBD | *to be drafted* |

### Specs & tests

| Suite | Link |
|-------|------|
| **Trie specs and tests** | https://github.com/ethereum/execution-specs/pull/3216 |
| **Migration specs and tests** | *TBD* |
