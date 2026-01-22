-- Staging view for locations (Silver layer)
-- Unnests locations array from raw JSON (1:N with studies)

CREATE OR REPLACE VIEW stg_locations AS
SELECT
    raw_json->>'$.protocolSection.identificationModule.nctId' AS nct_id,
    location->>'$.facility' AS facility,
    location->>'$.city' AS city,
    location->>'$.state' AS state,
    location->>'$.country' AS country,
    CAST(location->>'$.geoPoint.lat' AS DOUBLE) AS latitude,
    CAST(location->>'$.geoPoint.lon' AS DOUBLE) AS longitude
FROM raw_studies,
LATERAL unnest(from_json(
    raw_json->'$.protocolSection.contactsLocationsModule.locations',
    '["JSON"]'
)) AS t(location);
