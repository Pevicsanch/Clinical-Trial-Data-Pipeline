-- Most common conditions being studied
-- Answers: What are the most common conditions being studied?

SELECT
    condition_name,
    COUNT(DISTINCT nct_id) AS trial_count
FROM stg_conditions
GROUP BY condition_name
ORDER BY trial_count DESC
LIMIT 20;
