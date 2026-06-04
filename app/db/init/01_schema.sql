-- collections
CREATE TABLE IF NOT EXISTS collections (
    collection_name VARCHAR PRIMARY KEY,
    description VARCHAR,
    license_name VARCHAR,
    license_uri VARCHAR,
    data_description_uri VARCHAR
);

-- patients
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR PRIMARY KEY,
    patient_sex VARCHAR,
    patient_age INTEGER,
    ethnic_group VARCHAR
);

-- studies
CREATE TABLE IF NOT EXISTS studies (
    study_instance_uid VARCHAR PRIMARY KEY,
    collection_name_study VARCHAR REFERENCES collections(collection_name),
    study_date DATE,
    date_released DATE,
    study_description VARCHAR,
    series_count INTEGER,
    patient_id_study VARCHAR REFERENCES patients(patient_id),
    longitudinal_temporal_event_type VARCHAR,
    longitudinal_temporal_offset_from_event VARCHAR
);

-- series
CREATE TABLE IF NOT EXISTS series (
    series_instance_uid VARCHAR PRIMARY KEY,
    study_instance_uid_series VARCHAR REFERENCES studies(study_instance_uid),
    modality VARCHAR,
    body_part_examined VARCHAR,
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
CREATE TABLE IF NOT EXISTS extractions (
    id SERIAL PRIMARY KEY,
    image_number VARCHAR,
    series_instance_uid_extraction VARCHAR REFERENCES series(series_instance_uid),
    feature_name VARCHAR,
    value FLOAT
);

-- field mappings
CREATE TABLE IF NOT EXISTS field_mappings (
    field_name_dicom VARCHAR PRIMARY KEY,
    standardized_field_name VARCHAR,
    code BIGINT,
    vocabulary VARCHAR
);

INSERT INTO field_mappings (
    field_name_dicom,
    standardized_field_name,
    code,
    vocabulary
)
VALUES

-- =========================
-- COLLECTION
-- =========================
('collection_name', 'Name', 734841007, 'SNOMED'),
('description', 'Description', -1, ''),
('license_name', 'Licence name', -1, ''),
('license_uri', 'License uri', -1, ''),
('data_description_uri', 'Description uri', -1, ''),

-- =========================
-- STUDY
-- =========================
('study_instance_uid', 'Identifier', 118522005, 'SNOMED'),
('collection_name_study', 'Collection', -1, ''),
('study_date', 'Date', 410671006, 'SNOMED'),
('date_released', 'Date of release', 439771001, 'SNOMED'),
('study_description', 'Description in dialect', 900000000000510002, 'SNOMED'),
('series_count', 'Count of series', 410681005, 'SNOMED'),
('patient_id_study', 'Patient', 116154003, 'SNOMED'),
('longitudinal_temporal_event_type', 'Event', 272379006, 'SNOMED'),
('longitudinal_temporal_offset_from_event', 'Relative time', 118578006, 'SNOMED'),

-- =========================
-- SERIES
-- =========================
('series_instance_uid', 'Identifier', 118522005, 'SNOMED'),
('study_instance_uid_series', 'Identifier of study', -1, ''),
('modality', 'Imaging modality', 360037004, 'SNOMED'),
('body_part_examined', 'Body part', 38866009, 'SNOMED'),
('protocol_name', 'Protocols', 258049002, 'SNOMED'),
('series_date', 'Date', 410671006, 'SNOMED'),
('series_description', 'Description in dialect', 900000000000510002, 'SNOMED'),
('site', 'Healthcare facility', 257622000, 'SNOMED'),
('manufacturer', 'Manufacturer', -1, ''),
('manufacturer_model_name', 'Device', 49062001, ''),
('software_versions', 'Software', 706687001, 'SNOMED'),
('image_count', 'Count of images', 410681005, 'SNOMED'),
('max_submission_timestamp', 'Timestamp', 398215006, 'SNOMED'),
('file_size', 'File size bytes', -1, ''),
('third_party_analysis', 'Third party analysis', -1, ''),

-- =========================
-- PATIENT
-- =========================
('patient_id', 'Identifier', 118522005, 'SNOMED'),
('patient_sex', 'Gender', 263495000, 'SNOMED'),
('patient_age', 'Age', 397669002, 'SNOMED'),
('ethnic_group', 'Ethnic group', 372148003, 'SNOMED'),

-- =========================
-- EXTRACTION
-- =========================
('id', 'identifier', 118522005, 'SNOMED'),
('image_number', 'Image', 900000000000520007, 'SNOMED'),
('series_instance_uid_extraction', 'Series', 13039001, 'SNOMED'),
('feature_name', 'Name', 734841007, 'SNOMED'),
('value', 'Quantitative value', 30766002, 'SNOMED');

-- value mappings
CREATE TABLE IF NOT EXISTS value_mappings (
    original_value VARCHAR PRIMARY KEY,
    standardized_value VARCHAR,
    code BIGINT,
    vocabulary VARCHAR
);

INSERT INTO value_mappings (
    original_value,
    standardized_value,
    code,
    vocabulary
)
VALUES
('Eccentricity', 'Shape', 300842002, 'SNOMED'),
('GLCM Homogeneity', 'Texture', 246200002, 'SNOMED'),
('GLCM Correlation', 'Texture', 246200002, 'SNOMED'),
('GLRLM Short Run Emphasis', 'Texture', 246200002, 'SNOMED'),
('GLSZM Zone Entropy', 'Texture', 246200002, 'SNOMED'),
('NGTDM Coarseness', 'Texture', 246200002, 'SNOMED'),
('NGTDM Contrast', 'Texture', 246200002, 'SNOMED'),
('NGTDM Busyness', 'Texture', 246200002, 'SNOMED'),
('ROI Standard Deviation', 'Standard deviation', 386136009, 'SNOMED'),
('ROI Mean', 'Mean', 255586005, 'SNOMED'),
('M', 'Male', 10052007, 'SNOMED'),
('F', 'Female', 1086007, 'SNOMED'),
('MR', 'Magnetic resonance imaging', 113091000, 'SNOMED'),
('BRAIN', 'Brain part', 119235005, 'SNOMED'),
('DIAGNOSIS', 'Diagnosis', 439401001, 'SNOMED'),
('CT', 'Computed tomography', 77477000, 'SNOMED'),
('PT', 'Positron emission tomography', 82918005, 'SNOMED'),
('CHEST', 'Thoracic structure', 51185008, 'SNOMED'),
('WHOLEBODY', 'Entire body as a whole', 38266002, 'SNOMED'),
('NECKCHESTABDPELV', 'Neck, chest, abdomen, and pelvis', 416319003, 'SNOMED'),
('NECK', 'Neck structure', 45048000, 'SNOMED'),
('LSSPINE', 'Lumbar spine structure', 122496007, 'SNOMED'),
('CHESTABDOMEN', 'Chest and abdomen', 416550000, 'SNOMED'),
('ABDOMEN', 'Entire abdomen', 302553009, 'SNOMED');