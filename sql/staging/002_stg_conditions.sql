-- Staging view for conditions (Silver layer)
-- Unnests conditions array from raw JSON (1:N with studies)

CREATE OR REPLACE VIEW stg_conditions AS
SELECT
    raw_json->>'$.protocolSection.identificationModule.nctId' AS nct_id,
    unnest(from_json(
        raw_json->'$.protocolSection.conditionsModule.conditions',
        '["VARCHAR"]'
    )) AS condition_name
FROM raw_studies;
