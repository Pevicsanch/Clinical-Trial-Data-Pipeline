-- Interventions by completion rate
-- Answers: Which interventions have the highest completion rates?

SELECT
    i.intervention_type,
    COUNT(DISTINCT i.nct_id) AS trial_count,
    SUM(CASE WHEN s.overall_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_count,
    ROUND(100.0 * SUM(CASE WHEN s.overall_status = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(*), 2) AS completion_rate
FROM stg_interventions i
JOIN stg_studies s ON i.nct_id = s.nct_id
GROUP BY i.intervention_type
HAVING COUNT(DISTINCT i.nct_id) >= 1
ORDER BY completion_rate DESC;
