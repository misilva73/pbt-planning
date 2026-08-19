-- Block-final net nonce mutations. Used as half of the observed-BASIC_DATA mutation
-- proxy (project-scope.md): union with balance mutations on (block, account).
SELECT
    block_number,
    address,
    argMin(from_value, tuple(transaction_index, internal_index)) AS from_value,
    argMax(to_value, tuple(transaction_index, internal_index)) AS to_value
FROM canonical_execution_nonce_diffs
WHERE meta_network_name = 'mainnet'
  AND block_number BETWEEN {start_block} AND {end_block}
GROUP BY block_number, address
HAVING from_value != to_value
