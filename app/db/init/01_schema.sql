-- collections
CREATE TABLE IF NOT EXISTS collections (
    collectionName VARCHAR PRIMARY KEY,
    description VARCHAR,
    LicenseName VARCHAR,
    LicenseURI VARCHAR,
    DataDescriptionURI VARCHAR
);

-- patients
CREATE TABLE IF NOT EXISTS patients (
    PatientID VARCHAR PRIMARY KEY,
    PatientSex VARCHAR,
    PatientAge INTEGER,
    EthnicGroup VARCHAR
);

-- studies
CREATE TABLE IF NOT EXISTS studies (
    StudyInstanceUID VARCHAR PRIMARY KEY,
    Collection VARCHAR REFERENCES collections(collectionName),
    StudyDate DATE,
    DateReleased DATE,
    StudyDescription VARCHAR,
    SeriesCount INTEGER,
    PatientID VARCHAR REFERENCES patients(PatientID),
    LongitudinalTemporalEventType VARCHAR,
    LongitudinalTemporalOffsetFromEvent VARCHAR
);

-- series
CREATE TABLE IF NOT EXISTS series (
    SeriesInstanceUID VARCHAR PRIMARY KEY,
    StudyInstanceUID VARCHAR REFERENCES studies(instance_uid),
    Modality VARCHAR,
    BodyPartExamined VARCHAR,
    ProtocolName VARCHAR,
    SeriesDate DATE,
    SeriesDescription VARCHAR,
    Site VARCHAR,
    Manufacturer VARCHAR,
    ManufacturerModelName VARCHAR,
    SoftwareVersions VARCHAR,
    ImageCount INTEGER,
    MaxSubmissionTimestamp TIME,
    FileSize INTEGER,
    ThirdPartyAnalysis BOOLEAN
);

-- extractions
CREATE TABLE IF NOT EXISTS extractions (
    id SERIAL PRIMARY KEY,
    image_number VARCHAR,
    SeriesInstanceUID VARCHAR REFERENCES series(instance_uid),
    value FLOAT
);

CREATE TABLE IF NOT EXISTS field_mappings (
    field_name_DICOM VARCHAR PRIMARY KEY,
    standardized_field_name VARCHAR,
    code INTEGER,
    vocabulary VARCHAR
);

INSERT INTO field_mappings (
    field_name_DICOM,
    standardized_field_name,
    code,
    vocabulary
)
VALUES
('instance_uid', 'Identifier', 118522005, 'SNOMED'),
('description', 'Description', -1, ''),
('license_name', 'Imaging modality', -1, ''),
('license_uri', 'License uri', -1, ''),
('description_uri', 'Description uri', -1, ''),
('extraction_id', 'identifier', 118522005, 'SNOMED'),
('image_number', 'Image', 900000000000520007, 'SNOMED'),
('series_uid', 'Series', 13039001, 'SNOMED'),
('value', 'Quantitative value', 30766002, 'SNOMED'),
('id', 'Identifier', 118522005, 'SNOMED'),
('sex', 'Gender', 263495000, 'SNOMED'),
('age', 'Age', 397669002, 'SNOMED'),
('ethnic_group', 'Ethnic group', 372148003, 'SNOMED'),
('study_instance_uid', 'Identifier of study', -1, ''),
('modality', 'Imaging modality', 360037004, 'SNOMED'),
('body_part', 'Body part', 38866009, 'SNOMED'),
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
('collection', 'Collection', -1, ''),
('date', 'Date', 410671006, 'SNOMED'),
('date_released', 'Date of release', 439771001, 'SNOMED'),
('series_count', 'Count of series', 410681005, 'SNOMED'),
('patient_id', 'Patient', 116154003, 'SNOMED'),
('longitudinal_temporal_event_type', 'Event', 272379006, 'SNOMED'),
('longitudinal_temporal_offset_from_event', 'Relative time', 118578006, 'SNOMED');

CREATE TABLE IF NOT EXISTS value_mappings (
    original_value VARCHAR PRIMARY KEY,
    standardized_value VARCHAR,
    code INTEGER,
    vocabulary VARCHAR
);

INSERT INTO value_mappings (
    original_value,
    standardized_value,
    code,
    vocabulary
)
VALUES
('Eccentricity', 'Shape', 219329, 'SNOMED'),
('GLCM Homogeneity', 'Texture', 219329, 'SNOMED'),
('GLCM Correlation', 'Texture', 219329, 'SNOMED'),
('GLRLM Short Run Emphasis', 'Texture', 219329, 'SNOMED'),
('GLSZM Zone Entropy', 'Texture', 219329, 'SNOMED'),
('NGTDM Coarseness', 'Texture', 219329, 'SNOMED'),
('NGTDM Contrast', 'Texture', 219329, 'SNOMED'),
('NGTDM Busyness', 'Texture', 219329, 'SNOMED'),
('ROI Standard Deviation', 'Standard deviation', 219329, 'SNOMED'),
('ROI Mean', 'Mean', 219329, 'SNOMED'),
('M', 'Male', 219329, 'SNOMED'),
('F', 'Female', 219329, 'SNOMED'),
('MR', 'Magnetic resonance imaging', 219329, 'SNOMED'),
('BRAIN', 'Brain part', 219329, 'SNOMED'),
('DIAGNOSIS', 'Diagnosis', 219329, 'SNOMED'),
('CT', 'Computed tomography', 219329, 'SNOMED'),
('PT', 'Positron emission tomography', 219329, 'SNOMED'),
('CHEST', 'Thoracic structure', 219329, 'SNOMED'),
('WHOLEBODY', 'Entire body as a whole', 219329, 'SNOMED'),
('NECKCHESTABDPELV', 'Neck, chest, abdomen, and pelvis', 219329, 'SNOMED'),
('NECK', 'Neck structure', 219329, 'SNOMED'),
('LSSPINE', 'Lumbar spine structure', 219329, 'SNOMED'),
('CHESTABDOMEN', 'Chest and abdomen', 219329, 'SNOMED'),
('ABDOMEN', 'Entire abdomen', 219329, 'SNOMED');