# 07 — Sources & Re-fetching

## Primary sources (synced 2026-07-21)

| # | Source | What it covers | Freshness caveat |
|---|--------|----------------|------------------|
| 1 | **PBT spec (rendered)** — https://cperezz.github.io/pbt-spec/ | Rationale, zones, security, open questions, wormholes note | Describes an **earlier** design (3-bit/4-bit zone, truncated widths). Superseded by PR #11978 — see [05-design-evolution.md](05-design-evolution.md). |
| 2 | **EIP PR #11978** — https://github.com/ethereum/EIPs/pull/11978 | The **current** design: variable-length prefix-free keys, 2 node types, full-digest keys, merkelization | **Current source of truth** for tree specifics. Draft, under assessment. |
| 3 | **Migration roadmap** — https://hackmd.io/@CPerezz/H1Q2zt8NMe | Offline conversion strategy, 6 phases, converter, BAL-replay, snapshot, verification, params | Strategy doc; tree constants may lag. Approach is design-agnostic. |
| 4 | **Verkle transition options** — https://notes.ethereum.org/@parithosh/verkle-transition | **Historical** survey comparing 4 migration approaches (overlay, conversion-node, local bulk, state expiry) | Verkle-era, predates PBT. Context for *why* offline was chosen — see [04-migration.md](04-migration.md). |
| — | **EIP-8297 (published)** — https://eips.ethereum.org/EIPS/eip-8297 | The Draft as published | Pre-#11978 design; read PR #11978 for current. |

Authors — sources 1 & 3: **C. Perez (@CPerezz)**; source 4: **Parithosh Jayanthi
(@parithosh)**; PR #11978: **kevaundray**.

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
