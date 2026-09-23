# Security and historical notes

The live issue tracker is [open-questions.md](../open-questions.md). This page records security properties of the current [EIP-8297 draft](https://eips.ethereum.org/EIPS/eip-8297) and design questions that older drafts raised.

## Current security properties

- **Key collisions:** Account, storage-bucket, storage-group, and code-group positions use full 256-bit digests. Different zones have different first bytes. Identical bytecode deliberately shares code leaves; this is deduplication, not a collision.
- **Grinding:** An attacker can choose storage slots to search for long common prefixes. Path compression stores a common run in one branch prefix. The storage-group hash also includes the address, so a set chosen for one account does not transfer to another account's bucket.
- **Unambiguous node hashes:** Leaf and branch preimages have different tags. Branch prefixes include their bit length, so different logical nodes have different preimages before hashing.
- **Shared code deletion:** Under the current account-lifecycle rules, deciding whether a code leaf can be removed is local to the transaction. See [EIP-8297's content-addressed-code rationale](https://eips.ethereum.org/EIPS/eip-8297#content-addressed-code). A future rule allowing live contract-code replacement would need a new sharing rule.

These properties rely on collision resistance of the selected tree hash. That hash is still open.

## Superseded questions

Early drafts used truncated address prefixes and asked how to handle bucket collisions. The current draft uses full digests and byte-wide zones. Older descriptions of fixed-depth zone boundaries, four node types, or code chunks in account headers are also superseded. See [design evolution](05-design-evolution.md).

PBT's full-width account positions may help a separate privacy design such as [EIP-7503](https://eips.ethereum.org/EIPS/eip-7503); PBT itself does not implement it.
