-- Balance-read events, aggregated server-side. Used as half of the observed-BASIC_DATA
-- read proxy (project-scope.md): union with nonce reads on (block, transaction, account).
SELECT
    block_number,
    transaction_index,
    address,
    count() AS read_count
FROM canonical_execution_balance_reads
WHERE meta_network_name = 'mainnet'
  AND block_number BETWEEN {start_block} AND {end_block}
GROUP BY block_number, transaction_index, address
