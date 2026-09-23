# PBT overview

**Partitioned Binary Tree (PBT)** is a proposed replacement for Ethereum's hexary Merkle Patricia Tries (MPT). [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) is a Draft; its hash function is not final. This page describes the proposal, not an activated mainnet change.

## Why change the state tree?

The MPT uses RLP, Keccak, and separate account and storage tries. That makes state proofs large, code segments hard to prove, and root computation dependent on finishing a storage trie before its account leaf. EIP-8297 gives an illustrative account branch of about 5,760 bytes and a worst-case unchunked-code witness of about 1.8 GB.

PBT puts account data, storage, and chunked code in one binary tree. A leaf contains a full key and a 32-byte value. Binary branching and path compression reduce proof overhead; independent leaves let implementations compute parts of the root in parallel. The tree uses a hash rather than curve-based commitments. The choice of hash remains open; the reference implementation uses BLAKE3.

## How state is organized

The first key byte defines a **zone**: `0x00` for account headers, `0x01` for shared, content-addressed code, and `0xFF` for storage. `0x02`–`0xFE` are reserved. Each account header groups basic data, its code hash *or* delegation indicator, and storage slots 0–63. Larger storage slots live in an account-specific storage bucket. Contracts with identical bytecode share code leaves.

The EVM still uses ordinary 256-bit storage slots. Key derivation happens inside the client. `EXTCODEHASH` still uses Keccak on bytecode, independent of the tree hash. A separate proposal, [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347), describes conversion from the MPT and a later commitment swap.

## Terms

| Term | Meaning |
|---|---|
| **Stem** | Shared prefix of keys in one group: zone byte plus tree position. The last byte selects one of 256 sub-indices. |
| **Leaf / branch** | A leaf commits a full key and value. A branch commits a shared bit prefix and two children. |
| **`key_hash` / `H`** | The same proposed 32-byte hash is used for key placement and tree nodes; its selection is open. |
| **BAL** | Block-Level Access List, used by EIP-8347 to replay writes after conversion. |
| **Anchor / activation** | The finalized block whose MPT state is converted; the later fork that makes PBT canonical. Neither is scheduled by EIP-8347. |
| **Shadow root** | A pre-swap PBT root reported by an attester for a block's post-state. Reports are out of consensus. |

Read [tree structure](02-tree-structure.md), [key derivation](03-key-derivation.md), or [migration](04-migration.md) for details.
