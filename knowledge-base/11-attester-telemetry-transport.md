# 11 — Attester Telemetry During the Transition Period

> **Status: carrier architecture settled, transport design open.** That attesters compute
> the PBT root of each block's post-state and publish it **signed with their validator
> key**, **out of consensus**, is agreed across the roadmap, EIP-8347 and this knowledge
> base ([04-migration.md](04-migration.md#shadow-commitment--observability)). What is *not*
> settled is **how the signed reports travel**. This file records the design space for that
> carrier — the "companion specification" that
> [open-questions.md](../open-questions.md#shadow-root-publication--the-companion-specification)
> tracks and [B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md) points
> at.
>
> Primary input: a CL-side design discussion (**2026-07-27 → 2026-07-29**) between the
> migration lead and the CL specs team, with input from client and consensus-spec reviewers.
> Positions below are attributed by role, not by name.

## The problem being solved

The offline migration's defining property is that the swap is a **discrete event**: at
`PBT_ACTIVATION_FORK` the network stops committing to the MPT root and starts committing to the PBT
root of the same state. The uncomfortable corollary, in the migration lead's framing:

> we "swap roots at height X", but we do not know what the network has as root for the
> upcoming trie.

Every node has independently converted or ingested a snapshot and BAL-replayed to the tip.
Each therefore holds a *private opinion* about the PBT root at the head. Nothing in the
protocol compares those opinions before the fork makes one of them consensus-critical —
this is the **unvalidated flip** weak point
([04-migration.md](04-migration.md#known-weak-points--mitigations)).

The goal of attester telemetry is to make **root agreement observable before it becomes
binding**, so that the network can be seen to be ready — and the activation aborted if it
is not — **without tying fork choice or consensus to the signal**. Concretely it feeds two
of the three readiness-gate legs: cross-client agreement **≥ X%** and coverage **≥ Y%**
sustained **D** days
([B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md)).

### Who must be measured

**Validators, not nodes.** The specs team asked this explicitly and the answer from the
migration side was unambiguous: validators, *"as they are the ones who can fork the chain
and cause real consensus issues"*. This single answer eliminates most of the cheap options
below — anything that samples *nodes* (req/resp scraping, ENR advertisement) can estimate
migration progress but cannot tell you whether the **validating majority** agrees on a
root, which is the only quantity the gate is about.

It also confirms the choice already recorded in
[04-migration.md](04-migration.md#shadow-commitment--observability): sourcing reports from
**attesters** rather than block producers is what makes the measurement cover the
validating set, and validator-key signatures are what make each report attributable
against the registry.

---

## Design space

Six carriers were put on the table. Verdicts are the discussion's, not this file's.

| Carrier | How it would work | Verdict |
|---|---|---|
| **Global gossip topic, unrestricted** | Every validator broadcasts a signed status/root message once per epoch on one new topic | **Rejected on bandwidth** — see [§bandwidth](#the-bandwidth-arithmetic) |
| **Global gossip topic, publisher-restricted** | Same, but only a protocol-selected 1/N of validators is eligible to publish in a given epoch | **Preferred direction** |
| **Many subnets** | Shard the load the way attestation subnets do | Disfavoured — the specs team flagged a **complication with 1k+ subnets** and prefers restriction over sharding; a networking-team question |
| **Req/resp endpoint** | A large crawler node periodically scrapes peers for their migration status | Considered, rejected as the primary signal: **not exhaustive**, and does not identify validators |
| **ENR advertisement** | Nodes advertise status in their ENR | Rejected — same coverage limitation as req/resp, and still node-level not validator-level |
| **New beacon-state field** | Validators record status in consensus state, so no repeated broadcasts | Rejected: *"it would be nice to have, but I wouldn't want to modify the state for this"* — it puts temporary migration bookkeeping into consensus state |
| **Extend `AttestationData`** | Add a root or a ready-bit to the attestation | **Strongly rejected** — see [§attestations](#why-attestations-are-off-the-table) |

The convergence is narrow and worth stating plainly: **a new, temporary, publisher-rate-limited
global gossip topic carrying signed messages, deployable without a hard fork and retired at
the swap.**

### The bandwidth arithmetic

The specs team's own second thought killed the naive version: a global topic with **~800k
messages per epoch is too much**. The arithmetic behind that judgement:

- A minimal message — validator index, epoch, 32-byte root, BLS signature — is on the order
  of **~150 bytes** SSZ.
- ~800k active validators × once per epoch ≈ **120 MB per epoch**, ~25k messages per slot,
  **on one unsharded topic**, before gossipsub's propagation amplification.
- For scale: that is *the entire attestation load* (~800k per epoch) again — except
  attestations are spread across **64 subnets** and aggregated, and this would not be.

So the mechanism cannot ask every validator to speak every epoch. Two selection rules were
proposed:

1. **Index modulus (specs team).** A validator publishes only when
   `validator_index % N == current_epoch % N`. Keeps a single global topic, and makes
   ineligible messages **trivially identifiable as spam**.
2. **Committee-gated (specs team).** A validator publishes only if it is in a beacon
   committee in an eligible epoch, with the period `N` chosen as *"the time it takes to
   complete migration"* — smoothing bandwidth across the whole shadow period.

**Both are the same 1/N sampling with different selection functions**, and the trade-off
between them is validation cost, not bandwidth:

- The modulus rule is **stateless** — any peer can check eligibility from the index and the
  epoch alone, before touching the signature.
- Committee membership requires the epoch's **shuffling**, which nodes have anyway, but
  which is not a constant-time check on the hot path of an unauthenticated message.

*Analysis, not from the discussion:* `N` is not a free parameter — it fixes how long a full
sweep of the validator set takes, and therefore what "coverage over **D** days" can even
mean. At ~225 epochs/day, `N = 4096` sweeps the set in **~18 days**, while `N = 225` sweeps
it **daily** at ~3.5k messages/epoch (~0.5 MB/epoch) — roughly 1/225 of the naive load and
a small fraction of one attestation subnet. **`N` should be derived from the gate's `D`
window, not picked for round-number reasons**, and this is a concrete input
[B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md) needs from the
companion spec.

### Why attestations are off the table

The suggestion — from a client-team reviewer — was appealing: the CL already controls
fields the EL does not, so signal readiness there, and *"I don't think we need the whole
new root hash, just a signal that hey I'm ready for the transition"*. It was rejected on
three independent grounds.

- **There is no spare field.** EIP-7549 obsoleted the attestation `index` field, but ePBS
  has since reused it.
- **Attestation changes are far harder than they look.** The specs team's position, from
  experience the last time attestation structure changed: modifying attestation structures
  *"is more difficult than it sounds"*.
- **The blast radius is wide.** From the consensus-spec side: touching attestations affects
  **slashing detection**, **reduces aggregatability**, and **commits temporary migration
  state on-chain unnecessarily** — and **fast finality will itself be reworking
  attestations**, so any extra dependency there compounds that work.

*One point worth carrying forward independently of the carrier:* the reviewer's
"ready-bit instead of a root" instinct changes **what the gate can measure**. A binary
ready flag supports the **coverage** leg only. The **cross-client agreement** leg needs the
actual root, because its whole purpose is to detect that two correct-looking
implementations converged on *different* trees. The payload must be the root.

---

## Layering: this is an Ethereum protocol, not a libp2p change

A recurring framing question, resolved here so it does not get re-litigated.

Ethereum already defines its own gossip topics, message encodings, validation rules and
propagation behaviour **above** generic libp2p — `beacon_block`,
`beacon_aggregate_and_proof` and the attestation subnets all live at that layer. Shadow-root
telemetry belongs in exactly the same place.

| Layer | Change required |
|---|---|
| **Consensus specs** | Topic name, SSZ message container, signing domain, eligibility rule, publication cadence, message-validation rules |
| **CL clients** | Subscribe, publish, validate, aggregate/report, apply peer-scoring and de-peering rules; the EL→CL plumbing that delivers the computed PBT root to the validator client |
| **libp2p / gossipsub** | **None** — reused unchanged for transport, peer management and dissemination |

A libp2p-level change would only be needed if the design required something gossipsub
cannot express — for example, enforcing *at the protocol level* that only validators
eligible this epoch may publish. It does not: eligibility is naturally enforced by the
**application-level message validator**. Peers receive the message, check index/epoch/root
and signature, and reject it if ineligible. Gossipsub is explicitly designed as a generic
pub/sub substrate on which applications define their own topics and validation behaviour.

> **Frame it as:** a new Ethereum consensus-networking protocol *built on* libp2p — not a
> new libp2p feature.

That said, the **networking teams should be involved early**. A global topic with
validator-eligibility filtering, a novel bandwidth profile and bespoke spam controls can
run into implementation-specific limits across Lighthouse, Prysm, Teku, Nimbus and
Lodestar — and the subnet-count concern above is precisely the kind of thing only they can
adjudicate.

## Spam and signature-verification DoS — the main open risk

This is the one technical objection the discussion did **not** close.

**The concern (specs team):** *"It would be best if this didn't depend on a signature,
because an attacker might be able to spam these messages and cause nodes to perform a lot
of signature validations."* A BLS verification per message is orders of magnitude more
expensive than producing a garbage message, so an unauthenticated topic whose validation
requires a signature check is a natural amplification target.

**The partial answer, from the same source:** it may not be a big deal — messages with
invalid signatures **do not propagate**, and a peer sending even one bad message can be
de-peered immediately.

The mitigations available, all at the application layer:

- **Cheap checks strictly before signature verification** — is the claimed validator index
  *eligible this epoch* under the selection rule? Is the epoch current? This is the main
  argument for the stateless modulus rule: it turns the eligibility filter into an integer
  comparison.
- **Message-ID deduplication** — at most one message per eligible validator per epoch, so
  the legitimate message set has a hard, known size, and any second message from the same
  index is dropped without verification.
- **Strict per-peer rate limits** bounded by that known size.
- **Peer scoring and immediate de-peering** on a single invalid signature.

*Analysis, not from the discussion — and a reason the payload may be cheaper to handle than
attestations:* in the healthy case **every honest validator signs the identical message**
(same epoch, same root). Identical-message BLS signatures aggregate trivially, so an
aggregator scheme in the shape of `aggregate_and_proof` could compress "everybody agrees"
into a handful of aggregates with participation bitfields — and **disagreement would surface
naturally as a second aggregate over a different root**, which is exactly the signal the
agreement gate wants. This makes shadow-root telemetry *more* aggregatable than attestations
in the common case. It is untested and adds an aggregator-selection mechanism, so it is
listed as a candidate for the companion spec, not a recommendation.

## Deployment path

- **Fork-independent.** Because the signal is out of consensus, both the specs team and the
  migration side expect the mechanism can be **rolled out without a hard fork** — clients
  ship it, subscribe, and start publishing. The **swap itself still requires a hard fork**,
  activated only after confidence that validators have migrated.
- **Prototypable now.** Both specs-team participants judged this straightforward to
  prototype in clients and exercise on devnets (kurtosis-style), with one calling a "signed
  message of root and signature" sufficient for a first cut — while stressing that the
  approach must be **checked with client devs** before it is written up.
- **Temporary by construction.** The mechanism is intended to be **deprecated at the
  following upgrade**. Ethereum gossip topics are namespaced by fork digest
  (`/eth2/{fork_digest}/{name}/{encoding}`), so simply not subscribing after `PBT_ACTIVATION_FORK`
  retires the topic without a removal ceremony — a useful property for a mechanism whose
  whole purpose expires at the swap.
- **Default-on is what makes it work.** Nothing here changes the fact that coverage rests
  on CL clients shipping the sidecar **enabled by default**
  ([B-O3](../roadmap/deliverables/B-O3-shadow-root-ecosystem-readiness.md)); a
  gossip-based carrier is a delivery mechanism, not an enforcement mechanism.

## What remains open

1. **Selection rule and its period `N`** — index modulus vs committee-gated, and `N`
   derived from the gate's `D` sustained-observation window (see
   [§bandwidth](#the-bandwidth-arithmetic)).
2. **Spam / signature-verification DoS mitigation** — the ordered validation pipeline,
   rate limits, dedup keys and peer-scoring penalties, specified concretely rather than
   left to clients.
3. **Global topic vs subnets** — needs a networking-team ruling on the 1k+ subnet concern
   before the topic layout is frozen.
4. **Whether to aggregate**, and if so how aggregators are selected.
5. **Message container and signing domain** — the SSZ layout and a domain separator that
   cannot collide with attestation or block signing.
6. **EL→CL plumbing** — how the PBT post-state root reaches the validator client (engine-API
   extension vs a local RPC), still listed as open in
   [open-questions.md](../open-questions.md#shadow-root-publication--the-companion-specification).
7. **Who authors and owns the companion specification** — consensus-specs PR, and the
   client-dev sign-off the specs team asked for.

Items 1–5 are the substance of the companion specification named by
[B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md); item 6 is shared
with the EL side; item 7 is a coordination item for
[B-O3](../roadmap/deliverables/B-O3-shadow-root-ecosystem-readiness.md).

## Consequences for the rest of this repo

- **Nothing about the settled architecture changes.** Attester-sourced, validator-signed,
  out-of-consensus, never a block-validity condition, coverage-not-divergence for missing
  reports — all confirmed by this discussion rather than revised by it.
- **The carrier is now concretely scoped**: a temporary consensus-networking gossip topic,
  not an off-protocol reporting channel and not a libp2p feature. Where earlier text says
  "out-of-consensus telemetry sidecar", read it as *this*.
- **`N` couples the companion spec to the gate.** [B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md)
  cannot fix `Y` and `D` independently of the sampling period, and the companion spec cannot
  fix the sampling period independently of `D`. They must be settled together.
- **The payload must be the root, not a readiness bit** — otherwise the cross-client
  agreement leg of the gate has no input.
- **Networking-team engagement is a new, unscheduled dependency** for
  [B-O3](../roadmap/deliverables/B-O3-shadow-root-ecosystem-readiness.md).

## Sources

- CL-side design discussion on PBT root announcement and signing in the CL, 2026-07-27 →
  2026-07-29 (migration lead, CL specs team, client-team and consensus-spec reviewers).
  Participants are referred to by role in this file.
- [04-migration.md](04-migration.md#shadow-commitment--observability) — the settled shadow
  commitment architecture and the readiness gates.
- [open-questions.md](../open-questions.md#shadow-root-publication--the-companion-specification)
  — the tracker entry for the companion specification.
- [EIP-7549](https://eips.ethereum.org/EIPS/eip-7549) — obsoleted the attestation `index`
  field; that field is now reused by ePBS, which is why no spare attestation field exists.
- [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) — offline migration (now published;
  originated as [PR #12006](https://github.com/ethereum/EIPs/pull/12006)); the shadow
  period it defines is what this telemetry instruments.
