# Attester shadow-root telemetry

[EIP-8347](https://eips.ethereum.org/EIPS/eip-8347#shadow-commitment) asks attesters to **publish signed PBT roots before the swap**. Publication is a `SHOULD`, outside consensus. Its wire format, aggregation, timing, and EL-to-CL path are left to an unpublished companion EIP. This page records transport options discussed in July 2026; none is a selected protocol.

## The problem being solved

A node may have converted or downloaded PBT state and replayed BALs correctly while consensus still checks only the MPT root. Comparing signed PBT roots for the **same block hash** makes disagreements visible before activation. Missing or late reports lower coverage; they are not root mismatches. The relevant population is validators, because readiness needs evidence from the set that validates blocks.

## Design space

| Option | Advantage | Main limitation |
|---|---|---|
| Global CL gossip topic with sampled validators | Reports reach independent observers; one topic is simple | Traffic and signature-verification load need bounds |
| Gossip subnets | Distribute traffic | More discovery and subscription complexity |
| Request/response or ENR status | Simple node sampling | Cannot measure validator-level coverage reliably |
| Beacon-state field or attestation extension | Consensus-visible | Changes consensus data and risks putting PBT work on the critical path |

The July discussion favored investigating a **temporary, rate-limited CL gossip topic** carrying signed reports from a selected subset. This is a design candidate, not EIP-8347's wire specification. It would use Ethereum's existing libp2p networking stack; protocol message and validation rules belong in Ethereum specifications.

## Bandwidth and abuse checks

Publishing every validator's root for every block would be too costly. Any sampled design needs an explicit selection rule, maximum report size, epoch or block binding, duplicate policy, and per-peer rate limits. Verify eligibility and cheap fields before expensive signatures, but do not let unauthenticated traffic exhaust the receiver. The sampling rate must be chosen with the desired coverage window: fewer reports per epoch require more time to measure agreement.

A readiness observer should count distinct eligible validator signatures, distinguish missing reports from conflicting roots, and weight or report coverage in a way the eventual readiness rule specifies. A bare readiness bit would lose the root comparison that makes cross-client divergence visible.

## Deployment and open decisions

The sidecar is expected to be enabled by default in CL clients, but that is an operational expectation rather than a consensus rule. The companion specification still needs to define the signed payload, validator selection, gossip validation, aggregation, publication timing, EL-to-CL plumbing, and how to handle reorgs. It must also show that the design meets bandwidth and denial-of-service budgets. Track decisions in [open questions](../open-questions.md) and [migration](04-migration.md#shadow-commitment--observability).

Source: July 27–29, 2026 CL-side design discussion summarized in [source notes](07-sources.md#non-public-inputs); EIP-8347 is authoritative for the settled shadow-root requirement.
