# 03 — Key Derivation & Tree Embedding

> Current design per [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297).
> The tree hash is not final; BLAKE3 is used in the reference implementation.
> `code_hash` remains Keccak256 of bytecode.

All Ethereum state is embedded into the single key/value space. Data accessed together
is **co-located under one shared prefix (stem)** to minimize branch openings.

## Constants

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `BASIC_DATA_LEAF_KEY` | 0 | sub-index of the packed header leaf |
| `CODE_HASH_LEAF_KEY` | 1 | sub-index of the code-hash leaf |
| `DELEGATION_LEAF_KEY` | 2 | sub-index of the EIP-7702 delegation-indicator leaf |
| `HEADER_STORAGE_OFFSET` | 64 | storage slots 0..63 live in the header at sub-indices 64..127 |
| `HEADER_STORAGE_SLOTS` | 64 | number of storage slots held in the header stem |
| `STEM_SUBTREE_WIDTH` | 256 | leaves per stem (sub-index range) |
| `ACCOUNT_ZONE` | `0x00` | account headers |
| `CODE_ZONE` | `0x01` | code chunks, content-addressed |
| `STORAGE_ZONE` | `0xFF` | storage |
| `ACCOUNT_KEY_LENGTH` | 34 | `1 + 32 + 1` |
| `CODE_KEY_LENGTH` | 34 | `1 + 32 + 1` |
| `STORAGE_KEY_LENGTH` | 66 | `1 + 32 + 32 + 1` |

Required invariant: `HEADER_STORAGE_OFFSET + HEADER_STORAGE_SLOTS <= STEM_SUBTREE_WIDTH`.

The header sub-indices in use are exactly `BASIC_DATA_LEAF_KEY`, `CODE_HASH_LEAF_KEY`,
`DELEGATION_LEAF_KEY`, and `HEADER_STORAGE_OFFSET .. HEADER_STORAGE_OFFSET +
HEADER_STORAGE_SLOTS - 1`. **No code chunk lives in the header** — there is no
`CODE_OFFSET` constant, and code is always addressed via `CODE_ZONE` regardless of
chunk index (see [Code](#code) below; this replaces an earlier design where chunks
0..127 lived per-account in the header stem — see
[05-design-evolution.md](05-design-evolution.md)).

**`CODE_HASH_LEAF_KEY` and `DELEGATION_LEAF_KEY` are mutually exclusive**: being
delegated (EIP-7702) and holding contract code are mutually exclusive conditions, so
every account that exists holds exactly one of the two leaves, never both and never
neither (see [Delegation indicators](#delegation-indicators-eip-7702) below).

## Key construction primitives

```python
def key_hash(inp: bytes) -> bytes32:
    return blake3(inp).digest()      # reference impl; hash not final

def get_tree_key(zone: int, tree_position: bytes, sub_index: int) -> bytes:
    return bytes([zone]) + tree_position + bytes([sub_index])

def address20_to_address32(address: Address) -> Address32:
    return b"\x00" * 12 + address    # legacy 20-byte address -> Address32
```

Addresses are passed as `Address32`. A key = `zone byte || tree position || sub-index`;
the zone byte + tree position is the **stem**.

## Account header

Each account has **exactly one header stem**, keyed by the address alone.

```python
def get_tree_key_for_header(address: Address32, sub_index: int) -> bytes:
    key = get_tree_key(ACCOUNT_ZONE, key_hash(address), sub_index)
    assert len(key) == ACCOUNT_KEY_LENGTH   # 34
    return key

def get_tree_key_for_basic_data(address):  return get_tree_key_for_header(address, BASIC_DATA_LEAF_KEY)  # sub 0
def get_tree_key_for_code_hash(address):   return get_tree_key_for_header(address, CODE_HASH_LEAF_KEY)   # sub 1
def get_tree_key_for_delegation(address):  return get_tree_key_for_header(address, DELEGATION_LEAF_KEY)  # sub 2
```

The header stem holds, under one shared prefix:

- **`BASIC_DATA`** (sub-index 0) — packed fields (see below)
- **`CODE_HASH`** (sub-index 1) — `keccak256(bytecode)`, present **unless** the account is
  delegated (see below)
- **`DELEGATION`** (sub-index 2) — present **only if** the account is delegated (EIP-7702)
- **Storage slots 0..63** — at sub-indices `64..127`

No code chunk lives in the header stem — all code is content-addressed in `CODE_ZONE`
(see [Code](#code)).

Packing basic data into one leaf needs one branch opening instead of three or four,
reducing proof work. Any gas change needs a separate pricing rule. Setting any header field also sets
`version` to zero. `code_hash` and `code_size` are set on contract or EOA creation.

### BASIC_DATA layout

Fields packed into the `BASIC_DATA` leaf. **`code_size` is 4 bytes at offset 4** (widened
from the earlier 3 bytes at offset 5, taking one reserved byte); every other field keeps
its position:

- `version` (1 byte)
- reserved bytes
- `code_size` — **4 bytes at offset 4**, holds up to `2^32 − 1`
- `nonce`, `balance` (packed)

`EXTCODEHASH` is unaffected: the `code_hash` leaf stores `keccak256(bytecode)`
regardless of the tree's merkelization hash. A codeless account's code-hash leaf holds
the Keccak hash of empty bytecode.

## Code

**Every** code chunk, from chunk 0 onward, lives in `CODE_ZONE`, **content-addressed by
`code_hash`** — no chunk lives in the header stem and no chunk is keyed by address.
Contracts with identical bytecode always share the same leaves for the whole of their
code, not just an "overflow" tail past some size threshold. On account deletion, code leaves remain if another resulting-state account uses the
same `code_hash`. Under current lifecycle rules this can be decided from the
transaction, without a global reference count (see
[02-tree-structure.md § Zero values and deletion](02-tree-structure.md#zero-values-and-deletion)).
This replaces an earlier design where chunks 0..127 (~4 KB) lived per-account in the
header stem and only overflow chunks were content-addressed — see
[05-design-evolution.md](05-design-evolution.md).

```python
def get_tree_key_for_code_chunk(code_hash, chunk_id):
    tree_index = chunk_id // STEM_SUBTREE_WIDTH
    sub_index  = chunk_id %  STEM_SUBTREE_WIDTH
    key = get_tree_key(CODE_ZONE, key_hash(code_hash + tree_index.to_bytes(32, "big")), sub_index)
    assert len(key) == CODE_KEY_LENGTH
    return key
```

Chunk `i` stores a 32-byte value: bytes 1..31 are the i'th 31-byte slice of code;
byte 0 encodes how many leading bytes are inside a PUSH data region (chunkification per
[EIP-2926](https://eips.ethereum.org/EIPS/eip-2926) chunk-based code merkleization, via
`chunkify_code`).

## Delegation indicators (EIP-7702)

**Changed post-August-2026** (EIP-8297 [PR #12114](https://github.com/ethereum/EIPs/pull/12114),
EIP-8347 [PR #12115](https://github.com/ethereum/EIPs/pull/12115) — see
[05-design-evolution.md](05-design-evolution.md)). An account whose code is an
[EIP-7702](https://eips.ethereum.org/EIPS/eip-7702) delegation indicator — the 23 bytes
`0xef0100 || target` — holds it in its **header stem**, not as code:

```python
def get_tree_key_for_delegation(address: Address32):
    return get_tree_key_for_header(address, DELEGATION_LEAF_KEY)
```

The leaf value is the 23-byte indicator followed by nine zero bytes; `code_size` (in
`BASIC_DATA`) is fixed at 23. A delegated account emits **no `CODE_HASH_LEAF_KEY` leaf
and no `CODE_ZONE` chunk leaves** — the two header leaves are mutually exclusive (see
above), so there is nothing to content-address or reference-count for a delegation.
Clearing a delegation (an EIP-7702 authorization to the zero address) removes the
`DELEGATION_LEAF_KEY` leaf and restores `CODE_HASH_LEAF_KEY` holding the hash of empty
bytecode, with `code_size` zeroed.

This replaced an earlier design where the delegation indicator was chunked into
`CODE_ZONE` like ordinary code and content-addressed (shared across accounts delegating
to the same target). That broke locality — a node couldn't tell from block-local data
alone whether another account still referenced the same shared delegation leaf before
deleting it — and broke the migration's dual-check, which reassembles bytecode from
`CODE_ZONE` chunks and re-hashes to `code_hash`; a 23-byte indicator isn't reconstructible
that way. See [04-migration.md](04-migration.md#delegation-indicators-eip-7702) for the
converter/BAL-replay side.

## Storage

Slots 0..63 live in the header stem (sub-indices 64..127). Slots ≥64 live in the
storage zone. A storage key's stem = **storage zone byte + two full digests**:

```python
def storage_tree_position(address: Address32, tree_index: int) -> bytes:
    prefix = key_hash(address)                                   # per-account bucket
    suffix = key_hash(address + tree_index.to_bytes(32, "big"))  # spreads groups, bound to address
    return prefix + suffix

def get_tree_key_for_storage_slot(address, storage_key):
    if storage_key < HEADER_STORAGE_SLOTS:                       # storage_key < 64 -> header
        return get_tree_key_for_header(address, HEADER_STORAGE_OFFSET + storage_key)
    tree_index = storage_key // STEM_SUBTREE_WIDTH
    sub_index  = storage_key %  STEM_SUBTREE_WIDTH
    key = get_tree_key(STORAGE_ZONE, storage_tree_position(address, tree_index), sub_index)
    assert len(key) == STORAGE_KEY_LENGTH                        # 66
    return key
```

- `key_hash(address)` places **all** of an account's overflow storage under one shared
  prefix — its **storage bucket** (the unit later expiry/partial-statefulness prune or sync).
- `key_hash(address || tree_index)` spreads the account's storage groups within that
  bucket, and is **bound to the address** so a bucket collision cannot correlate two
  accounts' storage layouts (and restricts grinding to the attacker's own bucket).
- A **storage group** = an aligned range of 256 slots sharing one `tree_index`; its
  slots share a stem and differ only in the sub-index byte. Adjacent slots (common in
  mappings/arrays) group together.
- **Group 0 exception:** slots 0..63 live in the header, so group 0's storage-zone
  leaves are slots 64..255 only.

## Access events (gas)

The key layout identifies shared stems and code leaves, but does not set gas charges.
A separate repricing proposal must define event identity, warm/cold scope, and costs
from client benchmarks. In particular, a shared code key does not by itself specify
whether or when a transaction is charged for accessing it. See
[gas and access events](08-gas-and-access-events.md).

## Worked test vectors

`H(x)` is the full 32-byte digest of `x`. `A || 3` = `A` concatenated with the 32-byte
big-endian encoding of the integer.

```
# Account BASIC_DATA of address A
key    = 0x00 || H(A) || 0x00               length = 1 + 32 + 1 = 34

# Storage slot 5 of A  (in header, since 5 < 64)
sub_idx = HEADER_STORAGE_OFFSET + 5 = 69 (0x45)
key     = 0x00 || H(A) || 0x45              length = 34

# Storage slot 1000 of A  (storage zone, since 1000 >= 64)
tree_index = 1000 // 256 = 3
sub_idx    = 1000 %  256 = 232 (0xE8)
key        = 0xFF || H(A) || H(A || 3) || 0xE8   length = 1 + 32 + 32 + 1 = 66

# Code chunk 5 of bytecode with hash C  (always content-addressed)
tree_index = 5 // 256 = 0
sub_idx    = 5 %  256 = 5 (0x05)
key        = 0x01 || H(C || 0) || 0x05      length = 34

# Code chunk 300 of the same bytecode
tree_index = 300 // 256 = 1
sub_idx    = 300 %  256 = 44 (0x2C)
key        = 0x01 || H(C || 1) || 0x2C      length = 34
```
