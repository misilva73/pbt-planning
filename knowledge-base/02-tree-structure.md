# 02 — Tree Structure & Merkelization

> This documents the **current design per [EIP PR #11978](https://github.com/ethereum/EIPs/pull/11978)**.
> The published EIP-8297 page and the rendered spec site still describe an earlier
> variant (fixed 32-byte keys, `StemNode`/`InternalNode`, truncated storage prefix).
> See [05-design-evolution.md](05-design-evolution.md) for the diff.

## Keys

The tree stores **key → value** entries:

- **Key**: a non-empty, **variable-length** byte string, at most `MAX_KEY_LENGTH`
  bytes. Keys MUST be **prefix-free** — no key may be a prefix of another key in the
  tree. `insert` rejects keys that violate either constraint.
- **Value**: a 32-byte blob.

The **first byte** of every key is the **zone identifier** `Z`. A key is conceptually
`zone byte || hash-derived tree position || sub-index byte`; the zone byte + tree
position together form the **stem**.

Keys are traversed in **big-endian bit order** (MSB first): the path bit list is
`_bytes_to_bits(key)`, bit 0 = MSB of byte 0.

```python
def _bytes_to_bits(data: bytes) -> list[int]:
    return [(byte >> (7 - i)) & 1 for byte in data for i in range(8)]
```

### Prefix-freedom via fixed per-zone length

Every key produced by the embedding has a length **fixed by its zone** (see
[03-key-derivation.md](03-key-derivation.md)):

| Zone | Category | Key length |
|------|----------|-----------|
| `0x00` | Account headers | 34 bytes (`ACCOUNT_KEY_LENGTH`) |
| `0x01` | Code overflow (content-addressed) | 34 bytes (`CODE_KEY_LENGTH`) |
| `0x02`–`0xFE` | Reserved for future categories | — |
| `0xFF` | Storage | 66 bytes (`STORAGE_KEY_LENGTH`) |

Fixing one length per zone is what makes keys prefix-free **within** a zone (a shorter
same-zone key would otherwise be a prefix of a longer one). Keys of **different** zones
already differ in their first byte. Implementations MUST assert the length of every key
they construct. New categories MUST be allocated from `0x02`–`0xFE` and MUST keep their
keys mutually prefix-free.

### Maximum key length

`MAX_KEY_LENGTH = 8192` bytes. A branch prefix's bit count is stored in two bytes
(see merkelization), so the largest representable prefix is `2^16 − 1 = 65535` bits.
Two `L`-byte keys can share up to `8*L − 1` bits; solving `8*L − 1 ≤ 65535` gives
`L ≤ 8192`. `insert` MUST reject keys longer than `MAX_KEY_LENGTH` unconditionally
(so the bound is a stated property of every key, not a latent failure that only
appears once a second key shares enough prefix to overflow the count field).

## Node types (two)

```python
class LeafNode:
    def __init__(self, key: bytes, value: bytes):
        self.key = key          # the COMPLETE key
        self.value = value      # 32 bytes

class BranchNode:
    def __init__(self, prefix: list[int]):
        self.prefix = prefix    # bit string (possibly empty) of the shared run
        self.left = None
        self.right = None
```

- **`LeafNode`** commits its **complete key** (not a suffix relative to its position),
  so its meaning — and hash — never depends on where it sits. Splitting or merging
  branches elsewhere never changes an unrelated leaf's hash. *Position-independent.*
- **`BranchNode`** carries a `prefix`: the run of bits shared by every key below it
  that are **not** already consumed by an ancestor. There is **no separate extension
  node** — the prefix *is* the path compression.
- A `BranchNode` MUST have **two non-empty children**. A prefix shorter than the true
  shared run would leave the keys still agreeing at the next bit (emptying one side),
  which is invalid. This forces every prefix to be exactly the shared run, so **each
  key/value set has exactly one valid tree** (canonical form).

There is no `EmptyNode` type; an empty tree/child is represented by `None` and hashes
to 32 zero bytes.

## Insertion

Insert walks the path by bits. On hitting a `LeafNode`: if keys match, update value;
otherwise compute the shared run, make a `BranchNode` with that prefix and split the
two leaves left/right by the first differing bit. On a `BranchNode`: match against its
prefix; if fully matched, descend by the next bit; if the key **diverges inside** the
prefix, split the branch — a new branch takes the bits before divergence, the surviving
branch keeps the bits after.

```python
def insert(self, key: bytes, value: bytes):
    assert 1 <= len(key) <= MAX_KEY_LENGTH, "key length out of range"
    assert len(value) == 32, "value must be 32 bytes"
    if self.root is None:
        self.root = LeafNode(key, value)
        return
    self.root = self._insert(self.root, _bytes_to_bits(key), key, value, 0)

def _insert(self, node, bits, key, value, depth):
    if isinstance(node, LeafNode):
        if node.key == key:
            node.value = value
            return node
        other_bits = _bytes_to_bits(node.key)
        limit = min(len(bits), len(other_bits))
        run = 0
        while depth + run < limit and bits[depth + run] == other_bits[depth + run]:
            run += 1
        assert depth + run < limit, "insert violates prefix-freedom"
        prefix = bits[depth:depth + run]
        new_leaf = LeafNode(key, value)
        branch = BranchNode(prefix)
        if bits[depth + run] == 0:
            branch.left, branch.right = new_leaf, node
        else:
            branch.left, branch.right = node, new_leaf
        return branch

    matched = 0
    while (matched < len(node.prefix) and depth + matched < len(bits)
           and bits[depth + matched] == node.prefix[matched]):
        matched += 1
    assert depth + matched < len(bits), "insert violates prefix-freedom"
    if matched == len(node.prefix):
        split = depth + matched
        if bits[split] == 0:
            node.left = self._insert(node.left, bits, key, value, split + 1)
        else:
            node.right = self._insert(node.right, bits, key, value, split + 1)
        return node

    # key diverges inside the prefix: split the branch
    survivor = BranchNode(node.prefix[matched + 1:])
    survivor.left, survivor.right = node.left, node.right
    new_leaf = LeafNode(key, value)
    new_branch = BranchNode(node.prefix[:matched])
    if bits[depth + matched] == 0:
        new_branch.left, new_branch.right = new_leaf, survivor
    else:
        new_branch.left, new_branch.right = survivor, new_leaf
    return new_branch
```

## Zero values and deletion

Writing 32 zero bytes **stores that value like any other**: the leaf stays present, and
a zero-valued leaf is **distinct from an absent key** (it commits to a different root).
EVM execution never removes entries — insertion and in-place update are the only
mutations, so clients never need delete logic that re-canonicalizes by merging a lone
surviving child back into its parent. Removing entries is reserved for a future
**state-expiry** mechanism (see [06-open-questions.md](06-open-questions.md)).

## Merkelization

Tags: `LEAF_TAG = 0x00`, `BRANCH_TAG = 0x01`. `H` is the tree's 32-byte hash function
(the same function as `key_hash`; BLAKE3 in the reference implementation).

- `leaf_hash   = H(LEAF_TAG || key || value)`
- `branch_hash = H(BRANCH_TAG || encode_bit_prefix(prefix) || left_hash || right_hash)`
- hash of an empty tree / `None` child = `[0x00] * 32`

`encode_bit_prefix` packs a bit string as a **2-byte big-endian bit count** followed by
the bits (MSB first), zero-padded to a byte boundary:

```python
def encode_bit_prefix(prefix: list[int]) -> bytes:
    assert len(prefix) < 2**16, "prefix exceeds encodable bit count"
    packed = bytearray((len(prefix) + 7) // 8)
    for i, bit in enumerate(prefix):
        packed[i // 8] |= bit << (7 - i % 8)
    return len(prefix).to_bytes(2, "big") + bytes(packed)

def merkelize(node) -> bytes:
    if node is None:
        return b"\x00" * 32
    if isinstance(node, LeafNode):
        return H(bytes([LEAF_TAG]) + node.key + node.value)
    return H(
        bytes([BRANCH_TAG])
        + encode_bit_prefix(node.prefix)
        + merkelize(node.left)
        + merkelize(node.right)
    )
```

**Preimage injectivity (security):** every node's hash preimage begins with a one-byte
tag distinguishing leaf from branch, and a branch's prefix carries an explicit bit
count. No leaf and branch preimage can coincide, and no two prefixes of different bit
length pack to the same bytes — so the logical-node → preimage mapping is injective.

## Why path compression (prefix) exists

Storage buckets manufacture long shared runs: every one of an account's overflow
storage groups shares the same `key_hash(address)` (up to 256 bits). Without
compression this would produce long chains of branch nodes each with a single occupied
child. Folding the shared run into a branch's `prefix` collapses each chain to one node.
This also bounds the proof-size cost of a *grinded* set of groups (see
[06-open-questions.md](06-open-questions.md) — "Grinding").

## Arity-2 rationale

Average branch ≈ `32 * (k−1) * log(N) / log(k)` bytes, minimized at `k = 2`. For
`N = 2^24`:

| arity `k` | branch (chunks) | branch (bytes) |
|-----------|-----------------|----------------|
| 2 | 24 | 768 |
| 4 | 36 | 1152 |
| 8 | 56 | 1792 |
| 16 | 90 | 2880 |

Continue to [03-key-derivation.md](03-key-derivation.md) for how real state maps into keys.
