# 09 — Online (overlay) vs Offline (snapshot) migration: a deep dive

> A side-by-side comparison of the two MPT→PBT transition mechanisms — the **online
> overlay** and the **offline snapshot** — worked through the live objections raised on
> each side. It is written for the environment PBT actually ships into: **after H\*** (the
> spec-freeze / shadow fork) and around the swap at **I\*** (fork `PBT_ACTIVATION_FORK`, ≈ summer 2028), the
> network already runs **BALs (EIP-7928)**, **ePBS**, **zkEVM optional proofs**, and a
> **~400M gas limit**. [04-migration.md](04-migration.md) works the offline path out in
> detail (its six phases, converter, BAL-replay, snapshot, verification); this file is the
> *comparison*.
>
> It captures an open design debate. Positions are attributed to the **case** they make —
> the online (overlay) case and the offline (snapshot) case — and are laid out so a reader
> can weigh them, not settled here by authority. Where one side's point is conceded by the
> other, that is noted; where an argument reduces to an unresolved sub-question, that is
> flagged rather than scored.

## TL;DR

- **Both designs can be made *correct*.** The Verkle-era overlay is the most-researched
  transition mechanism we have, and its known weak spots (the two-tree read, the disk cost,
  observability) all have credible answers. The offline snapshot is closest to the
  conversion-node method, hardened with modern tooling. So the comparison is **not** "which
  one works" — it is a trade between two different sets of costs.
- **The defining structural difference:** online runs conversion *in* consensus, one block
  at a time; offline runs it *off* the consensus-critical path, at converter speed. Almost
  every downstream difference (proving, scheduling, disk, rehearsal) flows from this one.
- **Four features present at the swap** each bear on the comparison, and they do not all
  point the same way. **zkEVM proofs** and the **400M gas limit** raise the cost of doing
  conversion in-consensus (favouring offline); **BALs** make offline's catch-up cheap
  (enabling the offline path); **ePBS** gives block processing more headroom (favouring
  online). The overlay's original "known-tools engineering cost" framing predates all four.
- The **"two-tree read" objection is answerable**: a positional **conversion pointer** does
  reduce every access to a single tree, *including* non-existent keys — but only under a
  write discipline different from the prototyped move-on-write overlay, and it keeps the base
  MPT mutable rather than frozen. So access cost is **not** a decisive axis. See
  [§ The conversion-pointer question](#the-conversion-pointer-question-can-online-avoid-the-two-tree-read).

---

## The two designs in one breath

| | **Online (overlay)** | **Offline (snapshot)** |
|---|---|---|
| Where conversion runs | *In* consensus, one block at a time, over a ~1-month window | *Off* the consensus path, at converter speed, against a fixed anchor block `N` |
| State during the window | One logical tree, part binary / part MPT, advanced by a per-block iterator | Both full trees held side by side; MPT canonical until `PBT_ACTIVATION_FORK`, PBT built offline |
| Catch-up to tip | Inherent (the iterator *is* the chain) | **BAL-replay** from `N` to tip, no re-execution |
| The fork | Conversion machinery lives in the fork that runs the window | **`PBT_ACTIVATION_FORK` swaps the state commitment only** — no execution semantics move |
| Disk | ~1 tree (old entries deletable in real time) | ~2 trees during the window (extra ≈300 GB) |
| Distribution | None | ~100+ GB byte-canonical snapshot + manifest |

The overlay is option 1 of the Verkle-era survey; offline is closest to the
conversion-node method (option 2), hardened with modern tooling. See
[04-migration.md § Historical context](04-migration.md#historical-context-the-four-verkle-transition-options).

---

## The post-H\* environment (what the two designs are being compared *in*)

The overlay was designed and prototyped in the Verkle era, when a slot had a lot of idle
compute and the gas limit was a fraction of today's. PBT swaps at `I*` ≈ summer 2028, into a
network that has since gained four features. Each one changes the online/offline calculus,
and they do not all cut the same way:

1. **BALs (EIP-7928)** — shipped in Glamsterdam (≈ 2026-09), assumed mainnet-live. This is
   what makes the *offline* path cheap: a converted snapshot at anchor `N` is caught up to
   the tip by **replaying BALs** (per-entry translation into PBT leaf mutations), with **no
   re-execution**. The Verkle-era conversion-node method had to fall back on ad-hoc "catch-up
   messages"; BAL-replay replaces that. BALs do little for the overlay, which catches up for
   free by construction. **Bears on: offline's feasibility.**
2. **ePBS** — separates the proposer from the builder, so block *builders* get more
   wall-clock to produce a block. This softens the online case's "there's no time in the slot
   to also convert" worry. It does **not** bear on the offline path's **shadow-root**
   publication: shadow roots are signed **attester** telemetry, and attesters are already
   identified by the validator registry, so observability carries no ePBS dependency
   ([04-migration.md § Shadow commitment](04-migration.md#shadow-commitment--observability)).
   **Bears on: online (more in-slot headroom).**
3. **zkEVM optional proofs** — blocks carry validity proofs. With an overlay, provers must
   prove the **conversion steps for every block** in the window, on top of normal execution.
   Offline conversion is out of consensus, so it is **never proven** — guests keep proving
   plain MPT execution until `PBT_ACTIVATION_FORK`, then commit to the PBT root; there is no window in which the
   conversion itself is in the proof. **Bears on: offline (no conversion in the proof).** More
   in [§ zkEVM](#zkevm-having-the-code-path-vs-proving-it-every-block).
4. **~400M gas limit** — bigger blocks touch more state, so (a) online's fixed per-block
   conversion quota rises with the state it must chase, and (b) any per-access overhead the
   overlay introduces is multiplied across far more accesses per block. Offline's conversion
   throughput is independent of block cadence, so it does not inherit this. **Bears on:
   offline (conversion decoupled from block size).**

None of these is a tally to be summed into a winner; they define the *terrain* the two
designs compete on. Two of the four (zkEVM, 400M) make in-consensus conversion more
expensive, one (BALs) makes the off-consensus path feasible, and one (ePBS) makes
in-consensus conversion more affordable. A team's weighting of these is exactly the judgment
the comparison hands back to the reader.

---

## The arguments, one by one

Each subsection states the claim, the online (overlay) rebuttal, the offline reply, and a
neutral read of **what the argument actually turns on** — without declaring a winner.

### Observability: block header vs shadow root

- **Online view:** put the PBT root **in the block header** — why maintain a
  parallel view outside consensus at all?
- **Offline view:** a header field only carries the **builder's** PBT root. It gives
  no view of what the *network* thinks the PBT root is — no cross-client agreement signal,
  which is exactly the thing the pre-swap period exists to measure.
- **What it turns on:** for a *single carried* root the concern is symmetric — header or
  sidecar, one root is one producer's opinion. The designs differ in **what they sample**.
  The offline design's answer is the **shadow-commitment period**: attesters compute the PBT
  root of each block's post-state and publish it signed with their validator key, out of
  consensus, while the chain still runs on the MPT — so the signal is sourced from the
  **validating majority** rather than from block producers, conversion correctness becomes
  visible and attributable *before* consensus depends on it, and omissions degrade a
  **coverage** metric rather than causing divergence
  ([04-migration.md § Shadow commitment](04-migration.md#shadow-commitment--observability)).
  A header field is a fine *carrier* for a producer's root under either design, and nothing
  stops an overlay from adding the same attester-sourced signal; the question is whether you
  want a cross-client agreement gate before the swap at all, and if so how to source it. The
  offline answer is not free either: because publication is never a validity condition, its
  reach depends on the sidecar shipping **enabled by default** in CL clients rather than on
  the protocol compelling it.

### Consensus surface: "it's the same for every change"

- **Offline claim:** the overlay keeps **both trees consensus-live** for the whole window,
  exposing MPT↔PBT gas-discrepancy attack surface; `PBT_ACTIVATION_FORK` instead swaps only the state
  commitment, so execution semantics (gas, opcodes, tx validity) are unchanged and the fork
  is trivial to reason about.
- **Online rebuttal:** the consensus-surface argument does not persuade — *every*
  change we make has consensus surface; we have 10+ years of shipping complex consensus
  changes that converge on an identical Merkle root.
- **What it turns on:** the rebuttal is right that consensus surface is not disqualifying on
  its own. The offline point is narrower than "there is surface": it is that a
  **commitment-only swap** has *near-zero new execution surface* (nothing in the EVM's hot
  path changes at `PBT_ACTIVATION_FORK`), whereas the overlay adds live conversion logic *and* a period where
  two commitments with potentially different access costs are both authoritative. That extra
  surface largely evaporates **if** the two-tree read is truly avoidable (next section) —
  because then there is no gas-discrepancy surface to speak of. So this argument stands or
  falls with the pointer question rather than on its own.

### The two-tree read: can online avoid it?

This is the technical crux, so it gets its own section below. In short: **yes, a positional
conversion pointer avoids the two-tree read, including for non-existent keys** — but under a
write discipline that differs from the prototyped overlay, and at the cost of a mutable base
MPT. Worked through in [§ The conversion-pointer question](#the-conversion-pointer-question-can-online-avoid-the-two-tree-read).

### Repricing: is a migration-period gas schedule needed?

- **Offline claim:** if an overlay access can require touching **two trees** (e.g. a
  non-existent slot: miss in PBT, then miss in MPT), state-access opcodes must be **repriced
  for the migration period** to close the DoS vector — and under a 400M limit that is a lot
  of extra worst-case work per block.
- **Online rebuttal:** no repricing needed, because online is **fundamentally one
  tree** — "half binary, half MPT" — so the access cost is the same as a single tree.
- **What it turns on:** the online rebuttal holds **iff** the single-tree-read property holds
  (pointer model, below). If the overlay instead uses move-on-write semantics where reads must
  check the overlay *then* the base MPT, the worst case *is* two reads and a temporary
  repricing is in play — which the 400M limit makes both more necessary and more disruptive (a
  repricing that exists only during the window is itself consensus surface). So this reduces to
  the pointer question. Offline sidesteps it structurally: there is never a window with two
  consensus-live commitments, so no migration-only repricing arises under either read model.

### zkEVM: having the code path vs proving it every block

- **Online rebuttal:** the zkEVM argument does not land — the plan is to start with
  **existing guests**, which run the same logic as production clients and will therefore
  contain the conversion code path anyway. There are no guest-only implementations except
  `evm-asm`, which is not ready and shouldn't be used to measure protocol changes.
- **Offline reply:** having the *code path* is not the cost. The cost is that the
  overlay forces provers to **prove the conversion is done correctly at each block** during
  the window. Offline conversion is out of consensus, so there is **no block at which both
  trees are in consensus** and nothing about the conversion ever enters a proof — guests
  keep proving plain MPT execution, and after `PBT_ACTIVATION_FORK` they commit to the PBT root.
- **What it turns on:** the two claims are about different things — "the guest has the logic"
  and "the guest must prove the logic ran correctly for every block in a month-long window"
  are distinct costs, and only the online design incurs the second. Whether that recurring
  per-block proving cost is significant depends on how heavy the conversion step is to prove
  relative to normal execution, and on how mature zkEVM proving is at swap time — both
  quantifiable, neither yet measured for PBT conversion specifically. This asymmetry did not
  exist when the overlay was designed.

### Storage: 2× disk vs one tree

- **Online claim:** offline is **bad for storage** — converting the full state
  offline needs **double** the storage; online can delete from the old tree in real time as
  it converts, so it only ever stores ~one tree's worth.
- **Offline reply:** true that offline holds two trees through the window (an extra
  ≈300 GB), but with **history expiry** this is feasible, and the cost is **confined to the
  transition window and to converters/participating nodes**, not permanent.
- **What it turns on:** the raw number favours online — one tree beats two. Offline treats the
  2× as a bounded, temporary cost against history-expiry headroom, and in exchange keeps the
  MPT present and canonical until `PBT_ACTIVATION_FORK` (recoverability if conversion is found wrong). This is a
  genuine trade: disk efficiency vs an in-place fallback. A node that *cannot* meet the extra
  ≈300 GB is an enumerated offline failure mode with a fallback — snap-sync the PBT at
  `PBT_ACTIVATION_FORK` instead of converting (see
  [open-questions.md § Failure modes](../open-questions.md#failure-modes-to-enumerate)).

### Rehearsal: shadow fork vs end-to-end dry run

- **Online rebuttal:** rehearsal is possible online too, via a devnet / shadow fork.
- **Offline reply:** the offline procedure can be rehearsed **end-to-end on real mainnet
  state before activation** — convert `N`, distribute, BAL-replay to tip, dual-check verify,
  run the shadow period — and repeated until the readiness gate passes, with no consensus
  consequence if a rehearsal fails.
- **What it turns on:** both can rehearse; the difference is what a *failed* rehearsal costs
  and how faithfully it reproduces production. An offline rehearsal exercises the exact
  production artifacts (snapshot bytes, manifest, replay) against real state with the live
  chain untouched; an online shadow-fork rehearses conversion logic, but the real activation
  still runs the conversion *in* consensus for the first time on mainnet. How much that gap
  matters depends on confidence that shadow-fork fidelity approximates the real activation.

### Scheduling: can you lag and catch up?

- **Offline claim:** with online conversion, a **fixed minimum** amount of state
  must be converted every block to finish inside the window; a heavier block cannot "convert
  less now and catch up later." Offline can **lag under load and pick up later**, because
  conversion throughput is decoupled from block production.
- **Online rebuttal:** conversion competes with block processing in *both* designs,
  so both need scheduling anyway; and online can **pre-compute the next block's conversion
  ahead of time**. Also, post-ePBS there is *more* slot time, not less.
- **What it turns on:** the rebuttal is partly right — offline conversion also competes for
  I/O and CPU on converting nodes, so it is not free of scheduling. But the structural
  difference is real: the overlay's per-block quota is a **hard floor tied to the window
  length and the live state size** (Verkle-era sizing put it at `N ≥ 4,873` keys/block, ~3× a
  typical block's state touches — and that was *before* a 400M limit grew both the state and
  per-block churn), whereas offline conversion has **no per-block floor at all** — it can slow
  during a load spike and sprint afterward, and only converters bear it, not every validator.
  ePBS softens the online floor by adding wall-clock but does not remove the coupling: online's
  schedule is tied to consensus, offline's is not. Whether that coupling is a problem depends
  on how tight the window is against the ePBS-era slot budget at a 400M limit.

### Proof consumers / `eth_getProof`

- **Online rebuttal:** the `eth_getProof` concern is only *somewhat* valid — proof
  consumers need changes for a new tree **regardless** of how we migrate.
- **What it turns on:** largely symmetric. A new tree means new proof formats and coordinated
  consumer upgrades either way (tracked in
  [B-O1](../roadmap/deliverables/B-O1-proof-consumer-coordination.md)). The only divergence is
  narrow: during an overlay window, `eth_getProof` and similar must account for **two roots
  while conversion is in flight**; offline keeps it to one root until `PBT_ACTIVATION_FORK`, then one root after.
  A transient difference, not a structural one.

---

## The conversion-pointer question: can online avoid the two-tree read?

This deserves a careful treatment because it is where the debate is genuinely unresolved,
and because the answer determines whether the **consensus-surface** and
**repricing** arguments above have any force.

### The objection

In the **prototyped overlay** (EIP-7748 lineage), the base MPT is frozen read-only and an
initially-empty overlay tree takes all writes; a per-block iterator promotes keys. A read
checks the overlay **then** the MPT. For a **non-existent slot** the worst case is therefore
**two reads**: miss in the overlay, miss in the MPT, before you can conclude "absent." The
offline objection is that this two-read cost is *unavoidable* in that model, which (a) is a DoS
surface and (b) would need a migration-period repricing under a 400M limit.

### The online answer: a positional conversion pointer

Maintain a **conversion pointer** — an `(account, storage-slot)` position that delineates the
boundary of conversion in a fixed key order. Then for any key:

- key **before** the pointer → it lives in (and is resolved from) the **new** tree;
- key **after** the pointer → it lives in the **old** tree.

Crucially, this replaces move-on-write with **positional ownership**: a write to a key does
**not** promote it into the new tree. Instead you *"write to whichever tree is canonical at
the current point of conversion"* — if the key is already converted (before the pointer),
write to the new tree; otherwise write in place in the **old** tree, which stays **mutable**.
The pointer alone decides ownership.

### Does that resolve the non-existent-key case? Yes

Walk the worst case — a non-existent key `K`:

1. Compute `K`'s position and compare it to the pointer. This is arithmetic, **not** a tree
   access.
2. If `K` is before the pointer, read **only** the new tree. Everything before the pointer
   has been fully migrated, so the new tree is *authoritative* for that region — a miss there
   is a definitive "absent." **One read.**
3. If `K` is after the pointer, read **only** the old tree. That region is untouched by
   conversion and the old tree is authoritative — a miss is definitive. **One read.**

So the two-read problem is **specific to the move-on-write overlay**, where a key can be
"conceptually in the MPT but written into the overlay," forcing you to check both. Under
positional ownership no key is ever ambiguous, and a single access suffices — for existing
*and* non-existing keys. This is the meaning of "one tree, half binary and half MPT": the union
is a total partition by position, so access cost matches a single tree and **no
migration-period repricing is required**.

The offline follow-up — *"every write moves that slot into the new trie, so random keys get
promoted out of pointer order; how does the pointer help?"* — is a correct critique **of the
move-on-write overlay**, but it is answered by *not doing move-on-write*. That is precisely
the discipline the positional-ownership variant switches to.

### Making it concrete for PBT: three cursors, not one pointer

A single scalar `(account, slot)` pointer glosses over PBT's zone structure. Worked against
the real layout ([03-key-derivation.md](03-key-derivation.md)), **everything is per-account
except overflow code**: the header stem `0x00‖key_hash(addr)` bundles BASIC_DATA, CODE_HASH,
low storage (slots 0..63) and low code (chunks 0..127); overflow storage (slots ≥64) sits in
`0xFF‖…` per account; only overflow code chunks (≥128) live in `CODE_ZONE`
`0x01‖key_hash(code_hash‖ti)`, **content-addressed and shared** across contracts with
identical bytecode. So one pointer cannot express ownership for all three.

The escape hatch that makes single-read work is that the two trees use *different* hashes and
orders (MPT: `keccak`; PBT: `key_hash`/BLAKE3), but **at EVM-execution time the client always
holds the raw `address`, `slot`, and `code_hash`** — so it can compute *both* the `keccak(...)`
needed to locate a key against the boundary *and* the `key_hash(...)` needed to form the PBT
key. Define the boundary in the **source (keccak) domain** we are draining, and route every
access with metadata already in hand. That needs **three monotonic cursors**, one per
ownership class:

| Cursor | Domain / order | Governs |
|---|---|---|
| `A*` | `keccak(address)`, = MPT account order | The whole header stem **and** all of the account's overflow storage |
| `S*` | `keccak(slot)`, = MPT storage order | Overflow storage of the **single frontier account** (`keccak(addr)==A*`) only |
| `C*` | `code_hash` order | The shared `CODE_ZONE` (overflow code) |

`A*` and `C*` are independent: a converted account may reference not-yet-converted shared
code, and vice versa — code is always routed by `C*`, never by `A*`. Resolution reads exactly
one side, chosen by comparison, never by probing:

```text
resolve(access):                       # returns PBT or MPT; never both
  ha = keccak(address)
  if access in header_stem:            # BASIC_DATA, CODE_HASH, storage 0..63, code 0..127
     if ha < A*: return PBT
     if ha > A*: return MPT
     return PBT                         # frontier: header stem converts first, atomically
  if access is overflow_storage:       # slot >= 64, zone 0xFF
     if ha < A*: return PBT
     if ha > A*: return MPT
     return PBT if keccak(slot) < S* else MPT      # frontier only
  if access is overflow_code:          # chunk >= 128, zone 0x01
     return PBT if code_hash < C* else MPT          # code_hash from the CODE_HASH leaf
```

A miss on the chosen side is authoritative (within a converted account the PBT is the whole
truth; within an unconverted one, the MPT), so **the non-existent-key case is one read too**.
The header stem is ≤256 leaves, so it converts atomically as the frontier account opens; only
**overflow storage** is drained sub-account by `S*`, which is why only whale accounts stress
the schedule (see [§ scheduling](#scheduling-can-you-lag-and-catch-up)). Writes route the same
way and land in place on the owning side; a fully-converted account's MPT subtree is deleted in
bulk and the frontier's `storageRoot` is recomputed per drained batch (bounded to one account),
giving the online case's one-tree disk profile. Each block commits to
`(A*, S*, C*, root_PBT_converted, root_MPT_residual)`.

Two residual edges the scalar-pointer framing hid: **newly deployed contracts** during the
window have an immutable but arbitrarily-sorted `code_hash`, so an explicit rule is needed
(dedup onto an existing leaf, else write to the creating account's side); and the boundary is
**contiguous in `keccak` order but scattered in `key_hash` order**, so by-address resolution is
fine but anything reasoning about ownership while traversing in *tree-key* order (PBT range /
snapshot sync during the window, low-level range proofs) cannot use a simple range check.

### What the pointer costs

Resolving the two-read objection does not make the overlay free; the pointer model carries its
own costs, and each of them lands **on the consensus-critical path**:

1. **The partition must be consensus state on a deterministic schedule.** For all nodes to
   resolve ownership identically, `A*/S*/C*` and their per-block advancement rate must be in
   consensus — which *is* the fixed per-block conversion floor. It cannot slow under load or
   during a whale drain (see [§ scheduling](#scheduling-can-you-lag-and-catch-up)).
2. **The base MPT is no longer frozen.** Positional ownership keeps the old tree mutable in
   its un-migrated region while the converter iterates it, and the frontier account's
   `storageRoot` is recomputed per drained batch. Workable, but **more complex than a frozen
   base** and a *different* design from the frozen-base, move-on-write overlay that "has been
   under research for years and tested in prototypes" — so it means re-validating a variant.
3. **Reorgs must rewind the cursors** and un-convert the affected leaves — extra transition
   machinery with no offline analogue.
4. **Content-addressed code needs its own cursor plus an edge rule** for window-time
   deployments, and "unconverted account" is no longer purely MPT (its shared code may be
   PBT-side).
5. **The boundary is scattered in `key_hash` order**, so PBT range/snapshot sync and
   low-level range proofs during the window cannot use a simple range check.
6. **All of the above is proven every block under zkEVM** — the recurring proving cost
   discussed in [§ zkEVM](#zkevm-having-the-code-path-vs-proving-it-every-block), which the
   pointer does not touch.

Points 1 and 6 are notable because they are *independent* of the read cost: even a perfect
single-read overlay still has a **scheduling floor** and a **per-block conversion proof**. The
two-read objection, whatever its merits, is therefore not the axis the comparison rests on.

### Where the pointer leaves the read-cost argument

On the narrow question, the online case is right: with a positional pointer the overlay can be
**single-read and needs no migration repricing** — the flat "online always needs two reads"
claim is true only of the move-on-write overlay. The cost of that property is a **mutable base
MPT** and re-validating a design variant that differs from the prototyped one. So access cost
and repricing drop out as decisive axes for *both* designs, and the comparison moves to the
costs the pointer does not address — the scheduling floor and the per-block proving cost on
the online side, and the disk and rehearsal-fidelity trades on the offline side.

---

## Summary scorecard

The **Favours** column names which design a dimension advantages: **On** = online (overlay),
**Off** = offline (snapshot), **–** = roughly neutral / conceded by both. It is a map of the
trade space, not a tally to be summed.

| Dimension | Favours | One-line rationale |
|---|:---:|---|
| Conversion off consensus-critical path | Off | Structural property; the source of most other offline differences. |
| zkEVM proving | Off | Online proves conversion every block; offline never proves it. **(new post-H\*)** |
| Per-block scheduling / lag-and-catch-up | Off | Offline has no per-block conversion floor; online's floor grows with 400M. **(sharper post-H\*)** |
| Single small swap fork (commitment-only) | Off | No execution semantics move at `PBT_ACTIVATION_FORK`. |
| End-to-end rehearsal on real state | Off | A failed offline rehearsal has no consensus consequence. |
| Disk during the window | On | Online stores ~1 tree; offline ~2 (extra ≈300 GB), bounded and history-expiry-feasible. |
| ePBS slot headroom | On | More builder wall-clock softens online's conversion-in-slot worry. **(new post-H\*)** |
| Design maturity | On | The overlay is the most-researched, already-prototyped mechanism. |
| Migration-period repricing | – | Not needed under a single-read overlay; offline needs none regardless. |
| Two-tree read / access cost | – | Answerable online via a positional pointer; not a decisive axis. |
| `eth_getProof` / proof consumers | – | New tree ⇒ consumer changes either way; offline saves only a transient two-root case. |
| Consensus surface in the abstract | – | All changes have surface; offline's distinction is a *commitment-only* swap. |
| Observability | – | Both need a cross-client agreement signal; a header field ≠ network view. |

---

## Weighing the two

The comparison does not resolve to one design being *broken*. Both can be made correct; they
carry different costs, and which set a team prefers is a value judgment the technical analysis
narrows but does not make:

- **The online (overlay) case is strongest** if you weight design maturity (it is the
  most-researched, already-prototyped mechanism), raw disk efficiency (one tree, not two), and
  the extra in-slot headroom ePBS gives an in-consensus converter — and if you judge the
  per-block proving and scheduling floors to be affordable at swap-time zkEVM maturity and the
  ePBS-era slot budget.
- **The offline (snapshot) case is strongest** if you weight keeping conversion **off the
  consensus-critical path** — which is what neutralizes the zkEVM per-block conversion proof,
  removes the per-block scheduling floor, and means the first real conversion run does not
  happen in consensus on mainnet — and if you accept the bounded 2× disk cost and the
  distribution of a large snapshot as the price.

The post-H\* environment sharpens rather than settles this: **zkEVM** and the **400M limit**
push the cost of in-consensus conversion up, **ePBS** pushes it down, and **BALs** are what
make the off-consensus catch-up cheap enough to be a real option at all.

Two factual corrections the analysis establishes for either side to build on:

- The **"online always needs two tree reads"** framing is accurate only of the move-on-write
  overlay; a positional conversion pointer answers it (single-read, no migration repricing),
  at the cost of a mutable base MPT. See
  [§ The conversion-pointer question](#the-conversion-pointer-question-can-online-avoid-the-two-tree-read).
- The axes the pointer **cannot** touch — the per-block **proving** cost and the **scheduling
  floor** on the online side — are independent of read cost and are what the environment
  post-H\* most changes; they belong at the centre of any weighing, in place of the read-cost
  debate.

See also: [04-migration.md](04-migration.md) (the offline path worked out in full: phases,
converter, BAL-replay, snapshot, verification),
[08-gas-and-access-events.md](08-gas-and-access-events.md) (why any repricing is
benchmark-based and decoupled from `PBT_ACTIVATION_FORK`), and
[open-questions.md](../open-questions.md) (the §14 migration parameters, failure modes, and
the shadow-root companion specification).
