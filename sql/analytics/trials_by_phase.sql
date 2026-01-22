-- Trials by study type and phase
-- Answers: How many trials by study type and phase?

SELECT
    study_type,
    phase,
    COUNT(*) AS trial_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM stg_studies
GROUP BY study_type, phase
ORDER BY trial_count DESC;
