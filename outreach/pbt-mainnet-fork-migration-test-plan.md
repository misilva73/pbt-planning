# PBT migration rehearsal on a Glamsterdam mainnet fork

| | |
| --- | --- |
| **Status** | Draft for coordination; revised on 2026-09-30 following the September 28 sync |
| **Network** | Retained ethpandaops Glamsterdam mainnet fork (exact network TBD) |
| **Window** | After Glamsterdam testing and before the fork is decommissioned |
| **Goal** | Prove an end-to-end, multi-client MPT → PBT migration on mainnet-scale state |
| **Specs** | [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297), [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347), [EIP-7928](https://eips.ethereum.org/EIPS/eip-7928), [EIP-8159](https://eips.ethereum.org/EIPS/eip-8159) |

## Approach

Reuse the fork after Glamsterdam testing. Upgrade execution clients, then schedule two points:

- **`N` — snapshot anchor:** preserve the state at this block and wait for finality before conversion.
- **`S` — PBT activation:** schedule only after all clients have caught up and passed migration checks.

Leave both unset during Glamsterdam testing. One dedicated Erigon node exports the preimages and generates a PBT snapshot from the finalized state at `N`. ethpandaops distributes both artifacts to the remaining nodes. Each receiving node verifies the artifacts against its preserved MPT state at `N`, imports the PBT snapshot, and replays block-level access lists (BALs) from `N + 1` to catch up. Test both trees under load before activating PBT.

The converter that calculates the PBT snapshot at `N` can work offline and be retired once its artifacts are validated and retained. It can also be "beefier" to speed up the process. Receiving nodes should continue processing live MPT blocks during snapshot verification and PBT import. A brief restart to supply artifact paths may be required.

Consensus clients and validator assignments are expected to stay unchanged.

## Roles

| Entity | Responsibility |
| --- | --- |
| **ethpandaops** | Run and size the network, deploy builds/configuration, operate the Erigon generator, distribute preimages and the PBT snapshot, retain BALs, and collect metrics. |
| **State team** | Provide the specs and tests, coordinate `N` and `S`, compare results, and decide whether each step passes. |
| **client teams** | Implement snapshot verification/import, BAL replay, and activation. Provide builds and commands, and measure resource needs. |

## Planning assumptions

- **Storage and transfer:** current estimate is about 450 GB for the snapshot plus 40–50 GB for preimages. We will re-measure for the agreed PBT snapshot format and compression. ethpandaops must size storage and artifact distribution using those measurements.
- **Hardware:** aim for two node types:
  - 8-core, 16 GB RAM
  - 8-core, 32 GB RAM
- **BALs:** confirm that the normal 18-day retention covers generation, distribution, verification/import, and catch-up from `N + 1`, with margin for retries. Extend retention or preserve BALs separately if measurements show it is insufficient.
- **Window:** at least 2 weeks of BAL replay and maintaining both trees before activation. Generation, transfer, and import time are additional and still TBD.
- **Clients:** Geth, Nethermind, Besu, and Erigon.

## Implementation status

Every receiving client needs snapshot verification/import, BAL replay, and fork activation. Erigon must additionally provide the converter. All teams should still complete converters for separate benchmarks, even though they will not be exercised in the rehearsal. Their availability does not gate participation as a snapshot consumer.

| Client | Converter | Snapshot consumer | BAL replay | Fork activation |
| --- | --- | --- | --- | --- |
| **Geth** | ✅ | ✅ | ✅ | ✅ |
| **Nethermind** | ⚠️ | ⚠️ | ✅ | ✅ |
| **Besu** | ❌ | ❌ | ✅ | ✅ |
| **Erigon** | ❌ | ❌ | ✅ | ✅ |
| **Testing** | ✅ | ✅ | ⚠️ | ✅ |

The [pbt-devnet](https://github.com/CPerezz/pbt-devnet) already exercises BAL replay alongside activation, restart, and reorgs. Replay coverage exists but needs strengthening. We are adding the converter and snapshot consumer tests in [Hive](https://github.com/ethereum/hive/pull/1614).

### Remaining preparation

- **client teams:** confirm component status and Glamsterdam compatibility, finish missing consumer/replay/activation work, and provide pinned builds, commands, configuration keys, restart requirements, and resource measurements.
- **State team and client teams:** settle and pin the PBT snapshot format and compression.
- **Carlos / State team:** update the PBT devnet Kurtosis package and Hive fixtures to consume generated preimages and PBT snapshots. Run a small populated-state migration covering representative accounts, storage, and delegations through verification/import → BAL replay → activation across clients.
- **Artem / Erigon:** provide sample preimages and a PBT snapshot for cross-client import testing.
- **Carlos and client teams:** benchmark conversion separately on mainnet-scale state and share timing/resource results with ethpandaops.
- **Maria / ethpandaops:** align on `N`, the dedicated converter, artifact hosting and download procedures, and a coordinated consumer restart plan that preserves network finality. Confirm live Snapshotter deployment (use a merged version of [Snapshotter PR #41](https://github.com/ethpandaops/snapshotter/pull/41) or pin its branch/image).

## Run process

Throughout the run, ethpandaops collects Grafana/Prometheus data, client logs, `/proc` metrics, and other available host/hardware telemetry to track:

- **Resource usage:** CPU load, memory pressure, disk space and I/O, and network usage.
- **Time per phase:** generation, upload, download, verification, import, and BAL replay, measured separately.
- **Live network performance:** block-processing latency, head lag, and validator participation, especially during concurrent snapshot verification/import.

| Step | Actions | Ready to continue when |
| --- | --- | --- |
| **1. Prepare** | Client teams supply qualified builds. ethpandaops confirms storage and upgrades execution nodes after Glamsterdam testing. | The network finalizes normally after the upgrade. |
| **2. Capture `N`** | State team picks the anchor. ethpandaops preserves the Erigon source state and each consumer's MPT state needed to verify at `N`, and retains BALs from `N + 1`. | `N` is finalized; its hash and MPT root are recorded; generator and consumer anchor-state access is verified. |
| **3. Generate and distribute** | On the dedicated Erigon node, export preimages and generate one PBT snapshot at `N`. Distribute both artifacts across all devnet nodes. | The matching artifact pair is available to all nodes. |
| **4. Verify and import** | Each client verifies the shared artifacts against its MPT state at `N` and constructs its local PBT database while continuing live block processing. | Every node passes verification and imports the same PBT root at `N`. Network finality and live block processing remain healthy within agreed limits. |
| **5. BAL replay** | Nodes run BAL replay from `N + 1` while running normal block processing. PBT roots are recorded. | All clients reach the live head and agree on PBT roots at matching blocks. |
| **6. Activate `S`** | State team coordinates a future `S`. ethpandaops applies the configuration. | The network finalizes after `S` with all clients agreeing on head and PBT root. |
| **7. Capture client databases** | ethpandaops takes a snapshot of each client's native PBT database for later benchmarking. These are the client-specific database backups, distinct from the shared PBT snapshot used for migration. | A database backup for every client is retained. |

For Glamsterdam testing, ethpandaops plans to deploy the state needed for stateful benchmarks. The client-specific PBT database backups from step 7 should therefore be sufficient to run the same benchmarks on PBT and compare with MPT, without the need for custom spammers during step 5.
