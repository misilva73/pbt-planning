# PBT Planning

Plans and reference material for Ethereum's proposed **Partitioned Binary Tree (PBT)**
and the migration from the **Merkle Patricia Trie (MPT)**. PBT combines account data,
storage and contract code in one tree, designed to make state proofs smaller and easier
to generate.

## Start here

| Resource | Contents |
|----------|----------|
| [Knowledge base](knowledge-base/README.md) | Tree design, migration mechanics and supporting sources |
| [Roadmap](roadmap/README.md) | Delivery plan, milestones and responsibilities |
| [Open questions](open-questions.md) | Unresolved decisions and the work needed to close them |
| [Testing inventory](knowledge-base/12-testing-inventory.md) | Existing coverage, reported results and remaining gaps |

## Specifications

The canonical specifications live outside this repository. Both EIPs are **Draft**
(status checked 2026-09-23).

| Specification | Scope |
|---------------|-------|
| [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) | PBT structure and state encoding |
| [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) | Offline conversion, snapshot verification, catch-up and activation |

The tree's hash function remains undecided. PBT gas repricing is tracked separately in
[the roadmap](roadmap/deliverables/A-S2-gas-cost-recalibration.md).

## Tests and devnet

- **Tree tests:** [`execution-specs@projects/binary-trie`](https://github.com/ethereum/execution-specs/tree/projects/binary-trie)
  contains the EIP-8297 implementation and test suite.
- **Converter and snapshot-consumer tests:** [Hive PR #1614](https://github.com/ethereum/hive/pull/1614)
  adds shared checks for converter outputs and preimage/snapshot consumers. It is an
  **open draft** as of 2026-09-23; BAL replay is outside its scope.
- **Devnet:** [CPerezz/pbt-devnet](https://github.com/CPerezz/pbt-devnet) exercises
  PBT from genesis and live migration across geth, Erigon, Nethermind and Besu
  (client coverage checked 2026-09-17).

See the [testing inventory](knowledge-base/12-testing-inventory.md) for coverage and results.

## Client implementations

Development branches recorded in the **2026-09-17 source review**:

| Client | Implementation |
|--------|----------------|
| geth | [`CPerezz/go-ethereum@pbt`](https://github.com/CPerezz/go-ethereum/tree/pbt) |
| Erigon | [`erigontech/erigon@binary-trie`](https://github.com/erigontech/erigon/tree/binary-trie) |
| Nethermind | [`NethermindEth/nethermind@pbt-state`](https://github.com/NethermindEth/nethermind/tree/pbt-state) |
| Besu | [`matkt/besu@glamsterdam-devnet-8-pbt`](https://github.com/matkt/besu/tree/glamsterdam-devnet-8-pbt) and the [`besu-stateless` PBT library](https://github.com/besu-eth/besu-stateless/tree/feat/partitioned-binary-trie) |

These are reference links, not a reproducible build configuration. The Hive suite uses
its own client selections, including a different geth branch. For upstream PRs, known
limitations and instructions to verify status, see [Sources](knowledge-base/07-sources.md)
and the [Hive inventory](knowledge-base/12-testing-inventory.md#artifact-conformance).
