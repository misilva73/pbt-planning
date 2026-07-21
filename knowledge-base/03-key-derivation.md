# 03 — Key Derivation & Tree Embedding

> Current design per [EIP PR #11978](https://github.com/ethereum/EIPs/pull/11978).
> All hash outputs are unpinned (hash function not final; BLAKE3 in the reference impl).

All Ethereum state is embedded into the single key/value space. Data accessed together
is **co-located under one shared prefix (stem)** to minimize branch openings.

## Constants

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `BASIC_DATA_LEAF_KEY` | 0 | sub-index of the packed header leaf |
| `CODE_HASH_LEAF_KEY` | 1 | sub-index of the code-hash leaf |
| `HEADER_STORAGE_OFFSET` | 64 | storage slots 0..63 live in the header at sub-indices 64..127 |
| `CODE_OFFSET` | 128 | code chunks 0..127 live in the header at sub-indices 128..255 |
| `STEM_SUBTREE_WIDTH` | 256 | leaves per stem (sub-index range) |
| `ACCOUNT_ZONE` | `0x00` | account headers |
| `CODE_ZONE` | `0x01` | overflow code chunks |
| `STORAGE_ZONE` | `0xFF` | storage |
| `ACCOUNT_KEY_LENGTH` | 34 | `1 + 32 + 1` |
| `CODE_KEY_LENGTH` | 34 | `1 + 32 + 1` |
| `STORAGE_KEY_LENGTH` | 66 | `1 + 32 + 32 + 1` |

Required invariant: `STEM_SUBTREE_WIDTH > CODE_OFFSET > HEADER_STORAGE_OFFSET`.

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
```

The header stem holds, under one shared prefix:

- **`BASIC_DATA`** (sub-index 0) — packed fields (see below)
- **`CODE_HASH`** (sub-index 1) — `keccak256(bytecode)`
- **Storage slots 0..63** — at sub-indices `64..127`
- **Code chunks 0..127** — at sub-indices `128..255`

Packing basic data into one leaf needs one branch opening instead of three or four,
lowering gas and simplifying witness generation. Setting any header field also sets
`version` to zero. `code_hash` and `code_size` are set on contract or EOA creation.

### BASIC_DATA layout

Fields packed into the `BASIC_DATA` leaf. **In PR #11978, `code_size` widened from 3
bytes (at offset 5) to 4 bytes (at offset 4)**, taking one reserved byte; every other
field keeps its position:

- `version` (1 byte)
- reserved bytes
- `code_size` — **4 bytes at offset 4**, holds up to `2^32 − 1`
- `nonce`, `balance` (packed)

`EXTCODEHASH` is unaffected: the `code_hash` leaf stores `keccak256(bytecode)`
regardless of the tree's merkelization hash. A codeless account's code-hash leaf holds
the Keccak hash of empty bytecode.

## Code

Chunks 0..127 live in the header stem (sub-indices 128..255). Chunks ≥128 live in
`CODE_ZONE`, **content-addressed by `code_hash`** so contracts with identical bytecode
share leaves (only chunks beyond ~4 KB are shared; the first ~4 KB stay per-account and
need no reference counting).

```python
def get_tree_key_for_code_chunk(address, code_hash, chunk_id):
    if chunk_id < STEM_SUBTREE_WIDTH - CODE_OFFSET:            # chunk_id < 128 -> header
        return get_tree_key_for_header(address, CODE_OFFSET + chunk_id)
    overflow   = chunk_id - (STEM_SUBTREE_WIDTH - CODE_OFFSET)
    tree_index = overflow // STEM_SUBTREE_WIDTH
    sub_index  = overflow %  STEM_SUBTREE_WIDTH
    key = get_tree_key(CODE_ZONE, key_hash(code_hash + tree_index.to_bytes(32, "big")), sub_index)
    assert len(key) == CODE_KEY_LENGTH
    return key
```

Chunk `i` stores a 32-byte value: bytes 1..31 are the i'th 31-byte slice of code;
byte 0 encodes how many leading bytes are inside a PUSH data region (chunkification per
EIP-4762 lineage, via `chunkify_code`).

## Storage

Slots 0..63 live in the header stem (sub-indices 64..127). Slots ≥64 live in the
storage zone. A storage key's stem = **storage zone byte + two full digests**:

```python
def storage_tree_position(address: Address32, tree_index: int) -> bytes:
    prefix = key_hash(address)                                   # per-account bucket
    suffix = key_hash(address + tree_index.to_bytes(32, "big"))  # spreads groups, bound to address
    return prefix + suffix

def get_tree_key_for_storage_slot(address, storage_key):
    if storage_key < CODE_OFFSET - HEADER_STORAGE_OFFSET:        # storage_key < 64 -> header
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

PBT adopts **EIP-4762**'s access-event framework with two required modifications:

1. **Content-addressed code.** Overflow code chunks (≥128) are shared between
   contracts, so their access events MUST be keyed by the
   `(zone, tree_position, sub-index)` tree-key, **not** by `(address, chunk)` — a
   shared chunk is charged once per block regardless of which contract triggers it, and
   the witness contains one copy. Header chunks (0..127) remain per-account.
2. **Branch-cost recalibration.** EIP-4762 prices a witness branch at
   `WITNESS_BRANCH_COST = 1900`, calibrated for shallow (Verkle) branches. PBT's
   branches are deeper, so the witness gas constants MUST be recalibrated for PBT's
   depth profile. **The recalibrated values are not yet fixed in this draft.**

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

# Code chunk 5  (in header, since 5 < 128)
sub_idx = CODE_OFFSET + 5 = 133 (0x85)
key     = 0x00 || H(A) || 0x85              length = 34

# Code chunk 300 of bytecode with hash C  (overflow, since 300 >= 128)
overflow   = 300 - 128 = 172
tree_index = 172 // 256 = 0
sub_idx    = 172 %  256 = 172 (0xAC)
key        = 0x01 || H(C || 0) || 0xAC      length = 34
```
