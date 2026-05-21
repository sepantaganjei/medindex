let collections = [];
let seriesData = [];

function normalizeBaseUrl(apiBaseUrl) {
  if (!apiBaseUrl) {
    return "";
  }
  return apiBaseUrl.endsWith("/") ? apiBaseUrl.slice(0, -1) : apiBaseUrl;
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${url}`);
  }
  return response.json();
}

function mapSeries(seriesDetail) {
  return {
    seriesUid: seriesDetail.instance_uid,
    patientId: seriesDetail.patient_id ?? "Unknown",
    modality: seriesDetail.modality ?? "Unknown",
    bodyPart: seriesDetail.body_part ?? "Unknown",
    description: seriesDetail.series_description ?? "",
    numSlices: seriesDetail.image_count ?? 0,
    collection: seriesDetail.collection ?? "Unknown",
  };
}

function buildCollections(collectionsResponse, seriesRows) {
  const seriesCounts = seriesRows.reduce((counts, series) => {
    const key = series.collection;
    if (!counts[key]) {
      counts[key] = 0;
    }
    counts[key] += 1;
    return counts;
  }, {});

  return collectionsResponse.map((collection) => ({
    id: collection.name,
    name: collection.name,
    source: collection.license_name ?? "Mock",
    seriesCount: seriesCounts[collection.name] ?? 0,
  }));
}

async function loadMockData(apiBaseUrl) {
  const normalizedBaseUrl = normalizeBaseUrl(apiBaseUrl);
  const buildUrl = (path) => `${normalizedBaseUrl}${path}`;

  const [collectionsResponse, seriesResponse] = await Promise.all([
    fetchJson(buildUrl("/api/collections")),
    fetchJson(buildUrl("/api/series")),
  ]);

  const seriesDetails = await Promise.all(
    seriesResponse.map((series) =>
      fetchJson(buildUrl(`/api/series/${series.instance_uid}`)),
    ),
  );

  const mappedSeries = seriesDetails.map(mapSeries);

  return {
    collections: buildCollections(collectionsResponse, mappedSeries),
    seriesData: mappedSeries,
  };
}
