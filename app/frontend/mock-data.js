const collections = [
  {
    id: "collection_alpha_01",
    name: "collection_alpha_01",
    source: "TCIA",
    seriesCount: 128
  },
  {
    id: "dataset_brain_mri",
    name: "dataset_brain_mri",
    source: "TCIA",
    seriesCount: 64
  },
  {
    id: "local_upload_02",
    name: "local_upload_02",
    source: "Local",
    seriesCount: 18
  }
];

const seriesData = [
  {
    seriesUid: "1.2.840.10008...",
    patientId: "PT-00941",
    modality: "CT",
    bodyPart: "BRAIN",
    description: "Axial contrast-enhanced scan",
    numSlices: 128,
    collection: "collection_alpha_01"
  },
  {
    seriesUid: "1.2.840.10017...",
    patientId: "PT-00942",
    modality: "MRI",
    bodyPart: "CHEST",
    description: "T2 weighted scan",
    numSlices: 64,
    collection: "dataset_brain_mri"
  },
  {
    seriesUid: "1.2.840.10024...",
    patientId: "PT-00943",
    modality: "PET",
    bodyPart: "ABDOMEN",
    description: "PET whole body scan",
    numSlices: 256,
    collection: "collection_alpha_01"
  }
];