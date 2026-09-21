# PBT migration rehearsal on a Glamsterdam mainnet fork

| | |
| --- | --- |
| **Status** | Draft for coordination; devnet status checked 2026-09-18 |
| **Network** | Retained ethpandaops Glamsterdam mainnet fork (exact network TBD) |
| **Window** | After Glamsterdam testing and before the fork is decommissioned |
| **Goal** | Prove an end-to-end, multi-client MPT → PBT migration on mainnet-scale state |
| **Specs** | [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297), [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347), [EIP-7928](https://eips.ethereum.org/EIPS/eip-7928), [EIP-8159](https://eips.ethereum.org/EIPS/eip-8159) |

## Approach

Reuse the fork after Glamsterdam testing. Upgrade execution clients, then schedule two points:

- **`N` — snapshot anchor:** preserve the state at this block and wait for finality before conversion.
- **`S` — PBT activation:** schedule only after all clients have caught up and passed migration checks.

Leave both unset during Glamsterdam testing. Keep the network running with empty or low-traffic blocks while nodes convert locally using the same Erigon preimages. Then replay block-level access lists (BALs) to catch up and test both trees under load before activating PBT.

Consensus clients and validator assignments are expected to stay unchanged.

## Roles

| Entity | Responsibility |
| --- | --- |
| **ethpandaops** | Run and size the network, deploy builds/configuration, take snapshots, distribute preimages, retain BALs, and collect metrics. |
| **State team** | Provide the specs and tests, coordinate `N` and `S`, compare results, and decide whether each step passes. |
| **client teams** | Implement migration, provide builds and commands and measure resource needs.. |

## Planning assumptions

- **Storage:** about 300 GB for the snapshot plus 90 GB for preimages, or roughly 400 GB extra. Client teams must measure peak usage, including databases and temporary files, before ethpandaops sizes disks.
- **Hardware:** aim for the discussed 8-core, 32 GB RAM baseline.
- **BALs:** the normal 18-day retention should cover a run lasting a few days.
- **Window:** still TBD, as we need to measure self-conversion time.
- **Clients:** Geth, Nethermind, Besu, and Erigon.

## Implementation status

Baseline from 18 September; every participant needs all four components.

| Client | Converter | Snapshot consumer | BAL replay | Fork activation |
| --- | --- | --- | --- | --- |
| **Geth** | ✅ | ✅ | ✅ | ✅ |
| **Nethermind** | ✅ | ✅ | ✅ | ✅ |
| **Besu** | ❌ | ❌ | ❌ | ✅ |
| **Erigon** | ❌ | ❌ | ❌ | ✅ |
| **Testing** | ❌ | ❌ | ❌ | ✅ |

The [devnet](https://github.com/CPerezz/pbt-devnet) already covers activation, restart, and reorgs. Add converter, import, and common BAL-replay tests, including corrupt inputs, missing preimages, and wrong anchors.

### Remaining preparation

- **client teams:** finish missing components and provide pinned builds, commands, configuration keys, and resource measurements.
- **State team:** share the snapshot format and pinned spec revisions. Run a populated-state devnet test with client teams covering conversion → cross-import → BAL replay → activation.
- **ethpandaops:** confirm live Snapshotter deployment and preimage distribution. Use a merged version of [Snapshotter PR #41](https://github.com/ethpandaops/snapshotter/pull/41) or pin its branch/image.

## Run process

State team records the result of each step before ethpandaops proceeds.

| Step | Actions | Ready to continue when |
| --- | --- | --- |
| **1. Prepare** | Client teams supply qualified builds. ethpandaops confirms storage and upgrades execution nodes after Glamsterdam testing. | The network finalizes normally after the upgrade. |
| **2. Capture `N`** | State team coordinates the future cutoff. ethpandaops preserves each client's state at `N`, exports and distributes Erigon preimages, and retains BALs from `N + 1`. | `N` is finalized; its hash and MPT root are recorded; source databases and complete preimages are verified. |
| **3. Convert** | ethpandaops runs local conversion alongside the live network using client-team commands and  validates snapshots and report timing and resource usage. | All clients produce the same PBT root. |
| **4. BAL replay** | ethpandaops runs BAL replay and verifies both PBT and source MPT roots. | All clients reach the live head and agree on PBT roots at matching blocks. |
| **5. Test both trees** | ethpandaops runs transaction load while nodes mantain both tries. | Nodes remain at head, and agree on roots within the agreed resource limits. |
| **6. Activate `S`** | State team coordinates a future `S`. ethpandaops applies the configuration. | The network finalizes after `S` with all clients agreeing on head and PBT root. |

## When to stop

Do not activate if roots or configuration disagree, preimages or BALs are missing, import/recovery checks fail, a client cannot catch up, or disk space falls below the agreed margin.

ethpandaops pauses the next step, client teams investigate, and State team decides what must be rerun. If `S` is already scheduled, use the agreed deferral procedure. After activation, preserve evidence and follow the agreed recovery procedure.

## Confirm before the run

- **ethpandaops:**  BAL retention, snapshot deployment, artifact/log locations, and deferral/recovery procedure.
- **State team:** pinned specs and tests, network window, node sizing, and consensus-layer compatibility.
- **client teams:** final builds, operating commands, configuration behavior, and peak resource requirements.
