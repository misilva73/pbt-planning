# Open Questions — Trie Design & Migration

A living tracker of the **key unresolved design questions** for the Partitioned Binary
Tree (PBT) and the MPT → PBT migration. This is the single place to look for "what is
still not decided"; the [knowledge base](knowledge-base/README.md) documents what *is*
decided and the [roadmap](roadmap/README.md) says who closes each question and when.

Each item notes where it is tracked or resolved. Fold resolved questions back into the
knowledge base (and delete them here) as they settle. Roadmap deliverables that close a
given parameter are linked inline.

- **Trie:** [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) (Draft; last revised
  2026-08-06).
- **Migration:** the offline MPT→PBT migration EIP, **[EIP-8347](https://eips.ethereum.org/EIPS/eip-8347)**
  (Draft, published; `requires: 7523, 7928, 8159, 8297`; last revised 2026-08-25;
  originated as [PR #12006](https://github.com/ethereum/EIPs/pull/12006)). The migration
  items below are the "**§14 open parameters**" referenced throughout the roadmap
  deliverables.

*Reviewed against the live EIPs and the client implementations on **2026-09-17** (both EIPs
unchanged since 2026-08-25, so no question below was opened or closed by spec movement; the
client picture changed — a fourth implementation and a multi-client migration devnet). Several
items below are no longer purely open questions — a working geth implementation now exists
for the converter, dual-check, BAL-replay and swap, and it answers some of these in code
without them being specified. Where that is the case it is flagged inline; a client's
choice is not a spec.*

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

**Watch for de-facto pinning.** All **four** devnet clients now hardcode or default to BLAKE3
(geth-pbt hardcodes it for key derivation *and* node hashing; `besu-stateless` uses
`Blake3Digest(256)`; Erigon takes `COMMITMENT_BIN_HASH=blake3` as an env var against a
keccak default; Nethermind's `pbt-state`, which joined the devnet on 2026-09-14, builds its
node-grouping layout around a ~60 ns BLAKE3 at 64-byte granularity), and the devnet's genesis
pins roots computed with it. Cross-client root
agreement on that devnet is therefore **not** evidence about `H` — it is evidence about
everything else, measured at one choice of `H`. The risk is that BLAKE3 becomes the answer
by accumulation of pinned fixtures and shipped code rather than by the cryptography
review, which is the same trap [A-S1](roadmap/deliverables/A-S1-eip8297-spec-convergence.md)
already flags for spec convergence.

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
the zone topology (record the subtree hash, prune below it). Note: ordinary
**deletion-time** code refcounting (remove a `CODE_ZONE` leaf only if no live account
shares its `code_hash`) is now specified directly in EIP-8297 — see
[knowledge-base/02-tree-structure.md](knowledge-base/02-tree-structure.md#zero-values-and-deletion).
What remains open here is narrower: whether an **expiry** pass (pruning a still-referenced
but dormant subtree, as opposed to deleting on account/code-hash change) needs its own
refcounting or sweep pass, since expiry and deletion are different triggers over the same
shared leaves; and **resurrection** must re-attach a subtree consistent with the recorded
commitment. The expiry mechanism itself is deferred to a **separate future EIP**.

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

Provenance: several items below were raised in review of EIP-8347 while it was still
[PR #12006](https://github.com/ethereum/EIPs/pull/12006) (@kevaundray) and remain **not**
specified in the now-published EIP. Most are fixed by
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
  raw keys, so the extracted preimage set must be exhaustive. **Specified in the published
  EIP-8347, and revised on 2026-08-20**
  ([PR #12215](https://github.com/ethereum/EIPs/pull/12215)): a concatenation of
  **fixed-width** records `address[20] | slotCount[4, BE] | slotKey[32] * slotCount`
  (full 32-byte slot keys, leading zeros included), ordered by **hashed** key —
  `keccak256(address)` across records, `keccak256(slotKey)` within one — which is exactly
  MPT iteration order, so both consumers stream trie and file as a single sequential merge.
  **This reverses what this file previously recorded:** between 2026-07-30 and 2026-08-20
  the EIP specified RLP `[address, [slotKey…]]` records sorted by raw address, and that was
  noted here as superseding the fixed-width layout. The fixed-width, hashed-order layout is
  the spec now; the snapshot's RLP leaf records are unaffected. Consumed by
  [B-C1](roadmap/deliverables/B-C1-converter-prototype.md) — whose only existing
  implementation (geth's converter) **still emits the old layout**, so this is now a
  drift-closing task rather than an open design question.
- **Snapshot chunk encoding** — the byte-canonical *artifact* serialization is **specified
  in the published EIP-8347**: `pbtRoot[32] | leafCount[8, BE]` followed by `leafCount`
  RLP-encoded `[key, value]` leaf records (key at full zone-determined length, value as a
  canonical RLP integer with leading zeros stripped). What remains open is the **transport
  chunking**: chunk boundaries / sizing trade verification granularity against overhead at
  ~100+ GB scale and are left to the distribution layer. Validated at scale by
  [A-C4](roadmap/deliverables/A-C4-snapshot-serving-verification.md) and
  [B-T3](roadmap/deliverables/B-T3-dual-check-verification-scale.md).
- **Compression** — the RLP leaf record format is somewhat wasteful and should compress
  well. Start with naive compression on transport; a **stem-aware** format (many keys
  share a stem) is a possible later optimization.

### Re-anchor cadence & BAL expiry

BALs expire, so re-anchor snapshots must be **newer than the BAL expiry window** or a late
joiner won't have the BALs needed to replay from the chosen anchor. `REANCHOR_CADENCE`
(`N′`) must be chosen with the BAL expiry period and observed catch-up speed in mind. The
published EIP-8347 fixes **`REANCHOR_CADENCE = 50400` blocks (~1 week)**; the roadmap leaves it generic and
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

A CL-side design discussion (2026-07-27 → 2026-07-29) has since narrowed the carrier
further: it should be a **temporary, publisher-rate-limited global gossip topic** in the
consensus-networking spec, built on clients' existing libp2p/gossipsub stack, deployable
**without a hard fork** and retired at `PBT_ACTIVATION_FORK`. Alternatives were considered and
rejected — many subnets (1k+ subnet concerns), req/resp scraping and ENR advertisement
(node-level, non-exhaustive, don't identify validators), a beacon-state field (modifies
consensus state for temporary bookkeeping), and extending `AttestationData` (no spare field
post-ePBS; broad blast radius on slashing detection, aggregatability and fast-finality work).
Full analysis in
[knowledge-base/11-attester-telemetry-transport.md](knowledge-base/11-attester-telemetry-transport.md).

What genuinely remains:

- **The companion specification** — wire format, aggregation scheme, publication timing, and
  any EL→CL plumbing. Deliberately **out of scope for EIP-8347**. The concept is defined in
  [B-S1](roadmap/deliverables/B-S1-offline-migration-eip.md); the companion spec lands
  alongside [B-S2](roadmap/deliverables/B-S2-readiness-gate-activation-params.md) and is
  first exercised at scale in
  [B-C5](roadmap/deliverables/B-C5-testnet-migrations-shadow-fork.md).
- **Publisher-selection rule and its period `N`** — `validator_index % N == current_epoch % N`
  (stateless, so eligibility is checkable before signature verification) vs committee-gated
  every `N` epochs. `N` fixes how long a full sweep of the validator set takes, so it
  **cannot be chosen independently of the gate's `D` sustained-observation window**.
- **Spam / signature-verification DoS** — the one technical objection left open: a BLS verify
  per unauthenticated message is an amplification target. Mitigations are all
  application-level (cheap eligibility check before signature verification, dedup at one
  message per validator per epoch, per-peer rate limits, de-peer on a single bad signature), but
  they need specifying rather than leaving to clients.
- **Networking-team review** — a global topic with validator-eligibility filtering and a
  novel bandwidth profile may hit implementation-specific limits across Lighthouse, Prysm,
  Teku, Nimbus and Lodestar. An unscheduled dependency for
  [B-O3](roadmap/deliverables/B-O3-shadow-root-ecosystem-readiness.md).
- **The payload must be the root, not a readiness bit** — a bit supports the coverage leg
  only; the cross-client **agreement** leg exists to catch two correct-looking clients
  converging on different trees, which needs the root itself.
- **Default-on delivery** — because publication is an operational commitment rather than a
  protocol requirement, the coverage **Y%** gate (see [Readiness / activation
  thresholds](#readiness--activation-thresholds)) depends on CL client teams shipping the
  sidecar enabled. Track it as a delivery item, not a spec question.

### Reorg behavior around the swap

- **Partially specified.** The published EIP-8347 now gives a general BAL-replay reorg
  rule: rollback is performed by **discarding state, never reversing writes** (BALs
  record post-values only), so a reorged branch's replayed state is simply thrown away
  and replay resumes from the new canonical chain. See
  [knowledge-base/04-migration.md § BAL-replay](knowledge-base/04-migration.md#bal-replay).
- **Still open:** the specific fork-boundary case — what happens if the chain reorgs back
  to an MPT-committed block near `PBT_ACTIVATION_FORK` itself, i.e. across the swap. The
  most consensus-critical point is the block just before the swap, and the general
  discard-and-replay rule above does not by itself say what a client does when the
  canonical PBT root it just adopted needs to be un-adopted.
- **One client has now hit this for real**, which is worth reading as evidence rather than
  as a resolution. geth
  ([PR #33](https://github.com/CPerezz/go-ethereum/pull/33), merged 2026-09-01) found that a
  reorg whose two branches *each* cross activation independently wedged the node for 30
  seconds holding the chain mutex, then failed the import: the engine delivers such a branch
  block by block before the forkchoice switch, so insertion asks the migration follower for
  the shadow root of a block that is not yet canonical, and the height-bounded forward
  replay walk silently replays nothing. Their fix walks back through parent hashes to the
  nearest already-replayed ancestor, replays forward from there, and records roots by hash
  while leaving the canonical cursor untouched; they report a live four-node devnet healing
  a partition that spanned activation with a 41-block rewind across the format swap. That
  this failure mode was found by running the code and not by reading the EIP is the
  argument for specifying the procedure — it is exactly the shape of bug that would be
  correlated across clients if each invents its own answer.
- Behavior under both **short and long reorgs** during the transition window, at that
  specific boundary, must still be defined (recovery to the MPT is asserted, but the
  reorg mechanics there are not).

### Late joiners who can't finish catch-up in time

- A node joining shortly before `PBT_ACTIVATION_FORK` may be unable to verify + BAL-replay to the tip
  before the fork.
- Naive fallback: let such a node snap-sync the PBT directly instead of converting.
- Possible mitigation: run PBT snap-sync "in the shadow" during the shadow period as an
  additional distribution mechanism, so nodes joining near `PBT_ACTIVATION_FORK` see no observable
  difference. Downside: extra bandwidth.

### Failure modes to enumerate

- **Nodes lacking the extra storage.** Retaining both the MPT and the PBT through the
  transition window costs on the order of an extra ~300 GB. Define what a node does if it
  cannot meet that (refuse to enter the window? fall back to snap-syncing the PBT at
  `PBT_ACTIVATION_FORK`?).
- For contrast, the online overlay's analogous failure is nodes that can't keep up writing
  both trees and fall behind — not this design's problem, but worth stating so the
  trade-off is explicit.
- Short and long reorgs (see *Reorg behavior around the swap*).

### Sync-mode behavior across the transition

- Define snap-sync behavior for blocks *before* the transition point — likely only allow
  snap-syncing the PBT from `PBT_ACTIVATION_FORK` onward.
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
