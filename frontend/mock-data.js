const collections = [
  {
    id: "collection_alpha_01",
    name: "collection_alpha_01",
    source: "TCIA",
    seriesCount: 128
  },
  {
    id: "brain_mri_study",
    name: "brain_mri_study",
    source: "TCIA",
    seriesCount: 64
  },
  {
    id: "pet_test_study",
    name: "pet_test_study",
    source: "TCIA",
    seriesCount: 72
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
    seriesUid: "1.2.840.10008.001",
    patientId: "PT-00941",
    modality: "CT",
    bodyPart: "BRAIN",
    description: "Axial contrast-enhanced scan",
    numSlices: 128,
    collection: "collection_alpha_01"
  },
  {
    seriesUid: "1.2.840.10017.002",
    patientId: "PT-00942",
    modality: "MRI",
    bodyPart: "SPINE",
    description: "T2 weighted scan",
    numSlices: 64,
    collection: "brain_mri_study"
  },
  {
    seriesUid: "1.2.840.10024.003",
    patientId: "PT-00943",
    modality: "PET",
    bodyPart: "ABDOMEN",
    description: "Whole-body PET acquisition",
    numSlices: 256,
    collection: "pet_test_study"
  },
  {
    seriesUid: "1.2.840.10031.004",
    patientId: "PT-00944",
    modality: "CT",
    bodyPart: "CHEST",
    description: "Low-dose chest CT",
    numSlices: 180,
    collection: "collection_alpha_01"
  },
  {
    seriesUid: "1.2.840.10055.005",
    patientId: "PT-00945",
    modality: "MRI",
    bodyPart: "BRAIN",
    description: "Brain MRI FLAIR sequence",
    numSlices: 92,
    collection: "brain_mri_study"
  }
];