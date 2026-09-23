# Sources and verification

**Specification check: 2026-09-23.** The published [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) and [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) pages were checked for the rules summarized in this knowledge base. Both pages displayed `Draft`; EIP-8347 listed `requires: 7523, 7928, 8159, 8297`. The implementation snapshot below was last swept **2026-09-17** and was not refreshed during the September 23 spec check. A targeted [Hive artifact draft](https://github.com/ethereum/hive/pull/1614) review was added September 23. Dates matter: do not promote a dated branch finding into a current claim.

## Primary sources

| Source | Use it for | Limit |
|---|---|---|
| [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) | Tree nodes, key derivation, values, deletion, and security rationale | Draft; tree hash not final. |
| [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) | Offline migration, canonical files, verification, BAL replay, and swap | Draft; anchor/fork schedule and telemetry wire rules open. |
| [Migration strategy roadmap](https://hackmd.io/@CPerezz/H1Q2zt8NMe) | Program phases and operator planning | Strategy, not normative; may retain older artifact text. |
| [PBT spec rendering](https://cperezz.github.io/pbt-spec/) | Historical rationale | May render superseded key and node designs; see [design evolution](05-design-evolution.md). |
| [Verkle transition survey](https://notes.ethereum.org/@parithosh/verkle-transition) | Historical online/offline options | Predates PBT. |
| [EIP-2926](https://eips.ethereum.org/EIPS/eip-2926), [EIP-8038](https://eips.ethereum.org/EIPS/eip-8038), [EIP-8037](https://eips.ethereum.org/EIPS/eip-8037) | Related code- and state-gas proposals | Not a final PBT gas schedule. |
| [Code-chunk analysis](https://hackmd.io/@jsign/verkle-code-mainnet-chunking-analysis) | Verkle-era empirical code access data | Do not treat its gas estimates as PBT constants. |

EIP-8347's preimage file changed in [PR #12215](https://github.com/ethereum/EIPs/pull/12215) to fixed-width records sorted by hashed key. The snapshot still uses RLP leaf records. Its [PR #12239](https://github.com/ethereum/EIPs/pull/12239) added EIP-7523 as a dependency. EIP-8297's current delegation header leaf came through [PR #12114](https://github.com/ethereum/EIPs/pull/12114).

## Dated implementation evidence

| Source | September 2026 finding | Verification limit |
|---|---|---|
| [PBT devnet](https://github.com/CPerezz/pbt-devnet) | On 2026-09-17, tree-at-genesis ran seven nodes across geth, Besu, Erigon, and Nethermind. A four-client migration profile exercised different migration mechanisms. | The accepted M1 gate used empty state. Client evidence contracts differ; this is not mainnet-scale validation. |
| [geth PBT branch](https://github.com/CPerezz/go-ethereum/tree/pbt) | Converter, snapshot import/dual-check, BAL follower, activation, and transition-window code existed. | At the 2026-09-17 check, its preimage writer still used the old RLP/address-order format. A later Hive draft tested a corrected branch; recheck before calling the branch conformant. |
| [Erigon PBT branch](https://github.com/erigontech/erigon/tree/binary-trie) and [tracking issue](https://github.com/erigontech/erigon/issues/23389) | Commitment implementation, devnet participation, and conversion work in progress. | Its then-reported zero-leaf and account-removal behavior differed from EIP-8297. |
| [Nethermind PBT PR](https://github.com/NethermindEth/nethermind/pull/12573) | Active prototype and devnet participant. | PR retained a prototype/not-for-merge warning. |
| [Besu PBT library](https://github.com/besu-eth/besu-stateless/pull/92) | Tree and migration integration in a devnet branch. | Migration introspection was thinner than other clients in that snapshot. |
| [execution-specs binary-trie PR](https://github.com/ethereum/execution-specs/pull/3207) | EIP-8297 reference implementation and fixtures proposed upstream. | September 17 snapshot still saw no EIP-8347 migration suite on that branch. |
| [Hive artifact PR #1614](https://github.com/ethereum/hive/pull/1614) | September 23 draft with shared artifact mutations and producer checks. | PR-reported results, not re-run here; see [testing inventory](12-testing-inventory.md#artifact-conformance). |

For each implementation, inspect the branch/PR and its commit date before updating a status statement. A devnet pass shows what its workloads and evidence contracts checked, not full spec conformance. BLAKE3 root agreement among clients also does not settle EIP-8297's hash choice.

## Non-public inputs

A July 27–29, 2026 CL-side discussion covered candidate transports for signed attester shadow roots, including gossip, subnets, request/response, ENR, and consensus-field changes. It was a design conversation, not a specification or decision. [Attester telemetry](11-attester-telemetry-transport.md) summarizes its technical questions without attributing private comments by name. EIP-8347 remains authoritative on what is actually specified.

## How to re-verify

1. Read both published EIP pages and compare their specification sections with [tree structure](02-tree-structure.md), [key derivation](03-key-derivation.md), and [migration](04-migration.md).
2. Check each EIP's source commit history for changed text, especially key layout, zero handling, preimage encoding, and dependencies.
3. Inspect devnet source pins and client PRs at explicit commits. Re-run tests before reporting passes; preserve the source date when reporting a snapshot.
4. Update the [testing inventory](12-testing-inventory.md), [roadmap](../roadmap/README.md), and [open questions](../open-questions.md) if a spec decision or implementation gate actually changes.

Related protocol inputs: [EIP-7523](https://eips.ethereum.org/EIPS/eip-7523) (empty accounts), [EIP-7928](https://eips.ethereum.org/EIPS/eip-7928) (BALs), [EIP-8159](https://eips.ethereum.org/EIPS/eip-8159) (`eth/71` BAL exchange), and [EIP-7954](https://eips.ethereum.org/EIPS/eip-7954) (code size). Historical online transition proposals are [EIP-7612](https://eips.ethereum.org/EIPS/eip-7612) and [EIP-7748](https://eips.ethereum.org/EIPS/eip-7748).
