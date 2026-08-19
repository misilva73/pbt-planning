-- Storage-read events, aggregated server-side per project-scope.md ("Part 1 data contract"):
-- grouping preserves every dimension required by classification and dedup while collapsing
-- repeated reads of the same (block, transaction, address, slot) into a read_count.
SELECT
    block_number,
    transaction_index,
    contract_address AS address,
    slot,
    count() AS read_count
FROM canonical_execution_storage_reads
WHERE meta_network_name = 'mainnet'
  AND block_number BETWEEN {start_block} AND {end_block}
GROUP BY block_number, transaction_index, address, slot
