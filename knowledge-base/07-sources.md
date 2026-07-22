# 07 — Sources & Re-fetching

## Primary sources (synced 2026-07-21)

| # | Source | What it covers | Freshness caveat |
|---|--------|----------------|------------------|
| 1 | **PBT spec (rendered)** — https://cperezz.github.io/pbt-spec/ | Rationale, zones, security, open questions, wormholes note | Describes an **earlier** design (3-bit/4-bit zone, truncated widths). Superseded by PR #11978 — see [05-design-evolution.md](05-design-evolution.md). |
| 2 | **EIP PR #11978** — https://github.com/ethereum/EIPs/pull/11978 | The **current** design: variable-length prefix-free keys, 2 node types, full-digest keys, merkelization | **Current source of truth** for tree specifics. Draft, under assessment. |
| 3 | **Migration roadmap** — https://hackmd.io/@CPerezz/H1Q2zt8NMe | Offline conversion strategy, 6 phases, converter, BAL-replay, snapshot, verification, params | Strategy doc; tree constants may lag. Approach is design-agnostic. |
| 4 | **Verkle transition options** — https://notes.ethereum.org/@parithosh/verkle-transition | **Historical** survey comparing 4 migration approaches (overlay, conversion-node, local bulk, state expiry) | Verkle-era, predates PBT. Context for *why* offline was chosen — see [04-migration.md](04-migration.md). |
| — | **EIP-8297 (published)** — https://eips.ethereum.org/EIPS/eip-8297 | The Draft as published | Pre-#11978 design; read PR #11978 for current. |
| 5 | **EIP-4762** — https://eips.ethereum.org/EIPS/eip-4762 | Access-event / witness-gas framework PBT adopts (see [08-gas-and-access-events.md](08-gas-and-access-events.md)) | Verkle-era; PBT reuses it with modifications and un-recalibrated constants. |
| 6 | **Binary tree reference impl (Python)** — https://github.com/jsign/binary-tree-spec | Minimal Python reference implementation of the unified binary tree: `tree.py` (`BinaryTree`, merkelization), `embedding.py` (account/state encoding), `eth_types.py`, and `test_tree.py` / `test_embedding.py`; hashes with BLAKE3 | Targets **EIP-7864** (PBT's predecessor), **not** PR #11978. A starting point to **adapt** to PBT — variable-length prefix-free keys, the two node types, and zone partitioning all differ. Candidate reference impl for [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md) / [A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md). |
| 7 | **Verkle code-chunking mainnet analysis** — https://hackmd.io/@jsign/verkle-code-mainnet-chunking-analysis | Empirical gas-overhead study of putting contract code in the tree: ~1M mainnet txs (blocks 20,158,433–20,168,316, Jun 2024) via a Geth live-tracer capturing PC traces. Measures code-access gas overhead (**~32.6%** of current tx receipt gas on average; 95% of txs under 800k gas) and compares a **31-byte vs 32-byte** code chunker (32-byte ≈1.5% less total gas, +0.6% vs +3.7% contract-size overhead). Suggests mitigations (lower chunk charge, free-chunk allowance, multi-dimensional gas). | Verkle-era (EIP-4762, `CHUNK_SIZE = 31`), pre-PBT. Data is design-agnostic evidence for witness-gas recalibration ([A-S3](../roadmap/deliverables/A-S3-witness-gas-recalibration.md)) and the code-chunk cost in [08-gas-and-access-events.md](08-gas-and-access-events.md). Feedback credited to Guillaume/Josh/Dankrad. |

Authors — sources 1 & 3: **C. Perez (@CPerezz)**; source 4: **Parithosh Jayanthi
(@parithosh)**; PR #11978: **kevaundray**; sources 6 & 7: **Ignacio Hagopian (@jsign)**.

## How to re-fetch / re-verify

The command sandbox only whitelists `eips.ethereum.org` for network; GitHub needs the
sandbox disabled.

```bash
# EIP PR body, files, state (requires gh auth; run with sandbox disabled)
gh pr view 11978 --repo ethereum/EIPs --json title,body,state,files

# Full diff of the PR (the authoritative current spec text)
gh pr diff 11978 --repo ethereum/EIPs

# Published EIP page (allowed host)
# use WebFetch on https://eips.ethereum.org/EIPS/eip-8297
```

For the hackmd and GitHub-pages sources, use the `WebFetch` tool (they are public).
Responses are cached ~15 min per URL.

## Related EIPs

| EIP | Title / role |
|-----|--------------|
| **EIP-8297** | Partitioned Binary Tree (this KB's subject) |
| **EIP-7864** | Unified binary state tree — PBT's predecessor |
| **EIP-4762** | Statelessness gas cost changes / access-event framework (PBT `requires`) |
| **EIP-7612** | Verkle/overlay tree transition — the fork mechanism (PBT `requires`) |
| **EIP-7748** | State conversion to a binary tree — the migration EIP (adapted to PBT) |
| **EIP-7928** | Block-Level Access Lists (BAL) — used by BAL-replay & partial statefulness |
| **EIP-7954** | Increase code size limit to 64 KiB |
| **EIP-7870** | Hardware requirements matrix (used in migration rehearsals) |
| **EIP-2929** | Gas cost increases for state access (cold access = 2600) |
| **EIP-2930** | Optional access lists (fresh account access = 2400) |
| **EIP-7503** | Zero-knowledge wormholes (privacy; PBT enables, does not implement) |
| **EIP-6800** | (Verkle lineage) unified Verkle tree — historical context |

## Maintenance notes for future agents

- When updating any tree constant, update **both** [02-tree-structure.md](02-tree-structure.md)
  / [03-key-derivation.md](03-key-derivation.md) **and** the comparison table in
  [05-design-evolution.md](05-design-evolution.md).
- Re-run the `gh pr diff` command above to check whether PR #11978 has advanced or
  merged; if merged, the published EIP page becomes current and the "OLD vs CURRENT"
  framing in file 05 should be revisited.
- Keep the "Last synced" date in [README.md](README.md) current when you refresh.
