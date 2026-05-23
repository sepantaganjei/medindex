let collections = [];
let seriesData = [];

function normalizeBaseUrl(apiBaseUrl) {
  if (!apiBaseUrl) {
    return "";
  }

  return apiBaseUrl.endsWith("/") ? apiBaseUrl.slice(0, -1) : apiBaseUrl;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${url}`);
  }

  return response.json();
}

function mapSeries(seriesDetail) {
  const study = seriesDetail.study ?? {};

  return {
    seriesUid: seriesDetail.instance_uid,
    studyUid: seriesDetail.study_instance_uid,
    patientId: study.patient_id ?? "Unknown",
    modality: seriesDetail.modality ?? "Unknown",
    bodyPart: seriesDetail.body_part ?? "Unknown",
    protocolName: seriesDetail.protocol_name ?? "",
    seriesDate: seriesDetail.series_date ?? null,
    description: seriesDetail.series_description ?? "",
    numImages: seriesDetail.image_count ?? 0,
    collection: study.collection ?? "Unknown",

    site: seriesDetail.site ?? null,
    manufacturer: seriesDetail.manufacturer ?? null,
    manufacturerModelName: seriesDetail.manufacturer_model_name ?? null,
    softwareVersions: seriesDetail.software_versions ?? null,
    maxSubmissionTimestamp: seriesDetail.max_submission_timestamp ?? null,
    fileSize: seriesDetail.file_size ?? null,
    thirdPartyAnalysis: seriesDetail.third_party_analysis ?? null,
  };
}

function getCollectionSource(collectionName, savedCollectionMap) {
  const savedCollection = savedCollectionMap.get(collectionName);
  const description = savedCollection?.description ?? "";

  if (description.toLowerCase().includes("nifti")) {
    return "NIfTI";
  }

  return "DICOM";
}

function buildCollectionsFromSeries(seriesRows, savedCollections = []) {
  const collectionMap = new Map();
  const savedCollectionMap = new Map(
    savedCollections.map((collection) => [collection.name, collection]),
  );

  seriesRows.forEach((series) => {
    if (!series.collection || series.collection === "Unknown") {
      return;
    }

    if (!collectionMap.has(series.collection)) {
      collectionMap.set(series.collection, {
        id: series.collection,
        name: series.collection,
        source: getCollectionSource(series.collection, savedCollectionMap),
        seriesCount: 0,
      });
    }

    collectionMap.get(series.collection).seriesCount += 1;
  });

  return Array.from(collectionMap.values());
}

function mapAvailableCollection(collection) {
  return {
    name: collection.name,
    description: collection.description ?? "",
    source: "TCIA",
    licenseName: "DICOM",
    downloaded: false,
  };
}

async function loadMockData(apiBaseUrl) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);

  const [seriesResponse, savedCollectionsResponse] = await Promise.all([
    fetchJson(`${baseUrl}/api/series`),
    fetchJson(`${baseUrl}/api/savedCollections`).catch(() => []),
  ]);

  const mappedSeries = seriesResponse.map(mapSeries);

  return {
    collections: buildCollectionsFromSeries(
      mappedSeries,
      savedCollectionsResponse,
    ),
    seriesData: mappedSeries,
  };
}

async function loadAvailableCollections(apiBaseUrl) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);

  const collectionsResponse = await fetchJson(
    `${baseUrl}/api/collectionsToDownload`,
  );

  return collectionsResponse.map(mapAvailableCollection);
}

async function downloadAvailableCollection(apiBaseUrl, collectionName) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ collection_name: collectionName });

  const result = await fetchJson(`${baseUrl}/api/add_DICOM_dataset?${params}`, {
    method: "POST",
  });

  if (result.status_operation !== "success") {
    throw new Error(result.error ?? "Dataset import failed");
  }

  return result;
}

async function uploadDataset(apiBaseUrl, file) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);

  if (!file.name.toLowerCase().endsWith(".zip")) {
    throw new Error("Upload a .zip file for NIfTI datasets.");
  }

  const collectionName = file.name.replace(/\.zip$/i, "");

  const formData = new FormData();
  formData.append("collection_name", collectionName);
  formData.append("description", `Uploaded NIfTI dataset: ${collectionName}`);
  formData.append("zip_file", file);

  const result = await fetchJson(`${baseUrl}/api/add_NIFTI_dataset`, {
    method: "POST",
    body: formData,
  });

  if (result.status_operation !== "success") {
    throw new Error(result.error ?? "Dataset upload failed");
  }

  return result;
}
