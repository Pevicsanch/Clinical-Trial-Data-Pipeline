-- Staging view for interventions (Silver layer)
-- Unnests interventions array from raw JSON (1:N with studies)

CREATE OR REPLACE VIEW stg_interventions AS
SELECT
    raw_json->>'$.protocolSection.identificationModule.nctId' AS nct_id,
    intervention->>'type' AS intervention_type,
    intervention->>'name' AS intervention_name
FROM raw_studies,
LATERAL unnest(from_json(
    raw_json->'$.protocolSection.armsInterventionsModule.interventions',
    '[{"type": "VARCHAR", "name": "VARCHAR"}]'
)) AS t(intervention);
