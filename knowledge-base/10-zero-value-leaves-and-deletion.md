# Zero values and deletion

**Decision: Ethereum state writes of zero delete the leaf.** The current [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297#zero-values-and-deletion) and [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347#bal-replay) agree. This page records why an earlier keep-zero rule was dropped.

## The rule

The generic binary tree accepts any 32-byte leaf value. The Ethereum **state transition** maps a zero write to key deletion. A read of an absent key returns zero, and a second zero write changes nothing. Deletion restores the tree's canonical branch form. The state tree therefore contains no zero-valued leaves, even though the generic data structure could hold one.

This applies to storage in the header or storage zone and to all-zero code chunks. A code chunk's leading PUSHDATA count is part of its 32-byte value; a chunk is absent only when that count and all 31 code bytes are zero. `code_size` and `code_hash` still identify code whose chunks are all absent.

Account deletion removes the account header and storage leaves. Shared code leaves remain while another resulting-state account uses that code hash. Under current account-lifecycle rules the check is local to the transaction; [EIP-8297 explains why](https://eips.ethereum.org/EIPS/eip-8297#content-addressed-code).

## Why the earlier rule changed

An early draft treated a present zero leaf as distinct from an absent leaf. That would allow two PBT roots for the same EVM-visible state, depending on write history. It would also conflict with BAL replay: a BAL records post-values, not whether the original leaf existed or how it became zero. Deleting on zero makes a snapshot converted from an MPT and a snapshot advanced by BAL replay converge on the same leaf set.

Keeping zero leaves might have helped a future state-expiry scheme preserve proof history, but EIP-8297 does not implement that scheme. Zero leaves would increase retained state and complicate conversion, replay, and non-inclusion proofs today. Future expiry work can specify its own representation.

## What to test

- Insert, update, zero, and repeat-zero for header storage and overflow storage.
- All-zero code chunks, including chunks with a nonzero PUSHDATA continuation count.
- Account deletion, shared code, and canonical branch collapse.
- Equality of roots produced by direct conversion and by BAL replay to the same block.

See [tree structure](02-tree-structure.md#zero-values-and-deletion) and [testing inventory](12-testing-inventory.md).
