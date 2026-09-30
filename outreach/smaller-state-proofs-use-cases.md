# What smaller Ethereum state proofs could enable

*Outreach draft · 24 September 2026*

## The claim, precisely

[EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) proposes replacing Ethereum's Merkle Patricia Tries (MPT) with a Partitioned Binary Tree (PBT). Its binary branches, compressed paths, and shared paths for related leaves are designed to reduce the bytes needed to prove an account field, storage slot, or code chunk against an execution state root. Smaller proofs can lower network transfer, storage, and on-chain calldata costs. The benefit depends on the query: a single account, several nearby slots, and a block-wide witness have different savings. The EIP's branch-size examples are illustrations, not measured savings for every application.

Here, **state proof** means evidence about execution state committed by a block's `stateRoot`. A transaction receipt proof, beacon-chain light-client proof, application-specific Merkle proof, and zero-knowledge proof are different objects. PBT does not automatically shrink them.

## Use cases that consume state proofs today

| Consumer | What is proved today | Why smaller PBT proofs help | Concrete Examples |
| --- | --- | --- | --- |
| **Execution light clients** | RPC answers about balances, code, and storage. | Less data for verified wallet and app reads. | [Helios](https://github.com/a16z/helios) and [Nimbus Verified Proxy](https://github.com/status-im/nimbus-eth1/blob/master/nimbus_verified_proxy/README.md) verify RPC state proofs. [Ambire Wallet](https://help.ambire.com/en/articles/16106392-how-to-enable-colibri-verification) uses Colibri to verify balances and ENS results; [Nethereum Wallet](https://docs.nethereum.com/docs/consensus-light-client/guide-verified-state/) verifies balances. [Eth Docker](https://ethdocker.com/Usage/Advanced/RPCProxy/) provides a Nimbus proxy setup for node operators. |
| **DAO voting from an Ethereum snapshot** | Voting power stored in Ethereum contracts at a proposal's snapshot block. | Smaller proofs reduce data sent and checked for each vote. | [Aave Governance V3](https://github.com/aave-dao/aave-governance-v3/blob/main/docs/overview.md) and [Snapshot X](https://www.herodotus.cloud/en/learn/snapshot-x-storage-proofs) verify Ethereum voting power with storage proofs. |
| **Verified Ethereum proof RPCs** | Ethereum L1 storage values used by an L2 service. | Smaller proofs reduce RPC responses and the data relayed to the L2. | [Frax's Fraxtal Merkle Proof Oracles](https://docs.frax.finance/frax-oracle/fraxtal-merkle-proof-oracles) use `eth_getProof` to bring L1 vault data to Fraxtal price feeds, including sFRAX and sfrxETH. |

The near-term pitch is therefore **cheaper verified state access for existing proof consumers**. The size of the gain should be benchmarked against actual MPT proofs, including account-plus-storage paths, multi-slot reads, absence proofs, and code reads. We should also get a better view of how much usage these proofs get today.

### Do canonical L2 and stablecoin bridges use Ethereum state proofs?

**The surveyed canonical transfer paths are not direct PBT beneficiaries.** A bridge can verify a Merkle proof without verifying an *Ethereum L1 execution-state* proof. The commitment's origin matters:

| Bridge | What its transfer path authenticates | Direct gain from smaller Ethereum L1 state proofs? |
| --- | --- | --- |
| **OP Mainnet and Base (OP Stack)** | L1 deposits are derived from deposit events in L1 receipts. L2 withdrawals prove a message in the **L2** `L2ToL1MessagePasser` storage against an L2 output commitment. ([Base derivation](https://docs.base.org/base-chain/specs/protocol/consensus/derivation); [OP withdrawal spec](https://specs.optimism.io/protocol/withdrawals.html)) | **No** for the standard deposit/withdrawal path. The withdrawal proof concerns L2 storage; changing Ethereum L1's tree does not shrink it. |
| **Arbitrum One (Nitro)** | L1-to-L2 deposits use the Inbox; an L2-to-L1 Outbox execution supplies a Merkle proof that the message is in the rollup's **send root**. ([Nitro whitepaper](https://docs.arbitrum.io/nitro-whitepaper.pdf); [Outbox interface](https://github.com/OffchainLabs/nitro-contracts/blob/main/src/bridge/IOutbox.sol)) | **No**; this is a rollup message-tree proof. |
| **Scroll** | L2-to-L1 messages enter its separate append-only **Withdraw Trie**; withdrawal execution proves message inclusion under a root finalized on L1. ([Scroll cross-domain messaging](https://docs.scroll.io/en/technology/bridge/cross-domain-messaging/)) | **No**; the Withdraw Trie is separate from Ethereum's state tree. |
| **ZKsync Era** | L2 withdrawal finalization proves inclusion of an **L2-to-L1 message** to the L1 bridge. ([ZKsync asset bridging](https://docs.zksync.io/zksync-protocol/rollup/bridging-assets)) | **No** for the described withdrawal path. |
| **Starknet / StarkGate** | The L1 bridge accepts deposits through L1-to-L2 messaging; after a Starknet state update, an L2-to-L1 withdrawal message is recorded in the L1 Core contract and consumed by the bridge. ([StarkGate overview](https://docs.starknet.io/starkgate/cancelling-a-deposit/)) | **No**; finalization consumes a recorded message, rather than an Ethereum state proof supplied per transfer. |

**Stablecoins follow the transfer route, not a special proof format.** Bridged ERC-20s such as bridged USDC on [Arbitrum](https://docs.arbitrum.io/arbitrum-bridge/quickstart), or a stablecoin sent through an OP Stack standard bridge, use that bridge's messaging and withdrawal mechanism. Native USDC transferred via [Circle CCTP](https://www.circle.com/cross-chain-transfer-protocol) instead uses burn, Circle's signed attestation, and mint; it is a separate route and does not supply an Ethereum state proof to the destination. The same distinction applies when a token has both native and bridged forms. This survey addresses canonical transfer paths, not every third-party bridge or auxiliary light-client service.

An **Ethereum-state-proof bridge** remains a plausible future design: its destination could verify an L1 contract slot against an authenticated L1 state root, making the relayed proof smaller after PBT support. [Succinct's Goerli-to-Gnosis proof-of-consensus bridge](https://github.com/succinctlabs/eth-proof-of-consensus) demonstrates the idea but calls itself a prototype.

## Use cases smaller proofs could help unlock

### 1. Private and verifiable reads

The [EF Reads team's research design](https://ethresear.ch/t/sharded-pir-design-for-the-ethereum-state/24552) lets a wallet ask for Ethereum data without telling the server which address or storage slot it wants. It splits data into databases suited to different private information retrieval (PIR) schemes and sends decoy queries to the other databases, so the choice of database does not reveal the request. For live state, the design queries both a larger snapshot and a small database of recent changes.

The wallet must also check the answer against an authenticated state root. That means privately retrieving the **value and its state proof**. A normal `eth_getProof` request after the private lookup would expose the address or slot.

The Reads team is exploring two ways to deliver the proof within PIR:

| Proof delivery | Main cost in the proposed design | Effect of smaller PBT proofs |
| --- | --- | --- |
| **Fetch proof nodes privately:** query a PIR database for each tree level. | Several private queries and substantial server work. | A binary branch has one sibling hash instead of up to 15 in an MPT branch, so each path can be cheaper to retrieve and return. |
| **Store a proof with each value:** one private query returns both. | Much larger PIR database and more work to keep attached proofs current. | Shorter proofs reduce each stored record and the reply size. |

The Reads team's **earlier binary-trie model** illustrates the scale of this tradeoff. With about 10 billion leaves, it estimates roughly **9× versus 48×** the work of one PIR lookup for the first approach, and **1,280 versus 4,800 proof bytes per leaf** for the second (binary trie versus MPT).

These are estimates for an earlier trie, **not PBT measurements**. [PBT's compressed paths and key layout](https://eips.ethereum.org/EIPS/eip-8297) need their own measurements in the PIR design.

### 2. Block witnesses for stateless nodes and execution provers

A node without the full execution state could receive a block plus a witness for the account, storage, and code data its transactions touch. The node checks the witness against the pre-state root, re-executes the block, and checks the resulting root. Smaller shared state paths and provable code chunks reduce the bytes that the block producer must distribute.

An L1 execution prover could consume a similar witness when proving block execution. See the [optional execution-proofs EIP](https://eips.ethereum.org/EIPS/eip-8025) for the witness-based execution model.

These applications need a defined witness format, data availability, and resource bounds. PBT alone does not make nodes stateless or create validity proofs.

### 3. Checking pending transactions without full state

A stateless node receiving a pending transaction still needs to decide whether to relay it. For a basic ETH transfer, that means checking the sender's nonce and balance against recent state. Contract-based account validation could also require code and storage reads. The sender or a witness service could supply proofs for those values so the node can check the transaction without keeping the full state.

A validator preparing a proposed inclusion list faces a related problem. It needs to check a transaction before asking a block builder to include it. These are **pre-block** checks, so the block witness in the previous example arrives too late. Smaller PBT proofs could reduce the bandwidth of distributing many pending transactions with individual state witnesses.

Proofs would need refreshing or updating as the chain head changes. A successful check would not guarantee that a transaction remains valid when included. This use case depends on future stateless mempool or inclusion-list rules. [Vitalik identified both workflows back in 2024](https://vitalik.eth.limo/general/2024/10/23/futures4.html#use-cases-of-witnesses-other-than-verifying-blocks).

### 4. Reviving expired state

State expiry lets nodes prune an inactive account's storage subtrie while retaining its commitment. When the owner next uses that storage, a service or the user would supply the missing data and a proof that it matches the retained commitment. The node could then restore the subtrie and execute the transaction. Smaller paths could reduce the proof bytes sent with that restoration. In addition, PBT's separation of account headers and storage slots makes reviving accounts cheaper.

### 5. Private proofs of an Ethereum state condition

An anonymous community could admit someone who held at least 1 ETH at a chosen Ethereum block without learning their address or exact balance. The member would privately give a zero-knowledge prover an Ethereum balance path and evidence that they control the account. A separate circuit would check the path against an authenticated `stateRoot`, test the threshold, and bind the result to a one-use identifier. The community would verify the circuit's final proof.

The Ethereum state path is an input to that private computation. A smaller PBT path could reduce the data the prover receives or retains, but any change to proving time depends on the final tree hash and circuit. The final zero-knowledge proof does not automatically become smaller.

## Post-quantum relevance

Smaller state proofs can leave more bandwidth and storage headroom as other post-quantum components add overhead, and can make PQ-safe, hash-based state verification less costly for light clients and cross-chain consumers. This is a plausible system-level benefit, not a measured offset against future PQ signature sizes.

## Questions

- What are the median and tail byte sizes for MPT versus PBT account, storage, multi-slot, absence, and code proofs on representative mainnet queries?
- Which deployed consumers verify **Ethereum execution state** rather than receipts, beacon state, or an application tree, and what are their calldata and bandwidth costs today?
- For private reads, how much do PBT paths and multiproofs change PIR database size, server work, client bandwidth, and latency in a realistic wallet workload, including per-block updates and decoy queries across zones?
