-- Geographic distribution of clinical trials
-- Answers: Geographic distribution of clinical trials?

SELECT
    country,
    COUNT(DISTINCT nct_id) AS trial_count,
    COUNT(*) AS location_count,
    ROUND(100.0 * COUNT(DISTINCT nct_id) / SUM(COUNT(DISTINCT nct_id)) OVER (), 2) AS pct_of_trials
FROM stg_locations
WHERE country IS NOT NULL
GROUP BY country
ORDER BY trial_count DESC
LIMIT 20;
