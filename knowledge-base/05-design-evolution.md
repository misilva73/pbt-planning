# How PBT's design changed

The [current EIP-8297 draft](https://eips.ethereum.org/EIPS/eip-8297) takes precedence over older drafts and the third-party [PBT spec rendering](https://cperezz.github.io/pbt-spec/). Use this page to identify stale constants before copying them into code or tests.

## Lineage

[EIP-7864](https://eips.ethereum.org/EIPS/eip-7864) proposed a flat unified binary tree. EIP-8297 added zones, account-specific storage buckets, and content-addressed code. A later rework replaced fixed 32-byte keys and four node types with variable-length, prefix-free keys and two node types. Subsequent revisions moved *all* code into the shared code zone, made zero-valued state writes delete leaves, and placed EIP-7702 delegation indicators in the account header.

## Old and current forms

| Feature | Older design | Current EIP-8297 |
|---|---|---|
| Key | Fixed 32 bytes with truncated hash portions | Zone-dependent 34-byte account/code keys, 66-byte storage keys; generic maximum 8,192 bytes |
| Zone | High bits of a stem | First full byte: `0x00` account, `0x01` code, `0xFF` storage |
| Nodes | Internal, stem, leaf, empty | Full-key leaf and compressed-prefix branch; zero root for empty tree |
| Storage bucket | Truncated address prefix | Full `key_hash(address)` plus full address-bound group digest |
| Header | Basic data, storage, and sometimes first code chunks | Basic data; code hash **or** delegation; storage slots 0–63; no code chunks |
| Code | Early chunks per account, later chunks shared | Every chunk content-addressed by `code_hash` in `CODE_ZONE` |
| Zero write | Earlier draft could retain a present zero leaf | Ethereum state mapping deletes the key; generic tree still accepts any value |
| Boundary | Often described at a fixed node depth | Exact key-space region; compressed branches need not exist at fixed depths |

The current packed basic-data leaf has `version` at byte 0, `code_size` at bytes 4–7, `nonce` at bytes 8–15, and `balance` at bytes 16–31. The third-party rendering may still show a 3-bit or 4-bit zone variant, old offsets, or stem nodes. Do not combine those layouts with the current EIP.

## Why the changes matter

Full digests avoid the old short-prefix collision concern. Full-key leaves and compressed branches give one canonical tree for a key/value set. Uniform code sharing removes duplicate code across accounts. Deleting zero-valued state leaves makes MPT conversion and BAL replay converge. The dedicated delegation leaf avoids treating an EIP-7702 indicator as ordinary shared bytecode.

[EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) does not currently list the Verkle-era online migration EIP as a formal requirement; [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) separately specifies offline migration. See [tree structure](02-tree-structure.md), [key derivation](03-key-derivation.md), and the [zero-value decision](10-zero-value-leaves-and-deletion.md) for current mechanics.
