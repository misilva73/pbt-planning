---
marp: true
title: PBT & Migration overview
author: Maria Silva
footer: PBT & Migration overview · Aug 2026
theme: gaia
---

<!-- _class: lead invert -->

# PBT & Migration

## Design overview & discussion

# 🌳

---

<!-- _class: lead invert -->

# EIP-8297: Partitioned Binary Tree

# 📐

---

<style scoped>
section { font-size: 30px; }
h2 { font-size: 46px; }
img { display: block; margin: 0 auto; max-width: 100%; max-height: 320px; object-fit: contain; }
</style>

## PBT overview

![](https://eips.ethereum.org/assets/eip-8297/diagram.png)

- **Single binary tree** — accounts, storage, code merged, arity 2
- **Zones** — first key byte marks account / code / storage
- **No `storage_root` in leaves** — root recomputes in one parallel pass

---

<style scoped>
section { font-size: 32px; }
h2 { font-size: 44px; }
</style>

## Design decisions worth knowing

- **Code is fully content-addressed** — every chunk lives in `CODE_ZONE`, none in the header; cloned contracts fully dedup
- **Delegation indicators (EIP-7702) stay in the header** — not content-addressed, for deletion locality and dual-check correctness
- **Zero-value write ⇒ deletion** — kept from the MPT, not Verkle's distinct-zero design; root stays a pure function of state
- **Only two node types** (Leaf, Branch) — extension/stem nodes fold into a branch's bit-prefix

---

<style scoped>
section { font-size: 30px; }
h2 { font-size: 46px; }
table { font-size: 30px; }
</style>

## PBT open questions

| Question | Status |
| --- | --- |
| **Hash function** `H` | Likely to be BLAKE3 |
| **State-access gas repricing** | New benchmark-based EIP, values TBD |
| **State expiry & resurrection** | Mechanism deferred to a future EIP |
| **State tiering** (EIP-8188) | Fold into leaf schema or defer? |
| **Account-header sub-index layout** | Study optimal allocation of sub-indices based on access patterns |

---

<!-- _class: lead invert -->

# Migration

## Offline vs. online

# ⚖️

---

<style scoped>
section { font-size: 28px; }
h2 { font-size: 44px; }
table { font-size: 28px; }
</style>

## Online vs. Offline

| | **Online (overlay)** | **Offline (snapshot)** |
| --- | --- | --- |
| Conversion runs | In consensus, per block, ~1 month | Off consensus, snapshot or self-converting, couple hours |
| State during window | One tree, part binary / part MPT | Both trees held side by side |
| Catch-up | Inherent (iterator is the chain) | BAL-replay, no re-execution |
| Disk | ~1 tree | ~2 trees (+≈300 GB) |
| Distribution | Preimages | Snapshot + preimages |

---

<style scoped>
section { font-size: 26px; }
h2 { font-size: 44px; }
</style>

## The call: offline wins

Both paths can be made correct — it's a trade between two sets of costs.

**Offline buys:**

- Smaller consensus change (No conversion cursor lives in the state, and no MPT traversal order becomes consensus-critical)
- No hybrid proof verifiers (good for light clients, on-chain bridge contracts, and consumers of state proofs)
- No in-consensus conversion for zkEVM provers

**Offline pays:**

- More disk (~2×, transiently)
- No on-chain observability of conversion

---

<!-- _class: lead invert -->

# EIP-8347: Offline State Migration to the PBT

# 📦

---

<style scoped>
section { font-size: 29px; }
h2 { font-size: 44px; }
</style>

## Five protocol-lifecycle phases

1. **Conversion** (off-chain) — extract preimages, build the PBT snapshot at `ANCHOR_BLOCK`
2. **Distribution & verification** — publish artifacts, dual-check on ingest
3. **Catch-up** — BAL-replay to tip
4. **Shadow-commitment period** — attesters publish signed shadow roots, MPT still canonical
5. **Swap & transition window** — `PBT_ACTIVATION_FORK` makes PBT canonical; both trees held until finality

#### Two paths for validators: self-migrate (expert) or download snapshot (majority).

---

<style scoped>
section { font-size: 32px; }
h2 { font-size: 44px; }
</style>

## Open questions

- **Testing** — how to test the migration end-to-end, including the off-chain components
- **Snapshot + preimages distribution** — how to coordinate and serve
- **Telemetry spec** — off consessus, but default on CL clients; what to report, how to report it
- **Reorg at the swap boundary** — un-adopting a just-swapped PBT root
- **Syncing during the migration** — is BAL replay enough? Needs benchmarking
- **Post-swap MPT disposal timing** — validators vs. archive/RPC nodes

---

<!-- _class: lead invert -->

# 🌳

## Thank you

### Questions?
