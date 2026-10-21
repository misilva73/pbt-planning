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
- **`S` — PBT activation:** configure a provisional future timestamp before starting migration; confirm readiness before it is reached. Activate only after all clients have caught up and passed migration checks.

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

- **Storage and transfer:** For the PBT artifacts, we estimate 94.2 GB for the PBT snapshot and 61.0 GB for the preimage file. In addition, after the import, nodes will need an additional 450 GB for the PBT trie data.
- **Hardware:** aim for two node types:
  - 8-core, 16 GB RAM, 2 TB disk
  - 8-core, 32 GB RAM, 2 TB disk
- **BALs:** confirm that the normal 18-day retention covers generation, distribution, verification/import, and catch-up from `N + 1`, with margin for retries. Extend retention or preserve BALs separately if measurements show it is insufficient.
- **Window:** at least 2 weeks of BAL replay and maintaining both trees before activation. Generation, transfer, and import time are additional and still TBD.
- **Clients:** Geth, Nethermind, Besu, and Erigon.

## Implementation status

Every receiving client needs snapshot verification/import, BAL replay, and fork activation. Erigon must additionally provide the converter. All teams should still complete converters for separate benchmarks, even though they will not be exercised in the rehearsal. Their availability does not gate participation as a snapshot consumer.

| Client | Converter | Snapshot consumer | BAL replay | Fork activation |
| --- | --- | --- | --- | --- |
| **Geth** | ✅ | ✅ | ✅ | ✅ |
| **Nethermind** | ✅ | ✅ | ✅ | ✅ |
| **Besu** | ✅ | ✅ | ✅ | ✅ |
| **Erigon** | ✅ | ✅ | ✅ | ✅ |
| **Testing** | ✅ | ✅ | ⚠️ | ✅ |

The [pbt-devnet](https://github.com/CPerezz/pbt-devnet) already exercises BAL replay alongside activation, restart, and reorgs. Replay coverage exists but needs strengthening. Converter and snapshot consumer tests are implemented in [Hive](https://github.com/ethereum/hive/pull/1614).

### Client branches

Client branches used by [Hive](https://github.com/ethereum/hive/pull/1614):

- **Geth:** [CPerezz/go-ethereum — pbt](https://github.com/CPerezz/go-ethereum/tree/pbt)
- **Nethermind:** [NethermindEth/nethermind — pbt-state](https://github.com/NethermindEth/nethermind/tree/pbt-state)
- **Besu:** [matkt/besu — glamsterdam-devnet-8-pbt](https://github.com/matkt/besu/tree/glamsterdam-devnet-8-pbt), with [besu-stateless — feat/partitioned-binary-trie](https://github.com/besu-eth/besu-stateless/tree/feat/partitioned-binary-trie)
- **Erigon:** [erigontech/erigon — binary-trie](https://github.com/erigontech/erigon/tree/binary-trie)

### Commands

<details>
<summary><strong>Run the Erigon converter</strong></summary>

On the dedicated source node, stop at `N` and export both shared artifacts:

```sh
STOP_AFTER_BLOCK=<N> erigon <node-options>   # exits after executing N, before committing it
integration stage_exec --datadir=<source-datadir> --chain=<chain> --block=<N> --experimental.commitment-v3
erigon snapshots export-pbt --datadir=<source-datadir> --chain=<chain> \
  --out=<artifact-dir> --experimental.bin-commitment.hash=blake3
```

This writes `pbt-snapshot.bin`, `framed.bin` (preimages), and metadata. The halted node never sees `N` finalize, so the metadata reads `finalized: false`; check the recorded block hash against the finalized chain. [More info on export requirements](https://github.com/erigontech/erigon/blob/06d0833e3d2/docs/pbt-migration.md#export).

</details>

<details>
<summary><strong>Run the snapshot consumer</strong></summary>

**Geth:** two modes, both run inside the node, which keeps following the chain on the MPT throughout. Each takes one restart to add the flags below. [Source](https://github.com/CPerezz/go-ethereum/tree/pbt/cmd/geth): `bintrie_import.go`, `bintrie_selfconvert.go`, flags in [`cmd/utils/flags.go`](https://github.com/CPerezz/go-ethereum/blob/pbt/cmd/utils/flags.go).

First, schedule `S`. Geth refuses both modes unless its chain configuration schedules the binary tree.
- Add `"binaryTrieTime": <S>` (Unix seconds) to the `config` object of the genesis file the node runs with.
- `S` must not be before `amsterdamTime`, so EIP-7928 BALs are active before it.
- Pass the file with `--override.genesis <genesis.json>` on every start, or write it once with `geth --datadir <datadir> init <genesis.json>` while the node is stopped.

*Migration with the PBT snapshot.* Restart with both artifacts and the anchor:

```sh
geth --datadir <datadir> --syncmode=full --override.genesis <genesis-with-S> \
  --pbt.import.snapshot <artifact-dir>/pbt-snapshot.bin \
  --pbt.import.preimages <artifact-dir>/framed.bin \
  --pbt.import.anchor <hash-of-N> \
  <normal node options>
```

| Flag | Value |
| --- | --- |
| `--pbt.import.snapshot` | The PBT snapshot (Erigon's `pbt-snapshot.bin`). |
| `--pbt.import.preimages` | The preimage file (Erigon's `framed.bin`). |
| `--pbt.import.anchor` | `N`, as a block hash (recommended) or number. Geth waits until `N` is canonical and finalized, then checks the artifacts against `N`'s header. It does not need its own MPT state at `N`. |
| `--pbt.import.workers` | Optional, default `4`: parallel workers of the import. |
| `--pbt.import.force` | Only if the datadir already holds a PBT anchored at another block (an earlier import). It replaces that tree. |
| `--pbt.import.keep-artifacts` | Optional: keep the snapshot and the preimage file. By default geth empties each once it has read it. |

The log shows `Starting binary tree import in the background`, then `Import complete` with `binaryRoot` and `anchor`. Meanwhile `debug_migrationProgress` returns `"Phase": "importing"`.

*Self-migration (no PBT snapshot).* Without `--pbt.import.snapshot`, the node converts its own state, using the preimage file for the keys:

```sh
geth --datadir <datadir> --syncmode=full --override.genesis <genesis-with-S> \
  --pbt.import.preimages <artifact-dir>/framed.bin \
  --pbt.import.anchor <hash-of-N> \
  <normal node options>
```

Here `--pbt.import.anchor` is the preimage file's anchor `N`. `--pbt.import.workers` and `--pbt.import.force` work as above.

How it runs:
1. The node waits until `N` is finalized and until it has persisted a complete MPT flat state at some block `P ≥ N`. That needs the path state scheme (the default) and the flat state generated, so it cannot happen during snap sync.
2. It converts the state at `P`. Keys come from the preimage file plus the keys that blocks `N+1..P` wrote, read from their BALs; BALs missing locally are fetched from peers.
3. It attests the tree at `P` once `P` is finalized, and logs `Conversion complete anchor=<P> hash=<hash-of-P> binaryRoot=<root>`.

If traffic is too light for the node's write buffer to fill, `P` can stay behind `N` for a long time; the log then repeats `Binary tree conversion waiting for a complete state at or past its anchor`. `--history.state=<n>` makes geth persist once it trails the head by 128+`n` blocks (the pbt-devnet uses `8`). It also limits the state history geth keeps.

Both modes:
- **Artifacts:** geth empties the preimage file and the snapshot once it has read them, to give their disk space back during the import (a self-migration empties the preimage file after its scan). Pass `--pbt.import.keep-artifacts` to keep them, e.g. to retry without downloading again. A file geth can't write (permissions, a read-only mount) is read and kept.
- **Scratch:** written to `<datadir>/geth/pbt-import`, which must be on disk, not tmpfs. It is compressed, and each file is freed as it is read.
- **Failure:** the node logs `Binary tree import failed`, `debug_migrationProgress` returns `"Phase": "importFailed"` with the error in `Binary.Error`, and everything the run wrote is wiped. The node keeps following on the MPT. Restart with the same flags to retry; a stopped run also starts over. Once a run has started consuming the artifacts, a retry needs fresh copies unless it ran with `--pbt.import.keep-artifacts`: geth refuses consumed files up front and names them.
- **After success:** keep the flags on later restarts, and leave the emptied files where they are: geth checks that the paths exist at startup. Finished work is detected and not repeated.

**Nethermind:** before restarting, update the fork's chainspec with the provisional PBT activation Unix timestamp (`S`, in seconds): use `config.binaryTrieTime` in a Geth-style genesis, or `params.eip8347TransitionTimestamp` in a Nethermind/Parity-style chainspec. The timestamp must be after genesis and the snapshot anchor `N`, and far enough in the future to complete import, catch-up, and the testing window. This selects MPT → PBT migration mode; the PBT flags and artifact paths alone do not select it. EIP-7928 (BALs) and EIP-6780 must activate before `S`. [Mode selection](https://github.com/NethermindEth/nethermind/blob/91ba4d29/src/Nethermind/Nethermind.State.Pbt/PbtPlugin.cs), [migration prerequisites](https://github.com/NethermindEth/nethermind/blob/91ba4d29/src/Nethermind/Nethermind.State.Pbt/PbtMigrationConfigValidator.cs), [Geth-style timestamp mapping](https://github.com/NethermindEth/nethermind/blob/91ba4d29/src/Nethermind/Nethermind.Specs/ChainSpecStyle/GethGenesisLoader.cs).

Restart with that chainspec, the artifact paths, and the anchor. Import runs in the background. [Configuration](https://github.com/NethermindEth/nethermind/blob/91ba4d29/src/Nethermind/Nethermind.State.Pbt/IPbtConfig.cs).

```sh
nethermind --config <node-config> \
  --Init.ChainSpecPath=<updated-chainspec> \
  --Pbt.Enabled=true --FlatDb.Enabled=true --FlatDb.Layout=Flat \
  --Pbt.MigrationSnapshotPath=<snapshot> --Pbt.MigrationPreimagesPath=<preimages> \
  --Pbt.MigrationAnchor=<N> --Sync.FastSync=false
```

Before re-anchoring, stop the node and clear its native PBT database if it was previously seeded from another anchor.

**Besu:** restart with the artifact paths and the hash of `N`. The migrator verifies and loads the snapshot once the anchor is finalized. [Source](https://github.com/matkt/besu/blob/ba419e5/ethereum/core/src/main/java/org/hyperledger/besu/ethereum/trie/pathbased/bonsai/migration/eip8347/README.md#importing-a-snapshot-into-a-node).

```sh
besu --data-path=<datadir> --genesis-file=<genesis> \
  --Xpbt-snapshot-file=<snapshot> --Xpbt-preimages-file=<preimages> \
  --Xpbt-snapshot-anchor-block-hash=<hash-of-N>
```

**Erigon:** verifies the shared snapshot with:

```sh
erigon --datadir <datadir> snapshots verify-pbt \
  --snapshot <snapshot> --preimages <preimages> --block <N> --tmpdir <workdir>
```

It can also import it (`integration commitment import-pbt`, test-only), but in the rehearsal each node runs the v3 hex commitment (`--experimental.commitment-v3`), converts its own state and attaches the result, then maintains both trees until `S`:

```sh
integration commitment convert-pbt --datadir=<stopped-datadir> --chain=<chain> \
  --output.datadir=<converted-dir> --keep-hex --experimental.bin-commitment.hash=blake3
integration commitment attach-pbt --datadir=<datadir> --chain=<chain> \
  --from=<converted-dir> --experimental.bin-commitment.hash=blake3
```

Set `S` only after attach, in the chain configuration or with `--override.binary-trie=<S>` on every start. Before `S`, `debug_migrationProgress` must report `mode: "hex+bin"` and `shadowStopped: false`. [Conversion and attach](https://github.com/erigontech/erigon/blob/06d0833e3d2/docs/pbt-migration.md#conversion-and-publication).

</details>

<details>
<summary><strong>Run BAL replay</strong></summary>

- **Geth:** keep the node from the consumer section running; there is no separate replay command. Once the import or self-migration attests, the [migration follower](https://github.com/CPerezz/go-ethereum/blob/pbt/core/bintrie_follower.go) replays BALs to the head, from `N + 1` after an import and from `P + 1` after a self-migration. `debug_migrationProgress` then returns `"Phase": "running"`, with `Binary.Cursor` and `Binary.ShadowRoot` to compare PBT roots across clients at matching blocks.
- **Nethermind:** keep the consumer command above running. The [BAL follower starts after import](https://github.com/NethermindEth/nethermind/blob/91ba4d29/src/Nethermind/Nethermind.State.Pbt/Steps/InitializePbtMigration.cs); no separate replay command.
- **Besu:** keep the consumer command above running. The migrator catches up from the anchor using trie logs where available, otherwise BALs; no separate replay command.
- **Erigon:** no separate replay command; after attach the node re-executes from the conversion point and maintains both trees.

</details>

<br>

The Nethermind and Besu commands above use the source tested in the October 5 Hive run and the Hive shims. The Erigon commands use `binary-trie` at `06d0833e3d2`. The Geth commands use [`pbt`](https://github.com/CPerezz/go-ethereum/tree/pbt) as of `84a12eff9` (2026-10-20). Notes:

- Replace placeholders with the rehearsal paths and anchor, keeping the node's normal network, Engine API, and peer configuration.
- Configure the same provisional PBT activation timestamp (`S`) across execution clients before starting migration, using each client's supported chain-configuration field (see the Nethermind formats above). Allow for generation, distribution, verification/import, and catch-up, plus at least 2 weeks of BAL replay and maintaining both trees before activation; do not simply set `S` to 2 weeks after `N`. Agree a client-approved procedure to postpone `S` across the network before it is reached if readiness checks or the testing window are incomplete.

### Remaining preparation

- [X] **client teams:** confirm component status and Glamsterdam compatibility, finish missing consumer/replay/activation work, and provide pinned builds, commands, configuration keys, restart requirements, and resource measurements.
- [X] **State team and client teams:** settle and pin the PBT snapshot format and compression.
- [X] **Carlos / State team:** update the PBT devnet Kurtosis package and Hive fixtures to consume generated preimages and PBT snapshots. Run a small populated-state migration covering representative accounts, storage, and delegations through verification/import → BAL replay → activation across clients.
- [X] **Artem / Erigon:** provide sample preimages and a PBT snapshot for cross-client import testing.
- [ ] **Carlos and client teams:** benchmark conversion separately on mainnet-scale state and share timing/resource results with ethpandaops.
- [X] **Maria / ethpandaops:** align on `N`, the dedicated converter, artifact hosting and download procedures, and a coordinated consumer restart plan that preserves network finality.

## Run process

Throughout the run, ethpandaops collects the following metrics:

- **Resource usage:** CPU utilization and load, memory availability and swap usage, filesystem space, disk I/O, and network traffic. This is collected through Prometheus' [node_exporter](https://github.com/prometheus/node_exporter).
- **Time per phase:** generation, upload, download, verification, import, and BAL replay, measured separately.
- **Live network performance:** block-processing latency, head lag, and validator participation, especially during concurrent snapshot verification/import.

| Step | Actions | Ready to continue when |
| --- | --- | --- |
| **1. Prepare** | Client teams supply qualified builds. ethpandaops confirms storage and upgrades execution nodes after Glamsterdam testing. | The network finalizes normally after the upgrade. |
| **2. Capture `N`** | State team picks the anchor. ethpandaops preserves the Erigon source state and each consumer's MPT state needed to verify at `N`, and retains BALs from `N + 1`. | `N` is finalized; its hash and MPT root are recorded; generator and consumer anchor-state access is verified. |
| **3. Generate and distribute** | On the dedicated Erigon node, export preimages and generate one PBT snapshot at `N`. Distribute both artifacts across all devnet nodes. | The matching artifact pair is available to all nodes. |
| **4. Verify and import** | ethpandaops configures the same provisional future `S` across execution clients before starting migration. Each client verifies the shared artifacts against its MPT state at `N` and constructs its local PBT database while continuing live block processing. | Every node passes verification and imports the same PBT root at `N`. Network finality and live block processing remain healthy within agreed limits. |
| **5. BAL replay** | Nodes run BAL replay from `N + 1` while running normal block processing. PBT roots are recorded. | All clients reach the live head and agree on PBT roots at matching blocks. |
| **6. Activate `S`** | Before the configured `S` is reached, State team confirms migration checks and the testing window are complete. If needed, ethpandaops postpones `S` across execution clients using the agreed procedure before the existing timestamp is reached. | The network finalizes after `S` with all clients agreeing on head and PBT root. |
| **7. Capture client databases** | ethpandaops takes a snapshot of each client's native PBT database for later benchmarking. These are the client-specific database backups, distinct from the shared PBT snapshot used for migration. | A database backup for every client is retained. |

For Glamsterdam testing, ethpandaops plans to deploy the state needed for stateful benchmarks. The client-specific PBT database backups from step 7 should therefore be sufficient to run the same benchmarks on PBT and compare with MPT, without the need for custom spammers during step 5.
