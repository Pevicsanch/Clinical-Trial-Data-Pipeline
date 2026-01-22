-- Study duration analysis
-- Answers: Timeline analysis of study durations?

SELECT
    study_type,
    phase,
    COUNT(*) AS trial_count,
    ROUND(AVG(
        DATEDIFF('month',
            TRY_CAST(start_date AS DATE),
            TRY_CAST(completion_date AS DATE)
        )
    ), 1) AS avg_duration_months,
    MIN(
        DATEDIFF('month',
            TRY_CAST(start_date AS DATE),
            TRY_CAST(completion_date AS DATE)
        )
    ) AS min_duration_months,
    MAX(
        DATEDIFF('month',
            TRY_CAST(start_date AS DATE),
            TRY_CAST(completion_date AS DATE)
        )
    ) AS max_duration_months
FROM stg_studies
WHERE start_date IS NOT NULL
  AND completion_date IS NOT NULL
GROUP BY study_type, phase
ORDER BY avg_duration_months DESC NULLS LAST;
