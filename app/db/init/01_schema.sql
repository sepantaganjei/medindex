-- collections
CREATE TABLE IF NOT EXISTS collections (
    name VARCHAR PRIMARY KEY,
    description VARCHAR,
    license_name VARCHAR,
    license_uri VARCHAR,
    description_uri VARCHAR
);

-- patients
CREATE TABLE IF NOT EXISTS patients (
    id VARCHAR PRIMARY KEY,
    sex VARCHAR,
    age INTEGER,
    ethnic_group VARCHAR
);

-- studies
CREATE TABLE IF NOT EXISTS studies (
    instance_uid VARCHAR PRIMARY KEY,
    collection VARCHAR REFERENCES collections(name),
    date DATE,
    date_released DATE,
    description VARCHAR,
    series_count INTEGER,
    patient_id VARCHAR REFERENCES patients(id),
    longitudinal_temporal_event_type VARCHAR,
    longitudinal_temporal_offset_from_event VARCHAR
);

-- series
CREATE TABLE IF NOT EXISTS series (
    instance_uid VARCHAR PRIMARY KEY,
    study_instance_uid VARCHAR REFERENCES studies(instance_uid),
    modality VARCHAR,
    body_part VARCHAR,
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

-- extractions
CREATE TABLE IF NOT EXISTS extraction (
    id SERIAL PRIMARY KEY,
    image_number INTEGER,
    series_uid VARCHAR REFERENCES series(instance_uid),
    feature_name VARCHAR,
    standardized_feature_name VARCHAR,
    vocabulary VARCHAR,
    value FLOAT
);