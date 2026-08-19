-- Transaction mutations (project-scope.md "transaction mutation"): order diffs for a
-- (block, transaction, address, slot) by internal_index, take earliest from_value and
-- latest to_value, drop the key if they're equal. This is the incremental-client
-- sensitivity series.
SELECT
    block_number,
    transaction_index,
    address,
    slot,
    argMin(from_value, internal_index) AS from_value,
    argMax(to_value, internal_index) AS to_value,
    count() AS n_diffs
FROM canonical_execution_storage_diffs
WHERE meta_network_name = 'mainnet'
  AND block_number BETWEEN {start_block} AND {end_block}
GROUP BY block_number, transaction_index, address, slot
HAVING from_value != to_value
