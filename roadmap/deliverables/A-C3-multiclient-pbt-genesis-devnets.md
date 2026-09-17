# A-C3 · Multi-client PBT-genesis devnets

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2027-01 → 2027-06 (5 months) |
| **Migration phase** | Phase 2 — Devnets |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight, ~5 months early** (as of 2026-09-17) — a **four-client** PBT-genesis devnet with per-block root agreement and deliberate reorgs has been running since August 2026; Nethermind joined 2026-09-14 |

← [Back to roadmap](../README.md)

## Objective
Bring up multi-client devnets that start from a **PBT genesis** — the tree is
canonical from block 0, with no MPT and no migration in the picture — and
demonstrate that all execution clients advance the chain in lockstep with
byte-identical PBT roots. This is the first cross-client integration of the
A-C1 implementations under live block production and the primary evidence that
feeds the H\* milestone.

> **Update (2026-09-17).** This deliverable's core scope already exists as
> [CPerezz/pbt-devnet](https://github.com/CPerezz/pbt-devnet), five months ahead of its
> 2027-01 start. What is running (`make tree-at-genesis`): **seven nodes across four
> implementations** — two geth, two Besu, two Erigon and **one Nethermind**, which joined on
> 2026-09-14 — the first of them a protected bootnode, on an **Amsterdam-at-genesis** chain
> driven by real Lighthouse consensus clients, with the tree switched on by `binaryTrieTime`
> in the genesis and every execution client required to agree on every state root. It
> composes `ethpandaops/ethereum-package` with **no patches** — the binary tree is reached
> entirely through supported configuration — and reaches the tree through the genesis rather
> than per-participant flags, which is what let Erigon join (its launcher runs
> `erigon init && erigon …`, and `el_extra_params` extends only the second half).
>
> The pairs are configured *differently on purpose*, because two instances of one binary
> agree by construction and prove nothing: geth adds `--state.size-tracking` on one node and
> archive/`--syncmode=full` on the other; Besu adds
> `--bonsai-limit-trie-logs-enabled=false`; Erigon adds `--prune.include-commitment-history`.
> Nethermind runs unpaired, built as `nethermind-pbt:local` from the `pbt-state` branch with
> `--Pbt.Enabled=true` selecting the PBT backend and the chainspec deciding the mode (binary
> tree from genesis here, flat-to-PBT migration when `binaryTrieTime` is after genesis).
>
> It also goes beyond this deliverable's original scope in one respect worth keeping:
> **chaos is on by default.** `pbtchaos` forces a reorg every 15–30 blocks by cutting the
> p2p of whichever node proposes next, rotating the victim so reorgs land on all four
> clients, and six scenarios strand specific state on a branch that is then abandoned —
> `code-sole`, `code-shared` (the content-addressed-code pair from
> [go-ethereum#30](https://github.com/CPerezz/go-ethereum/pull/30), lifted from unit test to
> seven live nodes), `delegate` (EIP-7702), `account`, `storage-add` (slots either side of
> `HEADER_STORAGE_OFFSET`), `storage-del`.
>
> **What is still missing against the exit criteria below:** **Reth** (four clients, not
> five — and Reth still has no PBT work of any kind), and a genesis generator that is a
> shared spec rather than
> [one fork's branch](https://github.com/CPerezz/ethereum-genesis-generator/tree/pbt).
> Treat the devnet as the seed of this deliverable, not its completion. Note also that all
> four implementations agree *using BLAKE3*, so this devnet's root agreement is evidence
> about everything except the still-undecided `H`.

## Scope — what ships
- A PBT-genesis specification and genesis-state generator producing an initial
  tree and root usable unchanged by every EL client.
- Standing multi-client devnets (all five ELs paired with CLs) producing and
  importing blocks over a PBT canonical state.
- Cross-client **root agreement** harness: per-block PBT roots collected across
  clients and diffed automatically, with divergence flagged and attributable to
  a client.
- EVM-invisibility validation: `SLOAD`/`SSTORE` and `EXTCODEHASH` behave
  identically to MPT-era execution (key derivation runs below the EVM;
  `code_hash` stays `keccak256(bytecode)`).
- Devnet tooling and configs contributed back so B-thread and test deliverables
  can reuse the networks.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (+ CL where relevant)

## Dependencies
- **Upstream (blocks this):** [A-C1](A-C1-client-tree-implementations.md) (client tree implementations)
- **Downstream (this blocks):** [B-T2](B-T2-full-cycle-devnet-swap.md), [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md); **feeds H\*** (2027-06)

## Exit criteria (definition of done)
- [ ] A multi-client devnet runs from PBT genesis with **all five ELs in
      per-block root agreement** over a sustained run.
- [ ] Any injected divergence is detected by the agreement harness and
      attributed to the responsible client.
- [ ] Execution semantics (`SLOAD`/`SSTORE`, `EXTCODEHASH`, gas for standard
      ops) match MPT-era behavior.
- [ ] Genesis generator output is reproducible and consumed unchanged by every
      client.

## Risks & open questions
- Cross-client agreement is the H\* readiness signal, but a **correlated
  all-client bug** would pass agreement undetected — conformance vectors (A-T3)
  must backstop it. See [open-questions.md](../../open-questions.md).
- Not-yet-final PBT gas constants could surface as subtle cross-client gas
  divergences under adversarial blocks. **This has already happened:** Erigon's default
  Amsterdam carries the pre-revision EIP-8038 schedule and does not subtract `WARM_ACCESS`
  from the EIP-2930 access-list constants, so it diverges from geth-pbt by 100 gas per
  access-list entry — and the three clients hold three different positions on the EIP-7610
  `CREATE2`-into-a-storage-only-account rule. These had to be reconciled by hand before
  Erigon could join. See [knowledge-base/07-sources.md](../../knowledge-base/07-sources.md).
- **Agreement measured at one hash function is not agreement about the hash function.** The
  running devnet pins BLAKE3 everywhere (geth hardcodes it, `besu-stateless` uses
  `Blake3Digest(256)`, Erigon takes `COMMITMENT_BIN_HASH=blake3`). Every root pinned here
  will need regenerating if `H` resolves differently. See
  [open-questions.md](../../open-questions.md#hash-function-selection--the-dominant-open-parameter).
- **Amsterdam-at-genesis drags in Gloas-at-genesis**, since PBT requires Amsterdam, which
  forces Gloas at slot 0 — the devnet's CL-side work (Gloas beacon state, external EL under
  Gloas, Caplin as an `ethereum-package` `cl_type`) is a real dependency that this
  deliverable did not anticipate. Tracked in Erigon issue
  [#23389](https://github.com/erigontech/erigon/issues/23389).

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
