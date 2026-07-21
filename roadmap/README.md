<!--
  PBT ROADMAP — rendered best in the VS Code Markdown preview (Cmd+Shift+V),
  which honours the inline colour styles on the Gantt bars. On GitHub the colours
  are stripped by the HTML sanitizer, but the bars, spans and links still render.
  Every coloured bar is a link to that deliverable's detail page under ./deliverables/.
-->

# PBT Roadmap — Trie Design & Migration (2026-07 → 2028-08)

A month-by-month plan to ship **PBT (Partitioned Binary Tree, [EIP-8297](https://github.com/ethereum/EIPs/pull/11978))**
as Ethereum's canonical state commitment, and to **migrate mainnet state from the MPT to PBT**.

For the *what* and *why* of PBT itself, start at the [knowledge base](../knowledge-base/README.md).
This document is the *when* and *who*.

---

## The two forks (anchors)

| Fork | Date (assumed) | What it carries |
|------|----------------|-----------------|
| **H\*** | **Summer 2027** (≈ 2027-06) | **EIP-8297 spec frozen**; **shadow-commitment period opens** (builders publish per-block PBT roots while consensus stays on the MPT). PBT is *implemented and observable* but **not yet canonical**. |
| **I\*** | **Summer 2028** (≈ 2028-06) | **Fork `S` — the swap.** PBT becomes the canonical state commitment. MPT retained until finality, then sunset. |

> PBT-native gas improvements (chunk-granular code access, stem warm/cold semantics) are
> **deliberately decoupled** from the swap and previewed for a *later* fork — they are not on
> the critical path to I\* and are out of scope for this roadmap.
>
> Protocol prerequisites — **BAL (EIP-7928)** and the **64 KiB code-size limit (EIP-7954)** —
> ship in **Glamsterdam (≈ 2026-09)**, before this roadmap's window, so they are treated as
> **already available** and are out of scope here. BAL-replay ([B-S3](deliverables/B-S3-bal-replay-spec.md) /
> [B-C2](deliverables/B-C2-bal-replay-engine.md)) simply consumes the shipped BAL format.

---

## Two threads, four workstreams

The plan is organised as **two parallel threads**, each cut across the same **four workstreams**.
Colour = workstream throughout the Gantt below.

| Thread | Focus |
|--------|-------|
| **A · Trie Design** | The tree itself ([EIP-8297](../knowledge-base/02-tree-structure.md)): spec finalisation, hash-function choice, gas recalibration, client tree implementations, conformance tests, devnets. Must be *frozen & implemented* by **H\***. |
| **B · Migration** | The MPT→PBT offline conversion ([roadmap doc](../knowledge-base/04-migration.md), EIP-7748 adapted): converter, BAL-replay, snapshot distribution, dual-check verification, rehearsals, mainnet window. Culminates in the swap at **I\***. |

| Workstream | Colour | Meaning |
|------------|:------:|---------|
| **Specs** | 🟪 purple | EIPs, formal parameters, spec text |
| **Tests** | 🟦 cyan | EEST ports, test vectors, conformance, verification harnesses |
| **Client impl.** | 🟩 green | EL/CL client code: tree, converter, sync, snapshot, replay |
| **Ecosystem outreach** | 🟧 orange | Proof consumers, builders/relays, activation comms |

Each thread tracks the migration's **6 phases** ([04-migration.md](../knowledge-base/04-migration.md#six-phase-timeline)):
Phase 0 Spec Convergence · 1 Prototypes & Evidence · 2 Devnets · 3 Migration Machinery ·
4 Rehearsals · 5 Mainnet Window · 6 Swap & Aftermath.

---

## Gantt

**How to read it:** rows are deliverables (grouped by thread → workstream); columns are months.
Each coloured bar spans the delivery window and **links to a detail page**. `◆` marks a fork.

<table>
<thead>
<tr>
  <th rowspan="2" align="left">Deliverable</th>
  <th colspan="6">2026</th>
  <th colspan="12">2027</th>
  <th colspan="8">2028</th>
</tr>
<tr>
  <th>07</th><th>08</th><th>09</th><th>10</th><th>11</th><th>12</th>
  <th>01</th><th>02</th><th>03</th><th>04</th><th>05</th><th>06</th><th>07</th><th>08</th><th>09</th><th>10</th><th>11</th><th>12</th>
  <th>01</th><th>02</th><th>03</th><th>04</th><th>05</th><th>06</th><th>07</th><th>08</th>
</tr>
</thead>
<tbody>

<tr><td align="left"><b>◆ Forks</b></td>
  <td></td><td></td><td></td><td></td><td></td><td></td>
  <td></td><td></td><td></td><td></td><td></td><td align="center" bgcolor="#fde68a"><b>◆H*</b></td><td></td><td></td><td></td><td></td><td></td><td></td>
  <td></td><td></td><td></td><td></td><td></td><td align="center" bgcolor="#fca5a5"><b>◆I*</b></td><td></td><td></td>
</tr>

<tr><td colspan="27" bgcolor="#f1f5f9"><b>THREAD A · TRIE DESIGN</b></td></tr>

<tr><td align="left"><a href="deliverables/A-S1-eip8297-spec-convergence.md">A-S1 EIP-8297 convergence</a></td>
  <td colspan="5" style="background-color:#ede9fe"><a href="deliverables/A-S1-eip8297-spec-convergence.md">A-S1</a></td>
  <td colspan="21"></td></tr>

<tr><td align="left"><a href="deliverables/A-S2-hash-function-selection.md">A-S2 Hash-function selection</a></td>
  <td colspan="8" style="background-color:#ede9fe"><a href="deliverables/A-S2-hash-function-selection.md">A-S2</a></td>
  <td colspan="18"></td></tr>

<tr><td align="left"><a href="deliverables/A-S3-witness-gas-recalibration.md">A-S3 Witness-gas recalibration</a></td>
  <td colspan="3"></td>
  <td colspan="7" style="background-color:#ede9fe"><a href="deliverables/A-S3-witness-gas-recalibration.md">A-S3</a></td>
  <td colspan="16"></td></tr>

<tr><td align="left"><a href="deliverables/A-S4-eip8297-spec-freeze.md">A-S4 EIP-8297 spec freeze</a></td>
  <td colspan="8"></td>
  <td colspan="4" style="background-color:#ede9fe"><a href="deliverables/A-S4-eip8297-spec-freeze.md">A-S4→H*</a></td>
  <td colspan="14"></td></tr>

<tr><td align="left"><a href="deliverables/A-T1-eest-test-suite-port.md">A-T1 EEST test-suite port</a></td>
  <td colspan="1"></td>
  <td colspan="6" style="background-color:#cffafe"><a href="deliverables/A-T1-eest-test-suite-port.md">A-T1</a></td>
  <td colspan="19"></td></tr>

<tr><td align="left"><a href="deliverables/A-T2-tree-key-derivation-vectors.md">A-T2 Tree/key-derivation vectors</a></td>
  <td colspan="6" style="background-color:#cffafe"><a href="deliverables/A-T2-tree-key-derivation-vectors.md">A-T2</a></td>
  <td colspan="20"></td></tr>

<tr><td align="left"><a href="deliverables/A-T3-pbt-genesis-conformance-sync-tests.md">A-T3 Genesis conformance & sync tests</a></td>
  <td colspan="6"></td>
  <td colspan="6" style="background-color:#cffafe"><a href="deliverables/A-T3-pbt-genesis-conformance-sync-tests.md">A-T3</a></td>
  <td colspan="14"></td></tr>

<tr><td align="left"><a href="deliverables/A-T4-hardware-matrix-benchmarks.md">A-T4 Hardware-matrix benchmarks</a></td>
  <td colspan="12"></td>
  <td colspan="6" style="background-color:#cffafe"><a href="deliverables/A-T4-hardware-matrix-benchmarks.md">A-T4</a></td>
  <td colspan="8"></td></tr>

<tr><td align="left"><a href="deliverables/A-C1-client-tree-implementations.md">A-C1 Client tree implementations</a></td>
  <td colspan="1"></td>
  <td colspan="7" style="background-color:#dcfce7"><a href="deliverables/A-C1-client-tree-implementations.md">A-C1</a></td>
  <td colspan="18"></td></tr>

<tr><td align="left"><a href="deliverables/A-C2-pbt-native-state-sync.md">A-C2 PBT-native state sync</a></td>
  <td colspan="6"></td>
  <td colspan="5" style="background-color:#dcfce7"><a href="deliverables/A-C2-pbt-native-state-sync.md">A-C2</a></td>
  <td colspan="15"></td></tr>

<tr><td align="left"><a href="deliverables/A-C3-multiclient-pbt-genesis-devnets.md">A-C3 Multi-client genesis devnets</a></td>
  <td colspan="7"></td>
  <td colspan="5" style="background-color:#dcfce7"><a href="deliverables/A-C3-multiclient-pbt-genesis-devnets.md">A-C3</a></td>
  <td colspan="14"></td></tr>

<tr><td align="left"><a href="deliverables/A-C4-snapshot-serving-verification.md">A-C4 Snapshot serving & verification</a></td>
  <td colspan="8"></td>
  <td colspan="5" style="background-color:#dcfce7"><a href="deliverables/A-C4-snapshot-serving-verification.md">A-C4</a></td>
  <td colspan="13"></td></tr>

<tr><td align="left"><a href="deliverables/A-O1-tree-spec-socialization.md">A-O1 Tree-spec socialization / ACD</a></td>
  <td colspan="9" style="background-color:#ffedd5"><a href="deliverables/A-O1-tree-spec-socialization.md">A-O1</a></td>
  <td colspan="17"></td></tr>

<tr><td colspan="27" bgcolor="#f1f5f9"><b>THREAD B · MIGRATION</b></td></tr>

<tr><td align="left"><a href="deliverables/B-S1-eip7748-adaptation.md">B-S1 EIP-7748 → PBT adaptation</a></td>
  <td colspan="1"></td>
  <td colspan="7" style="background-color:#ede9fe"><a href="deliverables/B-S1-eip7748-adaptation.md">B-S1</a></td>
  <td colspan="18"></td></tr>

<tr><td align="left"><a href="deliverables/B-S2-preimage-snapshot-manifest-spec.md">B-S2 Preimage & snapshot manifest spec</a></td>
  <td colspan="2"></td>
  <td colspan="5" style="background-color:#ede9fe"><a href="deliverables/B-S2-preimage-snapshot-manifest-spec.md">B-S2</a></td>
  <td colspan="19"></td></tr>

<tr><td align="left"><a href="deliverables/B-S3-bal-replay-spec.md">B-S3 BAL-replay spec</a></td>
  <td colspan="4"></td>
  <td colspan="6" style="background-color:#ede9fe"><a href="deliverables/B-S3-bal-replay-spec.md">B-S3</a></td>
  <td colspan="16"></td></tr>

<tr><td align="left"><a href="deliverables/B-S4-readiness-gate-activation-params.md">B-S4 Readiness gate & activation params</a></td>
  <td colspan="14"></td>
  <td colspan="6" style="background-color:#ede9fe"><a href="deliverables/B-S4-readiness-gate-activation-params.md">B-S4</a></td>
  <td colspan="6"></td></tr>

<tr><td align="left"><a href="deliverables/B-T1-conversion-replay-vectors.md">B-T1 Conversion/replay vectors</a></td>
  <td colspan="2"></td>
  <td colspan="7" style="background-color:#cffafe"><a href="deliverables/B-T1-conversion-replay-vectors.md">B-T1</a></td>
  <td colspan="17"></td></tr>

<tr><td align="left"><a href="deliverables/B-T2-full-cycle-devnet-swap.md">B-T2 Full-cycle devnet w/ swap</a></td>
  <td colspan="8"></td>
  <td colspan="6" style="background-color:#cffafe"><a href="deliverables/B-T2-full-cycle-devnet-swap.md">B-T2</a></td>
  <td colspan="12"></td></tr>

<tr><td align="left"><a href="deliverables/B-T3-dual-check-verification-scale.md">B-T3 Dual-check verification at scale</a></td>
  <td colspan="15"></td>
  <td colspan="7" style="background-color:#cffafe"><a href="deliverables/B-T3-dual-check-verification-scale.md">B-T3</a></td>
  <td colspan="4"></td></tr>

<tr><td align="left"><a href="deliverables/B-C1-converter-prototype.md">B-C1 Converter (prototype)</a></td>
  <td colspan="3"></td>
  <td colspan="6" style="background-color:#dcfce7"><a href="deliverables/B-C1-converter-prototype.md">B-C1</a></td>
  <td colspan="17"></td></tr>

<tr><td align="left"><a href="deliverables/B-C2-bal-replay-engine.md">B-C2 BAL-replay engine</a></td>
  <td colspan="6"></td>
  <td colspan="5" style="background-color:#dcfce7"><a href="deliverables/B-C2-bal-replay-engine.md">B-C2</a></td>
  <td colspan="15"></td></tr>

<tr><td align="left"><a href="deliverables/B-C3-snapshot-production-pipeline.md">B-C3 Snapshot production pipeline</a></td>
  <td colspan="7"></td>
  <td colspan="6" style="background-color:#dcfce7"><a href="deliverables/B-C3-snapshot-production-pipeline.md">B-C3</a></td>
  <td colspan="13"></td></tr>

<tr><td align="left"><a href="deliverables/B-C4-production-rehearsals.md">B-C4 Production rehearsals (mainnet state)</a></td>
  <td colspan="12"></td>
  <td colspan="6" style="background-color:#dcfce7"><a href="deliverables/B-C4-production-rehearsals.md">B-C4</a></td>
  <td colspan="8"></td></tr>

<tr><td align="left"><a href="deliverables/B-C5-testnet-migrations-shadow-fork.md">B-C5 Testnet migrations + shadow fork</a></td>
  <td colspan="13"></td>
  <td colspan="6" style="background-color:#dcfce7"><a href="deliverables/B-C5-testnet-migrations-shadow-fork.md">B-C5</a></td>
  <td colspan="7"></td></tr>

<tr><td align="left"><a href="deliverables/B-C6-mainnet-window.md">B-C6 Mainnet window (block N → replay)</a></td>
  <td colspan="18"></td>
  <td colspan="6" style="background-color:#dcfce7"><a href="deliverables/B-C6-mainnet-window.md">B-C6→I*</a></td>
  <td colspan="2"></td></tr>

<tr><td align="left"><a href="deliverables/B-C7-swap-fork-s-aftermath.md">B-C7 Swap at fork S & aftermath</a></td>
  <td colspan="23"></td>
  <td colspan="3" style="background-color:#dcfce7"><a href="deliverables/B-C7-swap-fork-s-aftermath.md">B-C7</a></td></tr>

<tr><td align="left"><a href="deliverables/B-O1-proof-consumer-coordination.md">B-O1 Proof-consumer coordination</a></td>
  <td colspan="24" style="background-color:#ffedd5"><a href="deliverables/B-O1-proof-consumer-coordination.md">B-O1 — longest lead time</a></td>
  <td colspan="2"></td></tr>

<tr><td align="left"><a href="deliverables/B-O3-shadow-root-ecosystem-readiness.md">B-O3 Shadow roots & ecosystem readiness</a></td>
  <td colspan="12"></td>
  <td colspan="12" style="background-color:#ffedd5"><a href="deliverables/B-O3-shadow-root-ecosystem-readiness.md">B-O3</a></td>
  <td colspan="2"></td></tr>

<tr><td align="left"><a href="deliverables/B-O4-activation-comms.md">B-O4 Activation comms & fork-S coord.</a></td>
  <td colspan="19"></td>
  <td colspan="5" style="background-color:#ffedd5"><a href="deliverables/B-O4-activation-comms.md">B-O4</a></td>
  <td colspan="2"></td></tr>

</tbody>
</table>

**Legend:** 🟪 Specs · 🟦 Tests · 🟩 Client implementation · 🟧 Ecosystem outreach · `◆` fork.

---

## Phase alignment

| Window | Migration phase(s) | Headline outcome |
|--------|--------------------|------------------|
| 2026-07 → 2026-12 | **0 → 1** Spec Convergence, Prototypes & Evidence | EIP-8297 contention resolved; prototype tree + converter; first test vectors; outreach begins. |
| 2027-01 → 2027-06 | **2 → 3** Devnets, Migration Machinery | Multi-client PBT-genesis devnets; converter + BAL-replay + snapshot pipeline; full-cycle devnet swap. **→ H\* freezes the spec & opens shadow period.** |
| 2027-07 → 2027-12 | **4** Rehearsals | Production converter runs on mainnet state; public testnet migrations; mainnet shadow fork; hardware-matrix + perf metrics. |
| 2028-01 → 2028-06 | **5 → 6** Mainnet Window, Swap | Block `N` chosen; snapshot produced, cross-verified, distributed; BAL-replay to tip; readiness gate passed. **→ I\* = fork S, PBT canonical.** |
| 2028-06 → 2028-08 | **6** Aftermath | MPT retained to finality then sunset; snapshot disposed; fresh-node sync restored. |

---

## Critical path (what gates I\*)

```
A-S1 → A-S2/A-S3 → A-S4 (spec frozen @ H*) ──┐
A-C1 → A-C3 (multi-client devnets) ──────────┤→ B-C4 rehearsals → B-C5 shadow fork
B-S1 → B-C1 converter ───────────────────────┤   → B-C6 mainnet window → B-C7 swap @ I*
B-S3 → B-C2 BAL-replay ───────────────────────┘        ▲
B-S4 readiness gate (thresholds X/Y/D) ─────────────────┘
B-O1 proof-consumer upgrades — longest lead, must land before I*
(BAL / EIP-7928 + code-size / EIP-7954 assumed live from Glamsterdam ~2026-09)
```

The two hardest external dependencies: **hash-function selection (A-S2)** blocking every
implementation, and **proof-consumer readiness (B-O1)** — the longest-lead outreach item, started
in month 1 because on-chain systems that read `storage_root`/`eth_getProof` need coordinated upgrades
before the swap.

---

## Index of deliverables

| ID | Deliverable | Thread | Workstream | Window |
|----|-------------|:------:|------------|--------|
| [A-S1](deliverables/A-S1-eip8297-spec-convergence.md) | EIP-8297 spec convergence (PR #11978) | A | Specs | 2026-07 → 2026-11 |
| [A-S2](deliverables/A-S2-hash-function-selection.md) | Hash-function selection | A | Specs | 2026-07 → 2027-02 |
| [A-S3](deliverables/A-S3-witness-gas-recalibration.md) | Witness-gas recalibration | A | Specs | 2026-10 → 2027-04 |
| [A-S4](deliverables/A-S4-eip8297-spec-freeze.md) | EIP-8297 spec freeze for H\* | A | Specs | 2027-03 → 2027-06 |
| [A-T1](deliverables/A-T1-eest-test-suite-port.md) | EEST test-suite port | A | Tests | 2026-08 → 2027-01 |
| [A-T2](deliverables/A-T2-tree-key-derivation-vectors.md) | Tree & key-derivation vectors | A | Tests | 2026-07 → 2026-12 |
| [A-T3](deliverables/A-T3-pbt-genesis-conformance-sync-tests.md) | Genesis conformance & sync tests | A | Tests | 2027-01 → 2027-06 |
| [A-T4](deliverables/A-T4-hardware-matrix-benchmarks.md) | Hardware-matrix benchmarks (EIP-7870) | A | Tests | 2027-07 → 2027-12 |
| [A-C1](deliverables/A-C1-client-tree-implementations.md) | Client tree implementations | A | Clients | 2026-08 → 2027-02 |
| [A-C2](deliverables/A-C2-pbt-native-state-sync.md) | PBT-native state sync | A | Clients | 2027-01 → 2027-05 |
| [A-C3](deliverables/A-C3-multiclient-pbt-genesis-devnets.md) | Multi-client PBT-genesis devnets | A | Clients | 2027-02 → 2027-06 |
| [A-C4](deliverables/A-C4-snapshot-serving-verification.md) | Snapshot serving & verification | A | Clients | 2027-03 → 2027-07 |
| [A-O1](deliverables/A-O1-tree-spec-socialization.md) | Tree-spec socialization / ACD | A | Outreach | 2026-07 → 2027-03 |
| [B-S1](deliverables/B-S1-eip7748-adaptation.md) | EIP-7748 → PBT adaptation | B | Specs | 2026-08 → 2027-02 |
| [B-S2](deliverables/B-S2-preimage-snapshot-manifest-spec.md) | Preimage & snapshot manifest spec | B | Specs | 2026-09 → 2027-01 |
| [B-S3](deliverables/B-S3-bal-replay-spec.md) | BAL-replay spec (on EIP-7928) | B | Specs | 2026-11 → 2027-04 |
| [B-S4](deliverables/B-S4-readiness-gate-activation-params.md) | Readiness gate & activation params | B | Specs | 2027-09 → 2028-02 |
| [B-T1](deliverables/B-T1-conversion-replay-vectors.md) | Conversion/replay vectors | B | Tests | 2026-09 → 2027-03 |
| [B-T2](deliverables/B-T2-full-cycle-devnet-swap.md) | Full-cycle devnet with swap | B | Tests | 2027-03 → 2027-08 |
| [B-T3](deliverables/B-T3-dual-check-verification-scale.md) | Dual-check verification at scale | B | Tests | 2027-10 → 2028-04 |
| [B-C1](deliverables/B-C1-converter-prototype.md) | Converter (prototype) | B | Clients | 2026-10 → 2027-03 |
| [B-C2](deliverables/B-C2-bal-replay-engine.md) | BAL-replay engine | B | Clients | 2027-01 → 2027-05 |
| [B-C3](deliverables/B-C3-snapshot-production-pipeline.md) | Snapshot production pipeline | B | Clients | 2027-02 → 2027-07 |
| [B-C4](deliverables/B-C4-production-rehearsals.md) | Production rehearsals (mainnet state) | B | Clients | 2027-07 → 2027-12 |
| [B-C5](deliverables/B-C5-testnet-migrations-shadow-fork.md) | Testnet migrations + shadow fork | B | Clients | 2027-08 → 2028-01 |
| [B-C6](deliverables/B-C6-mainnet-window.md) | Mainnet window (block N → replay) | B | Clients | 2028-01 → 2028-06 |
| [B-C7](deliverables/B-C7-swap-fork-s-aftermath.md) | Swap at fork S & aftermath | B | Clients | 2028-06 → 2028-08 |
| [B-O1](deliverables/B-O1-proof-consumer-coordination.md) | Proof-consumer coordination | B | Outreach | 2026-07 → 2028-06 |
| [B-O3](deliverables/B-O3-shadow-root-ecosystem-readiness.md) | Shadow roots & ecosystem readiness | B | Outreach | 2027-07 → 2028-06 |
| [B-O4](deliverables/B-O4-activation-comms.md) | Activation comms & fork-S coordination | B | Outreach | 2028-02 → 2028-06 |

---

*Assumptions: H\* summer 2027, I\* summer 2028, monthly granularity. Dates and parameters
(`N`, `S`, readiness thresholds, hash function) are placeholders until fixed by the processes
in the deliverables above. Last updated 2026-07-21.*
