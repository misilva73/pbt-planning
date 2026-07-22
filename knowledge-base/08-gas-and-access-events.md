# 08 — Gas & Access Events (EIP-4762)

> **Status: starting point, not final.** [EIP-4762](https://eips.ethereum.org/EIPS/eip-4762)
> ("Statelessness gas cost changes") was written for the **Verkle** fork. PBT
> (EIP-8297) **adopts its access-event / gas framework** — PR #11978 adds `4762` to
> EIP-8297's `requires:` — but with modifications, and the numeric constants below are
> **not yet recalibrated** for PBT. Treat this file as the baseline the PBT gas model
> starts from, not a pinned spec. See [03-key-derivation.md](03-key-derivation.md#L138)
> (§ Access events) and [06-open-questions.md](06-open-questions.md) for the PBT deltas.

## What this EIP does, in one paragraph

EIP-4762 re-prices state access so gas reflects **the cost of building a witness**
rather than the cost of a database read. Every state touch is modelled as an **access
event** `(address, sub_key, leaf_key)`; the first touch of a *branch* (stem/subtree) and
the first touch of a *leaf* (chunk) are each charged once per transaction, then cached
warm. Writes add further charges, including a large one-time charge for filling a
previously-empty slot. In exchange, several Berlin-era costs are removed (per-byte code
cost, EIP-2200 `SSTORE` costs, value-bearing `CALL` surcharge). It also **requires
clients to change their DB layout** (store a whole stem's 256 leaves contiguously) so
that the newly-cheap "same-stem" accesses are not a DoS vector.

Status: **Draft**, Standards Track: Core. Authors: Guillaume Ballet (@gballet), Vitalik
Buterin (@vbuterin), Dankrad Feist (@dankrad), Ignacio Hagopian (@jsign), Tanishq Jasoria
(@tanishqjasoria), Gajinder Singh (@g11tech). Created 2022-02-03.

## Access events

Reading state emits one or more access events `(address, sub_key, leaf_key)` naming what
was touched. `sub_key` selects the stem/subtree (in PBT terms, the tree position);
`leaf_key` selects the leaf within it (the sub-index).

**Account headers** — an access event `(address, 0, BASIC_DATA_LEAF_KEY)` fires when:

- a non-precompile / non-system contract is the target of `*CALL`, `CALLCODE`,
  `SELFDESTRUCT`, `EXTCODESIZE`, or `EXTCODECOPY`;
- a non-precompile / non-system contract is the target of a contract creation whose
  initcode begins executing;
- any address is the target of `BALANCE`;
- a deployed contract calls `CODECOPY`.

Extra rules:
- A **value-bearing** `*CALL` / `CALLCODE` / `SELFDESTRUCT` (nonzero wei) also emits
  `(caller, 0, BASIC_DATA_LEAF_KEY)` — even if the callee is a precompile/system contract.
- Callee **existence** is checked by testing for an extension-and-suffix tree at the
  stem, *not* via `CODEHASH_LEAF_KEY`.
- `EXTCODEHASH` emits `(address, 0, CODEHASH_LEAF_KEY)` (precompiles/system contracts
  excluded — their hashes are client-known).
- Contract creation emits both `(contract_address, 0, BASIC_DATA_LEAF_KEY)` and
  `(contract_address, 0, CODEHASH_LEAF_KEY)`.

**Storage** — `SLOAD` / `SSTORE` on `(address, key)` emit `(address, tree_key, sub_key)`
where `tree_key, sub_key = get_storage_slot_tree_keys(key)`.

```python
def get_storage_slot_tree_keys(storage_key: int) -> [int, int]:
    if storage_key < (CODE_OFFSET - HEADER_STORAGE_OFFSET):   # < 64 -> header stem
        pos = HEADER_STORAGE_OFFSET + storage_key
    else:
        pos = MAIN_STORAGE_OFFSET + storage_key
    return (pos // 256, pos % 256)
```

> **PBT delta:** PBT drops `MAIN_STORAGE_OFFSET` entirely — overflow storage is
> separated by the `0xFF` **storage zone** and per-account bucket instead of a numeric
> offset (see [03-key-derivation.md](03-key-derivation.md#L107) and
> [05-design-evolution.md](05-design-evolution.md)). The header split at 64 is preserved.

**Code** — "chunk `chunk_id` is accessed" means an event
`(address, (chunk_id + 128) // 256, (chunk_id + 128) % 256)`. Chunk access is charged:

- At each EVM step with `PC < len(code)`, chunk `PC // CHUNK_SIZE` of the callee is
  accessed. Corner cases: a `JUMP`/taken-`JUMPI` destination counts as accessed even if
  it's inside pushdata or not a `JUMPDEST`; an untaken `JUMPI` dest does not; a dest is
  not accessed if execution can't afford the `JUMP`, if `dest >= len(code)`, or for
  `PC = len(code)` (walking off the end).
- A `PUSH{n}` accesses all chunks `(PC // CHUNK_SIZE) .. ((PC + n) // CHUNK_SIZE)`.
- A nonzero-size `CODECOPY` / `EXTCODECOPY` of bytes `x..y` accesses chunks
  `(x // CHUNK_SIZE) .. (min(y, code_size - 1) // CHUNK_SIZE)`.
- `CODESIZE`, `EXTCODESIZE`, `EXTCODEHASH` access **no** chunks.
- Contract creation accesses chunks `0 .. (len(code)+30)//31`.

> **PBT delta:** overflow code chunks (`chunk_id ≥ 128`) are **content-addressed and
> shared** between identical-bytecode contracts, so their access events MUST be keyed by
> the `(zone, tree_position, sub-index)` tree-key — **not** `(address, chunk)` — so a
> shared chunk is charged once per block and appears once in the witness. Header chunks
> (0..127) stay per-account. See [03-key-derivation.md](03-key-derivation.md#L138).

## Write events

A write event `(address, sub_key, leaf_key)` is always **also** an access event (writes
⊆ accesses).

- **Headers:** a nonzero-value `CALL` / `CALLCODE` / `SELFDESTRUCT` writes
  `(caller, 0, BASIC_DATA_LEAF_KEY)` and `(callee, 0, BASIC_DATA_LEAF_KEY)`; if the
  callee account doesn't exist, also `(callee, 0, CODEHASH_LEAF_KEY)`. Contract creation
  writes `(contract_address, 0, BASIC_DATA_LEAF_KEY)` and `(…, 0, CODEHASH_LEAF_KEY)`.
- **Storage:** `SSTORE` writes `(address, tree_key, sub_key)`.
- **Code:** creation writes chunks `i in 0 .. (len(code)+30)//31` at
  `((CODE_OFFSET + i) // W, (CODE_OFFSET + i) % W)` (`W = VERKLE_NODE_WIDTH = 256`). No
  warm cost is charged for code accesses — no code access list existed before this EIP.

## Witness gas costs

**Removed** (Berlin baseline): the nonzero-value `CALL` surcharge; EIP-2200 `SSTORE`
costs except `SLOAD_GAS`; the 200-gas-per-byte contract code cost; value-bearing
`CALLCODE` costs. **Reduced:** `CREATE`/`CREATE2` → 1000.

| Constant | Value | Charged when… |
|----------|-------|---------------|
| `WITNESS_BRANCH_COST` | 1900 | first access of a `(address, sub_key)` subtree |
| `WITNESS_CHUNK_COST` | 200 | first access of a `(address, sub_key, leaf_key)` leaf |
| `SUBTREE_EDIT_COST` | 3000 | first *write* to a subtree |
| `CHUNK_EDIT_COST` | 500 | first *write* to a leaf |
| `CHUNK_FILL_COST` | 6200 | write to a leaf that previously held `None` |

A transaction maintains four sets — `accessed_subtrees`, `accessed_leaves`,
`edited_subtrees`, `edited_leaves` — and charges each cost only on first insertion:

```
on access(address, sub_key, leaf_key):           # skip if it's a Transaction access event
    if (address, sub_key) not in accessed_subtrees:  charge WITNESS_BRANCH_COST; add it
    if leaf_key is not None and
       (address, sub_key, leaf_key) not in accessed_leaves:  charge WITNESS_CHUNK_COST; add it

on write(address, sub_key, leaf_key):             # skip if it's a Transaction write event
    if (address, sub_key) not in edited_subtrees:  charge SUBTREE_EDIT_COST; add it
    if leaf_key is not None and
       (address, sub_key, leaf_key) not in edited_leaves:  charge CHUNK_EDIT_COST; add it
    if state at (address, sub_key, leaf_key) was None:      charge CHUNK_FILL_COST
```

Key semantics (matches PBT — see [02-tree-structure.md](02-tree-structure.md#L148)
"Zero values and deletion"): a tree key can only be written to `0 .. 2**256-1`, and
**`0` is distinct from `None`**. Once a key goes `None → not-None` it never returns to
`None` — hence the one-time `CHUNK_FILL_COST`, and hence there is no delete logic.

Add-to-witness only if gas covers the event cost; otherwise consume all remaining gas.
The `1/64th` gas reservation of `CREATE*` / `*CALL` is checked **after** witness charges
for calls, but subtracted **before** witness charges for creates.

## Transaction-level, block-level, and system contracts

- **Transaction** access events: `(tx.origin/tx.target, 0, {BASIC_DATA,CODEHASH}_LEAF_KEY)`.
  Transaction write events: `(tx.origin, 0, BASIC_DATA_LEAF_KEY)`, plus
  `(tx.target, 0, BASIC_DATA_LEAF_KEY)` if value is nonzero. Transaction-level events are
  **exempt** from the per-event charges above (the `skip` branches).
- **Block level:** precompiles, system-contract accounts (and slots touched in a system
  call), the **coinbase**, and **withdrawal** accounts are **not warm** at transaction start.
- **System contracts:** when calling a system contract via a system call or to resolve a
  precompile/opcode, its code chunks and header accesses do **not** enter the witness
  (client-cached); any other accesses and **all** writes still do. Precompile/opcode
  resolution is charged witness costs, but a system call is not.
- **Account abstraction:** left `TODO` in the EIP (7702 vs 3074 undecided at time of writing).

## Rationale & the DB-layout requirement

`WITNESS_CHUNK_COST` targets ~6.25 gas/byte for chunks; `WITNESS_BRANCH_COST` ~13.2
gas/byte on an average 144-byte branch (~2.5 gas/byte worst case under adversarial
proof-length grinding). Net effects vs Berlin: **+200 gas per 31-byte code chunk**
(est. +6–12% average gas); adjacent same-group storage slots drop **2100 → 200** after
the first; header storage slots 0..63 drop to 200 including the first.

> **Empirical check (Verkle-era):** an analysis of ~1M mainnet txs (Jun 2024, via a Geth
> live-tracer over PC traces) measured code-access gas overhead averaging **~32.6% of the
> current tx receipt gas** (95% of txs under 800k gas). It also found a **32-byte** code
> chunker used ≈1.5% less total gas than the spec's **31-byte** chunker while adding far
> less contract-size overhead (+0.6% vs +3.7%), and suggests mitigations (lower per-chunk
> charge, a free-chunk allowance, multi-dimensional gas). Design-agnostic evidence for
> PBT's witness-gas recalibration and the code-chunk cost — see [07-sources.md](07-sources.md) #7.

**Security / DoS:** making same-stem accesses cheap is only safe if the DB matches.
The EIP requires clients to (1) **separate the commitment tree from data storage** — no
tree traversal to find a state element — and (2) store each stem's 256 × 32-byte leaves
**contiguously** (an ~8 kB blob), so reading many leaves of one stem is one seek. PBT's
own DB/witness recalibration builds on exactly this requirement.

## PBT deltas at a glance (why this is a starting point, not the final design)

1. **Content-addressed code keying** — shared overflow chunks are charged/witnessed by
   tree-key, not `(address, chunk)`. *(this file, § Code)*
2. **Branch-cost recalibration** — `WITNESS_BRANCH_COST = 1900` was calibrated for
   shallow Verkle branches; PBT's branches are deeper, so all witness gas constants MUST
   be recalibrated. **Values not yet fixed in the draft.**
   *(see [06-open-questions.md](06-open-questions.md))*
3. **No `MAIN_STORAGE_OFFSET`** — the `0xFF` storage zone + per-account bucket replace the
   numeric offset. *(see [03-key-derivation.md](03-key-derivation.md#L107))*

See [07-sources.md](07-sources.md) to re-fetch. The published EIP text (allowed host
`eips.ethereum.org`) is authoritative for the Verkle-era framework; PBT's adaptations
live in EIP-8297 / PR #11978.
