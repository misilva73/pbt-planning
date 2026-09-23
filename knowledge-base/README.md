# PBT knowledge base

This is a working guide to the proposed **Partitioned Binary Tree (PBT)** and MPT-to-PBT migration. [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) defines the tree; [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) defines the offline migration. Both were Drafts when checked on **2026-09-23**. The EIPs take precedence over this guide. The tree hash, activation fork, and shadow-root wire format remain open.

## Read by task

| Need | Page |
|---|---|
| Short explanation and terms | [Overview](01-overview.md) |
| Nodes, keys, root, and deletion | [Tree structure](02-tree-structure.md) |
| Account, code, delegation, and storage mapping | [Key derivation](03-key-derivation.md) |
| Conversion, snapshot, replay, and swap | [Migration](04-migration.md) |
| Old versus current designs | [Design evolution](05-design-evolution.md) |
| Security properties and superseded questions | [Security notes](06-open-questions.md) |
| Primary sources and dated implementation evidence | [Sources](07-sources.md) |
| Proposed access pricing | [Gas and access events](08-gas-and-access-events.md) |
| Migration trade-offs | [Online versus offline](09-online-vs-offline-migration.md) |
| Why state writes delete zero-valued leaves | [Zero and deletion decision](10-zero-value-leaves-and-deletion.md) |
| Proposed shadow-root transport | [Attester telemetry](11-attester-telemetry-transport.md) |
| Test coverage and gaps | [Testing inventory](12-testing-inventory.md) |

For unresolved decisions, use [the live question tracker](../open-questions.md). For schedules and owners, use [the roadmap](../roadmap/README.md).

## Reading rules

- **Specification:** EIP-8297 and EIP-8347 are the current source for normative rules. If the two disagree on tree behavior, check the latest revisions before implementing either.
- **Proposal:** Roadmap dates, readiness thresholds, gas costs, and telemetry designs are plans, not protocol rules.
- **Snapshot:** Client and test status is dated. See [sources](07-sources.md) for the evidence and date; do not treat an old count as current.
- **Historical:** The third-party PBT spec rendering and earlier EIP drafts may describe different key widths, node types, or code placement. Use [design evolution](05-design-evolution.md) to identify them.

The EIP-8347 preimage file is fixed-width and ordered by hashed keys; snapshot leaf records are separate. The reference tree uses BLAKE3, while artifact digests use Keccak256. These are different hash domains.
