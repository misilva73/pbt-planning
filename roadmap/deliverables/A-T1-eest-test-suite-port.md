# A-T1 · EEST test-suite port

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Tests |
| **Timeline** | 2026-08 → 2027-01 (6 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight** (as of 2026-09-02) — a substantial EIP-8297 suite exists on `execution-specs@projects/binary-trie` and is being consumed by clients; branch quiet since 2026-08-13 |

← [Back to roadmap](../README.md)

## Objective
Port the Ethereum Execution Spec Tests (EEST) framework so it can fill and execute
state-transition and access-event tests against PBT (EIP-8297) state commitments instead
of the MPT. This gives every client tree implementation a shared, executable oracle:
fixtures encode the expected PBT state and, once the hash function is pinned, the expected
PBT root. It is the backbone the cyan Tests workstream builds on and the reference all
green client implementations run against.

> **Update (2026-09-02).** The port exists and is in use. `execution-specs`'
> [`projects/binary-trie`](https://github.com/ethereum/execution-specs/tree/projects/binary-trie)
> branch carries a `src/ethereum/binary_trie/` + `src/ethereum/forks/binary_tree/`
> implementation and an EIP-8297 test suite
> (`tests/binary_tree/eip8297_partitioned_binary_tree/*`, `tests/binary_trie/*`) covering
> account and delegation lifecycle, code chunking and sharing, storage operations, and
> differential MPT-vs-binary-tree parity — plus, since the last sync, zero-code-chunk
> vectors ([#3305](https://github.com/ethereum/execution-specs/pull/3305)), consecutive
> deploys into a shared code zone ([#3316](https://github.com/ethereum/execution-specs/pull/3316))
> and delegation re-auth / 2935 ring-buffer / chunking edges
> ([#3338](https://github.com/ethereum/execution-specs/pull/3338)). It is proposed upstream
> into `forks/amsterdam` as draft [PR #3207](https://github.com/ethereum/execution-specs/pull/3207).
>
> Clients are consuming it: geth reports the suite **fully green**
> ([PR #13](https://github.com/CPerezz/go-ethereum/pull/13)), and Erigon reports **67 of
> 70** blockchain fixtures passing.
>
> **Two things to watch.** (1) The branch tip has not moved since **2026-08-13** — only
> merges down from `forks/amsterdam` — and two EIP-8297 test PRs (#3444 reorg-branch
> provider state, #3446 genesis commitment provider) were **closed unmerged** on 2026-08-28.
> Test-suite momentum has stalled while client work accelerated. (2) Erigon's three failures
> are fixtures the reference marks as pinning *current provider behaviour* rather than
> conformance — two zero-write tests where `state_pbt.py` deletes on a zero write, and one
> `CREATE2`-after-EIP-161-clear test the reference itself calls an open consensus question.
> **A suite that encodes provider behaviour rather than the spec cannot serve as the shared
> oracle this deliverable is for**; separating the two is now part of the work.

## Scope — what ships
- EEST state-test and blockchain-test fillers adapted to emit PBT key/value state and PBT
  roots, replacing MPT trie construction with the two-node-type tree (LeafNode/BranchNode,
  canonical prefix-compressed form) from EIP-8297.
- Key-embedding hooks so fillers derive tree keys via the zone/stem/sub-index scheme
  (account header stem, storage buckets, content-addressed code overflow).
- Gas fixtures covering PBT's state-access and code-chunk accounting: code events keyed by
  `(zone, tree_position, sub-index)` in the content-addressed `CODE_ZONE`, shared across
  accounts with the same `code_hash` and charged once per block — there are no per-account
  header chunks any more (EIP-8297 moved all code into `CODE_ZONE` on 2026-08-04) — with the
  actual state-access and per-chunk costs left as parameters until the gas repricing EIP
  ([A-S2](A-S2-gas-cost-recalibration.md)) fixes them from benchmarks.
- A fixture format that carries the PBT state root (parameterized on the hash function until
  the hash-function dependency lands) and CI wiring so clients consume the ported suite.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) — the key/value tree,
  node types and merkelization must be converged before fillers can target them.
- **Downstream (this blocks):** [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md) — the
  cross-client conformance suite executes these fixtures. Runs in parallel with
  [A-C1](A-C1-client-tree-implementations.md), which is validated against the port.

## Owners / teams
- EEST maintainers (framework, fillers, fixture format)
- Client test leads (per-client consumer integration, CI)

## Exit criteria (definition of done)
- [ ] EEST can fill and run PBT state/blockchain tests end to end, producing fixtures with
      PBT state (root parameterized on hash until the hash-function dependency resolves).
- [ ] Gas tests cover PBT's state-access accounting and content-addressed code-chunk
      accounting, with costs treated as parameters pending [A-S2](A-S2-gas-cost-recalibration.md).
- [ ] At least one client implementation ([A-C1](A-C1-client-tree-implementations.md))
      consumes the ported suite in CI.
- [ ] Fixture format is documented and stable enough for [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md).

## Risks & open questions
- Hash function is not final (BLAKE3 in the reference impl only): root-bearing fixtures must
  stay hash-parameterized until the [hash-function dependency](../README.md) resolves — see
  [open-questions.md](../../open-questions.md) (hash-function
  selection).
- PBT's state-access and code-chunk gas costs are not yet fixed; gas fixtures must treat
  them as parameters pending the benchmark-based repricing EIP
  ([A-S2](A-S2-gas-cost-recalibration.md)).

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [open-questions.md](../../open-questions.md)
- [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md)
- [jsign/binary-tree-spec](https://github.com/jsign/binary-tree-spec) — existing Python binary-tree
  reference impl (EIP-7864, BLAKE3) that the ported fillers can cross-check against once adapted to PBT.
