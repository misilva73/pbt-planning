-- Block-final net mutations (project-scope.md "block-final net mutation"): order all diffs
-- for a (block, address, slot) by (transaction_index, internal_index), take earliest
-- from_value and latest to_value, drop the key if they're equal. This is the primary
-- commitment series.
SELECT
    block_number,
    address,
    slot,
    argMin(from_value, tuple(transaction_index, internal_index)) AS from_value,
    argMax(to_value, tuple(transaction_index, internal_index)) AS to_value,
    count() AS n_diffs
FROM canonical_execution_storage_diffs
WHERE meta_network_name = 'mainnet'
  AND block_number BETWEEN {start_block} AND {end_block}
GROUP BY block_number, address, slot
HAVING from_value != to_value
