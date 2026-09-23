# 12 — Testing Inventory: Planned vs. Implemented

> **Status: snapshot of a moving target, verified 2026-09-03.** This file inventories the
> PBT and migration **test surface**: what the roadmap plans, what actually exists today,
> and where the gaps are. It is organised by the four things under test — the **trie**
> itself, the **EVM/state-transition rules** around it, the **converter**, and **BAL
> replay** — plus the cross-cutting **swap/lifecycle** layer that belongs to none of them
> alone.
>
> Sources enumerated directly: `pbt-planning/roadmap` (7 Tests-workstream deliverables plus
> test scope in 5 client rows) · `execution-specs@projects/binary-trie` at `09d2088`
> (2026-08-13, the branch tip) · `CPerezz/pbt-devnet` `main` + `migration-m1-tooling` ·
> `CPerezz/go-ethereum@pbt` · `state-project-status/meeting-notes/2026-08` (13 meetings).
>
> **Counts are test-function counts** (`def test_*` / `func Test*`); parametrised cases
> expand beyond them — the 56 EIP-8297 filler functions render as **70 blockchain
> fixtures**. Pass/fail claims (geth green, Erigon 67/70) are the clients' own reports,
> not re-run here.

> **Addendum — 2026-09-17 sync (counts not re-enumerated).** The 2026-09-17 source sweep
> ([07-sources.md](07-sources.md)) changed two things this file asserts, without changing any
> test count in `execution-specs` — whose branch is **still at `09d2088` (2026-08-13)**, the
> same tip this inventory was built against, so sections 1 and 2 remain accurate as written.
> What moved is the **devnet** column: (a) the tree-at-genesis devnet is now **seven nodes
> across four implementations**, not six across three — Nethermind joined 2026-09-14; and (b)
> **row 5's "one EL" is no longer true** — the migration devnet runs **four clients** through
> the swap (geth via BAL-replay, Erigon folding both commitment domains, Besu swapping the
> trie per header, Nethermind mirroring flat state), with a judge scoring fork block, straddle
> rewind, heal deadlines, orphan cleanup and shadow-root agreement per node. Rows **3 and 4
> are unchanged**: still zero converter and BAL-replay tests in the reference implementation,
> still one implementation of each, and the migration devnet still runs on **trivial state**
> with M1 (2026-08-27) as the last accepted gate — so "single-source" stands. The devnet's
> per-client evidence contracts (`internal/migmon/registry.go`) mean the four clients are
> **not** equally attested: Besu exposes no `debug_migrationProgress` or shadow-root RPC, so
> its migration evidence is the thinnest of the four. Re-enumerate the counts at the next
> sync if `execution-specs` moves.

> **Update — 2026-09-23: Hive artifact conformance now exists in an open draft.**
> [Hive PR #1614](https://github.com/ethereum/hive/pull/1614), reviewed at `b8703d2`, adds `ethereum/pbt-artifacts` for
> EIP-8347 converter outputs and snapshot/preimage consumers. This supersedes the
> September 18 blanket “no Hive” finding and the September 17 artifact single-source
> claim. It does **not** execute the 70 EIP-8297 blockchain fixtures or test BAL replay.
> The earlier EEST fixture-release/workflow gap remains a separate work item.
> Existing client/reference test-function counts below were not re-enumerated in this
> targeted update; the Hive manifest contains **58 mutation cases**, counted separately.

## The one-line summary

The tree and execution rules have **224 reference test functions** in the earlier
inventory. Migration artifacts now have a **shared Hive conformance suite in draft**:
58 mutation cases, valid-pair gates and producer-agreement checks. The PR reports two
matching preimage producers and two consumers, but only one snapshot producer.
BAL-replay conformance vectors, mainnet-scale verification and shared execution of
the EIP-8297 blockchain fixtures remain open.

## Coverage matrix

| Component | Roadmap | execution-specs | pbt-devnet | geth@pbt | Verdict |
|---|---|---|---|---|---|
| **1 · The trie itself**<br>merkelization, key derivation, encoding, canonical form | [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md), [A-T1](../roadmap/deliverables/A-T1-eest-test-suite-port.md) (A-T3, A-T4 downstream) | **96** + a JSON vector file | 2 pins (genesis root, root agreement) | 60 (incl. 4 fuzz targets) | **Strong** — roots stay provisional until `H` is pinned |
| **2 · EVM rules around PBT**<br>state transition, code chunking, deletion, delegation, gas events | [A-T1](../roadmap/deliverables/A-T1-eest-test-suite-port.md), [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md), [A-C3](../roadmap/deliverables/A-C3-multiclient-pbt-genesis-devnets.md), A-T4 | **72** unit + **56** fillers (70 fixtures) | 6 scenarios · 11 workloads · 8 oracles | 57 | **Strong** — gas costs still parameters; 3 fixtures pin provider behaviour |
| **3 · The converter**<br>scan → preimage check → key derivation → bottom-up root → artifacts | [B-T1](../roadmap/deliverables/B-T1-conversion-replay-vectors.md), [B-T3](../roadmap/deliverables/B-T3-dual-check-verification-scale.md), B-C1, B-C4, A-C4 | **0** | **0** — M1 ran on empty state | 34 (incl. 2 benchmarks) | **Shared artifact suite in draft** — Hive #1614 adds 58 mutations; two preimage producers, one snapshot producer (see below) |
| **4 · BAL replay**<br>translation rules, follower, catch-up, cursor, reorg | [B-T1](../roadmap/deliverables/B-T1-conversion-replay-vectors.md), B-C2, [B-T2](../roadmap/deliverables/B-T2-full-cycle-devnet-swap.md) | **0** | C1–C8 + F1–F3 (+31 harness unit tests) | 74 | **Single-source** — well tested in one client, unspecified as conformance |
| **5 · Swap & lifecycle**<br>`b*`, activation, both-trees window, finality close | [B-T2](../roadmap/deliverables/B-T2-full-cycle-devnet-swap.md), [B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md), B-C5, B-C6, B-C7 | 0 | 7-stage ladder (S1 → R3, accepted 2026-08-27) | 8 (catalyst lifecycle) | **Seeded** — trivial state, **four ELs since 2026-09**, still no convert/distribute step |

---

## 1 · The trie itself

EIP-8297's two node types, prefix-compressed canonical form, and the zone/stem/sub-index
embedding of Ethereum state into keys ([02-tree-structure.md](02-tree-structure.md),
[03-key-derivation.md](03-key-derivation.md)). The layer with the most tests and the fewest
surprises — and the one whose roots are all provisional until the hash function `H` is
chosen.

### Planned

| Deliverable | Window | What it ships |
|---|---|---|
| [A-T2](../roadmap/deliverables/A-T2-tree-key-derivation-vectors.md) | 2026-07 → 2026-12 · *in flight* | Canonical machine-checkable vectors in five families: **key derivation** (`BASIC_DATA`, `CODE_HASH_LEAF_KEY`, the EIP-7702 `DELEGATION_LEAF_KEY`, header-resident slot, storage-zone slot, code chunk), **zone/stem embedding** constants, **tree operations** (insert, leaf split, branch split, deletion), **encoding** (`encode_bit_prefix`, `LEAF_TAG`/`BRANCH_TAG` preimages), and **rejection** cases (prefix-freedom, `MAX_KEY_LENGTH`). Structure-only now; a hash-parameterised layer drops digests in once `H` lands. |
| [A-T1](../roadmap/deliverables/A-T1-eest-test-suite-port.md) | 2026-08 → 2027-01 · *in flight* | EEST fillers emitting PBT key/value state and a PBT root instead of an MPT root, with key-embedding hooks and a documented, stable fixture format. |
| [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md) | 2027-01 → 2027-06 | Canonical-tree invariants asserted **across clients**: two-non-empty-children branches, one valid prefix-compressed tree per state. |
| [A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md) | 2027-07 → 2027-12 | Insert/update and merkelization throughput, observed **branch-depth distribution**, and prefix-compression behaviour on grinded/pathological key sets, across the EIP-7870 hardware tiers. |

### Implemented — `execution-specs@projects/binary-trie`

**`tests/binary_trie/test_trie.py` — 42 tests.** The tree in isolation: bit handling,
canonical form, deletion, golden preimages, differential agreement against a second
reference implementation.

| Test | What it pins |
|---|---|
| `test_bytes_to_bit_list_is_msb_first` | Bit expansion order is MSB-first |
| `test_encode_bit_prefix_layout` | 2-byte big-endian count + MSB-first padded bits |
| `test_encode_bit_prefix_rejects_unrepresentable_counts` | Counts past the 2-byte field are refused |
| `test_encode_bit_prefix_counts_trailing_zero_bits` | Trailing zero bits still count toward the length |
| `test_empty_trie_root_is_all_zeros` | Empty tree commits to the zero root |
| `test_trie_set_and_get` | Basic set/get round trip |
| `test_trie_set_rejects_malformed_inputs` | Malformed keys/values rejected at set time |
| `test_copy_trie_is_independent` | A copied trie shares no mutable state |
| `test_single_key_is_a_leaf_at_the_root` | One key means a leaf, not a branch chain |
| `test_keys_sharing_a_stem_split_under_one_branch` | Shared prefix produces exactly one branch |
| `test_first_bit_divergence_has_empty_prefix` | Divergence at bit 0 gives the root an empty prefix |
| `test_canonical_form_example` | The EIP's worked canonical-form example |
| `test_binarize_builds_relative_prefixes_and_full_key_leaves` | Branches carry relative prefixes; leaves carry full keys |
| `test_zero_value_is_not_absence` | A stored zero-*byte* value ≠ an absent key |
| `test_prefix_key_violation_is_rejected` | One key being a prefix of another is invalid |
| `test_prefix_key_violation_in_mid_byte_group_is_rejected` | Same violation caught mid-byte |
| `test_root_matches_reference_implementation` | Root agrees with the independent reference |
| `test_root_matches_reference_with_variable_length_keys` | Same, with mixed key lengths |
| `test_root_is_insertion_order_independent` | One key/value set, one root, any insertion order |
| `test_reference_roots_are_insertion_order_independent` | The reference has the same property |
| `test_setting_none_removes_key_and_restores_prior_root` | Delete returns the tree to its earlier root |
| `test_setting_none_for_absent_key_is_a_no_op` | Deleting nothing changes nothing |
| `test_delete_collapses_branches_to_canonical_form` | Deletion re-collapses branches — the MPT edge case flagged as untested on 2026-08-19 |
| `test_delete_matches_reference_and_rebuild` | Delete agrees with both reference and full rebuild |
| `test_deleting_every_key_recommits_to_the_empty_root` | Emptying the tree returns the zero root |
| `test_delete_then_reinsert_roundtrips` | Delete + reinsert is identity |
| `test_overwriting_a_value_recommits_to_the_final_value` | Last write wins at root level |
| `test_remove_subtree_removes_exactly_the_matching_keys` | Subtree removal is prefix-exact |
| `test_remove_subtree_of_an_absent_prefix_does_nothing` | Removing an absent prefix is a no-op |
| `test_leaf_preimage_golden_vector` | Pinned `LEAF_TAG` preimage bytes |
| `test_branch_preimage_golden_vector` | Pinned `BRANCH_TAG` preimage bytes |
| `test_fixed_trie_root_is_pinned` | A fixed corpus's root frozen as a regression pin |
| `test_leaf_and_branch_tags_are_domain_separated` | Leaf and branch hashing cannot collide |
| `test_max_length_keys_diverging_at_last_bit` | 8192-bit keys differing only in the final bit |
| `test_trie_set_rejects_zero_and_thirty_three_byte_values` | Value width bounds enforced |
| `test_root_is_idempotent_and_does_not_mutate` | Computing the root twice is safe |
| `test_prefix_violation_only_fails_at_root_time` | Where the prefix check fires is pinned |
| `test_canonical_structure_holds_for_fixed_trie` | Structural assertion over the fixed corpus |
| `test_canonical_structure_holds_for_random_corpora` | Same assertion over random corpora |
| `test_deep_thermometer_chain_matches_reference` | Pathological deep chain agrees with the reference |
| `test_deep_chain_past_recursion_limit_is_an_implementation_limit` | Names recursion depth as an implementation, not spec, limit |
| `test_larger_random_corpora_match_reference` | Three seeds of large random corpora vs the reference |

**`tests/binary_trie/test_embedding.py` — 50 tests.** Key derivation and code chunking —
the A-T2 surface, already largely built. Note `test_key_hash_is_blake3`: the hash choice is
asserted here **as fact**.

| Test | What it pins |
|---|---|
| `test_address20_to_address32_prepends_zeros` | 20→32-byte address widening |
| `test_empty_code_hash_is_keccak_of_empty` | `code_hash` stays keccak, not `H` |
| `test_key_hash_is_blake3` | Pins `key_hash` to BLAKE3 — **the undecided parameter** |
| `test_get_tree_key_concatenates_its_three_parts` | Key = zone ‖ stem ‖ sub-index |
| `test_header_sub_index_wider_than_one_byte_is_rejected` | Header sub-index width bound |
| `test_header_key_vectors` | The EIP's worked header-key examples |
| `test_delegation_key_vector` | 7702 delegation leaf at sub-index `0x02` |
| `test_delegation_leaf_value_layout` | `0xef0100 ‖ target ‖ 0x00 * 9` |
| `test_storage_slot_in_header_vector` | Header-resident slot key |
| `test_storage_slot_overflow_vector` | Storage-zone (66-byte) key |
| `test_storage_slot_boundary_is_64` | `HEADER_STORAGE_OFFSET` boundary |
| `test_storage_slot_key_matrix` | Parametrised sweep across slot values |
| `test_storage_group_zero_never_uses_low_sub_indices` | The group-0 exception (slots 64..255 only) |
| `test_storage_tree_index_is_a_32_byte_big_endian_suffix` | Tree-index encoding |
| `test_code_chunk_vector` | Code chunk 300's key |
| `test_code_chunk_second_group_vector` | Chunk key in the second group |
| `test_code_keys_are_content_addressed` | Code keys derive from `code_hash`, not address |
| `test_code_chunk_key_matrix` | Parametrised chunk-id sweep |
| `test_code_group_rollover_changes_the_stem` | Group rollover moves the stem |
| `test_max_code_size_chunk_keys` | Keys at the EIP-7954 ceiling |
| `test_key_derivations_assert_their_own_key_length` | Per-zone length asserts (34 / 66 bytes) |
| `test_chunkify_empty_code` | Empty code chunkifies to nothing |
| `test_chunkify_code_without_pushes_pads_to_31_bytes` | Padding rule |
| `test_chunkify_code_eip_example` | The EIP's worked chunking example |
| `test_chunkify_code_caps_leading_push_data_count_at_31` | Leading-push-data byte is capped |
| `test_chunkify_code_push_data_truncated_by_end_of_code` | Truncated trailing PUSH |
| `test_chunkify_push0_is_not_push_data` | `PUSH0` carries no data |
| `test_chunkify_push_data_overhanging_into_padding` | Push data running into the pad |
| `test_chunkify_push_ending_exactly_at_chunk_boundary` | Exact-boundary push |
| `test_chunkify_code_length_multiples_need_no_padding` | Exact multiples of 31 |
| `test_chunkify_all_push32_code_matches_reference_scanner` | All-`PUSH32` vs an independent scanner |
| `test_chunkify_push_data_containing_push_opcodes` | Push opcodes inside push data |
| `test_chunkify_consecutive_pushes_across_boundary` | Back-to-back pushes spanning chunks |
| `test_delegation_is_classified_by_code_never_by_hash` | Delegation detected from code bytes, not hash |
| `test_embed_account_reads_the_code_not_the_code_hash` | Embedding reads real code |
| `test_remove_account_takes_the_delegation_leaf` | Account deletion removes the delegation leaf |
| `test_chunkify_designator_shaped_code_still_chunks` | Designator-shaped *code* is ordinary code |
| `test_encode_basic_data_layout` | `BASIC_DATA` field packing |
| `test_encode_basic_data_rejects_balance_past_sixteen_bytes` | Balance field width bound |
| `test_encode_basic_data_maximum_fields` | All fields at maximum |
| `test_remove_account_restores_prior_root` | Delete/undelete symmetry |
| `test_remove_account_takes_header_and_storage_with_it` | Header + storage leaves go together |
| `test_remove_account_never_reaches_the_code_zone` | Deletion does not touch shared code |
| `test_remove_account_leaves_code_for_the_caller` | Code-zone reclamation is the caller's job |
| `test_remove_code_chunks_spares_the_header` | Chunk removal leaves the header alone |
| `test_all_zero_basic_data_is_absent_from_the_tree` | All-zero `BASIC_DATA` is absence |
| `test_emptying_basic_data_removes_its_leaf` | Zeroing the header leaf deletes it |
| `test_zero_code_chunks_are_absent_from_the_tree` | Zero chunks are absent (execution-specs #3305) |
| `test_remove_all_storage_keeps_the_account_and_its_code` | Clearing storage keeps the account |
| `test_embed_and_remove_storage_slot_roundtrip` | Slot embed/remove round trip |

**`tests/binary_trie/test_spec_constants.py` — 4 tests.** Guards against exactly the failure
A-T2's risk section names: constants drifting out from under generated vectors.

| Test | What it pins |
|---|---|
| `test_spec_constants_match_implementation` | EIP constant table vs the code |
| `test_spec_header_offset_invariant_holds` | `HEADER_STORAGE_OFFSET` / `HEADER_STORAGE_SLOTS` / `STEM_SUBTREE_WIDTH` relation |
| `test_delegation_constants_match_the_fork_that_produces_them` | Delegation constants tied to their fork |
| `test_spec_basic_data_offsets_match_encode_basic_data` | Field offsets vs the encoder |

**Vector files.** `tests/binary_trie/vectors/binary_trie_vectors.json` with a
`dump_vectors.py` generator; geth carries its own `trie/bintrie/testdata/eip8297_vectors.json`
plus `export_vectors.py`.

### Implemented — `geth@pbt`, `trie/bintrie/*_test.go` (60 tests)

Listed at file level: this is a second implementation of the surface the spec suite already
covers, so it is corroboration rather than new coverage. The fuzz targets and the model test
are the parts the spec suite does **not** have.

| File | n | What it covers |
|---|---|---|
| `vectors_test.go` | 6 | Runs the checked-in `eip8297_vectors.json` — the shared-vector consumption A-T2 asks for |
| `model_test.go` | 6 | Differential against a naive model implementation |
| `fuzz_test.go` | 4 | Fuzz targets over set/delete/root; **no equivalent in the spec suite** |
| `multiproof_test.go` | 6 | Proof construction and verification |
| `bits_test.go` | 6 | Bit-prefix encode/decode primitives |
| `decode_validation_test.go` | 6 | Malformed node decoding is refused |
| `partial_stem_test.go` | 6 | Partial-stem handling under splits |
| `delete_atomicity_test.go` | 4 | Deletion is all-or-nothing |
| `batch_test.go` | 3 | Batched commit equals sequential commit |
| `records_test.go` | 3 | Record encoding for the sorter |
| `assemble_test.go` | 2 | Bottom-up assembly from sorted leaves |
| `db_test.go` | 2 | Node persistence layer |
| `delegation_test.go` | 1 | Delegation leaf at the trie layer |
| `baseline_bench_test.go` | 5 | Throughput baselines — the seed of what A-T4 formalises |

### Where it stands

- **Implemented.** 96 unit tests plus checked-in vector files. Substantially covers A-T2's
  scope, generated from the reference implementation rather than published as a standalone
  cross-client vector set.
- **Watch.** The reference branch tip has not moved since **2026-08-13**, and two EIP-8297
  test PRs — [#3444](https://github.com/ethereum/execution-specs/pull/3444) (reorg-branch
  provider state) and [#3446](https://github.com/ethereum/execution-specs/pull/3446)
  (genesis commitment provider) — were **closed unmerged** on 2026-08-28. Test-suite
  momentum stalled while client work accelerated.
- **Blocked.** Every root-bearing vector is BLAKE3-shaped by accumulation: four clients use
  it, the devnet genesis pins roots computed with it, and `H` is formally undecided until
  end-2026. **Devnet root agreement is evidence about everything *except* `H`.** See
  [../open-questions.md](../open-questions.md#hash-function-selection--the-dominant-open-parameter).

---

## 2 · EVM & state-transition rules around PBT

The rules that changed when state moved into the tree: where code lives, when a leaf is
deleted ([10-zero-value-leaves-and-deletion.md](10-zero-value-leaves-and-deletion.md)), how
delegation is represented, what account deletion sweeps, and what the EVM must **not**
notice. Two independent claims are under test: that PBT is **execution-invisible**, and that
PBT's own **state-access accounting** is right
([08-gas-and-access-events.md](08-gas-and-access-events.md)).

### Planned

| Deliverable | Window | What it ships |
|---|---|---|
| [A-T1](../roadmap/deliverables/A-T1-eest-test-suite-port.md) | 2026-08 → 2027-01 · *in flight* | EEST state- and blockchain-test fillers emitting PBT state, plus **gas fixtures** for state-access and content-addressed code-chunk accounting — code events keyed by `(zone, tree_position, sub-index)`, shared across accounts with the same `code_hash`, charged once per block. Costs stay parameters until [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md) fixes them from benchmarks. |
| [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md) | 2027-01 → 2027-06 | Cross-client block-processing conformance on a shared PBT genesis, asserting identical roots after each block; **PBT-native sync tests** (a joining client converges to the serving client's root); sustained-agreement tracking toward the readiness gate. |
| [A-C3](../roadmap/deliverables/A-C3-multiclient-pbt-genesis-devnets.md) | 2027-02 → 2027-06 · *in flight, ~5 months early* | **EVM-invisibility validation**: `SLOAD`/`SSTORE` and `EXTCODEHASH` behave identically to MPT-era execution; `code_hash` stays `keccak256(bytecode)`. Plus a root-agreement harness that attributes divergence to a client. |
| [A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md) | 2027-07 → 2027-12 | Measured cost of exactly the operations A-S2 prices: cold/warm account and storage access, storage writes, per-chunk code access — shared overflow chunks reported separately from per-account ones. |
| *(KB test surface, unowned)* | Phase 1 | **Adversarial / structural-cost suites** (spam patterns, chunk floods). Named in [04-migration.md § Testing framework](04-migration.md#testing-framework-eest-coverage) and in **no deliverable**; Carlos noted on 2026-08-03 that adversarial and benchmark edge cases were deliberately excluded from the 190-test devnet baseline. |

### Implemented — EIP-8297 blockchain fillers (56 functions → 70 fixtures)

In `tests/binary_tree/eip8297_partitioned_binary_tree/`. These are the fixtures clients
consume. geth reports the suite **fully green**
([go-ethereum#13](https://github.com/CPerezz/go-ethereum/pull/13)); Erigon reports **67 of
70** — the three failures are marked below.

**`test_account_lifecycle.py` — 9**

| Test | What it covers |
|---|---|
| `test_fund_fresh_eoa_via_value_transfer` | New header stem materialises on funding |
| `test_create_deploys_code_and_storage` | `CREATE` writes code-zone and storage leaves |
| `test_contract_creating_transaction` | Creation via a plain contract-creating tx |
| `test_selfdestruct_same_transaction_leaves_no_account` | Same-tx destruct leaves nothing behind |
| `test_selfdestruct_survives_and_sweeps_balance` | Post-6780 destruct sweeps balance only |
| `test_create_then_revert_leaves_child_nonexistent` | Reverted creation leaves no leaves |
| `test_empty_account_touch_not_materialized` | Touching an empty account writes nothing |
| `test_precompile_touch_and_value_transfer` | Precompile touches and transfers |
| `test_create2_recreate_with_different_code` | Redeploy at the same address with new code |

**`test_code_chunking.py` — 13**

| Test | What it covers |
|---|---|
| `test_deploy_and_execute_at_code_size` | Deploy and run at the code-size ceiling |
| `test_push_data_straddles_chunk_boundary` | Push data spanning two chunk leaves |
| `test_jump_into_pushdata_is_invalid` | Jump into push data still invalid under chunking |
| `test_jumpdest_at_chunk_boundary_is_valid` | `JUMPDEST` exactly on a boundary |
| `test_extcodecopy_full_and_partial_across_chunk_boundary` | `EXTCODECOPY` across chunks |
| `test_extcodecopy_past_end_zero_pads` | Reads past the end zero-pad |
| `test_extcodecopy_from_initcode_clones_chunked_code` | Copy out of initcode |
| `test_byte_identical_code_two_contracts_independent` | Identical code, independent accounts |
| `test_code_deposit_limit_via_create` | Deposit limit through `CREATE` |
| `test_initcode_size_limit_boundary` | Initcode size boundary |
| `test_code_ends_in_truncated_push` | Code ending mid-`PUSH` |
| `test_code_with_all_zero_chunk` | An all-zero chunk inside real code — the 2026-08-03 zeroisation decision |
| `test_delegated_eoa_executes_chunked_delegate` | Delegated EOA runs chunked target code |

**`test_storage_ops.py` — 10**

| Test | What it covers |
|---|---|
| `test_sstore_sload_round_trip` | Write/read round trip across the boundary |
| `test_sstore_zero_after_nonzero_same_tx` | Zeroing in the same tx — **Erigon fails** (pins provider behaviour) |
| `test_sstore_zero_across_transactions_or_blocks` | Zeroing later — **Erigon fails** (pins provider behaviour) |
| `test_sstore_overwrite_nonzero_value` | Overwrite with another non-zero |
| `test_sload_never_written_slot_returns_zero` | Absent leaf reads as zero |
| `test_storage_coexists_with_sizeable_code` | Storage plus large code on one account |
| `test_transient_storage_round_trip` | `TSTORE`/`TLOAD` touch no leaves |
| `test_storage_under_7702_delegation_lands_on_authority` | Delegated writes land on the authority |
| `test_two_accounts_same_slot_independent` | Same slot number, different accounts |
| `test_sstore_many_slots_header_and_overflow` | Header slots and storage-zone slots together |

**`test_multi_block.py` — 7**

| Test | What it covers |
|---|---|
| `test_contract_evolves_across_four_blocks` | State evolution over four blocks |
| `test_account_created_then_aged_selfdestruct_next_block` | Create, then destruct a block later |
| `test_withdrawals_credit_new_and_existing_accounts_across_blocks` | Withdrawal credits |
| `test_state_survives_empty_blocks_interleaved` | Empty blocks change nothing |
| `test_chain_with_no_transactions_at_all` | A chain that never transacts |
| `test_wrong_state_root_expectation_is_recorded_for_consumers` | Negative fixture for consumers |
| `test_consecutive_deploys_share_the_code_zone` | Consecutive deploys into one code zone (execution-specs #3316) |

**Remaining fillers — 17** (`test_code_sharing`, `test_delegation_lifecycle`,
`test_system_contracts`, `test_basic_data_values`, `test_tx_types`, `test_state_divergence`,
`test_state_root_smoke`)

| Test | What it covers |
|---|---|
| `test_shared_code_survives_sibling_same_tx_selfdestruct` | Shared chunks outlive one holder's destruct |
| `test_unshared_code_chunks_after_same_tx_selfdestruct` | Sole-holder chunks go |
| `test_shared_designator_survives_peer_redelegation` | Shared designator survives a peer re-delegating |
| `test_contract_hashing_to_the_delegation_marker_executes_as_code` | Marker-shaped code is code |
| `test_same_target_reauthorization_keeps_designator` | Re-auth to the same target is a no-op (execution-specs #3338) |
| `test_beacon_root_ring_buffer_across_blocks` | EIP-4788 ring buffer |
| `test_beacon_root_ring_buffer_collision_later_overwrites` | Ring-buffer collision |
| `test_history_contract_ring_buffer_across_blocks` | EIP-2935 ring buffer (execution-specs #3338) |
| `test_system_contract_and_user_contract_writes_coexist` | System and user writes together |
| `test_account_at_max_balance_field_transacts` | Max balance field |
| `test_sender_high_nonce_increments_correctly` | High nonce increment |
| `test_balance_field_round_trip_after_value_transfer` | Balance field round trip |
| `test_code_size_field_round_trip_after_create` | `code_size` round trip |
| `test_all_tx_types_write_storage` | Every tx envelope type writes storage |
| `test_genesis_codeless_account_with_storage_persists` | Codeless genesis account with storage |
| `test_create2_after_eip161_clear_of_storage_holding_account` | **Erigon fails** — the reference itself calls this an open consensus question |
| `test_storage_write_smoke` | Minimal root smoke test |

### Implemented — provider-level unit tests (72)

**`tests/binary_trie/test_state_pbt.py` — 60 tests.** How a block diff becomes tree writes.
The single largest test file in the project, and the one that encodes the deletion,
code-sharing and delegation semantics the client calls kept returning to.

| Test | What it pins |
|---|---|
| `test_empty_state_embeds_to_empty_root` | Empty state → zero root |
| `test_eoa_embeds_basic_data_and_code_hash_leaves` | An EOA's two header leaves |
| `test_contract_embeds_chunks_and_storage_slots` | A contract's chunk and slot leaves |
| `test_identical_bytecode_shares_chunk_leaves` | Dedup by `code_hash` |
| `test_empty_provider_commits_to_empty_root` | No-op provider is empty |
| `test_empty_diff_root_matches_direct_embedding` | Empty diff = direct embedding |
| `test_diff_root_matches_directly_built_post_state` | Diff application = rebuild |
| `test_deleting_the_only_account_empties_the_tree` | Last account out empties the tree |
| `test_zero_write_matches_never_written` | Zero write ≡ never written |
| `test_storage_clear_deletes_every_slot_leaf` | Clearing storage removes every leaf |
| `test_delegation_change_replaces_the_header_leaf` | Delegation swaps the header leaf |
| `test_deleting_a_sole_holder_removes_its_short_code` | Sole holder's short code goes |
| `test_deleting_the_last_holder_removes_its_code` | Last holder's code goes |
| `test_deleting_one_holder_keeps_shared_code` | Shared code stays |
| `test_deleting_an_account_removes_its_storage_leaves` | Deletion sweeps storage |
| `test_deleting_a_cleared_account_removes_its_storage_leaves` | Same after a prior clear |
| `test_storage_written_to_a_deleted_account_is_not_embedded` | Writes to a deleted account vanish |
| `test_delegating_an_account_reclaims_nothing` | Delegating frees no chunks |
| `test_random_diffs_match_flat_application_and_rebuild` | Randomised diffs vs a flat oracle |
| `test_header_root_matches_the_advanced_chain_state` | Provider root vs advanced chain state |
| `test_store_code_round_trips` | Code store/load round trip |
| `test_embedded_key_set_for_a_crafted_contract` | Exact key set for a crafted contract |
| `test_embedded_keys_never_use_a_reserved_zone_byte` | Reserved zone bytes stay unused |
| `test_embedded_state_root_is_pinned` | Regression pin on a full embedded root |
| `test_embedded_key_set_for_maximum_header_occupancy` | All 64 header slots occupied |
| `test_identical_code_shares_every_chunk_key` | Every chunk key shared, not just some |
| `test_chunk_values_are_distinct_across_the_code_group_boundary` | Values distinct across groups |
| `test_short_identical_code_shares_both_chunk_leaves` | Short shared code |
| `test_deleting_a_holder_keeps_chunks_a_survivor_still_holds` | Parametrised survivor cases |
| `test_deleting_the_last_holder_drops_every_group` | All groups dropped at once |
| `test_every_account_holds_exactly_one_of_the_two_leaves` | `code_hash` **xor** delegation |
| `test_delegating_replaces_the_code_hash_leaf` | Delegation removes `code_hash` |
| `test_undelegating_restores_the_empty_code_hash_leaf` | Clearing writes it back |
| `test_authorities_to_one_target_hold_separate_delegation_leaves` | Per-authority leaves |
| `test_shared_code_survives_until_the_last_holder_is_gone` | Refcount-by-existence semantics |
| `test_two_holders_deleted_in_one_block_drop_the_code_once` | Both holders in one block |
| `test_contract_deleted_then_recreated_with_different_code` | Delete + recreate with new code |
| `test_delegation_and_storage_writes_share_a_diff` | Delegation and storage in one diff |
| `test_group_exact_code_fills_group_zero_and_nothing_more` | Exactly-one-group code |
| `test_change_to_an_unresolvable_code_hash_is_a_pre_state_error` | Unresolvable `code_hash` errors |
| `test_absent_chunk_in_a_later_group_does_not_stall_removal` | Missing chunk doesn't block removal |
| `test_push_data_continuation_chunk_of_zero_bytes_is_present` | Zero continuation chunk is present |
| `test_account_has_storage_matches_the_embedded_leaf_set` | `account_has_storage` agrees with leaves |
| `test_deleting_an_unknown_address_is_a_no_op` | Deleting an unknown address does nothing |

Plus 16 helper-driven variants of the above (fresh/delegated fixtures, clone and flat-oracle
harnesses) counted in the 60.

**`tests/binary_trie/test_differential_mpt.py` — 7 tests.** The MPT-vs-PBT parity suite —
the closest thing to an *executable* statement of "the swap is commitment-only". Named
divergences are asserted **as** divergences.

| Test | What it pins |
|---|---|
| `test_account_delete_diverges_on_account_has_storage` | Deletion diverges where MPT depends on storage |
| `test_delete_then_recreate_resurrects_storage_only_under_mpt` | MPT-only storage resurrection |
| `test_account_delete_with_same_diff_storage_writes` | Delete plus storage writes in one diff |
| `test_all_zero_storage_changes_matches_never_written` | All-zero writes ≡ untouched, both trees |
| `test_code_changes_only_diff` | Code-only diffs agree |
| `test_zero_write_to_existing_slot_deletes_in_both` | Zero write deletes in both trees |
| `test_random_diff_sequences_keep_providers_equivalent` | Three seeds of random diff sequences |

**`test_fork_parity.py` + `test_block_execution.py` — 5 tests**

| Test | What it pins |
|---|---|
| `test_binary_tree_fork_matches_amsterdam_modulo_known_deltas` | The fork differs from Amsterdam **only** in allowed deltas — the machine-checked form of "commitment-only" |
| `test_binary_tree_fork_is_resolvable_by_tooling` | The fork resolves for EEST tooling |
| `test_binary_tree_fork_criteria_follows_amsterdam` | Fork ordering |
| `test_diff_lines_reports_lines_starting_with_diff_markers` | Harness self-check |
| `test_execute_block_rejects_a_tampered_state_root` | A tampered root is rejected |

### Implemented — `geth@pbt` (57 tests)

File level. Three groups have **no counterpart in the spec suite** and are worth lifting into
A-T3: reorg behaviour, stateless/witness execution, and datadir-scheme refusals.

| File | n | What it covers |
|---|---|---|
| `core/state/pbt_semantics_test.go` | 10 | `TestPBTHasStorage`, `PBTAccountDeletion`, `PBTCodeShrink`, `PBTDelegationSurvivesBalanceTouch`, `PBTCodeHashIsNotADelegation`, `PBTCodeSizePreserved`/`Writes`, `PBTPrefetcherWarmsOwners`, `PBTProofsVerify`, `PBTSharedCodeChunks` |
| `core/pbt_capabilities_test.go` | 8 | Stateless execution with and without writes, contract coinbase, incomplete-witness rejection, witness encoding survival, refusal of witness stats, datadir refusing a merkle reopen, self-validation on import |
| `core/pbt_reorg_test.go` + `pbt_reorg_code_test.go` | 3 + 4 | Rollback-unsupported reporting; reorg inside the window keeps flat state; past the window fails by name; code chunks dropped vs shared chunks kept; code across and past the persisted layer. **The unit-test origin of the devnet's `code-sole`/`code-shared` scenarios** ([go-ethereum#30](https://github.com/CPerezz/go-ethereum/pull/30)) |
| `core/pbt_genesis_pin_test.go` | 3 | `TestPBTGenesisPins` (one binary computes both tree kinds from one alloc), binary-tree selection, merkle-committing migration genesis |
| `core/pbt_chain_test.go`, `pbt_delegation_test.go`, `pbt_backend_parity_test.go`, `pbt_witness_test.go`, `pbt_scheme_test.go` | 3+3+2+1+3 | Chain-level integration, delegation, backend parity, witness, scheme selection |
| `core/state/pbt_destruct_test.go`, `pbt_flatstate_test.go`, `pbt_capabilities_test.go` | 1+2+1 | Destruct, flat state, capability gating |
| `core/vm/pbt_jump_table_test.go` | 4 | The jump table is unchanged — the EVM-invisibility claim at opcode level |
| `internal/ethapi/pbt_proof_test.go` | 1 | `eth_getProof` over the tree — the only RPC that reads it per key |
| `tests/pbt_prestate_test.go`, `eth/catalyst/pbt_test.go` | 2+1 | Fixture prestate loading, engine-API surface |
| `triedb/pathdb/pbt_reorg_flat_test.go`, `pbt_rollback_test.go`, `pbt_sentinel_test.go` | 1+2+2 | Flat-state reorg, rollback, sentinel |

### Implemented — `pbt-devnet@main`, the differential devnet

Not fixtures: a live network of **seven nodes across four implementations** (2×geth, 2×besu,
2×erigon, deliberately configured differently, plus 1×nethermind since 2026-09-14), the first
a never-partitioned bootnode, on an Amsterdam-at-genesis chain. Reorgs are forced every 15–30
blocks by cutting the p2p of whichever node proposes next; the doomed node rotates so reorgs
land on all four clients. **This is A-C3 and half of A-T3, running five months early.**

The design rationale is worth keeping: two instances of one binary agree by construction and
prove nothing; four implementations agreeing is evidence the specification is unambiguous
enough to implement four times.

**State-stranding scenarios — 6** (`cmd/pbtchaos`). Each partitions the network, waits until
the two sides genuinely disagree, sends transactions to the **minority's** RPC only, holds
for `DEPTH` blocks, heals, then asks every client the same question at a fixed height four
blocks below the majority's pre-heal tip — not `latest`, because a reorged-out tx returns to
the mempool and gets re-mined, so checking at head would measure pool re-broadcast speed
instead of the tree.

| Scenario | On the doomed branch | Must be true after the heal |
|---|---|---|
| `code-sole` | Unique bytecode, deployed once | No code on any client |
| `code-shared` | The same bytecode a surviving account already holds | The survivor's copy still reads back |
| `delegate` | 7702 delegations on fresh authorities | No code: back to a plain EOA |
| `account` | Fresh funded accounts | Zero balance everywhere |
| `storage-add` | Slots written below **and** above `HEADER_STORAGE_OFFSET` (64) | Both zero again — one scenario, two code paths |
| `storage-del` | Slots deleted that existed before the split | The values are back. Here the doomed change **is** an absence, which is why the check is a predicate rather than "assert absent" |

**Monitor oracles — 8** (`cmd/pbtmonitor`)

| Oracle | What it asserts |
|---|---|
| same-block agreement | Every tick, every client is asked for the same block number and must return identical hashes — on this chain that is a state-root assertion |
| `expected-genesis-root` | Every node's genesis state root, the client-agnostic proof the chain really is on the binary tree; also guards against silently coming up on `keccak256(rlp(""))` |
| `assertNoBadBlocks` | Blocks rejected during *this* run, baselined at preflight so an old rejection doesn't fail every later run |
| `probe` | Cross-node `eth_getProof` over addresses sampled from the latest block plus the system contracts. Deliberately **no** `debug_stateSize` check: the tree has no snapshot generator, so that check would always skip, and a check that always skips itself is worse than no check |
| `selfTest` | Builds a real payload, corrupts one byte of its state root, recomputes the block hash so the node must actually re-execute, and requires **every** other node to answer `INVALID`. `VALID` is catastrophic; `SYNCING`/`ACCEPTED` are not refusals. Without this, "0 findings" from a broken oracle is indistinguishable from a healthy chain |
| `captureDivergence` | Grabs bad blocks with RLP plus every client's head before teardown; capturing nothing is itself the failure |
| stall detection | Names a chain that stops producing after N identical polls |
| disruptoor-aware classification | A divergence during a partition we applied on purpose is counted apart from findings rather than mixed in |

**Load workloads — 11** (`cmd/pbthammer`). Aimed at what EIP-8297 changed rather than at
throughput. These generate traffic only — the assertion is the monitor's, so they catch
divergence *between* clients, not an implementation that is uniformly wrong. Receipts are
sampled 1-in-12; a workload that only ever reverts, or never mines, is a finding, because
that shape is then untested.

| Workload | What it exercises |
|---|---|
| `fanout` | Fresh recipients → new header stems |
| `storage` | Spread slots → the storage zone and its 66-byte keys |
| `codedup` | Identical code from several senders → code-zone leaves shared between accounts |
| `destruct` | Deploy a child then destroy it same-tx → code-zone leaves nothing reclaims |
| `delegate` | 7702 delegate, re-delegate, clear to zero → the delegation leaf and its removal |
| `zeroize` | Write then store zero → deletion, because zero is absence |
| `callread` | `CALL` into an `SLOAD` → the read path, present and absent leaves |
| `extcode` | `EXTCODESIZE`/`EXTCODECOPY` over a large contract → chunk-spread code reads |
| `legacy` | Type-0 envelope → the pre-2930 path |
| `accesslist` | Type-1 with a populated list → repriced access-list accounting |
| `revert` | Write slots then `REVERT` → intra-transaction rollback of tree writes |

**Standing finding:** the `gasDisagreement` reporter shows geth and besu pricing the same
deployment **2.9% apart** on `eth_estimateGas`. Real, known, and collapsed into one periodic
summary so it doesn't bury the next finding.

**Harness unit tests — 14** (`cmd/pbtchaos/scenario_run_test.go`), mostly about not blaming
the wrong node: `TestFrozenClientIsDetectedAfterWedgeTicks`, `TestFrozenNeedsEnoughRounds`,
`TestGloballyStalledChainNamesNobody`, `TestResumingClientClearsItsStall`,
`TestAllButOneFrozenIsReportedInOrder`, `TestParticipantIndexTiesTheTwoHalvesOfANode`,
`TestAFrozenClientWithNoPeersIsStarvedNotWedged`, `TestAFrozenClientWithPeersIsWedged`,
`TestAnUnknownPeerCountErrsTowardReporting`, `TestRotationSkipsProtectedNodes`,
`TestEligibleIsEveryNodeWhenNothingIsProtected`, `TestBothOnlyNamesClientsInEitherList`,
`TestBothIsEmptyWhenNothingOverlaps`, `TestDescribeHeadsSaysHowFarBehind`.

**Operator checks:** `make status` (heads and roots side by side), `make verify BLOCKS=100`
(every client at the *same* block number), `make diagnose` (where the chain split),
`make forks`, `make proposals`. Assertoor runs upstream's block-proposal, EOA-transaction and
synchronized checks alongside.

### Implemented — where the fixtures actually execute

The 70 blockchain fixtures above are a shared *artifact*. They are **not** executed by a shared *harness*. Workflow findings verified 2026-09-18. Hive #1614 adds a shared artifact harness, described in section 3, but does not run these blockchain fixtures.

| Venue | What runs there | Whose CI |
|---|---|---|
| **`execution-specs@projects/binary-trie`**, `test.yaml` | The 224 test functions — 168 unit in `tests/binary_trie/` + the 56 fillers | EF spec branch. **Tip stalled since 2026-08-13** |
| **`binary-trie-vectors.yaml`** | Regenerates `tests/binary_trie/vectors/binary_trie_vectors.json` and commits it back on change. The **only** PBT-specific workflow on the branch, and it publishes no artifact — so even the vector file is not distributed, only committed | EF spec branch |
| **`hive-consume.yaml` / `hive-execute.yaml`** | **Nothing PBT.** Inherited from `forks/amsterdam`; fire on `forks/**` pushes only, target Osaka, run `ethereum/eels/consume-{engine,rlp,sync}` | EF spec branch, inert here |
| **`release_fixtures.yaml`** | Nightly 02:00 UTC, "up to the latest mainnet fork — **no dev forks**". **No `binary_tree` feature**, so PBT fixtures are never released as a consumable tarball | EF spec branch |
| **Per-client fixture consumption** | geth reports the suite **fully green** ([go-ethereum#13](https://github.com/CPerezz/go-ethereum/pull/13)); Erigon reports **67 of 70** behind `--experimental.bin-commitment` | **Each client's own CI, separately** |
| **geth nightly** | `.github/workflows/pbt-nightly.yml` + the `PBT_FLAT_STATE_BASELINE.md` recorded baseline — the seed of the "minimum benchmarking loop" asked for on 2026-08-26 | `CPerezz/go-ethereum@pbt` |
| **Hive `ethereum/pbt-artifacts` (draft #1614)** | Shared EIP-8347 artifact consumer/producer checks; 58 mutations plus valid-pair and agreement checks. Does not execute the 70 blockchain fixtures | Hive PR branch; reviewed 2026-09-23 |
| **Client in-repo unit suites** | ~240 PBT tests in geth alone (60 trie, 57 EVM-rule, 34 converter, 74 BAL-replay, 8 catalyst lifecycle); Nethermind's published numbers are prototype measurements, not conformance | Client repos |
| **Assertoor, inside pbt-devnet** | Upstream block-proposal, EOA-transaction and synchronized checks alongside `pbtmonitor` — cross-client live-chain automation, complementary to the new Hive artifact suite | pbt-devnet |

**Why this matters for the numbers in this section.** "geth green, Erigon 67/70" are two clients' **own** reports, produced by their own CI, on their own schedule, in formats that do not compare. Nobody runs the 70 fixtures against all four clients and emits one report — which is exactly what a Hive `consume-rlp`/`consume-engine` job over a released `tests-binary-tree@vX` feature would produce, and it is the missing half of [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md)'s cross-client conformance claim that the devnet does **not** cover: the devnet proves four clients agree with *each other* on live blocks, not that any of them agrees with the *spec fixtures*.

**Sequencing caveat.** Promoting these fixtures to a shared cross-client oracle **before** separating spec from provider would bake `state_pbt.py`'s choices into conformance — three of the 70 pin provider behaviour rather than EIP text (the two zero-write cases and the `CREATE2`-after-EIP-161-clear case the reference itself calls an open consensus question). That is the same failure mode gap 1 names for the converter fixtures. Release the feature and wire Hive, but fix the three fixtures in the same motion.

### Where it stands

- **Implemented.** 56 fillers (70 fixtures) + 72 provider unit tests; geth green, Erigon
  67/70 — both **self-reported in each client's own CI**, not measured by a shared harness.
- **Watch.** Erigon's three failures are **not tree bugs** — two are zero-write fixtures
  pinning `state_pbt.py`'s deletion behaviour and one is a `CREATE2`-after-EIP-161-clear case
  the reference itself calls an open consensus question. **A suite that encodes provider
  behaviour cannot serve as the shared oracle A-T1 exists to provide**; separating the two is
  now part of that deliverable.
- **Absent.** No PBT-native sync tests. No adversarial/structural-cost suite. No
  hardware-matrix numbers. **No shared fixture-execution harness** — no released fixture
  feature or shared Hive report for these **EIP-8297 blockchain fixtures**. The new
  artifact simulator below covers a different surface.

---

## 3 · The converter

MPT leaf → PBT key/value, at mainnet scale, producing a byte-canonical snapshot plus a
preimage file that any node can authenticate without trusting the producer
([04-migration.md § Converter](04-migration.md)). **The thinnest-tested component in the
programme.**

### Planned

| Deliverable | Window | What it ships |
|---|---|---|
| [B-T1](../roadmap/deliverables/B-T1-conversion-replay-vectors.md) | 2026-09 → 2027-03 | **Converter golden fixtures** across the full pipeline: scan source leaves, validate `keccak(preimage)` ↔ trie path, derive PBT keys, and (in miniature) the external merge-sort + bottom-up construction that yields the root. Plus negative fixtures — mismatched preimage, empty account, shared code leaves, boundary sub-index cases. **Exit criterion: two independent implementations pass every vector with identical output.** |
| [B-T3](../roadmap/deliverables/B-T3-dual-check-verification-scale.md) | 2027-10 → 2028-04 | **Dual-check verification at mainnet scale.** Check 1: rebuild the PBT from snapshot leaves, derive keys, hash bottom-up, verify the *claimed* root. Check 2: rehash the same leaves under the **MPT schema** using distributed preimages and verify against block `N`'s header `stateRoot`. Plus a fresh-node run from snapshot + preimages + header alone, per-chunk verification against manifest hashes, and **failure injection** (corrupted chunk, wrong preimage, tampered root) confirming each is detected by the right check. |
| [B-C4](../roadmap/deliverables/B-C4-production-rehearsals.md) | 2027-07 → 2027-12 | **Cross-client snapshot equality:** snapshots produced by different clients over the same mainnet anchor are bit-identical (chunk hashes + manifest match), inside 2× disk, across the EIP-7870 hardware matrix. Hash-keyed clients exercise the preimage-driven path; raw-keyed clients exercise preimage extraction; all must converge on the same snapshot. |
| [A-C4](../roadmap/deliverables/A-C4-snapshot-serving-verification.md) | 2027-03 → 2027-07 · *in flight* | Chunked byte-canonical emission in PBT-key order, sequential bulk-load with resumability markers, one client serving while others ingest and independently verify to the same root. |

### Implemented — `geth@pbt` unit tests (34; September inventory)

**Nothing in `execution-specs`.** There is no EIP-8347 code on `projects/binary-trie` at all,
so there is no reference implementation to derive fixtures from. **The migration devnet does
not exercise the converter** either — M1 ran on empty state.

**Conversion** — `bintrie_convert_test.go`, `_parity`, `_lifecycle`, `_cli`

| Test | What it covers |
|---|---|
| `TestBintrieConvert` | The base conversion path end to end |
| `TestPBTDiskIsDetectable` | A converted datadir identifies itself |
| `TestBintrieConvertDeleteSource` | Source deletion after conversion |
| `TestConvertRefusesDirtyNamespace` | Refuses to convert into a non-virgin namespace |
| `TestConvertVerifiers` | The verifier wiring inside convert |
| `TestWipeRestoresVirginNamespace` | Wipe returns the namespace to virgin |
| `TestConvertCorruptPreimageRefused` | A corrupt preimage stops the conversion — B-T1's "mismatched preimage" negative fixture, in one client |
| `TestConvertMatchesReference` | Converter output equals the reference implementation |
| `TestConvertMatchesEmbedding` | Converter output equals direct embedding of the same state |
| `TestConvertMatchesChain` | Converter output equals the chain's own computed tree |
| `TestBintrieConvertDiskBacked` | Disk-backed (not in-memory) conversion |
| `TestConvertedBaseAcceptsCommits` | The converted base can be built on |
| `TestDeleteSourceLifecycle` | Full delete-source lifecycle |
| `TestBintrieConvertCLI` | CLI surface of `geth bintrie convert` |
| `TestBintrieImportCLI` | CLI surface of `geth bintrie import` |

**Artifacts** — `bintrie_artifacts_test.go`

| Test | What it covers |
|---|---|
| `TestSnapshotArtifactRoundTrip` | Snapshot write/read round trip |
| `TestPreimageFileRoundTrip` | Preimage file round trip |
| `TestArtifactsAreByteCanonical` | Byte-canonicity — the property B-C4's cross-producer equality claim rests on |
| `TestArtifactGoldenDigests` | Pinned artifact digests |
| `TestArtifactReaders` | Reader behaviour |
| `TestArtifactReadersReject` | Malformed artifacts are refused |

**Dual-check import** — `bintrie_import_test.go`, `bintrie_anchor_e2e_test.go`. The anchor is
resolved from the node's **own** header chain, with no `--anchor-root` flag by design — a
self-vouching artifact would make verification circular.

| Test | What it covers |
|---|---|
| `TestImportRoundTrip` | Import a snapshot and reach the claimed root |
| `TestImportVerifyOnly` | Verify without ingesting |
| `TestImportMatchesReference` | Imported state matches the reference |
| `TestImportRejects` | Bad snapshots are rejected |
| `TestAnchorSeededCatchup` | Anchor-seeded catch-up end to end |

**External sort & bottom-up build** — `trie/bintrie/extsort_test.go`, `triedb/pathdb`

| Test | What it covers |
|---|---|
| `TestLeafSorterOrders` | Leaves come out in PBT-key order |
| `TestLeafSorterRejects` | Invalid records are rejected |
| `TestLeafSorterEdges` | Edge cases at run boundaries |
| `TestLeafSorterMatchesStackBuilder` | Sorted stream and stack builder agree — the miniature form of B-T1's "external merge-sort + bottom-up construction" |
| `TestRecordSorterVarlen` | Variable-length record sorting |
| `TestAttestFlatState` | Flat-state attestation over the converted DB |

**Benchmarks** — `bintrie_convert_bench_test.go`

| Benchmark | What it measures |
|---|---|
| `BenchmarkConvertState` | Conversion throughput — the **only** conversion-cost measurement that exists. B-C4 needs this on ~220M accounts / 600M slots across the EIP-7870 tiers |
| `BenchmarkImportState` | Snapshot ingestion throughput |

Also present: `.github/workflows/pbt-nightly.yml` and `PBT_FLAT_STATE_BASELINE.md` — a
nightly CI job and a recorded performance baseline, the seed of the "minimum benchmarking
loop" the 2026-08-26 sync asked the group to define.

### Implemented — Hive artifact conformance (draft PR #1614)

[Hive PR #1614](https://github.com/ethereum/hive/pull/1614) is **open and draft** as of 2026-09-23. Reviewed source:
[`pbt-artifacts` at `b8703d2`](https://github.com/ethereum/hive/blob/b8703d2c782fdd18948f1ce771f447b8c027b852/simulators/ethereum/pbt-artifacts/README.md), including the
[manifest](https://github.com/ethereum/hive/blob/b8703d2c782fdd18948f1ce771f447b8c027b852/simulators/ethereum/pbt-artifacts/fixtures/manifest.json), simulator, generator and client shims.
This is executable shared coverage, not evidence of an upstream merge or an established CI gate.

**Count and scope.** The manifest has **58 mutations: 14 preimage rejections, 43 snapshot
rejections and one unscored `snapshot/empty` case**. These exclude the genesis-root gate,
valid-pair tests, conversion/output comparisons and per-artifact producer-agreement tests.
The fixture has **32 accounts and 363 PBT leaves**; it uses BLAKE3 and records EIP-8347
at 2026-08-25 and EIP-8297 at 2026-09-21. These are not additions to the 224 Python
reference test functions counted above.

| Surface | Coverage |
|---|---|
| Preimage consumer | Truncation/trailing bytes, oversized slot count, hashed-key ordering, duplicate addresses/slots, missing or surplus accounts/slots, empty file and slots assigned to the wrong account |
| Snapshot consumer | Root/count/version/framing and canonical encoding, key order/width/zones, zero or orphan leaves, missing storage/code, code hash/size/chunk/PUSHDATA checks, delegation rules and an artifact anchored to another state |
| Converter output | Convert the sound genesis allocation and compare each supported output byte-for-byte with the canonical fixture; check agreement separately for preimages and snapshots |
| Embedding edges | 31-byte code boundaries, PUSH straddles, zero chunks, two code groups, shared bytecode, delegation targets/designators, header/overflow storage, maximum nonce/balance |

**Oracle and scoring.** Preimages are derived directly from the allocation. Snapshot bytes
come from the reference converter, with the leaf set checked against an independent
embedding derivation before writing; snapshot byte canonicality still needs another
producer. Genesis-root agreement gates the run, and accepting the sound pair gates each
consumer suite. Exit 0 means accept, 1 reject, 3 unsupported; other exits are crashes,
which never count as conforming rejections. At the reviewed head, a rejection requires
exit 1 and nonempty stderr; the PR description's older regexp-attribution claim is not
implemented there. Mutation effects are recorded and duplicate effects rejected.

**Reported results in the PR description, not re-run here:**

| Client | Anchor root | Preimage rejection cases | Snapshot rejection cases | Produce preimages | Produce snapshot |
|---|---|---|---|---|---|
| geth | Matches | 14/14 | 43/43 | Canonical bytes | Canonical bytes |
| Nethermind | Matches | 12/14 | 42/43 | Unsupported | Unsupported |
| Erigon | Matches | Unsupported | Unsupported | Canonical bytes | Unsupported |
| Besu | Matches | Unsupported | Unsupported | Unsupported | Unsupported |

The reported Nethermind misses are crashes on truncated preimages, trailing preimage
bytes and a truncated snapshot. Both consumers reportedly reject the empty snapshot,
but the manifest leaves that case **unspecified**, so it is not a scored failure.
Reth is absent from the shipped client set. The PR's reported matrix is not a fresh
measurement of the reviewed head.

[`clients.yaml`](https://github.com/ethereum/hive/blob/b8703d2c782fdd18948f1ce771f447b8c027b852/simulators/ethereum/pbt-artifacts/clients.yaml) selects geth `pbt-preimage-format`
(dependent on [CPerezz/go-ethereum#41](https://github.com/CPerezz/go-ethereum/pull/41))
and Nethermind `pbt-state`; Erigon and Besu use stock, unpinned configurations.
This corrects the old format on the tested geth branch without establishing that the
older `pbt` branch has caught up. To run from the PR checkout:

```sh
./hive --sim ethereum/pbt-artifacts --client-file simulators/ethereum/pbt-artifacts/clients.yaml
go run ./simulators/ethereum/pbt-artifacts/tools/matrix workspace/logs > CAPABILITY.md
```

### Where it stands

- **In flight:** B-T1's artifact fixtures and A-C4's cross-client consumer checks now
  have a shared harness. The PR reports byte-identical geth/Erigon **preimages**.
- **Still open:** a second snapshot producer, all-case consumer conformance, upstream
  integration/CI, full converter-pipeline vectors and BAL-replay vectors.
- **Scale remains untested here:** these miniature artifacts do not demonstrate external
  sort/spill behaviour, mainnet-scale dual-checks, distribution/resumption, `(E, N]`
  preimage completion, or the live migration lifecycle. The old M1 run remains separate.

---

## 4 · BAL replay

Translating EIP-7928 block access lists into PBT writes, so a node converted at anchor `N`
can catch up to the tip without re-executing
([04-migration.md § BAL-replay](04-migration.md)). Load-bearing for the whole offline model:
**replay must converge faster than blocks are produced, or catch-up never completes.**

### Planned

| Deliverable | Window | What it ships |
|---|---|---|
| [B-T1](../roadmap/deliverables/B-T1-conversion-replay-vectors.md) | 2026-09 → 2027-03 | **BAL-replay vectors** for each translation rule — balance, nonce, storage, code — including **zero-write-deletes-leaf**, **account deletion without a marker** (the `nonce == 0 ∧ balance == 0 ∧ code_size == 0` trigger, exact in both directions only because EIP-7523 leaves no empty account in the MPT — added to EIP-8347's `requires` on 2026-08-25), the **7702 delegation set/clear pair**, and a small `(E, N]` BAL-completion sequence. |
| [B-C2](../roadmap/deliverables/B-C2-bal-replay-engine.md) | 2027-01 → 2027-05 · *in flight, ~5 months early* | The engine itself, validated against those vectors, consuming the BAL format as shipped in Glamsterdam. |
| [B-T2](../roadmap/deliverables/B-T2-full-cycle-devnet-swap.md) | 2027-03 → 2027-08 · *seeded* | Replay to tip on a live devnet, with **captured metrics**: replay catch-up rate vs block production, conversion time, distribution timing. |

### Implemented — `geth@pbt` (74 tests)

Nothing in `execution-specs`. The BAL-replay vector suite is named in the KB test surface and
has no implementation anywhere.

**Translation rules** — `core/bintrie_replay_test.go` (7). Maps almost exactly onto B-T1's
"all four entry types plus zero-write/deletion".

| Test | What it covers |
|---|---|
| `TestShadowReplayTransfers` | Balance/nonce entries |
| `TestShadowReplayContractStorage` | Storage entries |
| `TestShadowReplayAccountRemoval` | Account deletion without an explicit marker |
| `TestShadowReplaySelfDestruct` | Self-destruct through the BAL |
| `TestShadowReplayDelegation` | The 7702 set/clear pair |
| `TestShadowReplayWithdrawals` | Withdrawal credits, which are not transactions |
| `TestShadowReplaySystemContracts` | System-contract writes |

**Catch-up state machine** — `core/bintrie_follower_test.go` (13). **Nothing in the roadmap
plans this surface** — B-C2 describes an engine, not a follower that survives restarts,
reorgs, snap-sync and missing lists. Worth promoting into B-T1's scope.

| Test | What it covers |
|---|---|
| `TestFollowerTracksChain` | Steady-state following |
| `TestFollowerFollowsReorg` | Reorg handling |
| `TestFollowerRestartResumes` | Resume after restart |
| `TestFollowerRecoversWithoutJournal` | Recovery with no journal |
| `TestFollowerRequestsMissingLists` | Fetches BALs it lacks |
| `TestFollowerStalls` | Stall is detected, not silent |
| `TestFollowerIdlesDuringSnapSync` | Idles while snap-syncing |
| `TestFollowerRefusesTreesDuringSnapSync` | Refuses tree work mid-snap-sync |
| `TestFollowerResumesFromRecordAboveCursor` | Cursor/record ordering |
| `TestFollowerStopsOnCanonicalDiscontinuity` | Stops on a canonical gap rather than guessing |
| `TestFollowerBatchesDeepCatchup` | Batching for deep catch-up |
| `TestWaitCaughtUpAbortsOnStop` | Clean shutdown while waiting |
| `TestFollowerSharesCanonicalHandle` | Handle sharing with the chain |

**Fold, fetch, apply** — `core/types/bal/*`, `eth/bal_fetcher`, `eth/protocols/snap/bal_apply` (29)

| Test | What it covers |
|---|---|
| `TestFoldLastWriteWinsAcrossBlocks` | Folding many blocks keeps the last write |
| `TestFoldRemovalSplit` | Removal splits correctly in a fold |
| `TestFoldRemovalMarkerIsLatestOnly` | Only the latest removal marker survives |
| `TestFoldDropsReadOnlyAccounts` | Read-only accounts are dropped |
| `TestFoldOrdersAccountsAndSlots` | Deterministic ordering |
| `TestFoldPreservesEmptyCodeChange` | An empty code change is still a change |
| `TestFoldEmptyInput` | Empty input folds to nothing |
| `TestFoldMatchesSequentialApply` | Randomised: fold ≡ sequential application — **the property B-T1 would pin as a vector** |
| `TestBALFetcherFetchesMissing` | Fetches missing lists from peers |
| `TestBALFetcherDropsForgingPeer` | Drops a peer that forges a list |
| `TestBALFetcherRejectsOversizedReply` | Oversized replies refused |
| `TestBALFetcherSkipsUnavailable` | Unavailable lists skipped, not retried forever |
| `TestAccessListVerification` | List verification against the block |
| `TestAccessListApplication` | Applying a list to state |
| `TestAccessListApplicationMultiTx` | Multi-transaction lists |
| `TestAccessListApplicationZeroStorage` | Zero-storage writes — the deletion rule |
| `TestAccessListApplicationNewAccount` | New account creation |
| `TestAccessListApplicationSkipsUnfetched` | Unfetched accounts skipped |
| `TestAccessListApplicationSkipsUnfetchedStorage` | Unfetched storage skipped |
| `TestAccessListApplicationPartialStorage` | Partially fetched storage |
| `TestIsStorageFetched` | Fetched-state predicate |
| `TestAccessListApplicationSameTxCreateDestroy` | Create and destroy in one tx |
| `TestAccessListApplicationDestroyExisting` | Destroying a pre-existing account |
| `core/types/bal/bal_test.go` (6) | Encoding/decoding and lookup of the BAL type itself |

**Migration mode & rules** — `core/pbt_migration_test.go`, `core/rawdb/accessors_pbt_migration`,
`params/pbt_rules_test.go`, `core/eip161_test.go` (17)

| Test | What it covers |
|---|---|
| `TestStateModeResolution` | Which state mode a config resolves to |
| `TestMigrationGenesisIsMerkle` | A migration devnet starts on the MPT |
| `TestNewBlockChainMigrationMode` | Chain construction in migration mode |
| `TestMigrationRequiresPathScheme` | Migration requires the path scheme |
| `TestUnscheduledPBTStateStillRefused` | PBT state without a schedule is refused |
| `TestMigrationDoneSkipsFollower` | A finished migration stops following |
| `TestShadowStateRootStorage` | Shadow roots persist |
| `TestMigrationCursorStorage` | Cursor persists |
| `TestPBTMigrationDoneFlag` | Done flag persists |
| `TestWipeMigrationState` | Migration state can be wiped |
| `TestPBTChangesNoExecutionRule` | **The swap changes no execution rule** — the machine-checked form of "commitment-only" |
| `TestPBTKeepsEIP2929` | Access-list pricing unchanged |
| `TestPBTRequiresAmsterdam` | Fork ordering |
| `TestBinaryTrieTimeJSONKey` | `binaryTrieTime` genesis key — how Erigon picks up the tree at `init` |
| `TestIsBinaryTrie` | Activation predicate |
| `TestEIP161ClearingAgreesAcrossExecutors` | EIP-161 clearing agrees between executors |
| `TestEIP161TouchOfAbsentAccountLeavesBALAlone` | Touching an absent account writes no BAL entry |

### Where it stands

- **Implemented, in one client, beyond B-T1's scope.** The fold, the follower state machine,
  peer-level BAL fetching and the snap-protocol application path are all covered.
- **Watched live** by the migration devnet's F1/F2/F3 + NULL5/NULL10 findings and judged by
  C1–C8 (below).
- **Unproven.** The convergence-rate claim. M1 measured "done at T+519s" on an empty-state
  4-node network; nothing yet measures replay against mainnet block production.

---

## 5 · Swap & lifecycle (cross-cutting)

Crossing `binaryTrieTime`, running both trees until finality, and flipping the canonical
commitment. Belongs to no single component, and it is where the devnet work is furthest ahead
of the roadmap — and where the meeting notes ask for the most that nobody owns.

### Planned

| Deliverable | Window | What it ships |
|---|---|---|
| [B-T2](../roadmap/deliverables/B-T2-full-cycle-devnet-swap.md) | 2027-03 → 2027-08 · *seeded* | **Full cycle on a multi-client devnet:** convert → snapshot → distribute → BAL-replay → swap at a simulated fork `S`. Verify the swap changes the **state commitment only** — `EXTCODEHASH` byte-identical, no gas or opcode change. Exercise the both-trees window to finality. A fresh node with no prior state joins by ingesting the snapshot and reaches consensus post-swap. |
| [B-S2](../roadmap/deliverables/B-S2-readiness-gate-activation-params.md) | 2027-09 → 2028-02 | **Readiness gate:** cross-client agreement ≥ X%, coverage ≥ Y%, sustained D days — all three still placeholders — plus the unvalidated-flip mitigation design. |
| [B-C5](../roadmap/deliverables/B-C5-testnet-migrations-shadow-fork.md) | 2028-01 → 2028-03 | **Public testnet migrations with swaps** and a **mainnet shadow fork**, all five ELs participating, independent operators in the loop. |
| [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md) | 2027-01 → 2027-06 | **Sustained multi-client root agreement** over a defined window, packaged as H\* readiness evidence, plus root-agreement dashboards. |

### Implemented — `verify-migration` acceptance gates (C1–C8)

The pass/fail oracle for a migration devnet run. All eight passed on **R3** (4 nodes, offset
2400, chaos profile r3), accepted 2026-08-27. Two design notes worth keeping: the verifier
must speak **both naming conventions** (chaos says `node-2`, kurtosis and the monitor say
`el-2-geth-lighthouse`), and it defers sample-mismatch judgement to the monitor's hash-grouped
F1, because a split-shaped sample during a partition is legal.

| Gate | What it requires | R3 result |
|---|---|---|
| **C1** | ≥100 canonical blocks strictly before `b*`, with monitor `bstar` events agreeing with an independent RPC backwalk | `b*` = 345 |
| **C2** | An early first transaction (s0 ≤ 50) and ≥1 tx-bearing block in every 25-block bucket — proves the run carried real load, not empty blocks | s0 = 3, every bucket in [3,344] |
| **C3** | ≥4 healed chaos isolations corroborated by a reorg, ≥1 at depth ≥ 10, all healed before T−300 | 5/5 matched |
| **C4** | Three-way agreement on every block across the activation boundary | 43 blocks in [313,355] across 4 nodes |
| **C5** | No log mention of migration-window configuration, and every node's timeline strictly ordered | pass |
| **C6** | Enough good cross-node samples with zero unwaived criticals, under F1 semantics | 95 samples, 91 good, 0 unwaived criticals |
| **C7** | The pins file matches every node's real genesis — **state root only**, by design | pass across 4 nodes |
| **C8** | Exactly one `PBT_ARTIFACT_DIGESTS` line per EL log, identical across nodes | snapshot `0ea2e8…`, preimages `5bbc80…` identical across 4 nodes — **but all four are the same geth binary**, so this is reproducibility, not cross-producer equality |

### Implemented — live findings (`internal/migmon`)

Thresholds are the M1 plan's, not tunables. Shared between the monitor that emits them and
the verifier that consumes them.

| Finding | Definition |
|---|---|
| **F1 · root mismatch** | Two nodes report different non-null shadow roots for the **same block hash**. **Critical, never waived** — not by chaos windows, not by phase |
| **F2 · stall** | A direction reports stalled/error, or its cursor is frozen for ≥20 polls while the head advanced ≥10 blocks. Suspended while the direction is idle |
| **F3 · boundary** | At the first header with time ≥ T, the binary direction must park and the merkle direction must start following within 2 polls / 3 blocks; "done" must come strictly after `b*` |
| **NULL5 / NULL10** | A node keeps answering null for sampled shadow roots while claiming following\|synced — warn at 5 min, critical at 10 |
| *sampling* | One probe per minute at uniform random depth 3–16 behind the head. R3 finding: 1/min starves C6 (~37 usable samples in a 30-minute offset); 30 s cadence delivered 91/95 |

### Implemented — the M1 acceptance ladder (7 stages, all command-verified)

| Stage | Shape | Result |
|---|---|---|
| **S1** docker matrix | Canonical `pbt-geth:local` shim: armed / passthrough / restart / failure | PASS; found that the tip **requires `--cache.preimages`** for convert |
| **B1** egg harness | Offset 1800 / unset / 0, six gates | PASS; complements cross-identical both directions, 65539 embeddings of the right hash and 0 of the wrong, unset ≡ offset-0 byte-identical |
| **T8v** regression gate | The 7-client PBT-at-genesis devnet on the shimmed image | PASS; 50/50 blocks identical — the legacy tree devnet is unbroken |
| **S2** 1 node, offset 600 | First live migration | Binary parked, merkle took over, done at T+11m, 0 criticals |
| **S3** 4 nodes, one 3-min isolation | Chaos machinery | Divergence visible mid-partition with RPC still reachable; heal reorg drop=8/add=9; converged |
| **R2** 4 nodes, quiet | Volume run | `b*` ×4 at block 298 within 11 ms; done ×4 at T+521s |
| **R3** 4 nodes, chaos | **Acceptance** | 3 laps; final `b*` ×4 at 345, done ×4 at T+519s, C1–C8 all PASS, exit 0 |

**Two R3 findings that changed the design, and generalise:**

1. **Deep partitions do not self-heal on this stack.** Once a victim's branch diverges across
   a checkpoint the majority finalized, the **majority** side's lighthouse peer scoring bans
   the victim, remote bans survive a victim restart, and the node crosses the fork boundary
   alone on its own island — caught by the monitor's `b*` quorum check as the run's only
   critical (F3, `b*` 143 vs 263).
2. **Stake is the knob, not duration.** Giving the deep victim 256 of 640 validators (40%)
   pins the connected majority at 60% — below the 2/3 finality threshold — so finality stalls
   for the window instead of anyone getting banned, and a 40% proposer share yields depth ≥ 10
   inside a 190 s window (~99.2% across three tries).

Both are directly relevant to B-S2's unvalidated-flip mitigation
([11-attester-telemetry-transport.md](11-attester-telemetry-transport.md)) and to the
non-finality tests Nethermind asked for.

**Also worth copying:** R3 pinned the genesis **state root** (`0x1a20cc79…`) rather than the
genesis hash, because kurtosis renders a fresh timestamp every run — the alloc is the
invariant worth defending. `TestPBTGenesisPins` in
[go-ethereum#32](https://github.com/CPerezz/go-ethereum/pull/32) cross-references it, proving
one binary computes both tree kinds from one alloc.

### Implemented — migration-harness unit tests (31)

The harness tests its own judgement, which is what makes a green run believable.

| File | n | Tests |
|---|---|---|
| `cmd/verify-migration/main_test.go` | 7 | `TestCheckC3`, `TestCheckC6SplitShapedSampleIsNotAMismatch`, `TestCheckC6CriticalF1NeverWaived`, `TestCheckC6OutsideWindowCounting`, `TestCheckC7`, `TestCheckC8`, `TestBackwalkBStar` |
| `internal/migmon/timeline_test.go` | 8 | F2 immediate / dedup+rearm / slow-burn, F3 boundary, F3 done-early, initial-inactive warn-once, `b*` observed once, `b*` quorum |
| `internal/migmon/sampler_test.go` | 7 | Sample evaluation, F1 never waived pre-`b*`, null-tracker escalation and inactivity, reorg memory and its bound, live-fixture acceptance |
| `internal/migmon/progress_test.go` | 3 | Live-fixture decoding, flex cursor, refusal of shapeless progress (fixtures: `progress-prefork`, `progress-postboundary`, `progress-done`) |
| `cmd/migration-chaos/schedule_test.go` | 6 | `TestResolveR3`, `TestAdmissionRefusesCrossingOps`, `TestResolveSmoke`, `TestResolveGuards`, `TestEmitPlanShape`, `TestOthers` |

### Implemented — `eth/catalyst/pbt_migration_test.go` (8)

The swap lifecycle at engine-API level — the closest existing thing to B-T2's exit criteria,
minus convert/snapshot/distribute.

| Test | What it covers |
|---|---|
| `TestFullMigrationLifecycle` | Merkle → cross `b*` → PBT canonical, end to end |
| `TestFullMigrationLifecycleBlocksKnob` | Same, driven by block count rather than time |
| `TestDirectionPRevivesOnReorg` | The parked direction revives when a reorg needs it |
| `TestMigrationSurvivesRestartPreFork` | Restart before the fork resumes cleanly |
| `TestBatchImportAcrossTheFork` | Batch import spanning the activation |
| `TestMigrationBoundaryStraddleReorg` | **A reorg straddling the format swap** — listed in M1 as a *post-M1 candidate*, and it exists here as a unit test. [go-ethereum#33](https://github.com/CPerezz/go-ethereum/pull/33) lifts the same shape to four live nodes with a 41-block rewind |
| `TestShadowRootSidecar` | The shadow-root feed |
| `TestShadowRootStreamNeverBlocksImport` | Publishing shadow roots never stalls block import |

### Where it stands

- **Accepted (2026-08-27).** A kurtosis network that starts on empty merkle state, runs geth
  with the tree building in the background, survives spamoor load and forced reorgs for
  hundreds of blocks, crosses `binaryTrieTime`, and finishes the migration on every node.
- **The gap is the deliverable.** M1 ran on **empty state**, on **one execution client**, and
  does not exercise convert → snapshot → distribute at all. Stated next gates:
  populated-state single-client, then a second client — in that order, since bit-identical
  snapshots across producers still lack evidence; Hive now reports preimage agreement
  on its separate miniature fixture.
- **Remaining integration gap.** The September 17 update records four ELs exercising
  migration, but no full convert/distribute cycle. The Hive artifact suite is separate
  from that lifecycle test.

---

## Gap register

Ordered by how much of the programme's evidence they invalidate, not by how hard they are to
fix.

| # | Sev | Gap | Owner / next step |
|---|---|---|---|
| 1 | **Blocking** | **B-T1 is partial, not absent.** [Hive PR #1614](https://github.com/ethereum/hive/pull/1614) supplies artifact vectors and shared consumer checks, but full converter-pipeline and BAL-replay conformance vectors remain missing. Two clients passing every vector is not demonstrated. | Land the artifact suite and CI gate, fix consumer crashes, add remaining conversion/replay vectors; keep fixtures tied to explicit spec revisions. |
| 2 | **Blocking** | **Snapshot byte agreement still has one producer.** Hive reports matching geth/Erigon preimages and explicitly marks snapshot agreement inconclusive with geth alone. This is miniature-state evidence, not mainnet snapshot equality. | Add a second snapshot producer; extend agreement runs to B-C4 mainnet anchors. |
| 3 | **High** | **Dual-check verification remains unproven at mainnet scale.** Hive now injects malformed preimages, roots, encodings and wrong-anchor snapshots in miniature. Full-size fresh-node verification, transport-chunk failures and extraction/completion coverage remain open. | B-T3; reuse Hive mutations with B-C3/B-C4 artifacts and scale infrastructure. |
| 4 | **High** | **The reference suite has stopped moving, and part of it encodes provider behaviour.** Tip unchanged since 2026-08-13 apart from merges down from `forks/amsterdam`; PRs #3444 (reorg-branch provider state) and #3446 (genesis commitment) closed unmerged 2026-08-28 — precisely the areas the devnet is now exercising live. Erigon's three failures pin `state_pbt.py` rather than the EIP. | A-T1 / A-T2 — separating spec from provider is now part of the work |
| 5 | **High** | **EIP-8297 blockchain-fixture conformance still lacks shared execution.** The 70 blockchain fixtures are a shared artifact executed by no shared runner: geth's "fully green" and Erigon's "67 of 70" are each client's own CI, on its own schedule, in formats that do not compare, and neither result is reproducible by a third party. Hive #1614 covers EIP-8347 artifacts, not these blockchain fixtures; the branch's inherited `hive-consume.yaml` fires only on `forks/**`, targets Osaka and runs `ethereum/eels/consume-*`. The binding constraint is upstream of Hive: `release_fixtures.yaml` publishes "no dev forks" and has no `binary_tree` feature, so **no consumable fixture tarball exists**. The devnet does not substitute — it proves four clients agree with *each other* on live blocks, never that any agrees with the *spec fixtures*. Workflow findings verified 2026-09-18; scope distinguished from #1614 on 2026-09-23. | Add a `binary_tree` fixture feature to `release_fixtures.yaml` (a `tests-binary-tree@vX` release), **then** a Hive job consuming it — but fix the three provider-pinning fixtures in the same motion, or the shared oracle codifies `state_pbt.py`. Feeds [A-T1](../roadmap/deliverables/A-T1-eest-test-suite-port.md)'s "consumed in CI" exit criterion and [A-T3](../roadmap/deliverables/A-T3-pbt-genesis-conformance-sync-tests.md). |
| 6 | **High** | **Every root-bearing artifact is provisional until `H` is chosen.** All four client trees use BLAKE3, the devnet genesis pins BLAKE3 roots, and `test_key_hash_is_blake3` asserts it as fact — while `H` is formally undecided. A-T2's structure-only / hash-parameterised split is the right hedge and is not yet how the existing vectors are organised. A-T4's benchmarks are also hash-sensitive. | External dependency, end-2026; consumed by [A-S3](../roadmap/deliverables/A-S3-eip8297-spec-freeze.md) and every root-bearing vector |
| 7 | Medium | **Gas is a parameter everywhere, and there is no adversarial cost suite.** A-T1's gas fixtures treat costs as parameters pending A-S2 — correct sequencing, but no fixture currently fails when a cost is wrong. The KB's adversarial / structural-cost suites appear in no deliverable. The devnet already shows geth and besu 2.9% apart on the same deployment estimate. | Unowned; A-S2 (2028-01) consumes A-T4 (2027-07) |
| 8 | Medium | **No PBT-native sync tests exist.** A-T3's "a joining client reconstructs state and converges to the serving client's root" has no implementation. geth has the negative half (the follower refuses tree work during snap-sync); nothing tests the positive path, and A-C4's serve/ingest/verify devnet exercise has not run. | [A-C2](../roadmap/deliverables/A-C2-pbt-native-state-sync.md) (2027-01) → A-T3; A-C4 exercise |
| 9 | Medium | **Shadow-root telemetry is tested as an EL debug feed, not as the specified carrier.** geth has `TestShadowRootSidecar` and `debug_shadowRoots`, but that is an EL debug feed, not the CL-carried telemetry the design calls for; wire format, aggregation, timing and EL→CL plumbing are open §14 parameters. Nethermind's adversarial question — a meaningful share of validators publishing *wrong* roots, and where the 66%/75% circuit breaker sits — has no test and no owner. | [B-O3](../roadmap/deliverables/B-O3-shadow-root-ecosystem-readiness.md) / B-S2; telemetry spec unowned since 2026-08-12. See [11-attester-telemetry-transport.md](11-attester-telemetry-transport.md) |

---

## Asked for in meetings, absent from the roadmap

Every row below was committed to or requested in an August 2026 call
(`state-project-status/meeting-notes/2026-08`) and has **no matching deliverable, scope bullet
or exit criterion** in `roadmap/`. Several are cheap; four are load-bearing for the swap.
Worth deciding, per row, whether it becomes roadmap scope or is consciously dropped.

| Test / measurement | What it is | Asked by | Status |
|---|---|---|---|
| **Reorgs ≥ 64 blocks, forwards and backwards** | Drive the migration logic through deep reorgs in both directions across the activation. geth has a 41-block rewind (#33) and a boundary-straddle unit test; 64+ in both directions is not covered. B-T2's transition-window bullet names no depth. | Kevaundray, Besu call 08-12 | Partial |
| **Non-finality and extended non-finality** | Can clients hold and reorg all the way to the finalized point during the both-trees window, and what does block processing cost while they do? Target is near-instant reorg-to-finality, with externally validated data across all clients. R3 already produced the mechanism to induce it. | Łukasz Rozmej, Nethermind call 08-12 | **Absent** |
| **Migration failure / divergence recovery** | A defined recovery plan or circuit breaker, and tests for it. Room consensus was rollback to the last finalized state; the 66%/75% shadow-root agreement threshold was floated as the flip gate. B-S2 names the mitigation *design*; nothing tests it. | Nethermind + group, 08-12 | **Absent** |
| **Shadow-commitment spoofing** | Adversarial telemetry: a share of validators publishing incorrect PBT roots, and whether the readiness gate can be gamed. | Łukasz Rozmej, 08-12 | **Absent** |
| **Self-migration vs snapshot consumption** | Implement basic self-migration, then benchmark both modes head to head — including processing time while the node is live. Relevant because the EIP supports both and clients choose their default. B-C4 asks which tiers *can* self-convert; nobody planned the comparison. | Carlos + group, 08-26 | **Absent** |
| **Snapshot generate / consume / verify timing at mainnet scale** | Wall-clock for each of the three phases on a real ~600 GB state, on the Glamsterdam mainnet fork kept alive an extra week rather than a purpose-built devnet. B-C4 and B-T3 want these numbers; the September window is the concrete opportunity and is in no deliverable. | Carlos, Maria, 08-26 | Opportunity |
| **Retention window: 1 month vs 6 months** | Benchmark both as variables. Interacts with a hard constraint nobody has scoped: block data lives ~15 days (3,500 epochs), bounding how deep reorg testing can go and how long a migration window can be. | Group, 08-26 | **Absent** |
| **Survey of client test suites** | Ask client teams at ACD how they are testing PBT migration and assess how robust those suites are. Repeated messaging attempts got no response, which is itself a finding. | Carlos, 08-26 | Open action |
| **Shared bytecode with differing constants** | Investigate contracts that share bytecode but differ in embedded constant data, to check the ~60%-duplication dedup assumption the code zone is designed around. | Reth call, 08-19 | Unassigned |
| **MPT-side edge cases** | Collapsing-branch and similar MPT edge cases flagged as never explicitly tested — they matter because the both-trees window keeps the MPT live through the migration. The spec suite covers the PBT-side equivalent (`test_delete_collapses_branches_to_canonical_form`). | Carlos, 08-19 | Partial |
| **Review existing coverage for gaps** | "Evaluate existing tests to identify covered scenarios and potential edge cases." | Maria, 08-19 | **This file** |

---

## Four things worth doing with this

1. **Land and extend the Hive artifact suite.** Track its geth format dependency,
   fix Nethermind's consumer crashes, add a second snapshot producer and make the suite
   a CI gate. Keep its spec revision explicit; add the still-missing converter-pipeline
   and BAL-replay vectors under B-T1.
2. **Take the September mainnet fork.** A ~600 GB state on the Glamsterdam mainnet fork, kept
   alive an extra week, is the only near-term route to populated-state conversion numbers. It
   answers B-C4's sizing questions eighteen months before B-C4 opens, and turns the M1 ladder's
   next gate — populated state, one client — from a plan into a run.
3. **Propagate the oracle-proving pattern.** The devnet monitor refuses to be believed until it
   has manufactured a divergence and watched every client reject it; the migration verifier
   tests its own checks. Neither `execution-specs` nor the client suites do this. A-T3's
   conformance harness and B-T3's verification harness should both ship with a self-test, or
   "all clients agree" will not be a falsifiable claim.
4. **Release a `binary_tree` fixture feature, then wire Hive.** The cheapest unclaimed win in the programme: the fixtures exist, four clients already consume them, `release_fixtures.yaml` already knows how to cut a feature release, and Hive already runs `ethereum/eels/consume-*` for every other fork. What is missing is one fixture-release target and one simulator job — after which "geth green, Erigon 67/70" becomes one reproducible cross-client report instead of two self-reports. Do it together with separating the three provider-pinning fixtures from spec text, and it also unsticks A-T1's stalled half.

---

## Provenance

- **Roadmap:** all 26 deliverable pages in `../roadmap/deliverables`, with the seven
  Tests-workstream rows read in full and test scope extracted from A-C3, A-C4, B-C4, B-C5 and
  B-S2.
- **Spec tests:** `execution-specs@origin/projects/binary-trie` at `09d2088` (2026-08-13, the
  branch tip). 168 unit tests in `tests/binary_trie/` + 56 filler functions in
  `tests/binary_tree/eip8297_partitioned_binary_tree/` = **224 test functions**.
- **Devnet:** `CPerezz/pbt-devnet` `main` (differential tree devnet) and
  `migration-m1-tooling` (migration devnet, `M1-REPORT.md`).
- **Client tests:** `CPerezz/go-ethereum@pbt`. geth's trie and EVM-rule tests are listed at
  file level because they corroborate the same surface the spec suite covers; its converter and
  replay tests retain their September enumeration; shared artifact coverage is added above.
  Nethermind's `pbt-state` prototype is explicitly not for merge and Reth has no PBT work, so
  neither contributes tests.

- **Test-execution venues (2026-09-18):** `ethereum/hive@master` `simulators/ethereum/` (no
  binary-trie simulator; `simulators/ethereum/eest` does not exist — the EEST consumers are
  `eels/consume-*`) and `execution-specs@projects/binary-trie` `.github/workflows/`
  (`hive-consume.yaml`, `hive-execute.yaml`, `release_fixtures.yaml`,
  `binary-trie-vectors.yaml`, `test.yaml`). Read for triggers and targets, not re-run.

Last synced from sources: **2026-09-03**, with test counts re-verified **2026-09-17** (no
change) and **test-execution venues added 2026-09-18**. The devnet and client repos move
faster than this file; re-enumerate before quoting counts.

**Targeted artifact update: 2026-09-23.** [Hive PR #1614](https://github.com/ethereum/hive/pull/1614) at `b8703d2c782fdd18948f1ce771f447b8c027b852`; manifest counts and source inspected, reported client results not re-run. Other source snapshots retain their dates.
