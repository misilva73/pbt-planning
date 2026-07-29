# Open Questions — Trie Design & Migration

A living tracker of the **key unresolved design questions** for the Partitioned Binary
Tree (PBT) and the MPT → PBT migration. This is the single place to look for "what is
still not decided"; the [knowledge base](knowledge-base/README.md) documents what *is*
decided and the [roadmap](roadmap/README.md) says who closes each question and when.

Each item notes where it is tracked or resolved. Fold resolved questions back into the
knowledge base (and delete them here) as they settle. Roadmap deliverables that close a
given parameter are linked inline.

- **Trie:** [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) (Draft).
- **Migration:** the offline MPT→PBT migration EIP, **EIP-8347**
  ([PR #12006](https://github.com/ethereum/EIPs/pull/12006)). The migration items below
  are the "**§14 open parameters**" referenced throughout the roadmap deliverables.

Background and the settled security analysis (collision resistance, grinding, preimage
injectivity) live in
[knowledge-base/06-open-questions.md](knowledge-base/06-open-questions.md), along with
the older, superseded questions kept for historical context.

---

## Trie design (EIP-8297)

### Hash function selection — *the dominant open parameter*

The choice of `H` (used for both merkelization and `key_hash`) is treated as an external
dependency, **planned to complete by end of 2026**, and is no longer a scheduled roadmap
deliverable. Candidates:

- **BLAKE3** — good native performance, reasonable in-circuit, well-studied, used in the
  reference implementation.
- **Poseidon2** — SNARK-friendly; needs extra spec for field encoding; under EF
  cryptography-initiative review.
- **Keccak** — native ubiquity, weaker in-circuit.

The spec-freeze ([A-S3](roadmap/deliverables/A-S3-eip8297-spec-freeze.md)) and all
root-bearing test vectors consume the decided `H`; fixtures stay hash-parameterized until
it resolves.

### State-access gas repricing

PBT changes the real cost of touching state, so gas must be repriced for it. The repricing
is a **new benchmark-based EIP** with two components: a repricing of state-access opcodes
(cold/warm account and storage access, storage writes, code-metadata reads), in the spirit
of EIP-8038, and chunk-based code access (EIP-2926). **Values not yet fixed** — they are
derived from measured PBT read/write performance. Fixed by
[A-S2](roadmap/deliverables/A-S2-gas-cost-recalibration.md) using
[A-T4](roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md) benchmark data;
deliberately decoupled from the spec-freeze and previewed for a later gas-focused fork. The
PBT gas model is documented in
[knowledge-base/08-gas-and-access-events.md](knowledge-base/08-gas-and-access-events.md).

### State expiry & resurrection

Per-account (header stem) and per-bucket (`key_hash(address)` bucket) expiry is natural on
the zone topology (record the subtree hash, prune below it). Open issues:
content-addressed **code needs reference counting** (shared leaves) or deferral to a state
sweep; **resurrection** must re-attach a subtree consistent with the recorded commitment.
Mechanism deferred to a **separate future EIP**.

### State tiering (EIP-8188)

Whether to fold [EIP-8188](https://eips.ethereum.org/EIPS/eip-8188) (*Last-Written Block
for Accounts and Slots*) into the PBT leaf schema. EIP-8188 adds a `last_written_block`
field to accounts (+5 bytes) and storage slots (+6 bytes), letting clients partition state
into a **mutable tier** (recently written, tuned for write throughput) and a **stable
tier** (write-inactive, tuned for density and read throughput). It leaves tree topology
untouched but changes leaf encoding, and therefore merkelization and the state root — so
it must be decided *at the leaf-format level*, alongside the leaf record format that also
drives [compression](#artifact-formats--compression). Only writes update the field; reads
do not; no gas changes beyond bumping state-creation pricing for the extra bytes. Open:
do we bake the field into the PBT leaf now, defer it to a separate future EIP, or reject it
(the tiering signal partly overlaps the recency information [state expiry &
resurrection](#state-expiry--resurrection) already needs). Decision affects
root-bearing test vectors, so it should land before the spec-freeze
([A-S3](roadmap/deliverables/A-S3-eip8297-spec-freeze.md)).

### Multi-proof compression

Compact proof formats that exploit shared branches when proving both an account header and
its storage in the same proof.

### Reserved zones `0x02–0xFE`

Future categories (e.g. nullifiers) must stay mutually prefix-free with the existing
account-header / code / storage zones.

---

## Migration (EIP-8347, offline MPT→PBT — the §14 open parameters)

Provenance: several items below were raised in review of
[PR #12006](https://github.com/ethereum/EIPs/pull/12006) (@kevaundray) and are **not** yet
specified in the EIP. Most are fixed by
[B-S1](roadmap/deliverables/B-S1-offline-migration-eip.md) (the EIP itself) and
[B-S2](roadmap/deliverables/B-S2-readiness-gate-activation-params.md) (activation
parameters).

### Readiness / activation thresholds

Cross-client agreement **X%**, coverage **Y%**, sustained **D** days — all placeholders.
Fixed by [B-S2](roadmap/deliverables/B-S2-readiness-gate-activation-params.md) with
rationale tied to rehearsal data; the readiness signal is backstopped by conformance
vectors ([A-T3](roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md)) so a
correlated all-client bug can't pass agreement undetected.

### Artifact formats & compression

- **Preimage file byte-level format** — the MPT is hash-keyed and can't be walked back to
  raw keys, so the extracted preimage set must be exhaustive. **Now specified in the
  EIP-8347 draft** ([PR #12006](https://github.com/ethereum/EIPs/pull/12006)): per-account
  records `address[20] | slotCount[4, BE] | slotKey[32] * slotCount`, sorted
  byte-lexicographically by address then slot key. Pending review; consumed by
  [B-C1](roadmap/deliverables/B-C1-converter-prototype.md).
- **Snapshot chunk encoding** — the byte-canonical *artifact* serialization is **now
  specified in the EIP-8347 draft** (`pbtRoot[32] | leafCount[8, BE] | leafRecord*`, leaf
  records self-delimited by a zone byte). What remains open is the **transport chunking**:
  chunk boundaries / sizing trade verification granularity against overhead at ~100+ GB
  scale and are left to the distribution layer. Validated at scale by
  [A-C4](roadmap/deliverables/A-C4-snapshot-serving-verification.md) and
  [B-T3](roadmap/deliverables/B-T3-dual-check-verification-scale.md).
- **Compression** — the leaf record format is somewhat wasteful and should compress well.
  Start with naive compression on transport; a **stem-aware** format (many keys share a
  stem) is a possible later optimization.

### Re-anchor cadence & BAL expiry

BALs expire, so re-anchor snapshots must be **newer than the BAL expiry window** or a late
joiner won't have the BALs needed to replay from the chosen anchor. `REANCHOR_CADENCE`
(`N′`) must be chosen with the BAL expiry period and observed catch-up speed in mind. The
EIP-8347 draft ([PR #12006](https://github.com/ethereum/EIPs/pull/12006)) currently
proposes **`REANCHOR_CADENCE = 50400` blocks (~1 week)**; the roadmap leaves it generic and
targets a longer per-node dual-state window, so the two must be reconciled (see
[knowledge-base/04-migration.md](knowledge-base/04-migration.md#source-discrepancies-to-reconcile),
D1).
Possible optimization: **merge consecutive BALs** (collapse slot `1→2→3` into `1→3`) to
cut redundant IO during replay, and likely avoid recomputing the state root on every block
insertion into the PBT. `N′` fixed by
[B-S2](roadmap/deliverables/B-S2-readiness-gate-activation-params.md).

### Shadow-root publication — the companion specification

The **carrier architecture is settled** and agreed across the roadmap, EIP-8347 and the
knowledge base: shadow roots travel on an **out-of-consensus telemetry sidecar** —
attesters compute the PBT root of each block's post-state and publish it **signed with their
validator key**. It is never a block-validity condition; a missing or late root counts
against a **coverage** metric, not as a divergence. The sidecar is **expected to ship
enabled by default in CL clients**, so coverage comes from ordinary validator operation
rather than an opt-in program. Documented in
[knowledge-base/04-migration.md](knowledge-base/04-migration.md#shadow-commitment--observability).

Two earlier questions here are **closed** by that decision and have been removed: *builder
identification* — attesters are identified by the validator registry and their reports are
signed, so there is no builder-identity problem and **no ePBS dependency** for
observability; and *widening observability to attesters* — that is now the adopted design,
not a proposal.

What genuinely remains:

- **The companion specification** — wire format, aggregation scheme, publication timing, and
  any EL→CL plumbing. Deliberately **out of scope for EIP-8347**. The concept is defined in
  [B-S1](roadmap/deliverables/B-S1-offline-migration-eip.md); the companion spec lands
  alongside [B-S2](roadmap/deliverables/B-S2-readiness-gate-activation-params.md) and is
  first exercised at scale in
  [B-C5](roadmap/deliverables/B-C5-testnet-migrations-shadow-fork.md).
- **Default-on delivery** — because publication is an operational commitment rather than a
  protocol requirement, the coverage **Y%** gate (see [Readiness / activation
  thresholds](#readiness--activation-thresholds)) depends on CL client teams shipping the
  sidecar enabled. Track it as a delivery item, not a spec question.

### Reorg behavior around the swap

- What happens if the chain reorgs back to an MPT-committed block near `SWAP_FORK`? The
  most consensus-critical point is the block just before the swap.
- Behavior under both **short and long reorgs** during the transition window must be
  defined (recovery to the MPT is asserted, but the reorg mechanics are not).

### Late joiners who can't finish catch-up in time

- A node joining shortly before `SWAP_FORK` may be unable to verify + BAL-replay to the tip
  before the fork.
- Naive fallback: let such a node snap-sync the PBT directly instead of converting.
- Possible mitigation: run PBT snap-sync "in the shadow" during the shadow period as an
  additional distribution mechanism, so nodes joining near `SWAP_FORK` see no observable
  difference. Downside: extra bandwidth.

### Failure modes to enumerate

- **Nodes lacking the extra storage.** Retaining both the MPT and the PBT through the
  transition window costs on the order of an extra ~300 GB. Define what a node does if it
  cannot meet that (refuse to enter the window? fall back to snap-syncing the PBT at
  `SWAP_FORK`?).
- For contrast, the online overlay's analogous failure is nodes that can't keep up writing
  both trees and fall behind — not this design's problem, but worth stating so the
  trade-off is explicit.
- Short and long reorgs (see *Reorg behavior around the swap*).

### Sync-mode behavior across the transition

- Define snap-sync behavior for blocks *before* the transition point — likely only allow
  snap-syncing the PBT from `SWAP_FORK` onward.
- Define checkpoint-sync behavior from a block before the transition point.
- **Post-swap MPT disposal timing** — only validators can dispose of the MPT after
  finality; RPC and archive nodes may retain it well past finality. Dispose too early and
  reorg recovery / late joiners break; too late and the storage cost lingers. Sunset
  schedule fixed by
  [B-S2](roadmap/deliverables/B-S2-readiness-gate-activation-params.md); operator-facing
  comms in [B-O4](roadmap/deliverables/B-O4-activation-comms.md).

### Proof-consumer dependencies

Downstream consumers that must migrate with the tree: verification precompiles,
`eth_getProof` successors, and other proof formats. Coordinated in
[B-O1](roadmap/deliverables/B-O1-proof-consumer-coordination.md).
