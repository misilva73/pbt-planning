# Online versus offline state migration

[EIP-8347](https://eips.ethereum.org/EIPS/eip-8347) proposes **offline conversion** from MPT to PBT. This page summarizes why, and what an online overlay would cost. Both approaches can be designed correctly. Future assumptions about ePBS, zkEVM proving, or a 400M gas limit are scenarios, not prerequisites established by EIP-8347.

## The two designs

| | Online overlay | Offline snapshot (EIP-8347) |
|---|---|---|
| Conversion | Runs incrementally inside consensus | Runs against a finalized anchor outside consensus |
| Commitment during conversion | Tracks a partly converted state | Remains a full MPT root until one swap fork |
| Catch-up | Follows block execution | Applies BAL post-values to the converted PBT |
| Storage | Can retire old entries progressively | Holds both trees during the transition |
| Proofs | May need a hybrid proof while state is split | Use one whole-state commitment on either side of the fork |
| Failure handling | Conversion errors affect live consensus | Failed conversion can be retried before activation |

The offline path adds a large, off-chain artifact. EIP-8347 addresses distributor trust through verification against the finalized MPT `stateRoot` and keeps BAL replay bounded with periodic re-anchors. It still needs enough disk, preimages, and operational rehearsal. See [migration](04-migration.md).

## The conversion-pointer question

A positional pointer could tell an online client whether a key belongs in the old or new tree and avoid two reads for every access. That requires a deterministic consensus cursor and write rules for keys around the moving boundary. It also needs special handling for shared, content-addressed code, reorgs, and range-based sync. This is a design argument, not a feature specified by the online-overlay EIPs.

## What changes the trade-off

- **Proving:** If validity proofs are used during conversion, an online design must prove each conversion step. Offline conversion happens outside that proof.
- **Scheduling:** Online conversion needs a fixed amount of work per block or a way to account for lag. More execution load can make that harder.
- **Disk:** Offline nodes temporarily hold two complete commitments; online conversion can retire MPT data progressively.
- **Observability:** Offline conversion is not visible to consensus before the swap. EIP-8347 proposes signed shadow roots as an external agreement signal, with transport still unspecified.
- **Network conditions:** BAL availability is required for offline catch-up. More per-slot processing headroom could help online conversion, but depends on a future fork's actual rules.

## Conclusion

EIP-8347 chooses offline conversion to keep the swap a single commitment change and keep conversion outside consensus. The cost is temporary duplicate state and a verifiable distribution process. A single-read online overlay would narrow the read-cost objection, but would retain in-consensus conversion and cursor complexity. Exact cost comparisons need measured client data, not assumed future protocol parameters.

For historic proposals, see [EIP-7612](https://eips.ethereum.org/EIPS/eip-7612), [EIP-7748](https://eips.ethereum.org/EIPS/eip-7748), and [design evolution](05-design-evolution.md).
