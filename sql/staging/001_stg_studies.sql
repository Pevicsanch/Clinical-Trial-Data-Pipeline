-- Staging view for studies (Silver layer)
-- Extracts core fields from raw JSON into a normalized structure

CREATE OR REPLACE VIEW stg_studies AS
SELECT
    raw_json->>'$.protocolSection.identificationModule.nctId' AS nct_id,
    raw_json->>'$.protocolSection.identificationModule.briefTitle' AS brief_title,
    raw_json->>'$.protocolSection.identificationModule.officialTitle' AS official_title,
    raw_json->>'$.protocolSection.designModule.studyType' AS study_type,
    raw_json->>'$.protocolSection.statusModule.overallStatus' AS overall_status,
    raw_json->>'$.protocolSection.designModule.phases[0]' AS phase,
    CAST(raw_json->>'$.protocolSection.designModule.enrollmentInfo.count' AS INTEGER) AS enrollment_count,
    raw_json->>'$.protocolSection.statusModule.startDateStruct.date' AS start_date,
    raw_json->>'$.protocolSection.statusModule.primaryCompletionDateStruct.date' AS completion_date,
    raw_json->>'$.protocolSection.sponsorCollaboratorsModule.leadSponsor.name' AS sponsor_name,
    raw_json->>'$.protocolSection.sponsorCollaboratorsModule.leadSponsor.class' AS sponsor_class,
    raw_json->>'$.protocolSection.descriptionModule.briefSummary' AS brief_summary,
    source,
    ingested_at
FROM raw_studies;
