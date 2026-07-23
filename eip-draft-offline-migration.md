---
eip: <to be assigned>
title: Offline state migration to the Partitioned Binary Tree
description: Convert Ethereum state to the PBT off the consensus-critical path at a fixed anchor block, distribute a verifiable snapshot, and swap the state commitment at a single fork
author: Carlos Perez (@CPerezz), Maria Silva (@misilva73), Kevaundray Wedderburn (@kevaundray)
discussions-to: <URL>
status: Draft
type: Standards Track
category: Core
created: 2026-07-23
requires: 7928, 8297
---

## Abstract

This EIP specifies an **offline** migration of Ethereum's state from the hexary Merkle Patricia Trie (MPT) to the Partitioned Binary Tree (PBT) defined in [EIP-8297] (the successor to the unified binary tree of [EIP-7864]).

The full state at a finalized **anchor block `ANCHOR_BLOCK`** is converted off the consensus-critical path. The result is distributed as a byte-canonical, verifiable **snapshot**. That snapshot is caught up to the chain tip by replaying Block-Level Access Lists ([EIP-7928]), and it is made canonical at a single EL+CL hard fork **`SWAP_FORK`**. Both trees are maintained through a transition window until finality after `SWAP_FORK`.

 This proposal defines `ANCHOR_BLOCK`, `SWAP_FORK`, the snapshot artifact, the dual-check verification procedure, and the **shadow-root** observability concept.

## Motivation

Upgrades to Ethereum's state trie, such as [EIP-8297], require us to move live mainnet state to a new commitment without splitting the chain. There are two broad ways to do this. One is to convert the state *inside consensus* while the chain keeps running. This is the online overlay family, and [EIP-7748] and [EIP-7612] are its most developed proposals. The other is to convert the state *offline* and swap the commitment in one step.

The online overlay approach has real strengths. There is no distribution event, it uses less disk, and verification lives inside consensus. But it puts conversion code on the consensus-critical path. If that code has a bug, it is a consensus bug. It can split the chain, and it only shows up once consensus already depends on the new tree. The overlay approach also keeps two trees consensus-live for the whole conversion. That opens gas-discrepancy attack surface between the MPT and the PBT. It slows down state access, because a read or write may have to check the overlay tree and then the base MPT on the hot path. It also forces zkEVM provers to prove the in-consensus conversion steps for every block in the window.

This EIP takes the offline path instead. The classic downsides of going offline are distribution trust and catch-up correctness. We propose solutions to remove both. In return, conversion stays entirely off the consensus-critical path. This buys us four things:

- Conversion failures surface **before** consensus depends on the new tree, so there is no live chain split.
- The consensus change is a single, small fork that swaps the commitment.
- Execution semantics stay the same until activation, and the migration stays fully recoverable until the activation release deploys.
- We can rehearse the whole procedure end to end on real state.

## Specification

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119 and RFC 8174.

### Parameters

| Symbol | Meaning | VALUE |
|---|---|---|
| `ANCHOR_BLOCK` | Anchor block whose state is converted; MUST be finalized and is identified by block hash | TBD, selected during the mainnet window (post-rehearsal) |
| `SWAP_FORK` | EL+CL hard fork at which the PBT becomes the canonical state commitment | TBD, scheduled after the shadow-commitment period |
| `REANCHOR_CADENCE` | Re-anchoring cadence for late joiners | TBD |

### Process overview

The sections below define the pieces of the migration: the converter, the preimages, BAL-replay, the snapshot artifact, the dual-check verification, and the shadow commitment. Together they form one lifecycle. That lifecycle carries the network from an MPT-committed state to a PBT-committed state, and conversion never touches the consensus-critical path. This section shows how the pieces fit together and what node operators and validators do at each phase. Consensus runs on the MPT through all the pre-swap phases. The commitment does not change until `SWAP_FORK`.

The migration proceeds in five phases:

1. **Conversion (off-chain).** A finalized block is designated as `ANCHOR_BLOCK`. The [converter](#the-converter) reads the state committed by `ANCHOR_BLOCK`'s `stateRoot`, derives PBT keys per [EIP-8297], and produces two byte-canonical artifacts: the [snapshot](#snapshot-artifact) (the converted PBT, chunked with a manifest) and the [preimages](#preimages) (the key preimages needed to re-derive MPT paths). Because conversion is a pure function of committed state, independent converters MUST produce bit-identical output, and this step happens entirely off consensus.

2. **Distribution and verification.** The snapshot and preimages are published off-chain. Any node obtains them, either by downloading or by self-converting, and MUST run the [dual-check verification](#verification-dual-check). The node rebuilds the PBT and confirms the claimed root (internal consistency). It also re-hashes the leaves under the MPT schema, using the preimages, and confirms they reproduce `ANCHOR_BLOCK`'s `stateRoot` (consensus anchoring). This lets a node reject a corrupted or malicious artifact without trusting the distributor. The manifest digest, anchored in the activation client release, allows per-chunk authentication during download.

3. **Catch-up.** `ANCHOR_BLOCK` lags the chain tip, and continues to lag as new blocks are produced. A node brings its verified snapshot forward to the tip by [BAL-replay](#bal-replay): applying the recorded writes of each subsequent block's Block-Level Access List ([EIP-7928]) directly to the PBT, with no re-execution. Replay MUST outpace block production so the converted state converges to and then tracks the tip.

4. **Shadow-commitment period.** Once nodes track the tip on the PBT, block builders SHOULD publish a [shadow root](#shadow-commitment). This is the PBT root of each block's post-state, published while consensus still runs on the MPT. It makes conversion correctness observable and attributable per block, before it matters. Divergence is visible and harmless, so bugs are caught and fixed ahead of the swap rather than after. The length of this period is what builds confidence that the PBT root is correct across clients.

5. **Swap and transition window.** At the coordinated EL+CL hard fork [`SWAP_FORK`](#fork-swap_fork), the PBT becomes the canonical state commitment. Nothing else about execution changes. The [transition window](#transition-window) runs from `SWAP_FORK` activation until it is finalized. Through this window, nodes MUST maintain both trees and MUST keep the migration recoverable to the MPT. Only after finality MAY a node dispose of the MPT.

#### What node operators and validators do

- **Before the swap.** Obtain the snapshot and preimages, run the dual-check verification, and catch the state up to the tip by BAL-replay. A node that fails either check MUST reject the artifact and re-obtain or re-convert. From this point the node maintains the PBT alongside its MPT.
- **During the shadow-commitment period.** Continue tracking the tip on both trees. Validators that build blocks SHOULD publish shadow roots so that cross-client agreement on the PBT root can accumulate; a missing shadow root counts against coverage rather than as a divergence.
- **At `SWAP_FORK`.** Switch the canonical state commitment to the PBT. No action is required to preserve execution semantics. Gas, opcodes, transaction validity, and `EXTCODEHASH` are unchanged.
- **Through the transition window.** Keep both trees until `SWAP_FORK` is finalized so that a fault can be recovered by falling back to the MPT. Dispose of the MPT only after finality.

### Anchor block `ANCHOR_BLOCK`

The anchor block `ANCHOR_BLOCK` is the source of the conversion and the consensus-anchoring target.

- `ANCHOR_BLOCK` MUST be finalized before conversion output is published, and MUST be identified by its block hash.
- The conversion source is the state committed by `ANCHOR_BLOCK`'s header `stateRoot` under the MPT schema.
- The converted PBT is defined solely as a function of the key/value state at `ANCHOR_BLOCK`; it does not depend on any client's internal database layout.

### Fork `SWAP_FORK`

At fork `SWAP_FORK`, the PBT becomes the canonical state commitment.

- `SWAP_FORK` is a coordinated EL and CL hard fork.
- The swap changes the state commitment **only**. Gas schedule, opcode semantics, transaction validity rules, and the meaning of `code_hash` are unchanged by `SWAP_FORK`.
- `EXTCODEHASH` MUST return the same value across `SWAP_FORK` for every account, because `code_hash = keccak256(bytecode)` is independent of the PBT merkelization hash.
- Post-swap PBT-native gas changes (e.g. chunk-granular code access, stem warm/cold semantics) are out of scope for this EIP and MUST NOT be bundled with `SWAP_FORK`.

### The converter

The converter is a deterministic function from MPT state to PBT state. Given the state at `ANCHOR_BLOCK`, it MUST:

1. Scan the source (MPT) leaves.
2. Validate that `keccak256(preimage)` matches the trie path for each leaf.
3. Derive PBT keys per [EIP-8297].
4. Sort leaves by PBT key order (an external merge-sort for mainnet-scale state).
5. Construct the tree bottom-up in a single sequential pass.

Independent, correct converters operating on the same state at `ANCHOR_BLOCK` MUST produce a bit-identical PBT root and a bit-identical canonical snapshot. Sorting in PBT-key order lets snapshot ingestion be a sequential bulk-load rather than random inserts. Converters SHOULD emit resumability markers so an interrupted conversion can resume without restarting.

### Preimages

The MPT is hash-keyed and cannot be iterated back into raw keys, so key preimages MUST be distributed alongside the snapshot. Preimages serve (a) self-converters running on hash-keyed clients and (b) verifiers performing the consensus-anchoring check. Where preimages are extracted at an earlier height `EXTRACT_HEIGHT`, completeness over `(EXTRACT_HEIGHT, ANCHOR_BLOCK]` MUST be established by BAL-completion (see below).

The preimage file is a concatenation of per-account records with no framing between them. Each record is:

```text
address[20] | slotCount[4, big-endian] | slotKey[32] * slotCount
```

that is, the 20-byte account address, the number of storage-slot keys for that account as a 4-byte big-endian unsigned integer, followed by that many 32-byte storage-slot keys. An account with no storage has `slotCount = 0` and contributes no slot keys. Each record is self-delimiting, so the file is parsed by reading records sequentially until end of input.

The file MUST be byte-canonical, so independent producers emit bit-identical output. To achieve this, the ordering is fixed:

- Records MUST be sorted by `address` ascending, compared as 20-byte big-endian (byte-lexicographic) values. Each address MUST appear at most once.
- Within a record, `slotKey` entries MUST be sorted ascending, compared as 32-byte big-endian (byte-lexicographic) values, with no duplicates.

A verifier recovers the MPT account path as `keccak256(address)` and each storage path as `keccak256(slotKey)`; this is what makes the consensus-anchoring check against `ANCHOR_BLOCK`'s header `stateRoot` possible.

### BAL-replay

State transition from the anchor to the tip is performed by replaying Block-Level Access Lists ([EIP-7928]) **without re-execution**. For each block after `ANCHOR_BLOCK`, per-entry translation rules apply the recorded writes to the PBT:

- Balance and nonce changes and storage writes are applied as PBT leaf writes.
- In the migration context, a write of zero is encoded as leaf **absence**; zero-writes therefore delete leaves.
- Account deletion requires no special BAL marker.
- Replay MAY be batched; batching MUST keep the replay rate below steady-state block production so that a converted snapshot converges to the tip.

BAL-replay is used both to catch a snapshot up from `ANCHOR_BLOCK` to the chain tip and to close the `(EXTRACT_HEIGHT, ANCHOR_BLOCK]` gap when preimages are extracted at height `EXTRACT_HEIGHT`.

### Snapshot artifact

The conversion result is published as a snapshot with the following properties:

- **Byte-canonical.** Serialization is fully specified below, so independent producers MUST emit bit-identical output.
- **Sorted in PBT-key order** to enable bulk ingestion.
- **Chunked**, with per-chunk hashes recorded in a manifest whose digest is anchored in the activation client release, enabling per-chunk verification during download.

#### Leaf record

Each leaf of the [EIP-8297] PBT is serialized as a self-delimiting record:

```text
key[keyLen] | value[32]
```

where `key` is the full PBT tree key and `value` is its 32-byte leaf value. The leading **zone byte** of `key` fixes `keyLen`, so records are parsed without external framing:

| Zone byte | Zone | `keyLen` |
|---|---|---|
| `0x00` | account header | 34 |
| `0x01` | code | 34 |
| `0xFF` | storage | 66 |

An account/code key is `zone[1] | stem[32] | subindex[1]` and a storage key is `zone[1] | stem[64] | subindex[1]`, per [EIP-8297].

The trailing byte of every key is the **sub-index**. Two records belong to the same **stem** if and only if their keys are equal in all bytes except the sub-index. In other words, `key[:-1]` is identical. Because the snapshot is sorted in PBT-key order, all records sharing a stem are contiguous.

#### Chunking

Leaf records are grouped into chunks that never split a stem, using a fixed target size `SNAPSHOT_CHUNK_TARGET_BYTES = 16777216` (16 MiB):

1. Partition the sorted record stream into maximal **stem groups**, the maximal runs of records sharing `key[:-1]`.
2. Pack stem groups into chunks greedily in stream order. Before appending a group, if the current chunk is non-empty and appending the group would make the chunk exceed `SNAPSHOT_CHUNK_TARGET_BYTES`, close the current chunk and start a new one; then append the group.
3. Chunks are numbered from `0` in stream order.

A single stem holds at most 256 sub-indices, so the largest possible stem group is `256 * (66 + 32) = 25088` bytes. That is far below `SNAPSHOT_CHUNK_TARGET_BYTES`. Every stem group therefore fits in a chunk, the algorithm always makes progress, and each chunk is at most `SNAPSHOT_CHUNK_TARGET_BYTES`. Because the target size is fixed and the packing is deterministic, all correct producers cut chunk boundaries identically.

#### Manifest

The manifest is the byte-canonical index of the chunked snapshot:

```text
pbtRoot[32] | leafCount[8, big-endian] | chunkCount[4, big-endian] | chunkEntry * chunkCount
```

where each `chunkEntry`, in ascending `chunkIndex` order, is:

```text
chunkIndex[4, big-endian] | byteLength[4, big-endian] | chunkHash[32]
```

`chunkHash` is `keccak256` of the chunk's bytes. The **manifest digest** is `keccak256` of the manifest and is the value anchored in the activation client release; verifying it fixes both the set of chunk hashes and the claimed `pbtRoot`, so a downloader can authenticate any chunk in isolation and reject a corrupted one before ingesting it.

### Verification (dual-check)

Any node MUST be able to verify a downloaded snapshot without trusting the distribution source. This includes a fresh node with no prior state. To verify, the node performs both checks:

1. **Internal PBT consistency.** Rebuild the PBT from the snapshot leaves, derive keys per [EIP-8297], hash bottom-up, and verify the claimed PBT root.
2. **Consensus anchoring.** Re-hash the snapshot leaves under the **MPT schema** using the distributed preimages and verify the result against block `ANCHOR_BLOCK`'s header `stateRoot`.

A snapshot that fails either check MUST be rejected.

### Shadow commitment

During the pre-swap period, while consensus still runs on the MPT, block builders SHOULD compute and publish a **shadow root**: the PBT root of the post-state of each block. This makes conversion correctness observable per block, publicly and attributably. A missing shadow root counts against a **coverage** metric rather than as a divergence, preserving interpretability. The wire mechanism by which shadow roots are carried is an open parameter and is fixed in a companion specification.

### Transition window

Both the MPT and the PBT MUST be maintained from the activation of the PBT at `SWAP_FORK` until `SWAP_FORK` is finalized. Only after finality MAY a node dispose of the MPT. Until the activation release deploys, the migration MUST remain fully recoverable to the MPT.

## Rationale

### Why offline conversion instead of the online overlay

[EIP-7748] and [EIP-7612] convert the state in consensus behind a moving conversion boundary. An initially-empty overlay tree takes new writes over a frozen base MPT. That design is well developed and has genuine advantages: no distribution event, minimal disk overhead, and verification integrated into consensus. This EIP still rejects it, because it places conversion logic on the consensus-critical path. Correctness failures then become consensus failures, and they surface only after consensus already depends on the new tree. Two trees are consensus-live for the whole conversion, which exposes gas-discrepancy attack surface between the MPT and the PBT. State access pays a hot-path penalty, because a read or write may have to traverse both the overlay and the base MPT. Every zkEVM prover must also prove the in-consensus conversion. The offline model trades the distribution event and extra disk for keeping conversion entirely off that path. There, failures are observable and recoverable before the swap.

### What is borrowed and what is discarded

From [EIP-7748] this EIP keeps the **leaf-by-leaf conversion semantics**. That is the definition of how an MPT leaf maps to PBT keys and values. From [EIP-7612] it keeps the structural idea of a **frozen base tree plus a fresh tree that starts empty and takes new writes**, which is also how the [EIP-8297] tree begins. What it deliberately discards is the **live overlay iterator and the in-consensus conversion-boundary machinery**. Here the conversion boundary is a single finalized block `ANCHOR_BLOCK`, not a per-block cursor, and catch-up is done by BAL-replay rather than by an in-consensus iterator.

### Why an anchor block and a single fork

Pinning conversion to one finalized block `ANCHOR_BLOCK` makes the conversion output a pure function of committed state. So independent producers can be required to agree bit-for-bit, and a fresh node can anchor trust in `ANCHOR_BLOCK`'s `stateRoot` without trusting any distributor. Collapsing activation into one fork `SWAP_FORK` keeps the consensus change small and the swap semantics trivial (commitment only). That is what makes comprehensive rehearsal and full recoverability achievable.

### Why BAL-replay for catch-up

The conversion-node lineage this design descends from relied on ad-hoc catch-up messages. Replaying [EIP-7928] Block-Level Access Lists instead applies per-block writes directly and needs no re-execution. BALs are already produced for other reasons, so this needs no migration-specific gossip. Encoding zero as leaf absence keeps deletions implicit and avoids a special account-deletion marker.

### Why fixed-size, stem-aligned snapshot chunks

Chunking exists to let a downloader authenticate and ingest the snapshot incrementally. So the boundary rule has to balance verification granularity against manifest overhead. Three schemes were considered:

- **Fixed leaf count** (N leaves per chunk). This is trivial to implement. But a boundary can fall in the middle of a stem and split a stem's sub-indices across two chunks. Ingestion and per-subtree verification then need both chunks, and the byte size of a chunk varies with the mix of 34- and 66-byte keys.
- **One stem per chunk.** This gives the cleanest verification unit, since each chunk is exactly one PBT subtree. But at ~100+ GB of state it produces hundreds of millions of tiny chunks (a stem is at most ~25 KB, and most are far smaller). The manifest itself becomes enormous and download bookkeeping dominates.
- **Fixed max byte size, stem-aligned** (chosen). Chunks target a fixed byte budget (`SNAPSHOT_CHUNK_TARGET_BYTES`) and are cut only at stem boundaries. This keeps chunks uniformly sized for transport and keeps the manifest small. It also guarantees that every stem, and therefore every independently verifiable subtree, lives wholly within one chunk. A single stem (≤ 256 sub-indices, ≤ ~25 KB) is always smaller than the target, so packing never stalls and every chunk stays within budget.

Fixing the target size in this EIP, rather than leaving it to producers, is deliberate. The chunk boundaries feed the per-chunk hashes in the manifest, and the manifest digest is anchored in the activation release. So the boundaries must be reproducible bit-for-bit across independent producers.

### Why shadow roots

The offline model's weak point is that consensus does not observe conversion correctness before the swap. Publishing per-block PBT roots during the pre-swap period restores that observability. Divergence between a builder's shadow root and the expected PBT root is visible, attributable, and harmless, since consensus still runs on the MPT. So it can be caught and fixed before `SWAP_FORK` rather than after.

## Backwards Compatibility

`SWAP_FORK` changes the state commitment only, so it is backwards compatible at the application layer:

- **Contracts.** No change. Contracts continue to address storage by 256-bit slot number via `SLOAD`/`SSTORE`; PBT key derivation runs inside the client, below the EVM. No Solidity/Yul changes are required.
- **Execution semantics.** Gas costs, opcode behavior, and transaction validity are unchanged across `SWAP_FORK`. `EXTCODEHASH` is byte-identical.

The migration is **not** transparent to systems that depend on the state structure itself:

- **On-chain proof consumers.** The migration removes the per-account `storage_root` and changes the tree hash. So contracts and services that verify Merkle proofs of Ethereum state (bridges, light-client verifiers, `eth_getProof` consumers) require coordinated upgrades. This is the longest-lead-time dependency of the migration, and it is tracked separately.
- **Node operators.** Nodes MUST obtain and verify the snapshot (or self-convert) and MUST retain both trees through the transition window.

## Security Considerations

### Unvalidated-flip input

At `SWAP_FORK`, the PBT root activated for the final pre-fork block has not itself been validated by consensus. So a converter bug affecting only those final blocks could be activated. There are two mitigations. Hard-enforce the shadow root for the final blocks before `SWAP_FORK`, or rely on sustained cross-client agreement over the shadow-commitment period. A correlated all-client conversion bug would be undetectable under either the online or the offline model, so this is not unique to this proposal.

### Validator observability gap

The shadow-root stream measures block *producers*, not the validating majority, so it does not directly observe what most validators would compute. Pre-swap divergence is nonetheless harmless and self-detectable, and a proposer-signed post-import sidecar is the designed fallback for closing the gap.

### Distribution trust

The snapshot is large (~100+ GB) and distributed off-chain. In principle this could be a vector for serving corrupted state. The dual-check verification neutralizes it. Internal PBT consistency plus consensus anchoring against `ANCHOR_BLOCK`'s `stateRoot` lets any node reject a bad artifact without trusting the source, including a fresh node. Per-chunk manifest hashes anchored in the activation release extend this guarantee to partial downloads.

### Recoverability

Both trees are maintained until `SWAP_FORK` is finalized, and the MPT is not disposed of before then. So a fault discovered during or immediately after the swap can be recovered by falling back to the MPT, until the activation release deploys.

## Copyright

Copyright and related rights waived via [CC0](../LICENSE).

<!-- Reference links -->
[EIP-7612]: https://eips.ethereum.org/EIPS/eip-7612
[EIP-7748]: https://eips.ethereum.org/EIPS/eip-7748
[EIP-7864]: https://eips.ethereum.org/EIPS/eip-7864
[EIP-7928]: https://eips.ethereum.org/EIPS/eip-7928
[EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297
