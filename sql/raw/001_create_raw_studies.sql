-- Raw studies table for bronze layer
-- Stores unmodified API responses with ingestion metadata

CREATE SEQUENCE IF NOT EXISTS raw_studies_id_seq;

CREATE TABLE IF NOT EXISTS raw_studies (
    id INTEGER PRIMARY KEY DEFAULT nextval('raw_studies_id_seq'),
    nct_id VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    raw_json JSON NOT NULL,
    content_hash VARCHAR UNIQUE NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_studies_nct_id ON raw_studies(nct_id);
CREATE INDEX IF NOT EXISTS idx_raw_studies_ingested_at ON raw_studies(ingested_at);
CREATE INDEX IF NOT EXISTS idx_raw_studies_source ON raw_studies(source);
