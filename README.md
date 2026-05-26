# 2026-bioimages

Team 2, Year 2026

## Start

1. Create your env file:

```bash
cp .env.example .env
```

### Local start

Install dependencies (equivalent to `requirements.txt` install):

```bash
pip install .
```

Run the API:

```bash
python -m app.main
```

### Docker start

```bash
docker build -t bioimages-app .
docker compose up
```

The API will be available at `http://localhost:8000` (`/hello` endpoint, object storage under `/object-storage`).
The frontend mock UI will be available at `http://localhost:8080`.
MinIO will be available at `http://localhost:9000` (API) and `http://localhost:9001` (console).

## ZIP Dataset Ingestion

Use `POST /addZipDataset` to ingest uploaded DICOM or NIfTI ZIP archives. The endpoint stores collection, patient, study, and series metadata in the database and uploads image files to MinIO.

Common multipart fields:

- `dataset_type`: `dicom` or `nifti`
- `zip_file`: ZIP archive
- `collection_name`: optional; defaults to the single top-level ZIP folder or ZIP filename
- `description`: optional
- `column_mapping`: optional JSON object for spreadsheet column aliases
- `use_folder_structure`: optional, defaults to `true`
- `id_resolution_mode`: optional, `auto`, `xlsx`, or `folder`

### DICOM ZIP

DICOM metadata is read from the actual uploaded DICOM file headers. Files missing `PatientID`, `StudyInstanceUID`, or `SeriesInstanceUID` are skipped; non-DICOM files are skipped with a warning. MinIO object names use:

```text
collection_name/patient_id/study_instance_uid/series_instance_uid/sop_instance_uid.dcm
```

Example:

```bash
curl -X POST http://localhost:8000/addZipDataset \
  -F dataset_type=dicom \
  -F collection_name=LungStudy \
  -F description="Local DICOM upload" \
  -F zip_file=@dicom_dataset.zip
```

### NIfTI ZIP

NIfTI files are discovered by `.nii` and `.nii.gz` suffix. Optional `.xlsx` or `.csv` metadata rows are used only when they can be linked unambiguously to files by `relative_path`, `file_path`, `path`, `file_name`, `filename`, `nifti_file`, or `object_name`. A single metadata row may also match a single NIfTI file.

If the spreadsheet has no file linkage column, `id_resolution_mode=auto` can still use TCIA-style metadata such as `Patient ID`, `Patient Sex`, `Study Instance UID`, and `Study Date` when the patient ID appears in the NIfTI folder or filename. Series IDs are only taken from the spreadsheet when the NIfTI filename maps unambiguously to one series row; otherwise the series ID is derived from the filename. Use `id_resolution_mode=xlsx` to fail with `422` instead of falling back.

Folder fallback expects:

```text
collection/patient_id/study_uid/series_uid/file.nii.gz
```

When no series folder exists, the NIfTI filename stem is used as the series ID. Object names use:

```text
collection_name/patient_id/study_uid/series_uid/file_name
```

Example:

```bash
curl -X POST http://localhost:8000/addZipDataset \
  -F dataset_type=nifti \
  -F collection_name=BrainStudy \
  -F id_resolution_mode=auto \
  -F column_mapping="$(cat column_mapping.example.json)" \
  -F zip_file=@nifti_dataset.zip
```

`column_mapping` maps canonical API fields to spreadsheet headers. For example,
`"patient sex": "sex"` means the spreadsheet column `sex` will populate the
patient `sex` field. Header matching is case-insensitive and treats spaces and
underscores the same. The bundled `column_mapping.example.json` matches the
TCIA-style headers in `BraTS-TCGA-GBM.xlsx`; for that file, the mapping is
effectively documentation because the default aliases already recognize those
headers.
