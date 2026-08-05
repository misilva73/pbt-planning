# 10 — Zero-Value Leaves vs. Deletion on Zeroization

> **Status: RESOLVED.** EIP-8297 has been revised to require **(B) delete on
> zeroization**, matching EIP-8347's BAL-replay rules and closing the contradiction this
> file was written to analyze. The tracking issue,
> [misilva73/pbt-planning#3](https://github.com/misilva73/pbt-planning/issues/3), is
> **closed**. This file is kept as the **decision record** — the axis-by-axis analysis
> below is why (B) was the right call, not an open debate. The live, settled rule is
> documented normatively in
> [02-tree-structure.md § Zero values and deletion](02-tree-structure.md#zero-values-and-deletion).
> See also [execution-specs#3254](https://github.com/ethereum/execution-specs/issues/3254)
> (the fixture-conformance issue this unblocks) and
> [execution-specs#3246](https://github.com/ethereum/execution-specs/pull/3246) (the test
> work that originally surfaced the contradiction).

## The question that was open

When an `SSTORE` writes 32 zero bytes to a slot that held a non-zero value, does the PBT

- **(A) keep the leaf**, present with value zero and distinct from an absent key
  (*no-deletion* — an earlier EIP-8297 draft, inherited from Verkle); or
- **(B) remove the leaf**, so zero and absent are the same thing
  (*delete-on-zeroization* — MPT semantics, what `ethereum.state_pbt` actually did, and
  what the **current, adopted** EIP-8297 text now requires)?

It was not a cosmetic question — the two options commit to **different state roots for
the same execution**. It has since been settled in favour of (B), ahead of the spec
freeze ([A-S3](../roadmap/deliverables/A-S3-eip8297-spec-freeze.md)).

## The spec set used to disagree with itself

This section is kept for record: at the time this file was first written, the question
was not "undecided" — it was **decided both ways in two EIPs that `require` each other**.

| Source | Said (at the time) |
|---|---|
| EIP-8297 § *Zero values and deletion* (**normative**, not Rationale) — earlier draft | "the leaf stays present, and a zero-valued leaf is distinct from an absent key"; "implementations never need delete logic"; "Removing entries is reserved for a future state-expiry mechanism." |
| **EIP-8347** BAL-replay rules — `requires: 8297` | "**Zero-writes delete leaves** — a value of zero is encoded as leaf *absence* … This matches MPT semantics and keeps independently converged PBTs bit-identical." ([04-migration.md](04-migration.md#bal-replay)) |
| `ethereum.state_pbt` reference implementation | Removes zeroed slots; drops an account's storage on account deletion. The *raw tree layer* was conformant to the old text (`test_zero_value_is_not_absence` pinned it); only the provider layer removed. |
| This repo's own roadmap | Asserted **(A)** in [A-C1](../roadmap/deliverables/A-C1-client-tree-implementations.md), [A-C2](../roadmap/deliverables/A-C2-pbt-native-state-sync.md), [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md); asserted **(B)** in [B-C2](../roadmap/deliverables/B-C2-bal-replay-engine.md), [B-T1](../roadmap/deliverables/B-T1-conversion-replay-vectors.md), [B-S1](../roadmap/deliverables/B-S1-offline-migration-eip.md). |

**Current EIP-8297 text now normatively requires (B)** — see the "Zero Values and
Deletion" and "Collapsing Zero and Absent" quotes in
[02-tree-structure.md](02-tree-structure.md#zero-values-and-deletion). The roadmap
deliverables above that asserted (A) should be treated as **stale** and updated to (B).

EIP-8347's rule was never sloppy — it was **forced** (see
[Migration determinism](#1--migration-determinism--the-forcing-constraint)) — and
EIP-8297 has now been brought into line with it rather than the other way around.

## Where the no-deletion rule actually came from

The rule is inherited from Verkle, and the inheritance is traceable to exactly one
motivation, which no longer applies.

- **Verkle mechanism.** [EIP-6800](https://eips.ethereum.org/EIPS/eip-6800) had to *buy*
  the distinction with an explicit **leaf marker** — bit 128 of the lower half of each
  value, set iff the leaf has ever been written. Verkle paid a real encoding cost for
  something PBT gets free from leaf presence.
- **Original motivation: epoch-based / multi-tree state expiry.**
  The [state-expiry note](https://notes.ethereum.org/@vbuterin/state_expiry_eip) is the
  source, and is explicit: *"'zero' and 'absent' are no longer synonyms — 'zero' means
  there's nothing there and 'absent' means 'the latest version of this object might be in
  older trees, check those first'."* Reading an object from period `e` in period `f`
  requires a witness of **absence in every intervening tree** `S_(e'+1) … S_(f−2)`. If a
  zeroed slot were deleted, "absent" would be ambiguous and the walk-back is unsound.
  **This is the whole argument, and it is specific to the multi-tree design.**
- **That design is dead.** Confirmed in review by the original state-expiry design work:
  the motivation for leaving values at zero was the expectation of epoch-based state expiry
  shortly afterwards, which does require it; under the current state-size strategy,
  switching to removal breaks nothing.
- **The live expiry family does not need it.**
  [EIP-7736](https://eips.ethereum.org/EIPS/eip-7736) (leaf-level expiry, explicitly
  portable to binary trees) expires a *stem* by deleting values and subcommitments while
  **retaining a keepsake commitment plus the stem** for resurrection. Its soundness comes
  from that stub, not from zero-valued leaves. Its rationale never invokes the
  zero-vs-absent distinction. PBT's own planned expiry — per-account-stem and per-bucket,
  record the subtree hash and prune below it ([../open-questions.md](../open-questions.md))
  — is the same shape: the marker is a **stub node introduced by the expiry fork**, not a
  population of zero leaves preserved from years earlier.

**Conclusion on provenance:** the "it's needed for expiry" claim is not hand-wavy in
origin — it was precisely correct for a design that has been abandoned. Carried into
PBT + a subtree-expiry roadmap, it no longer buys anything. Re-confirming this against the
original state-expiry design work was the right step to take before deciding, and the
confirmation came back negative.

---

## The trade-off, axis by axis

### 1 · Migration determinism — the forcing constraint

**Decisive, and in favour of (B).**

The offline migration's correctness rests on one property: **the PBT at height `h` is a
pure function of the MPT state at `h`**. Everything downstream depends on it —

- **Re-anchoring.** A distributor re-converts at `ANCHOR_BLOCK + n·REANCHOR_CADENCE`; a
  late joiner picks a *later* anchor than an early adopter. Their PBTs must converge
  bit-identically ([04-migration.md](04-migration.md#re-anchoring--late-joiners)).
- **Dual-check verification.** Check 2 re-hashes snapshot leaves under the *MPT schema*
  and compares against `ANCHOR_BLOCK`'s `stateRoot`. The MPT contains no record of deleted
  slots, so a PBT holding zero-valued leaves cannot round-trip.
- **Shadow roots.** Every attester's shadow root for block `h` must match, whether it
  converted at `N` and replayed 500k blocks or converted at `h` directly.

Under (A) the incrementally-maintained PBT accumulates zero leaves the converted PBT
cannot have, and independently-derived roots diverge. There is no fix that keeps (A)
during the shadow period. Hence:

> Option (A) **requires two tree semantics** — delete-on-zero for the whole pre-swap
> period, keep-at-zero from `PBT_ACTIVATION_FORK` — with a semantic discontinuity at exactly the
> most consensus-critical block in the programme.

*Fair counter, and it should be stated:* the two behaviours live in **different
components with different lifetimes** — the deleting path is the BAL-replay engine
([B-C2](../roadmap/deliverables/B-C2-bal-replay-engine.md)), throwaway migration code,
while the keeping path is the post-swap EVM state writer. That is less bad than "two
implementations of the trie". But the **trie library must support both**, the EEST/vector
suites must cover both regimes, and archive nodes and pre-swap snap-sync keep needing the
deleting semantics indefinitely. The unvalidated-flip weak point
([04-migration.md](04-migration.md#known-weak-points--mitigations)) gets strictly worse if
the swap block is also where deletion semantics change.

### 2 · The root stops being a function of the state

**Under-appreciated, and in favour of (B).**

Under (A), two chains with **identical live state** but different histories have
**different state roots**. The root commits to history, not to state. Consequences that
outlast the migration:

- **Flat state must store explicit zeros.** No client's flat/snapshot layer does today —
  a zero value *is* the absence of a record. Every client must add explicit zero
  retention, and every export/import/repair path must preserve it. Dropping one zero
  silently produces a wrong root: a **silent consensus-bug class that does not exist under
  (B)**.
- **State cannot be verified from a state dump.** The "rebuild the tree from state and
  compare roots" check — the backbone of migration verification, and of ordinary
  debugging — is only sound if the root is a function of the state.
- **Test formats cannot express the state.** EEST `pre`/`post` allocs are
  `address → {storage: {slot: value}}` mappings in which a `0x00` value is
  conventionally indistinguishable from an absent slot. Under (A) there is **no way to
  write a fixture whose pre-state contains a zero-valued leaf** without extending the
  fixture format across the tooling. This is not hypothetical; it is why #3254 says
  EIP-8297 fixtures cannot currently be treated as conformance vectors.
- **Two representations of zero, forever, at the proof layer.** Absent keys still exist
  (never-written slots), so under (A) a consumer proving "slot == 0" must accept *either*
  an exclusion proof *or* an inclusion proof of zero. `eth_getProof` successors,
  verification precompiles and bridges
  ([B-O1](../roadmap/deliverables/B-O1-proof-consumer-coordination.md)) all inherit the
  ambiguity. (B) leaves exactly one canonical representation of zero.

### 3 · Implementation and prover complexity

**Real but small, and the argument is weaker than it looks — mildly in favour of (B).**

Concretely, what deletion costs in PBT. Delete key `K` whose parent branch `B` (prefix
`p`) has sibling `S`; `B` must be re-canonicalized because a `BranchNode` MUST have two
non-empty children:

- **`S` is a `LeafNode`** → replace `B` with `S`. **`S`'s hash does not change**, because
  a PBT leaf commits its *complete key* and is position-independent
  ([02-tree-structure.md](02-tree-structure.md#node-types-two)). Zero extra data, zero
  extra hashing.
- **`S` is a `BranchNode`** (prefix `q`) → the replacement is
  `BranchNode(p ‖ bit ‖ q)` carrying `S`'s children. Hashing it needs `q`,
  `hash(S.left)`, `hash(S.right)` — a proof of `K` supplies only `hash(S)`. So deletion
  needs **one extra node expanded in the witness** (~66+ bytes).
- **Merging is one level only.** `B`'s parent still has two children, so it never
  cascades. No unbounded restructuring.
- **The circuit machinery already exists.** Insertion already slices a prefix at an
  arbitrary bit offset — `BranchNode(node.prefix[:matched])` and
  `BranchNode(node.prefix[matched+1:])` in
  [02-tree-structure.md](02-tree-structure.md#insertion). Deletion is the *inverse*
  operation (concatenate two prefixes and a bit). Variable-offset bit repacking is the
  annoying part in-circuit, and it is **unavoidable for insertion regardless**. The
  assessment from prover-side review — that this is not a prover-killer — matches the
  structure.
- **It is strictly simpler than the MPT deletion every client already ships.** MPT leaves
  commit a *path-relative suffix*, so MPT deletion re-encodes the surviving sibling's key
  and juggles three node types including extension nodes. PBT deletion re-hashes nothing
  in the leaf case and merges two prefixes in the branch case.

So "(A) is simpler" is true, but the increment is **one bounded, one-level, already-tooled
operation** — and it is being weighed against having to run *both* semantics (§1) plus
explicit-zero plumbing in every client's flat state (§2).

### 4 · State size

**Genuinely in favour of (A) being costly — magnitude unmeasured.**

- **Both options get a free one-time GC at the swap.** Conversion reads the MPT, which
  contains no historically-deleted slots, so the post-swap PBT starts clean either way.
  Every zero leaf ever accumulated in today's MPT is dropped at `PBT_ACTIVATION_FORK` regardless.
  The cost of (A) is therefore **entirely forward-looking**.
- **Per retained zero slot:** a storage leaf record is `66 + 32 = 98` bytes in the
  snapshot format; on disk with index and branch-node overhead call it ~100–150 bytes.
  EIP-8037 books a new slot at 64 "state bytes". So **~100M retained zero slots ≈ 6–15 GB**.
- **Sensitivity.** Net state growth is ~100 GB/yr. At an assumed gross clear rate of
  1M slots/day, (A) retains ~365M leaves/yr ≈ **25–50 GB/yr of pure garbage** — a quarter
  to a half of net growth. At 0.1M/day it is ~3–5 GB/yr — noise. **The plausible range
  spans an order of magnitude and straddles the point where it matters**, which is why
  this needs measuring rather than arguing (see
  [What to measure](#what-to-measure-before-freezing)).
- **The equilibrium caveat cuts the other way** — see §6. If (B) makes clearing
  irrational, (B) does not actually reclaim this space either; it just converts zero
  leaves into non-zero ones.

### 5 · Proof size, tree depth, non-inclusion

**A non-argument. Neither option wins.**

- PBT keys are full-digest and uniformly distributed, so depth is `log2(N)`. Going from
  ~1e9 leaves (today's ~100+ GB snapshot ÷ ~98 B/leaf) to 1.3e9 adds **0.4 bits of average
  depth**. Retained zero leaves cost essentially nothing in proof size.
- On the objection that *non-inclusion could get expensive with a deep tree of empty
  leaves*: an attacker must grind `key_hash(address ‖ tree_index)` within **their own
  bucket** (the suffix is address-bound, [06-open-questions.md](06-open-questions.md)), and
  `d` real extra levels cost ~`2^d` work *plus* state-creation gas per leaf. An attacker
  building depth would never zero the slots, so (B) does not undo the attack either. The
  same attack is already available on the MPT today, at benchmarked but prohibitive setup
  cost.
- Non-inclusion proofs themselves are unaffected in shape: you prove the divergence point.
  (A) only adds the *second* representation of zero noted in §2.

### 6 · Gas pricing and developer experience

**The strongest argument for (A) — and the one that should be answered rather than
dismissed.**

The argument: slots legitimately cycle `0 → 1 → 0 → 1` across blocks (ERC-20
allowances zeroed by `transferFrom`, closing/reopening positions, tick and bitmap words,
order-book entries). Under (B), every re-creation pays state-creation gas again. Under
(A) the leaf persists, so state creation is charged **once per slot, ever**.

Put numbers on it under [EIP-8037](https://eips.ethereum.org/EIPS/eip-8037):

- `STATE_BYTES_PER_STORAGE_SET (64) × CPSB (1530) =` **97,920 state-gas per new slot**.
- The reservoir only absorbs gas *above* `TX_MAX_GAS_LIMIT`
  (`gas_left = min(execution_gas_budget, evm_gas)`), so for ordinary transactions this is
  **real gas out of `gas_left`**.
- Refills are **same-transaction only** (LIFO, for reverted/undone creations, and for a
  slot created and zeroed within the same tx). A slot cleared in block `N` and recreated
  in block `N+1` pays in full and recovers only the legacy `SSTORE_CLEARS_SCHEDULE`
  refund of **4,800 gas** ([EIP-3529](https://eips.ethereum.org/EIPS/eip-3529)).

That is a **~20:1 asymmetry**. Re-running EIP-3529's own break-even calculation with
8037-era numbers: it lowered the incentive-to-clear threshold to
`4800/17100 ≈ 28.1%` reuse probability; at ~98k re-creation cost the threshold becomes
**≈ 4–5%**. Which yields the argument that actually matters:

> **Under (B) plus 8037-style pricing, clearing a slot is irrational for essentially
> every slot.** Rational developers keep slots at `1` and cycle `1 ↔ 2` — exactly the
> workaround that is widely acknowledged as bad devex. The state then grows *just as much
> as under (A)*, only with non-zero garbage instead of zero garbage, and an extra tax on naive
> developers who wrote the obvious code. **(B)'s state-size win (§4) is partly an
> accounting illusion; (A) at least does not lie about it** — you paid once for a
> permanent slot and you got a permanent slot.

*But note what this argument is actually about.* It is about **the gas schedule needing a
memory of "this slot was already paid for"** — not about the trie's shape. (A) supplies
that memory by keeping ~100 bytes of consensus state per ever-created slot, forever. That
is a very expensive place to store one bit.

#### A cheaper place to put the pricing memory

Worth putting on the table, since the swap is plausibly the last chance to reach a
minimally-ugly solution to this whole problem. Both variants keep deletion semantics
**(B)** and fix the churn penalty independently of the tree:

1. **Refill the state-gas dimension on clear (intra-transaction generalization).**
   Credit `state_gas_reservoir` — not `gas_left` and not `refund_counter` — when a
   pre-existing slot is cleared. The user cannot cash it out, so it **cannot become a gas
   token**; it is not execution gas, so it **cannot inflate block execution gas** — and
   [EIP-7778](https://eips.ethereum.org/EIPS/eip-7778) independently removes refunds from
   block-gas accounting, killing the other half of the objection. Worst case is a
   bounded 2× tree-write amplification within one transaction (clear N, create N), the
   same shape of bound EIP-3529 relied on. Fixes only same-transaction churn.
2. **Per-account high-water-mark state quota.** Keep a `storage_hwm` counter in
   `BASIC_DATA` (there are reserved bytes; cf. EIP-8032's `storage_count` and
   [EIP-8188](https://eips.ethereum.org/EIPS/eip-8188)'s precedent for widening the leaf).
   Charge state-creation gas only when an account's live slot count exceeds its historical
   peak; clearing decrements the live count and genuinely shrinks the tree; re-creating up
   to the peak is free. **This is sound because the resource being priced is occupancy,
   and the HWM bounds occupancy** — live ≤ peak always, and every churn write still pays
   ordinary write gas. Cost: ~4 bytes **per account**, versus ~100 bytes per
   ever-created **slot** under (A) — three to four orders of magnitude cheaper for the
   same economic effect, and it fixes cross-block churn too. Caveat: an account that
   legitimately shrinks retains a large free quota forever (a decay schedule is possible),
   and it must be reconciled with the leaf-format decisions already pending for 8188 and
   compression.

Neither is free, both need scrutiny, and both are gas-EIP work
([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) rather than trie work.
The point is that **the pricing objection does not have to be paid for with trie
semantics**, and paying for it with trie semantics is the most expensive available option.

### 7 · Future optionality — and it is asymmetric

**In favour of (B).**

- **Ship (B), later want the three-state distinction** → a future expiry fork introduces
  it going forward (stub nodes, or a marker, or 7736-style keepsakes). Only *pre-fork*
  deletions are unrecoverable — and no live expiry design needs them, because expiry
  prunes based on what exists at prune time. The "we can always change it later" argument
  holds here.
- **Ship (A), later want (B)** → the accumulated zero leaves can only be removed by a
  **network-wide zero-sweep at a fork**: a deterministic full-tree recomputation, i.e. a
  second migration event, with its own snapshot/verification programme. Feasible, but
  enormously more expensive than the reverse.

So **(B) is the more reversible default**, which is the relevant property for a decision
being frozen under uncertainty about a state-expiry design that does not exist yet.

### 8 · EVM-observable edges (must be specified either way)

The framing "this only changes the state commitment, not execution" is **not quite true**,
and the test work already caught it:

- **EIP-7610 / `CREATE` collision.**
  [execution-specs#3253](https://github.com/ethereum/execution-specs/issues/3253):
  `account_has_storage` gates `CREATE`/`CREATE2`, and `state_mpt` and `state_pbt` disagree
  about whether a cleared account still has storage — so *creation into a cleared address
  succeeds under `BinaryTree` and is rejected under MPT*. PBT removes `storage_root` from
  the account header, so "does this address have storage" becomes a tree-range question
  whose answer is determined by this decision. **Fix independently of it:** define
  `account_has_storage` as "has any **non-zero** storage value", which is
  representation-independent.
- **Account-level deletion is a separate question from slot-level.** Same-transaction
  `SELFDESTRUCT` (post-[EIP-6780](https://eips.ethereum.org/EIPS/eip-6780)) and EIP-158
  state clearing delete an *account*. Whichever slot rule is chosen, the spec must say
  explicitly whether the header stem's leaves and the account's storage leaves are removed
  or zeroed. Under (A), a self-destructed account leaves zeroed header leaves and the
  client must map "all-zero `BASIC_DATA`" back to "account does not exist" — another place
  for a consensus bug.
- **The code zone deletes on a reference-count check, not on zeroing.** *(Updated: an
  earlier version of this point said code deletion was deferred/never happened; the
  current EIP-8297 text specifies it directly.)* All code chunks are content-addressed
  and shared by `code_hash`, so `CODE_ZONE` leaves are removed on account deletion or a
  `code_hash` change **only if no resulting-state account still shares that `code_hash`**
  — this is orthogonal to the (A)/(B) storage-slot question. Adopting (B) does not by
  itself clean the code zone; the refcount check does. Storage-slot deletion semantics
  (this file's subject) apply to storage leaves and per-account header leaves only.

### 9 · Storage layer

**Roughly a wash; small structural point for (A).**

- **(B)** writes an LSM tombstone that reclaims space at the next compaction — toxic waste
  in the LSM, but it does trim size. Real, and correct.
- **(A)** makes the key set **monotonically growing**, which is friendlier to append-only
  layouts, static/perfect-hash indexes, and a read-optimized "stable tier" — which is
  exactly what the [EIP-8188](https://eips.ethereum.org/EIPS/eip-8188) tiering question
  wants. But the same tier then carries dead weight that hurts read density, so the
  benefit is partly self-cancelling.
- "Store a marker instead of the data" and "a marker is as toxic as the data" are both
  right in their own frame: the *commitment* only needs one bit, but the *flat state* needs
  a real record at a real key either way, because §2 requires the zero to be explicit.

---

## Scorecard

| Axis | (A) keep zero leaf | (B) delete on zeroization |
|---|---|---|
| Migration determinism (§1) | ✗ forces two semantics, switching at the swap block | ✓ conversion ≡ replay, as EIP-8347 already requires |
| Root = f(state) (§2) | ✗ history-dependent; explicit zeros in every flat-state layer; fixtures can't express it | ✓ verifiable from a state dump |
| Trie / prover complexity (§3) | ✓ no merge logic | ~ one bounded one-level merge; inverse of insert's existing bit-slicing; simpler than MPT delete |
| State size (§4) | ✗ est. 3–50 GB/yr of retained garbage (unmeasured) | ✓ on paper — partly illusory, see §6 |
| Proof size / depth (§5) | ~ +0.4 bits at +30% leaves | ~ identical |
| Churn pricing / devex (§6) | ✓ state creation charged once ever | ✗ ~98k gas per re-creation vs 4,800 refund; pushes devs to `1↔2` |
| Future expiry (§7) | ~ gives a distinction no live design needs | ✓ recoverable at a later fork; (A) is not |
| EVM edges (§8) | ✗ cleared accounts leave zeroed headers; 7610 interaction | ~ 7610 interaction too; both need explicit rules |
| Storage layer (§9) | ~ monotone key set | ~ tombstones, but reclaims |

## Recommendation (adopted)

**(B) — delete on zeroization — was adopted, and EIP-8297's "Zero Values and Deletion"
section has been revised accordingly.** The churn-pricing problem is tracked as a gas-EIP
item ([A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md)) rather than a
reason to keep the leaves — this remains open and is not resolved by the trie decision.

The reasoning that carried the decision:

1. EIP-8347 **already normatively requires** (B) for the entire pre-swap period, and that
   requirement is forced by conversion/replay determinism. (A) therefore does not buy one
   simple rule; it buys two rules with a discontinuity at the swap (§1).
2. (A) makes the state root a function of history rather than state, which costs explicit
   zero retention in every client's flat state, breaks state-dump-based verification, and
   is **not expressible in the test fixture format** (§2). These costs are permanent, not
   migration-scoped.
3. The original justification — multi-tree epoch expiry — is confirmed dead by its own
   author, and the live expiry family (7736-style stubs, PBT's own subtree pruning) does
   not need the distinction (§*provenance*).
4. (A)'s complexity saving is one bounded operation that is the inverse of machinery
   insertion already requires, and strictly simpler than the MPT deletion every client
   ships today (§3).
5. (B) is the reversible choice: adding the three-state distinction later is a normal fork
   change, whereas removing accumulated zero leaves later requires a second migration
   event (§7).

**The strongest counter-argument, stated honestly, and still live:** under 8037-era
state-creation pricing (~98k gas), (B) plus a 4,800-gas clear refund makes clearing
irrational, so (B) may reclaim far less state than §4 suggests while imposing a real tax
and a real devex regression on `0→1→0→1` patterns. **This did not block the trie
decision, and it is not resolved by it** — it belongs in
[A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md) as an explicit requirement,
with the state-gas-refill and per-account-HWM options in §6 as the starting candidates.

**Specified alongside the decision, per the now-current EIP-8297 text** (see
[02-tree-structure.md](02-tree-structure.md#zero-values-and-deletion)):

- `account_has_storage` / EIP-7610 in representation-independent terms ("any non-zero
  value") — closes [execution-specs#3253](https://github.com/ethereum/execution-specs/issues/3253).
- Account-level deletion scope: header stem leaves and storage leaves, explicitly.
- **Code-leaf deletion is reference-counted, not deferred:** `CODE_ZONE` leaves are
  removed on account/code-hash change **only if no resulting-state account shares the
  same `code_hash`**, and persist otherwise. This is now normative — an earlier version
  of this file (and the roadmap) treated code refcounting as future/deferred work; the
  published EIP specifies it directly, and it applies to *all* code chunks now that code
  is uniformly content-addressed (see
  [05-design-evolution.md](05-design-evolution.md)).
- That intra-transaction `0 → x → 0` remains a same-tx state-gas refill (EIP-8037
  behaviour), independent of the trie rule.

## What to measure before freezing

§4 and §6 are empirical, and the measurements are cheap relative to the decision:

1. **Gross clear rate.** `SSTORE` non-zero→zero events per day on mainnet, from state
   diffs or a live tracer. Converts §4's order-of-magnitude range into a number.
2. **Re-creation rate.** Of slots cleared in block `h`, the fraction written non-zero
   again within 1 / 10³ / 10⁵ blocks. This is *the* number separating "churn, so (A)'s
   pricing argument dominates" from "genuine cleanup, so (B) reclaims real space".
   Note that [EIP-1153](https://eips.ethereum.org/EIPS/eip-1153) `TSTORE` already moved
   the classic intra-transaction pattern (reentrancy locks) off storage, so the residual
   is narrower than the folklore suggests.
3. **Ever-written vs. live slot counts** over history, as the upper bound on what (A)
   would have retained had it always been in force. For calibration, the published
   state-dormancy figures (~80% of storage slots untouched for a year) bound the *dormant*
   set, not the *deleted* set — the two are routinely conflated.

## Sources

- [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) — PBT, § *Zero values and deletion*
  (normative).
- [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) — offline migration (published;
  originated as [PR #12006](https://github.com/ethereum/EIPs/pull/12006)), BAL-replay
  translation rules.
- [*State expiry EIP* note](https://notes.ethereum.org/@vbuterin/state_expiry_eip) — the
  origin of the zero-vs-absent rule ("check older trees first").
- [EIP-6800](https://eips.ethereum.org/EIPS/eip-6800) — Verkle, the leaf marker at bit 128.
- [EIP-7736](https://eips.ethereum.org/EIPS/eip-7736) — leaf-level expiry via retained
  stem + keepsake commitment; portable to binary trees.
- [EIP-8037](https://eips.ethereum.org/EIPS/eip-8037) — state-gas,
  `STATE_BYTES_PER_STORAGE_SET = 64`, `CPSB = 1530`, same-transaction LIFO refills.
- [EIP-3529](https://eips.ethereum.org/EIPS/eip-3529) — `SSTORE_CLEARS_SCHEDULE = 4800`,
  the 20% refund cap, and the break-even reasoning reused in §6.
- [EIP-7778](https://eips.ethereum.org/EIPS/eip-7778) — refunds excluded from block-gas
  accounting.
- [EIP-8032](https://eips.ethereum.org/EIPS/eip-8032) — per-account `storage_count`
  precedent for the HWM idea; [EIP-8188](https://eips.ethereum.org/EIPS/eip-8188) —
  precedent for widening the leaf/header.
- [execution-specs#3254](https://github.com/ethereum/execution-specs/issues/3254),
  [#3253](https://github.com/ethereum/execution-specs/issues/3253),
  [#3246](https://github.com/ethereum/execution-specs/pull/3246) — the implementation
  divergence and the fixture-conformance consequence.
