CREATE TABLE IF NOT EXISTS collections (
    name VARCHAR PRIMARY KEY,
    description VARCHAR,
    license_name VARCHAR,
    license_uri VARCHAR,
    description_uri VARCHAR
);

CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR PRIMARY KEY,
    sex VARCHAR,
    age INTEGER,
    ethnic_group VARCHAR
);

CREATE TABLE IF NOT EXISTS studies (
    instance_uid VARCHAR PRIMARY KEY,
    collection VARCHAR REFERENCES collections(name),
    date DATE,
    date_released DATE,
    description VARCHAR,
    series_count INTEGER,
    patient_id VARCHAR REFERENCES patients(id),
    "LongitudinalTemporalEventType" VARCHAR,
    "LongitudinalTemporalOffsetFromEvent" VARCHAR
);

CREATE TABLE IF NOT EXISTS series (
    instance_uid VARCHAR PRIMARY KEY,
    study_instance_uid VARCHAR REFERENCES studies(instance_uid),
    modality VARCHAR,
    protocol_name VARCHAR,
    series_date DATE,
    series_description VARCHAR,
    site VARCHAR,
    manufacturer VARCHAR,
    manufacturer_model_name VARCHAR,
    software_versions VARCHAR,
    image_count INTEGER,
    max_submission_timestamp TIME,
    file_size INTEGER,
    third_party_analysis BOOLEAN
);
