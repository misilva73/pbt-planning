# 07 — Sources & Re-fetching

## Primary sources (synced 2026-09-02)

| # | Source | What it covers | Freshness caveat |
|---|--------|----------------|------------------|
| 1 | **PBT spec (rendered)** — https://cperezz.github.io/pbt-spec/ | Rationale, zones, security, open questions, wormholes note | Third-party render; may describe an **earlier** design (3-bit/4-bit zone, truncated widths, per-account header code chunks). Superseded by the current EIP-8297 — see [05-design-evolution.md](05-design-evolution.md). |
| 2 | **EIP-8297 (published)** — https://eips.ethereum.org/EIPS/eip-8297 | The **current** design: variable-length prefix-free keys, 2 node types, full-digest keys, merkelization, delete-on-zeroization, fully content-addressed code, `DELEGATION_LEAF_KEY` header leaf for EIP-7702 delegations | **Current source of truth** for tree specifics. Draft, Standards Track: Core. No `requires:` field (an earlier note recorded `requires: 7612`; that dependency has been dropped — see [05-design-evolution.md](05-design-evolution.md)). Delegation indicators moved from `CODE_ZONE` into the header stem via [PR #12114](https://github.com/ethereum/EIPs/pull/12114), merged 2026-08-06. |
| 3 | **EIP-8347 (published)** — https://eips.ethereum.org/EIPS/eip-8347 | The **formal, normative** offline migration spec: five-phase lifecycle, converter, preimage/snapshot artifact formats, dual-check verification, BAL-replay translation rules, delegation-indicator handling, shadow commitment, activation, transition window, security considerations | **Current source of truth** for migration specifics; supersedes the HackMD roadmap (#4) wherever they conflict. Draft, Standards Track: Core; `requires: 7523, 7928, 8159, 8297` (EIP-7523 added 2026-08-25, [PR #12239](https://github.com/ethereum/EIPs/pull/12239)). Authored by Carlos Perez, Maria Silva, Kevaundray Wedderburn. Originated as [PR #12006](https://github.com/ethereum/EIPs/pull/12006), now merged/published — treat the PR link as historical provenance only. Two revisions since the 2026-08-12 sync: header-leaf delegation indicators ([PR #12115](https://github.com/ethereum/EIPs/pull/12115), 2026-08-06) and — **the substantive one** — the **preimage file re-cut to fixed-width, hashed-key-ordered records** ([PR #12215](https://github.com/ethereum/EIPs/pull/12215), 2026-08-20). The snapshot's RLP leaf records are unchanged. |
| 4 | **Migration roadmap** — https://hackmd.io/@CPerezz/H1Q2zt8NMe | Offline conversion strategy, 6 program phases, converter, BAL-replay, snapshot, verification, params | Strategy/operator doc, not normative — where it disagrees with the published EIP-8347 (#3), the EIP wins. Tree constants may also lag EIP-8297. Approach is design-agnostic. |
| 5 | **Verkle transition options** — https://notes.ethereum.org/@parithosh/verkle-transition | **Historical** survey comparing 4 migration approaches (overlay, conversion-node, local bulk, state expiry) | Verkle-era, predates PBT. Context for *why* offline was chosen — see [04-migration.md](04-migration.md). |
| 6 | **EIP-2926** — https://eips.ethereum.org/EIPS/eip-2926 · **EIP-8038** — https://eips.ethereum.org/EIPS/eip-8038 | The two bases for PBT's gas repricing: per-chunk code access (EIP-2926, chunk-based code merkleization) and empirically-estimated state-access costs (EIP-8038). See [08-gas-and-access-events.md](08-gas-and-access-events.md). | PBT reprices from measured PBT prototype performance; the constants themselves are pending [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md). |
| 7 | **Binary tree reference impl (Python)** — https://github.com/jsign/binary-tree-spec | Minimal Python reference implementation of the unified binary tree: `tree.py` (`BinaryTree`, merkelization), `embedding.py` (account/state encoding), `eth_types.py`, and `test_tree.py` / `test_embedding.py`; hashes with BLAKE3 | Targets **EIP-7864** (PBT's predecessor), **not** the current EIP-8297. A starting point to **adapt** to PBT — variable-length prefix-free keys, the two node types, and zone partitioning all differ. Candidate reference impl for [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md) / [A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md). |
| 8 | **Verkle code-chunking mainnet analysis** — https://hackmd.io/@jsign/verkle-code-mainnet-chunking-analysis | Empirical gas-overhead study of putting contract code in the tree: ~1M mainnet txs (blocks 20,158,433–20,168,316, Jun 2024) via a Geth live-tracer capturing PC traces. Measures code-access gas overhead (**~32.6%** of current tx receipt gas on average; 95% of txs under 800k gas) and compares a **31-byte vs 32-byte** code chunker (32-byte ≈1.5% less total gas, +0.6% vs +3.7% contract-size overhead). Suggests mitigations (lower chunk charge, free-chunk allowance, multi-dimensional gas). | Pre-PBT (Verkle-era measurement, `CHUNK_SIZE = 31`). Data is design-agnostic evidence for PBT's code-chunk pricing ([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) and the code-chunk cost in [08-gas-and-access-events.md](08-gas-and-access-events.md). |
| 9 | **PBT devnet** — https://github.com/CPerezz/pbt-devnet | The live differential devnet for EIP-8297. As of 2026-09-02: **three implementations, six nodes under test** (two geth, two Besu, two Erigon) plus a protected geth bootnode, on an **Amsterdam-at-genesis** chain (which forces Gloas at slot 0) driven by real Lighthouse CLs, composing `ethpandaops/ethereum-package` with no patches. The tree is switched on by `binaryTrieTime` in the genesis; every EL must agree on every state root, and `pbtchaos` forces a reorg every 15–30 blocks plus six targeted state-stranding scenarios (`code-sole`, `code-shared`, `delegate`, `account`, `storage-add`, `storage-del`). Separate **migration devnet** on `migration-devnet` / `migration-m1` / `migration-m1-tooling`: merkle genesis with the tree fork ahead, a migration monitor / chaos driver / verifier, and an accepted **M1 report ("the empty-state migration devnet is accepted", 2026-08-27)**. | Implementation status, not a spec source — verify devnet behavior against the current EIP-8297 revision rather than assuming parity. Client coverage is a moving target; re-read [`scripts/sources.sh`](https://github.com/CPerezz/pbt-devnet/blob/main/scripts/sources.sh) (it pins every client branch) before citing it. Nethermind and Reth are **not** in it. Evidence source for [A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md) and [A-C3](../roadmap/deliverables/A-C3-multiclient-pbt-genesis-devnets.md). |
| 10 | **Client PBT branches** (pinned by #9's `scripts/sources.sh`) — geth `CPerezz/go-ethereum@pbt` · Erigon `erigontech/erigon@binary-trie` · Besu `CPerezz/besu@fix/pbt-fcu-null-trie-node` over `matkt/besu@glamsterdam-devnet-8-pbt` + library `besu-eth/besu-stateless@feat/partitioned-binary-trie` · genesis `CPerezz/ethereum-genesis-generator@pbt` | The three implementations the devnet runs. **geth** is the most advanced and is the only one carrying EIP-8347 migration code (see #11). **Erigon**'s branch lives in the *upstream* repo and reads `binaryTrieTime` out of the genesis at `erigon init`. **Besu** takes `--data-storage-format=BINARY` and hashes with `Blake3Digest(256)`; its tree lives in the `besu-stateless` library. Note Besu has moved org: `besu-eth/besu`, not `hyperledger/besu`. | Implementation status, not spec sources — fork branches, none merged upstream. All three hardcode/expect **BLAKE3**, which the spec does **not** pin ([open-questions.md](../open-questions.md#hash-function-selection--the-dominant-open-parameter)) — do not read devnet agreement as evidence that `H` is settled. |
| 11 | **EIP-8347 migration implementation in geth** — `CPerezz/go-ethereum@pbt`, PRs [#14](https://github.com/CPerezz/go-ethereum/pull/14) (converter), [#16](https://github.com/CPerezz/go-ethereum/pull/16) (snapshot import + dual-check), [#31](https://github.com/CPerezz/go-ethereum/pull/31) (BAL-replay follower, swap, transition window), [#33](https://github.com/CPerezz/go-ethereum/pull/33) (sidechain replay into the shadow tree) | The only end-to-end EIP-8347 implementation that exists. `geth bintrie convert` emits the byte-canonical snapshot + preimage artifacts; `geth bintrie import` verifies them with the spec's dual-check; a follower replays BALs onto whichever tree execution is not committing, backfilling missing lists over `eth/71`, and the header root swaps source at `binaryTrieTime` with the merkle side held until a post-fork block finalizes. `debug_shadowStateRoot` / `debug_shadowRoots` / `debug_migrationProgress` expose the sidecar feed. Reported figures on a 70k-account / 140k-slot / 5.2k-code fixture (114.7 MB datadir, page-cache-resident): **convert 5.05 s (13.9k accounts/s), import 2.03 s (34.5k accounts/s), artifacts 29.4 MB**; the author's naive extrapolation to ~270 GB mainnet state puts the **compute** floor at 3–4 h. | Implementation status, not a spec source, and **known to lag the spec**: PR #14's preimage writer still emits **RLP, address-sorted** records, the format EIP-8347 replaced on 2026-08-20 with fixed-width hashed-key-ordered records (#3). Treat the perf numbers as compute-only on cached fixtures — not mainnet I/O. Evidence source for [B-C1](../roadmap/deliverables/B-C1-converter-prototype.md), [B-C2](../roadmap/deliverables/B-C2-bal-replay-engine.md), [A-C4](../roadmap/deliverables/A-C4-snapshot-serving-verification.md). |
| 12 | **Upstreaming PRs** — geth [ethereum/go-ethereum#35436](https://github.com/ethereum/go-ethereum/pull/35436) · Erigon [erigontech/erigon#22942](https://github.com/erigontech/erigon/pull/22942) + tracking issue [#23389](https://github.com/erigontech/erigon/issues/23389) · Nethermind [NethermindEth/nethermind#12573](https://github.com/NethermindEth/nethermind/pull/12573) · besu-stateless [#92](https://github.com/besu-eth/besu-stateless/pull/92) · execution-specs [#3207](https://github.com/ethereum/execution-specs/pull/3207) | Where each implementation is headed upstream. geth's is literally the devnet branch (`CPerezz/go-ethereum@pbt`), opened draft "temporary, for discussion". Erigon's is `--experimental.bin-commitment`, off by default, with **67 of 70** EIP-8297 blockchain fixtures passing. Nethermind's is a **prototype behind a not-for-merge warning** (branch `pbt-state`, author `asdacap`) exploring node-grouping layouts for a binary tree on RocksDB. execution-specs' `projects/binary-trie` is proposed into `forks/amsterdam`. | All drafts; none merged. Erigon's PR documents **real divergences from the spec and from geth**: it keeps zero-valued leaves (against current EIP-8297), refuses account removal outright, and leaks code chunks above a shortened redeploy's length. Nethermind's numbers (~3 ms → ~11 ms root calculation; depth-4-interleave fastest) are prototype measurements, not conformance evidence. |

> **Cross-client divergences worth tracking** (from Erigon issue
> [#23384](https://github.com/erigontech/erigon/issues/23384), closed 2026-09-02, and PR
> #22942): Erigon's default Amsterdam ships the **pre-revision EIP-8038 schedule**
> (8000 / 3000 / 11000 / 12480) while geth-pbt matches the current one
> (`ACCOUNT_WRITE` 9000, `COLD_STORAGE_ACCESS` 2100, `CREATE_ACCESS` 12000,
> `STORAGE_CLEAR_REFUND` 11616); Erigon does not subtract `WARM_ACCESS` from the
> EIP-2930 access-list constants (100 gas per entry of drift); and the three clients
> disagree on the EIP-7610 `CREATE2`-into-a-storage-only-account rule (geth uses an empty
> per-chain allowlist, Besu drops the check with the compensating nonce bump unimplemented,
> Erigon rejects). These are gas/semantics divergences riding *alongside* PBT, not tree
> bugs — but they are what a multi-client root-agreement gate will trip over first. See
> [08-gas-and-access-events.md](08-gas-and-access-events.md).

## Non-public inputs

| # | Source | What it covers | Caveat |
|---|--------|----------------|--------|
| 13 | **CL-side design discussion on attester shadow-root telemetry** — internal chat, 2026-07-27 → 2026-07-29 (migration lead, CL specs team, client-team and consensus-spec reviewers) | The transport design space for shadow-root publication: rate-limited global gossip topic vs subnets / req/resp / ENR / beacon-state field / attestation extension; the ~800k-messages-per-epoch bandwidth objection; the signature-verification DoS concern; fork-independent deployment. Summarized in [11-attester-telemetry-transport.md](11-attester-telemetry-transport.md). | **Not a specification and not public.** A design conversation, not a decision record — positions may move. Participants are referred to by role. Supersedes nothing in EIP-8347; the companion spec is still unwritten. |

## How to re-fetch / re-verify

The command sandbox whitelists `eips.ethereum.org` for network; the published EIP page is
the authoritative current spec text. GitHub (for source history) needs the sandbox disabled.

```bash
# Published EIP pages — authoritative current spec text (allowed host)
# use WebFetch on https://eips.ethereum.org/EIPS/eip-8297
# use WebFetch on https://eips.ethereum.org/EIPS/eip-8347

# Raw EIP source in the repo (requires gh auth; run with sandbox disabled)
gh api repos/ethereum/EIPs/contents/EIPS/eip-8297.md -H "Accept: application/vnd.github.raw"
gh api repos/ethereum/EIPs/contents/EIPS/eip-8347.md -H "Accept: application/vnd.github.raw"

# What changed since the last sync — the fastest way to spot spec drift.
# Read the per-commit diffs rather than re-reading the whole EIP.
gh api 'repos/ethereum/EIPs/commits?path=EIPS/eip-8297.md&per_page=25' \
  --jq '.[] | "\(.commit.author.date) \(.sha[0:8]) \(.commit.message | split("\n")[0])"'
gh api 'repos/ethereum/EIPs/commits?path=EIPS/eip-8347.md&per_page=25' \
  --jq '.[] | "\(.commit.author.date) \(.sha[0:8]) \(.commit.message | split("\n")[0])"'
gh api repos/ethereum/EIPs/commits/<sha> --jq '.files[] | .patch'

# Implementation status — the devnet pins every client branch in one file
gh api repos/CPerezz/pbt-devnet/contents/scripts/sources.sh \
  -H "Accept: application/vnd.github.raw"
gh api 'repos/CPerezz/pbt-devnet/branches?per_page=50' --jq '.[].name'
gh api 'repos/CPerezz/go-ethereum/pulls?state=all&sort=updated&direction=desc&per_page=25' \
  --jq '.[] | "\(.merged_at != null) #\(.number) \(.title)"'
```

Note the `?`/`&` in those URLs need single quotes under `zsh`, and `gh` reads credentials
from `~/.config/gh`, which the sandbox denies — run these with the sandbox disabled.

For the hackmd and GitHub-pages sources, use the `WebFetch` tool (they are public).
Responses are cached ~15 min per URL.

## Related EIPs

| EIP | Title / role |
|-----|--------------|
| **EIP-8297** | Partitioned Binary Tree (this KB's subject) |
| **EIP-8347** | Offline State Migration to the PBT — the **actual chosen migration EIP**; `requires: 7523, 7928, 8159, 8297` |
| **EIP-7523** | Empty accounts deprecation (`Last Call`) — added to EIP-8347's `requires` on 2026-08-25; it is what makes BAL-replay's `nonce == 0 ∧ balance == 0 ∧ code_size == 0` deletion trigger exact in both directions, since no empty account survives in the MPT |
| **EIP-8037** | State Creation Gas Cost Increase (`Review`) — the Amsterdam state-creation companion to EIP-8038; `requires: … 8038` |
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
- Re-fetch both published EIP pages (commands above) each sync. As of 2026-08-07:
  EIP-8297 has been revised three times since the key/node-type rework — code is now
  uniformly content-addressed (no header chunks), zero-writes now delete leaves, and
  EIP-7702 delegation indicators now live in a `DELEGATION_LEAF_KEY` header leaf instead
  of `CODE_ZONE` — see [05-design-evolution.md](05-design-evolution.md); EIP-8347 has
  moved from PR #12006 to a published EIP page with `requires: 7928, 8159, 8297`,
  RLP-based artifact formats, and matching delegation-leaf converter/BAL-replay rules.
  *(Historical: both of those EIP-8347 details have since changed — `requires` gained
  `7523` on 2026-08-25, and the preimage file left RLP for fixed-width hashed-key-ordered
  records on 2026-08-20. See the 2026-09-02 note below.)*
  When the two disagree, **EIP-8297 (the tree spec) wins** per this KB's standing
  convention.
- **2026-08-12 re-verification:** re-fetched both EIP pages in full against every
  numbered file in this KB (01–10). Tree structure, key derivation constants, zero/deletion
  rule, and delegation-leaf handling all still match the current EIP-8297 text exactly —
  no drift found there. One correction made: EIP-8347's "Canonical digests" section pins
  `snapshotDigest` and `preimageDigest` as **keccak256, unconditionally** — the KB's
  [04-migration.md](04-migration.md#hash-domains) hash-domains table previously hedged this
  as "BLAKE3 (snapshots) or keccak256 (self-migration)," which is now corrected. Also
  confirmed execution-specs issues
  [#3253](https://github.com/ethereum/execution-specs/issues/3253) and
  [#3254](https://github.com/ethereum/execution-specs/issues/3254) (the EIP-7610/`CREATE`
  and zero-value-leaf fixture-conformance issues) are both **closed**, consistent with
  [10-zero-value-leaves-and-deletion.md](10-zero-value-leaves-and-deletion.md)'s "resolved"
  status. Confirmed `execution-specs`' `projects/binary-trie` branch directly (a local
  clone exists at `~/Documents/ef/execution-specs`; GitHub's tree view doesn't render via
  WebFetch since it's client-side JS — `git fetch`/`git show` against the local clone is
  the reliable way to inspect it): actively developed (last commit 2026-08-10), with a
  `src/ethereum/binary_trie/` + `src/ethereum/forks/binary_tree/` implementation and a
  substantial EIP-8297 test suite (`tests/binary_tree/eip8297_partitioned_binary_tree/*`,
  `tests/binary_trie/*` — account/delegation lifecycle, code chunking/sharing, storage
  ops, differential MPT-vs-binary-tree parity). Its 2026-08-06 "store delegation
  indicators in the account header" commit matches EIP-8297 PR #12114's merge date exactly.
  Found **no** EIP-8347 migration/converter/preimage-extraction code on this branch (the
  two hits that looked relevant by name — `fuzzer_bridge/converter.py`,
  `test_create_preimage_layout.py` — are unrelated: a fuzzer-DTO converter and a
  `CREATE`-address preimage test helper, respectively). The top-level README's "Migration
  specs and tests: *TBD*" is confirmed still accurate, not just unverified. Note also a
  dormant `projects/ubt` branch (last commit 2026-04-29, disjoint history from
  `projects/binary-trie`) — almost certainly the stale EIP-7864 ("Unified Binary Tree")
  predecessor effort per [05-design-evolution.md](05-design-evolution.md); superseded, not
  a second current implementation.
- **2026-09-02 re-verification.** Checked the commit history of both EIP files rather than
  re-reading them whole (commands above), then swept the implementations.
  - **EIP-8297: unchanged.** Last commit is still 2026-08-06 (`2c6da5e9`, the reserved-fields
    note). Every tree constant, key-derivation rule, deletion rule and delegation-leaf rule
    in files 01–03, 05 and 10 of this KB still matches. No action taken.
  - **EIP-8347: two revisions.** `a08f51fe` (2026-08-20, [PR
    #12215](https://github.com/ethereum/EIPs/pull/12215)) **re-cut the preimage file** from
    RLP `[address, [slotKey…]]` records sorted byte-lexicographically by address to
    **fixed-width `address[20] | slotCount[4, BE] | slotKey[32] * slotCount` records sorted
    by `keccak256(address)` / `keccak256(slotKey)`** — i.e. in MPT iteration order, so the
    consensus-anchoring re-hash and a hash-keyed self-converter can walk trie and file as
    one sequential merge with no random access and no in-memory index. Converter step 2 is
    now a sequential merge against the scan rather than an indexed lookup. This **reverses**
    a supersession this KB and [../open-questions.md](../open-questions.md) had recorded the
    other way round; both are corrected. The snapshot's RLP `[key, value]` leaf records are
    **not** affected. `21e1d9ec` (2026-08-25, [PR
    #12239](https://github.com/ethereum/EIPs/pull/12239)) added **EIP-7523** to `requires`,
    citing it as what makes the BAL-replay account-deletion trigger exact in both directions.
  - **execution-specs `projects/binary-trie`:** tip `09d2088c`, 2026-08-13 — three weeks
    quiet, and only merges from `forks/amsterdam` since 2026-08-10. Now proposed upstream as
    draft [PR #3207](https://github.com/ethereum/execution-specs/pull/3207) into
    `forks/amsterdam`. Two EIP-8297 test PRs (#3444 reorg-branch provider state, #3446
    genesis commitment provider) were **closed unmerged** on 2026-08-28. Still **no**
    EIP-8347 migration code on the branch, so the top-level README's "Migration specs and
    tests: *TBD*" remains accurate.
  - **The action moved to the clients.** Sources #9–#12 above are new and carry the detail.
    Headlines: the devnet went from geth-only to **three implementations under differential
    test** (geth, Besu, Erigon), Erigon's tree lives in the **upstream** repo, geth has a
    **complete EIP-8347 implementation** (convert / import+dual-check / BAL-replay / swap /
    transition window), a **migration devnet passed its M1 gate** on empty state
    (2026-08-27), and Nethermind has a prototype it labels not-for-merge. Reth has nothing.
  - **Two drifts to watch,** both recorded in #11/#12: geth's preimage writer still emits
    the pre-2026-08-20 RLP layout, and Erigon deliberately keeps zero-valued leaves against
    current EIP-8297 while refusing account removal.
- Keep the "Last synced" date in [README.md](README.md) current when you refresh, and the
  "Verified against live sources" date in the [top-level README](../README.md).
