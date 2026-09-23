# MPT to PBT migration

[EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) is the Draft specification for offline migration; [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) defines the tree. The [strategy roadmap](https://hackmd.io/@CPerezz/H1Q2zt8NMe) adds planning context. This page follows the EIP when their details differ. Neither the anchor block nor activation fork is scheduled in the EIP.

## Implementation status

The [2026-09-17 source snapshot](07-sources.md) found tree implementations in geth, Erigon, Besu, and Nethermind, plus a four-client migration devnet. That is an implementation snapshot, not a protocol readiness claim. The accepted M1 migration gate used empty state; mainnet-scale conversion, independent snapshot production, and the CL shadow-root carrier remained unproven. A [2026-09-23 Hive draft](12-testing-inventory.md#artifact-conformance) added shared artifact checks and reported matching geth/Erigon preimages, but still had only one snapshot producer. Recheck these dated claims before quoting them.

## Source discrepancies to reconcile

The strategy roadmap's suggested 2–3 week dual-state period differs from EIP-8347's **50,400-block re-anchor cadence**. These measure different things: cadence limits how far a new node must replay; the EIP's post-swap transition window lasts until activation finality. The roadmap also contains older artifact descriptions. Use the EIP's current byte formats below.

## The core decision: offline conversion (not online overlay)

Conversion runs against a finalized MPT state outside consensus. Before activation, the MPT remains canonical while nodes build and advance PBT locally. At one fork, the existing `stateRoot` field changes from an MPT root to a PBT root. This avoids putting a conversion cursor or per-block conversion work in consensus. It costs temporary disk space for two trees and requires distributing a large artifact. [The comparison](09-online-vs-offline-migration.md) covers the trade-off.

## Historical context: the four Verkle-transition options

Earlier transition studies considered an online overlay, a conversion node, local bulk conversion, and state expiry. EIP-8347 develops the offline conversion approach with canonical artifacts, independent verification, and BAL-based catch-up. Those earlier options are background, not alternate procedures in the current EIP.

## Six-phase program timeline

The [roadmap](../roadmap/README.md) groups the work into spec convergence, prototypes, devnets, migration machinery, rehearsals, mainnet preparation, and swap/aftermath. Its dates and fork labels `H*` and `I*` are planning assumptions. EIP-8347 instead defines a five-part lifecycle: conversion, distribution and verification, catch-up, shadow reporting, then swap and transition. The first four can overlap across nodes.

### Migration lifecycle (the EIP view)

1. Select a finalized `ANCHOR_BLOCK` by block hash and extract the required preimages.
2. Convert its MPT state into a byte-canonical PBT snapshot.
3. Download or self-produce the artifacts, then perform both verification checks.
4. Replay subsequent Block-Level Access Lists (BALs) to the tip and report shadow roots before activation.
5. Activate PBT at `PBT_ACTIVATION_FORK`; keep both trees until that fork finalizes.

## Two migration paths for node operators

### Option A — Self-migrate (expert path)

A node that still holds the anchor's MPT state can run the converter locally. It must still check the output. Retaining the required preimages or reconstructing them is a separate, potentially expensive task; hashed MPT paths cannot be inverted.

### Option B — Download snapshot (majority path)

A node obtains the snapshot and preimage file from any distributor. Digests help compare producers before download, but are not proof of correctness. The node verifies the artifact against its own header chain before replaying BALs. A node that has pruned the anchor state uses this path.

## Key machinery

### The Converter

The converter scans the anchor's MPT leaves and reconstructs their full hashed paths. It matches each account and slot preimage by Keccak hash in both directions; missing *or surplus* preimages are errors. It derives PBT keys, writes each shared code leaf once, omits zero-valued leaves, sorts by PBT key, and builds the tree bottom-up. Correct producers must emit the same root and artifact bytes for the same anchor.

### BAL-replay

BALs record post-values. Replay applies their writes to PBT without re-executing transactions. A zero storage write deletes its leaf; account deletion removes its header and storage bucket. Code and delegation updates follow EIP-8297's mutually exclusive header leaves. Rollback discards unfinalized PBT layers rather than trying to invert BALs. BALs are fetched over `eth/71` ([EIP-8159](https://eips.ethereum.org/EIPS/eip-8159)); availability is bounded through re-anchoring.

### Delegation indicators (EIP-7702)

A delegated account has a `DELEGATION_LEAF_KEY` header leaf instead of a code-hash leaf and no code-zone leaves. Clearing delegation removes that leaf and restores the empty-code hash leaf. See [key derivation](03-key-derivation.md#delegation-indicators-eip-7702).

### Actors and roles

Anyone may produce or distribute artifacts. Every consuming node verifies them; attesters are additionally asked to report signed shadow roots. Distribution identity is not a root of trust.

### Snapshot distribution

The snapshot is `pbtRoot[32] | leafCount[8, big-endian] | leafRecord * leafCount`, sorted by full PBT key. Each leaf record is RLP `[key, value]`; the value is a minimal canonical integer and is left-padded to 32 bytes for tree hashing. The file contains leaves, not inner nodes. Transport chunking and optional indexes do not change verification.

### Preimages — why they're needed

MPT paths are Keccak hashes of account addresses or 32-byte slot keys. The preimage file provides those raw keys for conversion and for rebuilding the MPT commitment from snapshot leaves. Each fixed-width record is `address[20] | slotCount[4, big-endian] | slotKey[32] * slotCount`. Records sort by `keccak256(address)`; slot keys within each record sort by `keccak256(slotKey)`. The file must match the MPT key set exactly. This replaced an older RLP, address-sorted format.

## Verification — dual-check authentication

A consumer must (1) rebuild PBT from all leaves and match the claimed `pbtRoot`, and (2) re-hash the state under the MPT schema using preimages and match the anchor header's `stateRoot`. Because the MPT does not hold bytecode, the second check also reassembles each distinct contract's chunks, verifies Keccak against its code hash, then re-chunks it to verify the encoded chunk values. The header chain, not a distributor's manifest, supplies the anchor root.

## Hash domains

| Use | Hash |
|---|---|
| MPT paths and EVM `code_hash` | Keccak256 |
| PBT key placement and node hashes | `H`, not final; reference uses BLAKE3 |
| `snapshotDigest` and `preimageDigest` over complete artifact bytes | Keccak256, fixed by EIP-8347 |

Artifact digests are quick producer-comparison signals. Dual-check runs regardless of them.

## Shadow commitment & observability

Before activation, attesters **SHOULD** publish each block's PBT post-state root signed with their validator key. The MPT remains canonical; missing reports reduce measured coverage, while different roots for the *same block hash* show divergence. EIP-8347 calls for an out-of-consensus telemetry sidecar but leaves wire format, aggregation, timing, and EL-to-CL plumbing to a future companion EIP. A gossip topic is one [design option](11-attester-telemetry-transport.md), not a selected protocol.

## Testing framework (EEST coverage)

Testing must cover tree and state-transition conformance, canonical conversion artifacts, BAL replay, snapshot verification, reorgs across activation, and mainnet-scale operation. The dated [testing inventory](12-testing-inventory.md) separates implemented coverage from gaps.

## Parameters

| Parameter | Current EIP-8347 treatment |
|---|---|
| `ANCHOR_BLOCK` | Finalized block, identified by hash; to be selected. |
| `PBT_ACTIVATION_FORK` | Later EL+CL fork; scheduled by a fork meta EIP, not EIP-8347. |
| `REANCHOR_CADENCE` | 50,400 blocks, about one week at 12-second slots. |
| Shadow-root carrier and readiness thresholds | Open; the sidecar details and any thresholds need separate decisions. |

### Re-anchoring & late joiners

Distributors produce a fresh, independently verified snapshot and preimage file at successive finalized anchors. A joining node takes the latest available finalized anchor and replays from there. The cadence must keep the required BAL range within BAL retention.

## Known weak points & mitigations

- **Last pre-fork root:** It has not yet been consensus validated as a PBT root. Sustained cross-client shadow agreement provides evidence; EIP-8347 also discusses possible hard enforcement for the final blocks, without specifying it as the normal rule.
- **Coverage:** Shadow reports are voluntary, so low validator coverage means weak evidence rather than agreement.
- **Bad artifacts:** Dual-check rejects fabricated snapshots against the node's own anchor header. Transport integrity only helps identify bad chunks earlier.
- **Reorgs and recovery:** A reorg across activation returns to MPT commitment before the fork. Both trees stay available until activation finality.

## Ecosystem impact

Contracts keep the same storage and code semantics. The swap changes the commitment only; any PBT gas repricing belongs to a separate EIP. Proof consumers, including bridges and `eth_getProof` users, need migration plans because the root and proof format change. Fresh-node sync can use a recent snapshot plus BAL replay until PBT-native sync is available.
