# Gas and access events

PBT changes the work needed to read and write state, but [EIP-8297](https://eips.ethereum.org/EIPS/eip-8297) does **not** set new gas prices. [EIP-8347](https://eips.ethereum.org/EIPS/eip-8347#backwards-compatibility) keeps gas and execution semantics unchanged at the commitment swap and calls for a separate, benchmark-based repricing EIP. No PBT-specific costs should be treated as final yet.

## What changes in the data layout

Account fields and the first 64 storage slots share a header stem. Later storage slots share account-specific groups. All contract code is stored in `CODE_ZONE`, in 31-byte payloads plus a one-byte PUSHDATA count. Contracts with identical bytecode share leaves. These facts can change read latency and caching, but the gas effect needs measurement on client implementations and representative hardware.

## Baseline and proposed pricing

[EIP-8038](https://eips.ethereum.org/EIPS/eip-8038) and [EIP-8037](https://eips.ethereum.org/EIPS/eip-8037) are related state-access and creation-gas proposals, not the PBT price schedule. Their status and constants may change. A PBT repricing should benchmark cold and warm account reads, storage reads and writes, code-metadata reads, and access-list behavior against the gas schedule actually active at the swap. [A-S2](../roadmap/deliverables/A-S2-gas-cost-recalibration.md) tracks this work; [A-T4](../roadmap/deliverables/A-T4-hardware-matrix-benchmarks.md) tracks measurements.

[EIP-2926](https://eips.ethereum.org/EIPS/eip-2926) studies chunk-granular code access. PBT fixes the **tree representation** at 31 code bytes per 32-byte leaf; it does not by itself define when execution charges a code-chunk access or how sharing affects gas. Any access-event identity, warm/cold scope, and charge must be specified in the separate pricing work. A Verkle-era [mainnet code-chunk study](https://hackmd.io/@jsign/verkle-code-mainnet-chunking-analysis) is useful evidence, but its estimates are not PBT gas constants.

## Measurement checklist

- Read and write costs by client and hardware, including same-stem and different-stem access.
- Code execution, `EXTCODECOPY`, creation, and shared-code workloads.
- Worst-case slot and chunk patterns, cache pressure, and concurrent MPT/PBT operation during migration.
- Consensus safety of any proposed decrease; if PBT access is more expensive, EIP-8347 says an increase must precede the commitment swap.

See [key derivation](03-key-derivation.md#access-events-gas), [open questions](../open-questions.md), and the [source index](07-sources.md).
