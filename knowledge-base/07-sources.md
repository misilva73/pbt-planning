# 07 — Sources & Re-fetching

## Primary sources (synced 2026-08-05)

| # | Source | What it covers | Freshness caveat |
|---|--------|----------------|------------------|
| 1 | **PBT spec (rendered)** — https://cperezz.github.io/pbt-spec/ | Rationale, zones, security, open questions, wormholes note | Third-party render; may describe an **earlier** design (3-bit/4-bit zone, truncated widths, per-account header code chunks). Superseded by the current EIP-8297 — see [05-design-evolution.md](05-design-evolution.md). |
| 2 | **EIP-8297 (published)** — https://eips.ethereum.org/EIPS/eip-8297 | The **current** design: variable-length prefix-free keys, 2 node types, full-digest keys, merkelization, delete-on-zeroization, fully content-addressed code | **Current source of truth** for tree specifics. Draft, Standards Track: Core. No `requires:` field (an earlier note recorded `requires: 7612`; that dependency has been dropped — see [05-design-evolution.md](05-design-evolution.md)). |
| 3 | **EIP-8347 (published)** — https://eips.ethereum.org/EIPS/eip-8347 | The **formal, normative** offline migration spec: five-phase lifecycle, converter, RLP-encoded preimage/snapshot artifact formats, dual-check verification, BAL-replay translation rules, shadow commitment, activation, transition window, security considerations | **Current source of truth** for migration specifics; supersedes the HackMD roadmap (#4) wherever they conflict. Draft, Standards Track: Core; `requires: 7928, 8159, 8297`. Authored by Carlos Perez, Maria Silva, Kevaundray Wedderburn. Originated as [PR #12006](https://github.com/ethereum/EIPs/pull/12006), now merged/published — treat the PR link as historical provenance only. |
| 4 | **Migration roadmap** — https://hackmd.io/@CPerezz/H1Q2zt8NMe | Offline conversion strategy, 6 program phases, converter, BAL-replay, snapshot, verification, params | Strategy/operator doc, not normative — where it disagrees with the published EIP-8347 (#3), the EIP wins. Tree constants may also lag EIP-8297. Approach is design-agnostic. |
| 5 | **Verkle transition options** — https://notes.ethereum.org/@parithosh/verkle-transition | **Historical** survey comparing 4 migration approaches (overlay, conversion-node, local bulk, state expiry) | Verkle-era, predates PBT. Context for *why* offline was chosen — see [04-migration.md](04-migration.md). |
| 6 | **EIP-2926** — https://eips.ethereum.org/EIPS/eip-2926 · **EIP-8038** — https://eips.ethereum.org/EIPS/eip-8038 | The two bases for PBT's gas repricing: per-chunk code access (EIP-2926, chunk-based code merkleization) and empirically-estimated state-access costs (EIP-8038). See [08-gas-and-access-events.md](08-gas-and-access-events.md). | PBT reprices from measured PBT prototype performance; the constants themselves are pending [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md). |
| 7 | **Binary tree reference impl (Python)** — https://github.com/jsign/binary-tree-spec | Minimal Python reference implementation of the unified binary tree: `tree.py` (`BinaryTree`, merkelization), `embedding.py` (account/state encoding), `eth_types.py`, and `test_tree.py` / `test_embedding.py`; hashes with BLAKE3 | Targets **EIP-7864** (PBT's predecessor), **not** the current EIP-8297. A starting point to **adapt** to PBT — variable-length prefix-free keys, the two node types, and zone partitioning all differ. Candidate reference impl for [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md) / [A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md). |
| 8 | **Verkle code-chunking mainnet analysis** — https://hackmd.io/@jsign/verkle-code-mainnet-chunking-analysis | Empirical gas-overhead study of putting contract code in the tree: ~1M mainnet txs (blocks 20,158,433–20,168,316, Jun 2024) via a Geth live-tracer capturing PC traces. Measures code-access gas overhead (**~32.6%** of current tx receipt gas on average; 95% of txs under 800k gas) and compares a **31-byte vs 32-byte** code chunker (32-byte ≈1.5% less total gas, +0.6% vs +3.7% contract-size overhead). Suggests mitigations (lower chunk charge, free-chunk allowance, multi-dimensional gas). | Pre-PBT (Verkle-era measurement, `CHUNK_SIZE = 31`). Data is design-agnostic evidence for PBT's code-chunk pricing ([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) and the code-chunk cost in [08-gas-and-access-events.md](08-gas-and-access-events.md). |

## Non-public inputs

| # | Source | What it covers | Caveat |
|---|--------|----------------|--------|
| 9 | **CL-side design discussion on attester shadow-root telemetry** — internal chat, 2026-07-27 → 2026-07-29 (migration lead, CL specs team, client-team and consensus-spec reviewers) | The transport design space for shadow-root publication: rate-limited global gossip topic vs subnets / req/resp / ENR / beacon-state field / attestation extension; the ~800k-messages-per-epoch bandwidth objection; the signature-verification DoS concern; fork-independent deployment. Summarized in [11-attester-telemetry-transport.md](11-attester-telemetry-transport.md). | **Not a specification and not public.** A design conversation, not a decision record — positions may move. Participants are referred to by role. Supersedes nothing in EIP-8347; the companion spec is still unwritten. |

## How to re-fetch / re-verify

The command sandbox whitelists `eips.ethereum.org` for network; the published EIP page is
the authoritative current spec text. GitHub (for source history) needs the sandbox disabled.

```bash
# Published EIP pages — authoritative current spec text (allowed host)
# use WebFetch on https://eips.ethereum.org/EIPS/eip-8297
# use WebFetch on https://eips.ethereum.org/EIPS/eip-8347

# Raw EIP source in the repo (requires gh auth; run with sandbox disabled)
gh api repos/ethereum/EIPs/contents/EIPS/eip-8297.md --jq .content | base64 -d
gh api repos/ethereum/EIPs/contents/EIPS/eip-8347.md --jq .content | base64 -d
```

For the hackmd and GitHub-pages sources, use the `WebFetch` tool (they are public).
Responses are cached ~15 min per URL.

## Related EIPs

| EIP | Title / role |
|-----|--------------|
| **EIP-8297** | Partitioned Binary Tree (this KB's subject) |
| **EIP-8347** | Offline State Migration to the PBT — the **actual chosen migration EIP**; `requires: 7928, 8159, 8297` |
| **EIP-7864** | Unified binary state tree — PBT's predecessor |
| **EIP-2926** | Chunk-based code merkleization — the code-chunk access pricing PBT adopts |
| **EIP-8038** | Benchmark-based state-access gas repricing — the model PBT's gas EIP follows |
| **EIP-7928** | Block-Level Access Lists (BAL) — the data format BAL-replay consumes |
| **EIP-8159** | `eth/71` devp2p wire-protocol extension — how BALs are exchanged for BAL-replay; `EIP-8347 requires` this |
| **EIP-7612** / **EIP-7748** | The Verkle-era **online overlay** transition mechanism and its adaptation — the migration approach PBT *rejected* in favour of EIP-8347's offline conversion (see [09-online-vs-offline-migration.md](09-online-vs-offline-migration.md)); no longer in EIP-8297's `requires` |
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
- Re-fetch both published EIP pages (commands above) each sync. As of 2026-08-05:
  EIP-8297 has been revised twice since the key/node-type rework — code is now uniformly
  content-addressed (no header chunks) and zero-writes now delete leaves — see
  [05-design-evolution.md](05-design-evolution.md); EIP-8347 has moved from PR #12006 to
  a published EIP page with `requires: 7928, 8159, 8297` and RLP-based artifact formats.
  When the two disagree, **EIP-8297 (the tree spec) wins** per this KB's standing
  convention.
- Keep the "Last synced" date in [README.md](README.md) current when you refresh.
