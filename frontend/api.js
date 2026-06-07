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
    const error = new Error(`Request failed (${response.status}): ${url}`);
    error.status = response.status;
    error.url = url;
    throw error;
  }

  return response.json();
}

function mapSeries(seriesDetail) {
  const study = seriesDetail.study ?? {};
  const patient = study.patient ?? seriesDetail.patient ?? {};
  const patientId = firstDefined(
    study,
    ["patient_id", "patient_id_study", "patientId", "PatientID"],
    firstDefined(patient, ["id", "patient_id", "patientId"], "Unknown"),
  );

  return {
    seriesUid: firstDefined(seriesDetail, [
      "series_instance_uid",
      "instance_uid",
      "seriesUid",
      "SeriesInstanceUID",
    ]),
    studyUid: firstDefined(seriesDetail, [
      "study_instance_uid_series",
      "study_instance_uid",
      "studyUid",
      "StudyInstanceUID",
    ]),
    patientId,
    modality: seriesDetail.modality ?? "Unknown",
    bodyPart: firstDefined(seriesDetail, [
      "body_part_examined",
      "body_part",
      "bodyPart",
      "BodyPartExamined",
    ], "Unknown"),
    protocolName: seriesDetail.protocol_name ?? "",
    seriesDate: seriesDetail.series_date ?? null,
    description: seriesDetail.series_description ?? "",
    numImages: seriesDetail.image_count ?? 0,
    collection: firstDefined(
      study,
      ["collection_name_study", "collection", "collection_name", "Collection"],
      firstDefined(seriesDetail, ["collection", "collection_name", "Collection"], "Unknown"),
    ),

    site: seriesDetail.site ?? null,
    manufacturer: seriesDetail.manufacturer ?? null,
    manufacturerModelName: seriesDetail.manufacturer_model_name ?? null,
    softwareVersions: seriesDetail.software_versions ?? null,
    maxSubmissionTimestamp: seriesDetail.max_submission_timestamp ?? null,
    fileSize: seriesDetail.file_size ?? null,
    thirdPartyAnalysis: seriesDetail.third_party_analysis ?? null,

    patientSex: patient.sex ?? patient.patient_sex ?? study.patient_sex ?? seriesDetail.patient_sex ?? null,
    patientAge: patient.age ?? patient.patient_age ?? study.patient_age ?? seriesDetail.patient_age ?? null,
    patientEthnicGroup:
      patient.ethnic_group ??
      study.ethnic_group ??
      seriesDetail.ethnic_group ??
      null,
  };
}

function firstDefined(source, keys, fallback = "") {
  for (const key of keys) {
    if (source?.[key] !== undefined && source[key] !== null) {
      return source[key];
    }
  }

  return fallback;
}

function asArrayResponse(response) {
  if (Array.isArray(response)) {
    return response;
  }

  if (Array.isArray(response?.items)) {
    return response.items;
  }

  if (Array.isArray(response?.results)) {
    return response.results;
  }

  if (Array.isArray(response?.data)) {
    return response.data;
  }

  return response ? [response] : [];
}

function mapDicomSeries(seriesDetail) {
  const study = seriesDetail.study ?? {};

  return {
    instance_uid: firstDefined(seriesDetail, [
      "instance_uid",
      "series_instance_uid",
      "seriesUid",
      "SeriesInstanceUID",
    ]),
    study_instance_uid: firstDefined(seriesDetail, [
      "study_instance_uid",
      "studyUid",
      "StudyInstanceUID",
    ]),
    patient_id: firstDefined(
      seriesDetail,
      ["patient_id", "patientId", "PatientID"],
      firstDefined(study, ["patient_id", "patientId", "PatientID"], "Unknown"),
    ),
    collection: firstDefined(
      seriesDetail,
      ["collection", "collection_name", "Collection"],
      firstDefined(study, ["collection", "collection_name", "Collection"], "Unknown"),
    ),
    modality: firstDefined(seriesDetail, ["modality", "Modality"], "Unknown"),
    body_part: firstDefined(seriesDetail, [
      "body_part",
      "bodyPart",
      "BodyPartExamined",
    ]),
    protocol_name: firstDefined(seriesDetail, [
      "protocol_name",
      "protocolName",
      "ProtocolName",
    ]),
    series_date: firstDefined(seriesDetail, [
      "series_date",
      "seriesDate",
      "SeriesDate",
    ]),
    series_description: firstDefined(seriesDetail, [
      "series_description",
      "description",
      "seriesDescription",
      "SeriesDescription",
    ]),
    image_count: firstDefined(seriesDetail, [
      "image_count",
      "imageCount",
      "numImages",
      "ImageCount",
    ], 0),
    file_size: firstDefined(seriesDetail, ["file_size", "fileSize", "FileSize"]),
    manufacturer: firstDefined(seriesDetail, ["manufacturer", "Manufacturer"]),
    manufacturer_model_name: firstDefined(seriesDetail, [
      "manufacturer_model_name",
      "manufacturerModelName",
      "ManufacturerModelName",
    ]),
  };
}

function mapDicomStudy(studyDetail) {
  return {
    instance_uid: firstDefined(studyDetail, [
      "instance_uid",
      "study_instance_uid",
      "studyUid",
      "StudyInstanceUID",
    ]),
    collection: firstDefined(studyDetail, [
      "collection",
      "collection_name",
      "Collection",
    ], "Unknown"),
    date: firstDefined(studyDetail, ["date", "study_date", "studyDate", "StudyDate"]),
    date_released: firstDefined(studyDetail, [
      "date_released",
      "dateReleased",
      "DateReleased",
    ]),
    description: firstDefined(studyDetail, [
      "description",
      "study_description",
      "studyDescription",
      "StudyDescription",
    ]),
    series_count: firstDefined(studyDetail, [
      "series_count",
      "seriesCount",
      "SeriesCount",
    ], 0),
    patient_id: firstDefined(studyDetail, [
      "patient_id",
      "patientId",
      "PatientID",
    ], "Unknown"),
    longitudinal_temporal_event_type: firstDefined(studyDetail, [
      "longitudinal_temporal_event_type",
      "longitudinalTemporalEventType",
    ]),
    longitudinal_temporal_offset_from_event: firstDefined(studyDetail, [
      "longitudinal_temporal_offset_from_event",
      "longitudinalTemporalOffsetFromEvent",
    ]),
  };
}

function mapDicomPatient(patientDetail) {
  return {
    id: firstDefined(patientDetail, ["id", "patient_id", "patientId", "PatientID"]),
    sex: firstDefined(patientDetail, ["sex", "patient_sex", "patientSex", "PatientSex"]),
    age: firstDefined(patientDetail, ["age", "patient_age", "patientAge", "PatientAge"]),
    ethnic_group: firstDefined(patientDetail, [
      "ethnic_group",
      "ethnicGroup",
      "EthnicGroup",
    ]),
  };
}

function normalizePatient(patientDetail) {
  return mapDicomPatient(patientDetail ?? {});
}

function deriveDicomStudiesFromSeries(seriesRows) {
  const studies = new Map();

  seriesRows.forEach((series) => {
    const studyUid = series.study_instance_uid;

    if (!studyUid) {
      return;
    }

    if (!studies.has(studyUid)) {
      studies.set(studyUid, {
        instance_uid: studyUid,
        collection: series.collection,
        date: series.series_date,
        date_released: "",
        description: series.series_description,
        series_count: 0,
        patient_id: series.patient_id,
        longitudinal_temporal_event_type: "",
        longitudinal_temporal_offset_from_event: "",
      });
    }

    studies.get(studyUid).series_count += 1;
  });

  return Array.from(studies.values());
}

function deriveDicomPatientsFromSeries(seriesRows) {
  const patients = new Map();

  seriesRows.forEach((series) => {
    const patientId = series.patient_id;

    if (!patientId || patientId === "Unknown") {
      return;
    }

    if (!patients.has(patientId)) {
      patients.set(patientId, {
        id: patientId,
        sex: "",
        age: "",
        ethnic_group: "",
      });
    }
  });

  return Array.from(patients.values());
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
    savedCollections.map((collection) => [
      firstDefined(collection, ["name", "collection_name", "Collection"]),
      collection,
    ]),
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
  const name = firstDefined(collection, ["name", "collection_name", "Collection"]);

  return {
    name,
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

async function loadPatient(apiBaseUrl, patientId) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ id: patientId });
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetchJson(`${baseUrl}/api/patientOnId?${params}`, {
      signal: controller.signal,
    });

    return normalizePatient(Array.isArray(response) ? response[0] : response);
  } finally {
    window.clearTimeout(timeout);
  }
}

async function searchDicomSeries(apiBaseUrl, collectionName) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ collectionName });
  const response = await fetchJson(`${baseUrl}/api/seriesOnDemand?${params}`);

  return asArrayResponse(response).map(mapDicomSeries);
}

async function searchDicomStudies(apiBaseUrl, collectionName) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ collectionName });

  try {
    const response = await fetchJson(`${baseUrl}/api/studiesOnDemand?${params}`);
    return asArrayResponse(response).map(mapDicomStudy);
  } catch (error) {
    if (error.status !== 404) {
      throw error;
    }

    const seriesRows = await searchDicomSeries(apiBaseUrl, collectionName);
    return deriveDicomStudiesFromSeries(seriesRows);
  }
}

async function searchDicomPatients(apiBaseUrl, collectionName) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ collectionName });

  try {
    const response = await fetchJson(`${baseUrl}/api/patientsOnDemand?${params}`);
    return asArrayResponse(response).map(mapDicomPatient);
  } catch (error) {
    if (error.status !== 404) {
      throw error;
    }

    const seriesRows = await searchDicomSeries(apiBaseUrl, collectionName);
    return deriveDicomPatientsFromSeries(seriesRows);
  }
}

async function searchDicomSeriesOnUid(apiBaseUrl, uid) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ uid });
  const response = await fetchJson(`${baseUrl}/api/seriesOnDemandOnUid?${params}`);

  return asArrayResponse(response).map(mapDicomSeries);
}

async function searchDicomSeriesOnStudyUid(apiBaseUrl, studyUid) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ study_uid: studyUid });
  const response = await fetchJson(
    `${baseUrl}/api/seriesOnDemandOnStudyUid?${params}`,
  );

  return asArrayResponse(response).map(mapDicomSeries);
}

async function searchDicomPatientsOnUid(apiBaseUrl, collectionName, patientId) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({
    collectionName,
    patient_id: patientId,
  });
  const response = await fetchJson(
    `${baseUrl}/api/patientsOnDemandOnUid?${params}`,
  );

  return asArrayResponse(response).map(mapDicomPatient);
}

async function downloadAvailableCollection(apiBaseUrl, collectionName) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = new URLSearchParams({ collection_name: collectionName });

  const result = await fetchJson(`${baseUrl}/api/addDICOMdataset?${params}`, {
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

  const result = await fetchJson(`${baseUrl}/api/addNIFTIdataset`, {
    method: "POST",
    body: formData,
  });

  if (result.status_operation !== "success") {
    throw new Error(result.error ?? "Dataset upload failed");
  }

  return result;
}

function buildViewerParams(baseUrl, collectionName) {
  const params = new URLSearchParams();
  if (collectionName) {
    params.set("collection", collectionName);
  }
  if (baseUrl) {
    params.set("base_url", baseUrl);
  }
  return params;
}

function withQuery(url, params) {
  const query = params.toString();
  return query ? `${url}?${query}` : url;
}

function buildSeriesViewerUrl(apiBaseUrl, seriesUid, collectionName) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const params = buildViewerParams(baseUrl, collectionName);
  const url = `${baseUrl}/api/viewer/series/${encodeURIComponent(seriesUid)}`;
  return withQuery(url, params);
}

async function fetchSeriesViewer(apiBaseUrl, seriesUid, collectionName) {
  return fetchJson(buildSeriesViewerUrl(apiBaseUrl, seriesUid, collectionName));
}
