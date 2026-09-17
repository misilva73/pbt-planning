# 07 — Sources & Re-fetching

## Primary sources (synced 2026-09-17)

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
| 9 | **PBT devnet** — https://github.com/CPerezz/pbt-devnet | The live differential devnet for EIP-8297 **and EIP-8347**. As of 2026-09-17 it runs **two profiles, four implementations**, composing `ethpandaops/ethereum-package` with no patches on an **Amsterdam-at-genesis** chain (which forces Gloas at slot 0) under real Lighthouse CLs. **`make tree-at-genesis`** — EIP-8297, **seven nodes**: two geth, two Besu, two Erigon and **one Nethermind**, each pair configured differently, all starting on the binary tree (`binaryTrieTime` in genesis) and required to agree on every state root through forced reorgs; `pbtchaos` cuts the next proposer's p2p every 15–30 blocks and runs six state-stranding scenarios (`code-sole`, `code-shared`, `delegate`, `account`, `storage-add`, `storage-del`). **`make migration` / `make migration-smoke`** — EIP-8347, **five participants across four clients** (geth on 1 and 3, Erigon on 2, Besu on 4, Nethermind on 5) starting on the **merkle** trie and switching at `binaryTrieTime`, with partitions **before, across and after** the fork block `I*`, a straddle phase that islands every light across `I*` and forces it to rewind and re-cross on the anchor's block, and a judge emitting one `PASS`/`FAIL`/`INCONCLUSIVE` line per check (fork block per node, per-victim straddle rewind, heal deadlines, orphaned fork blocks gone, **shadow-root agreement**, completion after the fork block finalized, lap manifest). Each client migrates differently: geth from **BALs**, Erigon by **folding both commitment domains** from `erigon init` (`COMMITMENT_HEX_BIN=true`), Besu by **swapping the trie per header**, Nethermind by **mirroring flat state into its PBT backend** (`--Pbt.Enabled`, anchor bootstrapped from the genesis allocation). | Implementation status, not a spec source — verify devnet behavior against the current EIP-8297 revision rather than assuming parity. **Evidence is scoped per client**, not uniform: `internal/migmon/registry.go` gives each client an evidence contract and checks scope to what it declares, so a thinner contract weakens the verdict rather than failing it. Besu exposes **no** `debug_migrationProgress` / shadow-root RPC, so its migration evidence is the weakest of the four; Erigon keeps folding both domains and is **not** judged on shadow retirement; geth and Nethermind retire the merkle shadow once the fork block finalizes. The last accepted milestone is still **M1 — "the empty-state migration devnet is accepted", 2026-08-27** (`migration-m1-tooling`); there is **no M2 and no run on non-trivial state**, so multi-client migration is *wired and exercised*, not *validated at scale*. Re-read [`scripts/sources.sh`](https://github.com/CPerezz/pbt-devnet/blob/main/scripts/sources.sh) before citing client pins — but note it is **currently stale in two ways**: it does not list Nethermind at all (that image builds from the `pbt-state` branch via `scripts/build-images.sh` / `PBT_NETHERMIND_SRC`), and it pins Besu to `CPerezz/besu@glamsterdam-devnet-8-pbt`, **a branch that does not exist in that fork** (404) — the branch of that name lives in `matkt/besu`. Reth is still **not** in it. Evidence source for [A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md), [A-C3](../roadmap/deliverables/A-C3-multiclient-pbt-genesis-devnets.md) and [B-T2](../roadmap/deliverables/B-T2-full-cycle-devnet-swap.md). |
| 10 | **Client PBT branches** — geth `CPerezz/go-ethereum@pbt` (tip `e31a37fb`, 2026-09-07) · Erigon `erigontech/erigon@binary-trie` (tip `c69ae9f1`, 2026-09-17) · Nethermind `NethermindEth/nethermind@pbt-state` (tip `9aa5717f`, 2026-09-17) · Besu `matkt/besu@glamsterdam-devnet-8-pbt` (tip `487d91e0`, 2026-09-14, "add pbt devnet apis") + library `besu-eth/besu-stateless@feat/partitioned-binary-trie` (tip `de1a3c33`, 2026-09-09, "fix reorg issues") · genesis `CPerezz/ethereum-genesis-generator@pbt` | The **four** implementations the devnet now runs. **geth** carries the only *complete* EIP-8347 implementation (see #11) but has been **quiet since 2026-09-07** — the rest of the field is now moving faster. **Erigon**'s branch lives in the *upstream* repo, reads `binaryTrieTime` at `erigon init`, and is under daily development (bin-witness replay fixes for `CREATE` pre-state storage and delete-then-rewrite accounts; a 41% allocation cut in the `pbin` fold). **Nethermind**'s `pbt-state` has gone from dormant prototype to the **most active branch in the field** (parallel trie-updater folds, node groups keyed by zero-padded path + nibble count, RocksDB block-restart tuning, dropping the depth-prefixed node-path encoding, and a correctness fix counting **delegation leaves as code references** on rebuild). **Besu** hashes with `Blake3Digest(256)` and keeps its tree in the `besu-stateless` library; it takes `--data-storage-format=BINARY` for the tree-at-genesis profile but must **omit** it to migrate, since that flag fixes the format for the whole datadir at startup. Note Besu has moved org: `besu-eth/besu`, not `hyperledger/besu`. | Implementation status, not spec sources — fork branches, none merged upstream. All four hardcode/expect **BLAKE3**, which the spec does **not** pin ([open-questions.md](../open-questions.md#hash-function-selection--the-dominant-open-parameter)) — do not read devnet agreement as evidence that `H` is settled; a fourth independent implementation agreeing on BLAKE3 roots raises the switching cost again without deciding anything. **Reth** still has nothing: no branch, issue or PR matching PBT / EIP-8297 as of 2026-09-17. |
| 11 | **EIP-8347 migration implementation in geth** — `CPerezz/go-ethereum@pbt`, PRs [#14](https://github.com/CPerezz/go-ethereum/pull/14) (converter), [#16](https://github.com/CPerezz/go-ethereum/pull/16) (snapshot import + dual-check), [#31](https://github.com/CPerezz/go-ethereum/pull/31) (BAL-replay follower, swap, transition window), [#33](https://github.com/CPerezz/go-ethereum/pull/33) (sidechain replay into the shadow tree), [#34](https://github.com/CPerezz/go-ethereum/pull/34) (replay a sidechain parent before delaying a payload; merged 2026-09-07) | The only end-to-end EIP-8347 implementation that exists. `geth bintrie convert` emits the byte-canonical snapshot + preimage artifacts; `geth bintrie import` verifies them with the spec's dual-check; a follower replays BALs onto whichever tree execution is not committing, backfilling missing lists over `eth/71`, and the header root swaps source at `binaryTrieTime` with the merkle side held until a post-fork block finalizes. `debug_shadowStateRoot` / `debug_shadowRoots` / `debug_migrationProgress` expose the sidecar feed. Reported figures on a 70k-account / 140k-slot / 5.2k-code fixture (114.7 MB datadir, page-cache-resident): **convert 5.05 s (13.9k accounts/s), import 2.03 s (34.5k accounts/s), artifacts 29.4 MB**; the author's naive extrapolation to ~270 GB mainnet state puts the **compute** floor at 3–4 h. | Implementation status, not a spec source, and **still known to lag the spec**: re-checked `cmd/geth/bintrie_artifacts.go` on 2026-09-17 — the preimage writer continues to emit **RLP records re-sorted into address order** (`rlp.EncodeToBytes`, an external `RecordSorter` keyed on the address, and a reader that rejects records "out of address order"), four weeks after EIP-8347 replaced that layout with fixed-width hashed-key-ordered records (#3). The irony is that the code's own comment notes the scan already walks in hashed-key order — the sorter exists purely to undo the order the current spec wants. The snapshot writer's RLP `[key, value]` records are correct and unaffected. Treat the perf numbers as compute-only on cached fixtures — not mainnet I/O. Evidence source for [B-C1](../roadmap/deliverables/B-C1-converter-prototype.md), [B-C2](../roadmap/deliverables/B-C2-bal-replay-engine.md), [A-C4](../roadmap/deliverables/A-C4-snapshot-serving-verification.md). |
| 12 | **Upstreaming PRs** — geth [ethereum/go-ethereum#35436](https://github.com/ethereum/go-ethereum/pull/35436) · Erigon [erigontech/erigon#22942](https://github.com/erigontech/erigon/pull/22942) + tracking issue [#23389](https://github.com/erigontech/erigon/issues/23389) · Nethermind [NethermindEth/nethermind#12573](https://github.com/NethermindEth/nethermind/pull/12573) · besu-stateless [#92](https://github.com/besu-eth/besu-stateless/pull/92) · execution-specs [#3207](https://github.com/ethereum/execution-specs/pull/3207) | Where each implementation is headed upstream. geth's is literally the devnet branch (`CPerezz/go-ethereum@pbt`), opened draft "temporary, for discussion" (last touched 2026-09-07). Erigon's is `--experimental.bin-commitment`, off by default, with **67 of 70** EIP-8297 blockchain fixtures passing. Nethermind's is still formally a **prototype behind a not-for-merge warning** (branch `pbt-state`, author `asdacap`) exploring node-grouping layouts for a binary tree on RocksDB. execution-specs' `projects/binary-trie` is proposed into `forks/amsterdam`. Erigon's tracking issue [#23389](https://github.com/erigontech/erigon/issues/23389) is the best single status page in the ecosystem: it lists the commitment engine, devnet join (issue [#23384](https://github.com/erigontech/erigon/issues/23384), **closed 2026-09-02**) and **"mainnet PBT state conversion — in progress"**, and records that **PBT needs no Caplin change** because `ExecutionPayload.state_root` is opaque to the beacon chain — per EIP-8347, "the consensus-layer change is fork scheduling alone". | All drafts; none merged, and **none has moved toward merge in this sync window** — only the branches behind them moved. Erigon's PR still documents the same **real divergences from the spec and from geth**, unchanged as of 2026-09-17: it keeps zero-valued leaves (against current EIP-8297, and the reason two of its three fixture failures are deliberate), refuses account removal outright, and leaks code chunks above a shortened redeploy's length — which it notes makes recompute-from-domains invalid as an oracle for any code-bearing account, reachable via an EIP-7702 delegation clear. **Nethermind's label is now at odds with its role**: the PR still says "exploratory and likely throwaway… expect force-pushes", while the branch is the most actively developed in the field and is a live participant in *both* devnet profiles. Its published numbers (~3 ms → ~11 ms root calculation; depth-4-interleave fastest; clustered layout "completely broken") remain prototype measurements, not conformance evidence. Note the CL claim above scopes to *the swap*; it says nothing about the shadow-root telemetry carrier, which is still unspecified — see [11-attester-telemetry-transport.md](11-attester-telemetry-transport.md). |

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
- **2026-09-17 re-verification.** Same method as the 2026-09-02 sweep: commit history for both
  EIP files, then the implementations. **Nothing in this KB's spec content changed; everything
  that moved is implementation status.**
  - **Both EIPs unchanged.** EIP-8297's tip is still `2c6da5e9` (2026-08-06) and EIP-8347's is
    still `21e1d9ec` (2026-08-25). Frontmatter re-read directly: both still `Draft`, EIP-8347
    still `requires: 7523, 7928, 8159, 8297`. No new PBT-related EIP or EIP PR opened; the
    **gas-repricing EIP is still undrafted**. Files 01–05, 08 and 10 of this KB need no change.
  - **execution-specs is still stalled.** `projects/binary-trie` tip is *still* `09d2088c`
    (2026-08-13) — now five weeks quiet — and draft PR [#3207](https://github.com/ethereum/execution-specs/pull/3207)
    has not been touched since. Still **no EIP-8347 migration code**, so the top-level README's
    "Migration specs and tests: *TBD*" stays accurate. This is now the **slowest-moving link in
    the chain**: four client implementations are being differentially tested against a reference
    suite whose branch nobody has advanced in over a month.
  - **The headline: the migration devnet became multi-client.** On 2026-09-02 EIP-8347 was a
    geth-only story. Between 2026-09-11 and 2026-09-16 the devnet brought **Erigon, Besu and
    Nethermind** through the migration profiles, each with a *different* strategy (BAL-replay,
    folding both commitment domains, per-header trie swap, flat-state mirroring). "Anything
    multi-client on the migration side", listed as not-yet-demonstrated in the last sync, has
    flipped — see #9 for what that does and does not prove.
  - **Nethermind joined the devnet and woke up.** It is now a participant in **both** profiles
    (the tree-at-genesis devnet went from six nodes / three implementations to **seven nodes /
    four**), and `pbt-state` has been committing daily through 2026-09-17. Its upstream PR still
    carries the not-for-merge warning; treat the label as stale relative to the branch.
  - **Two drifts from the last sync both persist, unfixed.** geth's preimage writer still emits
    the pre-2026-08-20 RLP address-sorted layout (re-read the source, #11), and Erigon still
    keeps zero-valued leaves while refusing account removal (#12). Neither has an open fix.
  - **Still not demonstrated:** independent producers emitting **bit-identical** artifacts;
    conversion at **mainnet scale** (Erigon lists it "in progress"); any migration run on
    **non-trivial state** — M1 (empty state, 2026-08-27) is still the last accepted gate; and the
    shadow-root **CL carrier**.
  - **Two stale pins in the devnet's `scripts/sources.sh`** worth fixing upstream: it omits
    Nethermind entirely, and its Besu line points at a branch that 404s. Detail in #9.
- Keep the "Last synced" date in [README.md](README.md) current when you refresh, and the
  "Verified against live sources" date in the [top-level README](../README.md).
