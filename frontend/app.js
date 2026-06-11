const appShell = document.getElementById("app-shell");
const collectionsList = document.getElementById("collections-list");
const seriesTable = document.getElementById("series-table");
const seriesTableHead = document.querySelector("#series-browser-section thead tr");
const seriesPagination = document.getElementById("series-pagination");
const searchInput = document.getElementById("search-input");
const modalityFilter = document.getElementById("modality-filter");
const resultCount = document.getElementById("result-count");

const searchPage = document.getElementById("search-page");
const viewerPage = document.getElementById("viewer-page");
const backButton = document.getElementById("back-button");

const viewerTitle = document.getElementById("viewer-title");
const viewerSubtitle = document.getElementById("viewer-subtitle");
const viewerModality = document.getElementById("viewer-modality");
const viewerImages = document.getElementById("viewer-images");
const imageSlider = document.getElementById("image-slider");
const metadataContent = document.getElementById("metadata-content");
const metadataSeriesTab = document.getElementById("metadata-series-tab");
const metadataPatientTab = document.getElementById("metadata-patient-tab");
const viewerPlaceholder = document.getElementById("viewer-placeholder");
const viewerLoading = document.getElementById("viewer-loading");
const viewerError = document.getElementById("viewer-error");
const dicomViewer = document.getElementById("dicom-viewer");
const dicomImage = document.getElementById("dicom-image");
const viewerControls = document.querySelector(".viewer-controls");
const openRoiButton = document.getElementById("open-roi-button");

const seriesViewButton = document.getElementById("series-view-button");
const availableViewButton = document.getElementById("available-view-button");
const dicomViewButton = document.getElementById("dicom-view-button");
const extractionsViewButton = document.getElementById("extractions-view-button");
const seriesBrowserSection = document.getElementById("series-browser-section");
const availableCollectionsSection = document.getElementById(
  "available-collections-section",
);
const dicomExplorerSection = document.getElementById("dicom-explorer-section");
const extractionsSection = document.getElementById("extractions-section");
const availableSearchInput = document.getElementById("available-search-input");
const availableCollectionsList = document.getElementById(
  "available-collections-list",
);
const availableResultCount = document.getElementById("available-result-count");
const availablePagination = document.getElementById("available-pagination");
const dicomSeriesModeButton = document.getElementById(
  "dicom-series-mode-button",
);
const dicomStudiesModeButton = document.getElementById(
  "dicom-studies-mode-button",
);
const dicomPatientsModeButton = document.getElementById(
  "dicom-patients-mode-button",
);
const dicomCollectionInput = document.getElementById("dicom-collection-input");
const dicomSearchButton = document.getElementById("dicom-search-button");
const dicomStatus = document.getElementById("dicom-status");
const dicomResultCount = document.getElementById("dicom-result-count");
const dicomResultsContainer = document.getElementById("dicom-results");
const dicomPagination = document.getElementById("dicom-pagination");
const extractionsResultCount = document.getElementById("extractions-result-count");
const refreshExtractionsButton = document.getElementById(
  "refresh-extractions-button",
);
const extractionsStatus = document.getElementById("extractions-status");
const extractionsList = document.getElementById("extractions-list");

const uploadInput = document.getElementById("dataset-upload-input");
const uploadButton = document.getElementById("dataset-upload-button");
const uploadStatus = document.getElementById("upload-status");
const uploadModal = document.getElementById("upload-modal");
const uploadForm = document.getElementById("upload-form");
const uploadModalClose = document.getElementById("upload-modal-close");
const uploadCancelButton = document.getElementById("upload-cancel-button");
const uploadDatasetType = document.getElementById("upload-dataset-type");
const uploadCollectionName = document.getElementById("upload-collection-name");
const uploadDescription = document.getElementById("upload-description");
const uploadMetadataFile = document.getElementById("upload-metadata-file");
const uploadDescriptionSeriesMatching = document.getElementById(
  "upload-description-series-matching",
);
const uploadColumnMapping = document.getElementById("upload-column-mapping");
const uploadNiftiFields = document.getElementById("upload-nifti-fields");
const uploadModalStatus = document.getElementById("upload-modal-status");
const uploadSubmitButton = document.getElementById("upload-submit-button");

const collectionsCount = document.getElementById("collections-count");
const selectAllCollectionsButton = document.getElementById(
  "select-all-collections",
);
const clearCollectionsButton = document.getElementById("clear-collections");
const backToTopButton = document.getElementById("back-to-top-button");

let selectedCollections = new Set();

let availableCollectionsData = [];
let dicomFieldMappings = { series: {}, studies: {}, patients: {} };
let dicomFieldMappingsPromise = null;
let activeDicomSearchType = "series";
let dicomResults = [];
let extractionsData = [];
let extractionsLoaded = false;
let isExtractionsLoading = false;
let extractionsError = "";
let lastDicomCollectionName = "";
let dicomIsLoading = false;
let dicomError = "";
let activeViewerSeries = null;
let activeViewerInfo = null;
let activeMetadataTab = "series";
let lastSearchScrollY = 0;
let isSeriesLoading = true;
let isAvailableCollectionsLoading = true;
let seriesPage = 1;
let availableCollectionsPage = 1;
let dicomPage = 1;
let activeImageObjects = [];

const seriesPageSize = 100;
const availableCollectionsPageSize = 25;
const dicomPageSize = 100;

function getSeriesFieldLabel(keys, fallback) {
  return fieldLabel(dicomFieldMappings.series, keys, fallback);
}

function getStudyFieldLabel(keys, fallback) {
  return fieldLabel(dicomFieldMappings.studies, keys, fallback);
}

function getPatientFieldLabel(keys, fallback) {
  return fieldLabel(dicomFieldMappings.patients, keys, fallback);
}

function renderSeriesTableHeaders() {
  if (!seriesTableHead) {
    return;
  }

  seriesTableHead.innerHTML = `
    <th>${escapeHtml(getSeriesFieldLabel(["SeriesInstanceUID", "series_instance_uid"], "Series UID"))}</th>
    <th>${escapeHtml(getSeriesFieldLabel(["PatientID", "PatientID_study", "patient_id_study"], "Patient"))}</th>
    <th>${escapeHtml(getSeriesFieldLabel(["Modality", "modality"], "Modality"))}</th>
    <th>${escapeHtml(getSeriesFieldLabel(["BodyPartExamined", "body_part_examined"], "Body Part"))}</th>
    <th>${escapeHtml(getSeriesFieldLabel(["SeriesDescription", "series_description"], "Description"))}</th>
    <th>${escapeHtml(getSeriesFieldLabel(["ImageCount", "image_count"], "Images"))}</th>
    <th>${escapeHtml(getSeriesFieldLabel(["Collection", "CollectionName_study", "collection_name_study"], "Collection"))}</th>
    <th></th>
  `;
}

async function ensureDicomFieldMappings() {
  if (!dicomFieldMappingsPromise) {
    dicomFieldMappingsPromise = loadSnomedFieldMappings(apiBaseUrl)
      .then((loadedMappings) => {
        dicomFieldMappings = loadedMappings;
        renderSeriesTableHeaders();
        renderDicomResults();
        return loadedMappings;
      })
      .catch((error) => {
        console.warn("Could not load SNOMED field mappings.", error);
        dicomFieldMappings = { series: {}, studies: {}, patients: {} };
        return dicomFieldMappings;
      });
  }

  return dicomFieldMappingsPromise;
}

const modalityFilterGroups = [
  ["CT", "Computed tomography"],
  ["MR", "Magnetic resonance imaging"],
  ["PT", "PET", "Positron emission tomography"],
];

function normalizeModality(value) {
  const rawValue = String(value ?? "").trim();

  if (!rawValue) {
    return "Missing";
  }

  const normalizedValue = rawValue.toLowerCase();
  const group = modalityFilterGroups.find((aliases) =>
    aliases.some((alias) => alias.toLowerCase() === normalizedValue),
  );

  return group ? group.at(-1) : rawValue;
}

function getModalityFilterKey(value) {
  const rawValue = String(value ?? "").trim();

  if (!rawValue) {
    return "Missing";
  }

  const normalizedModality = rawValue.toLowerCase();
  const group = modalityFilterGroups.find((aliases) =>
    aliases.some((alias) => alias.toLowerCase() === normalizedModality),
  );

  return group ? group.join(" / ") : rawValue;
}

function getDisplayValue(value) {
  if (value === undefined || value === null || value === "") {
    return "Missing";
  }

  return value;
}

function getPatientAgeDisplayValue(value) {
  if (value === -1 || value === "-1") {
    return "Missing";
  }

  return getDisplayValue(value);
}

function getSeriesSource(series) {
  if (series?.source) {
    return series.source;
  }

  if (String(series?.collectionType ?? "").trim().toLowerCase() === "nifti") {
    return "NIfTI";
  }
  if (String(series?.collectionType ?? "").trim().toLowerCase() === "dicom") {
    return "DICOM";
  }

  if (String(series?.modality ?? "").trim().toUpperCase() === "NIFTI") {
    return "NIfTI";
  }

  const collectionMeta = collections.find(
    (collection) => collection.id === series.collection,
  );

  if (String(collectionMeta?.type ?? "").trim().toLowerCase() === "nifti") {
    return "NIfTI";
  }
  if (String(collectionMeta?.type ?? "").trim().toLowerCase() === "dicom") {
    return "DICOM";
  }
  if (collectionMeta?.source) {
    return collectionMeta.source;
  }

  return "DICOM";
}

function normalizeViewerSeries(series) {
  if (series?.seriesUid) {
    const collectionMeta = collections.find(
      (collection) => collection.id === series.collection,
    );
    return {
      ...series,
      collectionType: series.collectionType ?? collectionMeta?.type ?? null,
      remote: Boolean(series.remote ?? collectionMeta?.remote),
      source: getSeriesSource(series),
    };
  }

  const collectionName = series.collection ?? series.collection_name ?? "";
  const collectionMeta = collections.find(
    (collection) => collection.id === collectionName,
  );

  return {
    seriesUid: series.instance_uid ?? series.seriesUid ?? "",
    studyUid: series.study_instance_uid ?? series.study_instance_uid_series ?? "",
    patientId: series.patient_id ?? "Unknown",
    modality: series.modality ?? "Unknown",
    bodyPart: series.body_part ?? "",
    protocolName: series.protocol_name ?? "",
    seriesDate: series.series_date ?? "",
    description: series.series_description ?? "",
    numImages: series.image_count ?? 0,
    collection: collectionName,
    collectionType: series.collectionType ?? series.type ?? collectionMeta?.type ?? null,
    remote: Boolean(series.remote ?? collectionMeta?.remote),
    manufacturer: series.manufacturer ?? "",
    manufacturerModelName: series.manufacturer_model_name ?? "",
    source: "DICOM",
  };
}

function resetViewerState() {
  viewerLoading?.classList.add("hidden");
  viewerError?.classList.add("hidden");
  viewerPlaceholder?.classList.add("hidden");
  dicomViewer?.classList.add("hidden");
  viewerControls?.classList.add("hidden");
  if (openRoiButton) {
    openRoiButton.disabled = true;
  }
  activeImageObjects = [];
  activeViewerInfo = null;

  if (dicomImage) {
    dicomImage.removeAttribute("src");
  }
}

function setViewerLoading(message) {
  if (viewerLoading) {
    viewerLoading.textContent = message;
    viewerLoading.classList.remove("hidden");
  }
  viewerError?.classList.add("hidden");
  viewerPlaceholder?.classList.add("hidden");
}

function setViewerError(message) {
  if (viewerError) {
    viewerError.textContent = message;
    viewerError.classList.remove("hidden");
  }
  viewerLoading?.classList.add("hidden");
  dicomViewer?.classList.add("hidden");
}

function showImageSlice(index) {
  if (!dicomImage || activeImageObjects.length === 0) {
    return;
  }

  const clampedIndex = Math.max(0, Math.min(index, activeImageObjects.length - 1));
  const object = activeImageObjects[clampedIndex];
  if (imageSlider) {
    imageSlider.value = clampedIndex + 1;
  }
  dicomImage.onload = () => {
    viewerLoading?.classList.add("hidden");
  };
  dicomImage.onerror = () => {
    setViewerError("Image slice failed to render.");
  };
  dicomImage.src = object.url;
}

function loadImageSliceViewer(viewerInfo) {
  activeImageObjects = viewerInfo.objects ?? [];
  activeViewerInfo = viewerInfo;
  if (activeImageObjects.length === 0) {
    throw new Error("No images were found for this series.");
  }

  dicomViewer?.classList.remove("hidden");
  viewerPlaceholder?.classList.add("hidden");
  viewerControls?.classList.remove("hidden");

  if (imageSlider) {
    imageSlider.min = 1;
    imageSlider.max = activeImageObjects.length;
    imageSlider.value = 1;
  }
  if (viewerImages) {
    viewerImages.textContent =
      viewerInfo.source === "NIfTI"
        ? `${activeImageObjects.length} slices`
        : `${activeImageObjects.length} images`;
  }
  if (openRoiButton) {
    openRoiButton.disabled = false;
  }

  showImageSlice(0);
}

function getSelectedImageObject() {
  if (activeImageObjects.length === 0) {
    return null;
  }
  const selectedIndex = imageSlider ? Number(imageSlider.value) - 1 : 0;
  const clampedIndex = Math.max(0, Math.min(selectedIndex, activeImageObjects.length - 1));
  return activeImageObjects[clampedIndex];
}

function openSelectedImageInRoi() {
  const object = getSelectedImageObject();
  if (!object || !activeViewerInfo) {
    return;
  }

  const selectedIndex = imageSlider ? Number(imageSlider.value) - 1 : 0;
  const imageNumber = Math.max(
    1,
    Math.min(activeImageObjects.length, selectedIndex + 1),
  );
  const url = new URL("roi.html", window.location.href);
  url.searchParams.set("image_url", object.url);
  url.searchParams.set("source", activeViewerInfo.source);
  url.searchParams.set("object_name", object.object_name);
  url.searchParams.set("series_uid", activeViewerInfo.series_uid);
  url.searchParams.set("image_number", String(imageNumber));

  if (activeViewerInfo.source === "NIfTI") {
    url.searchParams.set("axis", object.axis ?? activeViewerInfo.axis ?? "z");
    url.searchParams.set("slice", String(object.slice ?? 0));
  } else {
    url.searchParams.set("frame", String(object.frame ?? 0));
  }

  window.location.href = url.toString();
}

async function loadViewerForSeries(series) {
  resetViewerState();
  setViewerLoading("Loading image series...");

  try {
    const viewerInfo = await fetchSeriesViewer(
      apiBaseUrl,
      series.seriesUid,
      {
        collection: series.collection,
        patientId: series.patientId,
        studyUid: series.studyUid,
        collectionType: series.collectionType,
        remote: series.remote,
      },
    );
    loadImageSliceViewer(viewerInfo);
  } catch (error) {
    console.error("Viewer load failed", error);
    setViewerError(`Viewer failed: ${error.message}`);
  }
}

function renderCollections() {
  collectionsList.innerHTML = "";

  collectionsCount.textContent = `${selectedCollections.size}/${collections.length}`;

  if (isSeriesLoading) {
    collectionsList.innerHTML = `
      <p class="sidebar-loading">Loading collections...</p>
    `;
    return;
  }

  collections.forEach((collection) => {
    const isSelected = selectedCollections.has(collection.id);

    const card = document.createElement("div");
    card.className = "collection-card";

    if (isSelected) {
      card.classList.add("active");
    }

    card.innerHTML = `
      <div class="collection-checkbox">
        <span class="checkbox-box">${isSelected ? "✓" : ""}</span>
      </div>

      <div class="collection-info">
        <strong>${collection.name}</strong>
        <span>${collection.source} · ${collection.seriesCount} series</span>
      </div>
    `;

    card.addEventListener("click", () => {
      if (selectedCollections.has(collection.id)) {
        selectedCollections.delete(collection.id);
      } else {
        selectedCollections.add(collection.id);
      }

      resetSeriesPage();
      renderCollections();
      renderModalityFilter();
      renderSeries();
    });

    collectionsList.appendChild(card);
  });
}

function getFilteredSeries() {
  const searchTerm = searchInput.value.toLowerCase();
  const selectedModality = modalityFilter.value;

  return seriesData.filter((series) => {
    const matchesCollection = selectedCollections.has(series.collection);

    const matchesModality =
      selectedModality === "all" ||
      getModalityFilterKey(series.modality) === selectedModality;

    const matchesSearch = Object.values(series).some((value) =>
      String(value).toLowerCase().includes(searchTerm),
    );

    return matchesCollection && matchesModality && matchesSearch;
  });
}

function resetSeriesPage() {
  seriesPage = 1;
}

function resetAvailableCollectionsPage() {
  availableCollectionsPage = 1;
}

function resetDicomPage() {
  dicomPage = 1;
}

function renderPagination({
  container,
  currentPage,
  pageSize,
  totalResults,
  onPageChange,
  scrollTarget,
}) {
  const totalPages = Math.max(1, Math.ceil(totalResults / pageSize));

  if (totalResults === 0 || totalPages === 1) {
    container.innerHTML = "";
    return currentPage;
  }

  const safePage = Math.min(currentPage, totalPages);
  const startResult = (safePage - 1) * pageSize + 1;
  const endResult = Math.min(safePage * pageSize, totalResults);

  container.innerHTML = `
    <div class="pagination-summary">
      Showing ${startResult}-${endResult} of ${totalResults}
    </div>
    <div class="pagination-actions">
      <button class="pagination-prev" type="button" ${
        safePage === 1 ? "disabled" : ""
      }>Previous</button>
      <span>Page ${safePage} of ${totalPages}</span>
      <button class="pagination-next" type="button" ${
        safePage === totalPages ? "disabled" : ""
      }>Next</button>
    </div>
  `;

  container.querySelector(".pagination-prev").addEventListener("click", () => {
    onPageChange(Math.max(1, safePage - 1));
    scrollTarget?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  container.querySelector(".pagination-next").addEventListener("click", () => {
    onPageChange(Math.min(totalPages, safePage + 1));
    scrollTarget?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  return safePage;
}

function renderSeriesPagination(totalResults) {
  if (isSeriesLoading) {
    seriesPagination.innerHTML = "";
    return;
  }

  seriesPage = renderPagination({
    container: seriesPagination,
    currentPage: seriesPage,
    pageSize: seriesPageSize,
    totalResults,
    scrollTarget: seriesBrowserSection,
    onPageChange: (nextPage) => {
      seriesPage = nextPage;
      renderSeries();
    },
  });
}

function renderSeries() {
  renderSeriesTableHeaders();

  const filteredSeries = getFilteredSeries();
  const totalPages = Math.max(1, Math.ceil(filteredSeries.length / seriesPageSize));

  seriesPage = Math.min(seriesPage, totalPages);

  const startIndex = (seriesPage - 1) * seriesPageSize;
  const visibleSeries = filteredSeries.slice(
    startIndex,
    startIndex + seriesPageSize,
  );

  seriesTable.innerHTML = "";
  resultCount.textContent = `${filteredSeries.length} results`;
  renderSeriesPagination(filteredSeries.length);

  if (isSeriesLoading) {
    seriesTable.innerHTML = `
      <tr>
        <td colspan="8" class="empty-state">
          Loading downloaded series...
        </td>
      </tr>
    `;
    return;
  }

  if (filteredSeries.length === 0) {
    seriesTable.innerHTML = `
      <tr>
        <td colspan="8" class="empty-state">
          No series to show. Download an available collection first.
        </td>
      </tr>
    `;
    return;
  }

  visibleSeries.forEach((series) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${escapeHtml(series.seriesUid)}</td>
      <td>${escapeHtml(series.patientId)}</td>
      <td><span class="modality-badge">${escapeHtml(
        normalizeModality(series.modality),
      )}</span></td>
      <td>${escapeHtml(getDisplayValue(series.bodyPart))}</td>
      <td>${escapeHtml(getDisplayValue(series.description))}</td>
      <td>${escapeHtml(series.numImages)}</td>
      <td>${escapeHtml(series.collection)}</td>
      <td>
        <button class="view-button">View</button>
      </td>
    `;

    row.querySelector(".view-button").addEventListener("click", () => {
      openViewer(series);
    });

    seriesTable.appendChild(row);
  });
}

function escapeHtml(value) {
  return String(value ?? "—")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setMainView(view) {
  const showingSeries = view === "series";
  const showingAvailable = view === "available";
  const showingDicom = view === "dicom";
  const showingExtractions = view === "extractions";

  seriesBrowserSection.classList.toggle("hidden", !showingSeries);
  availableCollectionsSection.classList.toggle("hidden", !showingAvailable);
  dicomExplorerSection.classList.toggle("hidden", !showingDicom);
  extractionsSection.classList.toggle("hidden", !showingExtractions);

  seriesViewButton.classList.toggle("active", showingSeries);
  availableViewButton.classList.toggle("active", showingAvailable);
  dicomViewButton.classList.toggle("active", showingDicom);
  extractionsViewButton.classList.toggle("active", showingExtractions);
}

function renderModalityFilter() {
  const currentValue = modalityFilter.value || "all";
  const visibleSeries = seriesData.filter((series) =>
    selectedCollections.has(series.collection),
  );
  const modalities = Array.from(
    new Set(visibleSeries.map((series) => getModalityFilterKey(series.modality))),
  )
    .filter((modality) => modality && modality !== "Unknown")
    .sort();

  modalityFilter.innerHTML = `
    <option value="all">All modalities</option>
    ${modalities
      .map(
        (modality) =>
          `<option value="${escapeHtml(modality)}">${escapeHtml(modality)}</option>`,
      )
      .join("")}
  `;

  modalityFilter.value = modalities.includes(currentValue)
    ? currentValue
    : "all";
}

function setDicomSearchType(searchType) {
  activeDicomSearchType = searchType;
  dicomResults = [];
  lastDicomCollectionName = "";
  dicomError = "";
  resetDicomPage();

  renderDicomExplorer();
}

function renderDicomExplorer() {
  dicomSeriesModeButton.classList.toggle(
    "active",
    activeDicomSearchType === "series",
  );
  dicomStudiesModeButton.classList.toggle(
    "active",
    activeDicomSearchType === "studies",
  );
  dicomPatientsModeButton.classList.toggle(
    "active",
    activeDicomSearchType === "patients",
  );

  dicomSearchButton.disabled = dicomIsLoading;
  dicomCollectionInput.disabled = dicomIsLoading;

  if (dicomIsLoading) {
    dicomStatus.className = "dicom-status loading";
    dicomStatus.textContent = `Searching ${lastDicomCollectionName}...`;
  } else if (dicomError) {
    dicomStatus.className = "dicom-status error";
    dicomStatus.textContent = dicomError;
  } else if (lastDicomCollectionName && dicomResults.length > 0) {
    dicomStatus.className = "dicom-status";
    dicomStatus.textContent = `Showing remote ${activeDicomSearchType} for ${lastDicomCollectionName}.`;
  } else {
    dicomStatus.className = "dicom-status";
    dicomStatus.textContent = "";
  }

  renderDicomResults();
}

function renderDicomResults() {
  dicomResultCount.textContent = `${dicomResults.length} results`;

  if (dicomIsLoading) {
    dicomPagination.innerHTML = "";
    dicomResultsContainer.innerHTML = `
      <section class="table-card">
        <p class="empty-state">Searching remote DICOM metadata...</p>
      </section>
    `;
    return;
  }

  if (dicomError) {
    dicomPagination.innerHTML = "";
    dicomResultsContainer.innerHTML = `
      <section class="table-card">
        <p class="empty-state">No results to show until the search succeeds.</p>
      </section>
    `;
    return;
  }

  if (dicomResults.length === 0) {
    dicomPagination.innerHTML = "";
    const message = lastDicomCollectionName
      ? "No remote DICOM results found for this collection."
      : "Enter a collection name to search remote DICOM metadata.";

    dicomResultsContainer.innerHTML = `
      <section class="table-card">
        <p class="empty-state">${message}</p>
      </section>
    `;
    return;
  }

  const totalPages = Math.max(1, Math.ceil(dicomResults.length / dicomPageSize));
  dicomPage = Math.min(dicomPage, totalPages);

  const startIndex = (dicomPage - 1) * dicomPageSize;
  const visibleResults = dicomResults.slice(startIndex, startIndex + dicomPageSize);

  if (activeDicomSearchType === "studies") {
    renderDicomStudiesTable(visibleResults);
    renderDicomPagination(dicomResults.length);
    return;
  }

  if (activeDicomSearchType === "patients") {
    renderDicomPatientsTable(visibleResults);
    renderDicomPagination(dicomResults.length);
    return;
  }

  renderDicomSeriesTable(visibleResults);
  renderDicomPagination(dicomResults.length);
}

function renderDicomPagination(totalResults) {
  dicomPage = renderPagination({
    container: dicomPagination,
    currentPage: dicomPage,
    pageSize: dicomPageSize,
    totalResults,
    scrollTarget: dicomExplorerSection,
    onPageChange: (nextPage) => {
      dicomPage = nextPage;
      renderDicomResults();
    },
  });
}

function renderDicomSeriesTable(results) {
  dicomResultsContainer.innerHTML = `
    <section class="table-card">
      <div class="table-header">
        <h2>Remote Series</h2>
        <p>${results.length} results</p>
      </div>

      <table>
        <thead>
          <tr>
            <th>${escapeHtml(getSeriesFieldLabel(["SeriesInstanceUID", "series_instance_uid"], "Series UID"))}</th>
            <th>${escapeHtml(getSeriesFieldLabel(["PatientID", "PatientID_study", "patient_id_study"], "Patient"))}</th>
            <th>${escapeHtml(getSeriesFieldLabel(["Modality", "modality"], "Modality"))}</th>
            <th>${escapeHtml(getSeriesFieldLabel(["BodyPartExamined", "body_part_examined"], "Body Part"))}</th>
            <th>${escapeHtml(getSeriesFieldLabel(["SeriesDescription", "series_description"], "Description"))}</th>
            <th>${escapeHtml(getSeriesFieldLabel(["ImageCount", "image_count"], "Images"))}</th>
            <th>${escapeHtml(getSeriesFieldLabel(["Collection", "CollectionName_study", "collection_name_study"], "Collection"))}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${results
            .map(
              (series, index) => `
                <tr>
                  <td>${escapeHtml(series.instance_uid)}</td>
                  <td>${escapeHtml(series.patient_id)}</td>
                  <td><span class="modality-badge">${escapeHtml(
                    normalizeModality(series.modality),
                  )}</span></td>
                  <td>${escapeHtml(getDisplayValue(series.body_part))}</td>
                  <td>${escapeHtml(
                    getDisplayValue(series.series_description),
                  )}</td>
                  <td>${escapeHtml(series.image_count)}</td>
                  <td>${escapeHtml(series.collection)}</td>
                  <td>
                    <button class="view-button" data-dicom-series-index="${index}">
                      View
                    </button>
                  </td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </section>
  `;

  dicomResultsContainer
    .querySelectorAll(".view-button[data-dicom-series-index]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        const series = results[Number(button.dataset.dicomSeriesIndex)];
        if (series) {
          openViewer({
            ...series,
            source: "DICOM",
            collectionType: "dicom",
            remote: true,
          });
        }
      });
    });
}

function renderDicomStudiesTable(results) {
  dicomResultsContainer.innerHTML = `
    <section class="table-card">
      <div class="table-header">
        <h2>Remote Studies</h2>
        <p>${results.length} results</p>
      </div>

      <table>
        <thead>
          <tr>
            <th>${escapeHtml(getStudyFieldLabel(["StudyInstanceUID", "study_instance_uid"], "Study UID"))}</th>
            <th>${escapeHtml(getStudyFieldLabel(["PatientID", "PatientID_study", "patient_id_study"], "Patient"))}</th>
            <th>${escapeHtml(getStudyFieldLabel(["StudyDate", "study_date"], "Date"))}</th>
            <th>${escapeHtml(getStudyFieldLabel(["StudyDescription", "study_description"], "Description"))}</th>
            <th>${escapeHtml(getStudyFieldLabel(["SeriesCount", "series_count"], "Series Count"))}</th>
            <th>${escapeHtml(getStudyFieldLabel(["Collection", "CollectionName_study", "collection_name_study"], "Collection"))}</th>
          </tr>
        </thead>
        <tbody>
          ${results
            .map(
              (study) => `
                <tr>
                  <td>${escapeHtml(study.instance_uid)}</td>
                  <td>${escapeHtml(study.patient_id)}</td>
                  <td>${escapeHtml(study.date)}</td>
                  <td>${escapeHtml(study.description)}</td>
                  <td>${escapeHtml(study.series_count)}</td>
                  <td>${escapeHtml(study.collection)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </section>
  `;
}

function renderDicomPatientsTable(results) {
  dicomResultsContainer.innerHTML = `
    <section class="table-card">
      <div class="table-header">
        <h2>Remote Patients</h2>
        <p>${results.length} results</p>
      </div>

      <table>
        <thead>
          <tr>
            <th>${escapeHtml(getPatientFieldLabel(["PatientID", "PatientId", "patient_id"], "Patient ID"))}</th>
            <th>${escapeHtml(getPatientFieldLabel(["PatientSex", "patient_sex"], "Sex"))}</th>
            <th>${escapeHtml(getPatientFieldLabel(["PatientAge", "patient_age"], "Age"))}</th>
            <th>${escapeHtml(getPatientFieldLabel(["EthnicGroup", "ethnic_group"], "Ethnic Group"))}</th>
          </tr>
        </thead>
        <tbody>
          ${results
            .map(
              (patient) => `
                <tr>
                  <td>${escapeHtml(patient.id)}</td>
                  <td>${escapeHtml(patient.sex)}</td>
                  <td>${escapeHtml(getPatientAgeDisplayValue(patient.age))}</td>
                  <td>${escapeHtml(patient.ethnic_group)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </section>
  `;
}

async function handleDicomSearch() {
  const collectionName = dicomCollectionInput.value.trim();

  if (!collectionName) {
    dicomError = "Enter a collection name before searching.";
    dicomResults = [];
    lastDicomCollectionName = "";
    renderDicomExplorer();
    return;
  }

  dicomIsLoading = true;
  dicomError = "";
  lastDicomCollectionName = collectionName;
  resetDicomPage();
  renderDicomExplorer();

  try {
    await ensureDicomFieldMappings();

    if (activeDicomSearchType === "studies") {
      dicomResults = await searchDicomStudies(apiBaseUrl, collectionName);
    } else if (activeDicomSearchType === "patients") {
      dicomResults = await searchDicomPatients(apiBaseUrl, collectionName);
    } else {
      dicomResults = await searchDicomSeries(apiBaseUrl, collectionName);
    }
  } catch (error) {
    console.error("DICOM search failed", error);
    dicomResults = [];
    dicomError = `Search failed: ${error.message}`;
  } finally {
    dicomIsLoading = false;
    renderDicomExplorer();
  }
}

function syncAvailableCollectionStatus() {
  const downloadedNames = new Set(
    collections.map((collection) => collection.id),
  );

  availableCollectionsData = availableCollectionsData.map((collection) => ({
    ...collection,
    downloaded: downloadedNames.has(collection.name),
  }));
}

function renderAvailableCollections() {
  const searchTerm = availableSearchInput.value.trim().toLowerCase();

  if (isAvailableCollectionsLoading) {
    availableResultCount.textContent = "Loading collections";
    availablePagination.innerHTML = "";
    availableCollectionsList.innerHTML = `
      <p class="empty-state">Loading available collections...</p>
    `;
    return;
  }

  const filteredCollections = availableCollectionsData.filter((collection) => {
    const searchableText = [
      collection.name,
      collection.description,
      collection.licenseName,
      collection.source,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    return searchTerm === "" || searchableText.includes(searchTerm);
  });

  availableResultCount.textContent = `${filteredCollections.length} collections`;
  availableCollectionsList.innerHTML = "";

  if (filteredCollections.length === 0) {
    availablePagination.innerHTML = "";
    availableCollectionsList.innerHTML = `
      <p class="empty-state">No available collections match the search.</p>
    `;
    return;
  }

  const totalPages = Math.max(
    1,
    Math.ceil(filteredCollections.length / availableCollectionsPageSize),
  );
  availableCollectionsPage = Math.min(availableCollectionsPage, totalPages);

  const startIndex = (availableCollectionsPage - 1) * availableCollectionsPageSize;
  const visibleCollections = filteredCollections.slice(
    startIndex,
    startIndex + availableCollectionsPageSize,
  );

  visibleCollections.forEach((collection) => {
    const card = document.createElement("article");
    card.className = "available-card";

    const actionButton = collection.downloaded
      ? `<button class="download-button downloaded" disabled>Downloaded</button>`
      : `<button class="download-button" data-collection-name="${escapeHtml(
          collection.name,
        )}">Download</button>`;

    card.innerHTML = `
      <div class="available-card-main">
        <div>
          <h3>${escapeHtml(collection.name)}</h3>
          <p>${escapeHtml(collection.description)}</p>
        </div>

        <div class="available-meta">
          <span>${escapeHtml(collection.source)}</span>
          <span>${escapeHtml(collection.licenseName)}</span>
        </div>
      </div>

      <div class="available-card-action">
        ${actionButton}
      </div>
    `;

    availableCollectionsList.appendChild(card);
  });

  renderAvailableCollectionsPagination(filteredCollections.length);

  document
    .querySelectorAll(".download-button[data-collection-name]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        handleCollectionDownload(button.dataset.collectionName, button);
      });
    });
}

function renderAvailableCollectionsPagination(totalResults) {
  availableCollectionsPage = renderPagination({
    container: availablePagination,
    currentPage: availableCollectionsPage,
    pageSize: availableCollectionsPageSize,
    totalResults,
    scrollTarget: availableCollectionsSection,
    onPageChange: (nextPage) => {
      availableCollectionsPage = nextPage;
      renderAvailableCollections();
    },
  });
}

function getExtractionFeatureName(feature) {
  return feature.feature_name || `Feature ${feature.id}`;
}

function getExtractionSnomedTerm(feature) {
  return feature.standardized_feature_name || "Missing SNOMED CT term";
}

function formatFeatureValue(value) {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  }

  return getDisplayValue(value);
}

function formatExtractionCount(count) {
  return `${count} ${count === 1 ? "extraction" : "extractions"}`;
}

function getExtractionImageIndex(extraction, objectCount) {
  const imageNumber = Number(extraction.image_number);

  if (!Number.isFinite(imageNumber)) {
    return 0;
  }

  const zeroBasedIndex = imageNumber > 0 ? imageNumber - 1 : imageNumber;
  return Math.max(0, Math.min(objectCount - 1, zeroBasedIndex));
}

function drawStoredRoiOverlay(ctx, points, scale, offsetX, offsetY) {
  if (!Array.isArray(points) || points.length < 2) {
    return;
  }

  ctx.save();
  ctx.beginPath();
  points.forEach((point, index) => {
    const x = offsetX + Number(point.x) * scale;
    const y = offsetY + Number(point.y) * scale;

    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(14, 165, 164, 0.18)";
  ctx.strokeStyle = "#0ea5a4";
  ctx.lineWidth = 2;
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function drawStoredRoiOnly(canvas, points) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#f8fafc";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (!Array.isArray(points) || points.length < 2) {
    ctx.fillStyle = "#64748b";
    ctx.font = "13px Inter, Arial, sans-serif";
    ctx.fillText("No ROI coordinates", 18, 28);
    return;
  }

  const xs = points.map((point) => Number(point.x));
  const ys = points.map((point) => Number(point.y));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const roiWidth = Math.max(1, maxX - minX);
  const roiHeight = Math.max(1, maxY - minY);
  const scale = Math.min(
    (canvas.width - 32) / roiWidth,
    (canvas.height - 32) / roiHeight,
  );
  const offsetX = (canvas.width - roiWidth * scale) / 2 - minX * scale;
  const offsetY = (canvas.height - roiHeight * scale) / 2 - minY * scale;

  drawStoredRoiOverlay(ctx, points, scale, offsetX, offsetY);
}

async function drawExtractionPreview(extraction) {
  const canvas = document.querySelector(
    `[data-extraction-preview="${extraction.roi_id}"]`,
  );

  if (!canvas) {
    return;
  }

  canvas.width = 280;
  canvas.height = 190;
  drawStoredRoiOnly(canvas, extraction.roi_coordinates);

  try {
    const viewerInfo = await fetchSeriesViewer(
      apiBaseUrl,
      extraction.series_instance_uid_roi,
    );
    const objects = viewerInfo.objects ?? [];

    if (objects.length === 0) {
      return;
    }

    const imageObject = objects[getExtractionImageIndex(extraction, objects.length)];
    const image = new Image();
    image.onload = () => {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const scale = Math.min(
        canvas.width / image.naturalWidth,
        canvas.height / image.naturalHeight,
      );
      const dw = image.naturalWidth * scale;
      const dh = image.naturalHeight * scale;
      const dx = (canvas.width - dw) / 2;
      const dy = (canvas.height - dh) / 2;

      ctx.drawImage(image, dx, dy, dw, dh);
      drawStoredRoiOverlay(ctx, extraction.roi_coordinates, scale, dx, dy);
    };
    image.onerror = () => drawStoredRoiOnly(canvas, extraction.roi_coordinates);
    image.src = imageObject.url;
  } catch (error) {
    console.warn("Could not render extraction image preview.", error);
  }
}

function renderExtractions() {
  extractionsResultCount.textContent = formatExtractionCount(
    extractionsData.length,
  );

  if (isExtractionsLoading) {
    extractionsStatus.textContent = "Loading stored extractions...";
    extractionsStatus.className = "dicom-status loading";
    extractionsList.innerHTML = `
      <p class="empty-state">Loading stored extractions...</p>
    `;
    return;
  }

  if (extractionsError) {
    extractionsStatus.textContent = extractionsError;
    extractionsStatus.className = "dicom-status error";
  } else {
    extractionsStatus.textContent = extractionsLoaded
      ? "Showing stored feature extractions."
      : "Open this page to load saved extractions.";
    extractionsStatus.className = "dicom-status";
  }

  if (extractionsData.length === 0) {
    extractionsList.innerHTML = `
      <p class="empty-state">
        No stored extractions yet. Compute and save an ROI extraction first.
      </p>
    `;
    return;
  }

  extractionsList.innerHTML = extractionsData
    .map((extraction) => {
      const features = extraction.features_extracted ?? [];
      return `
        <article class="extraction-card">
          <div class="extraction-preview">
            <canvas data-extraction-preview="${escapeHtml(extraction.roi_id)}"></canvas>
          </div>
          <div class="extraction-details">
            <div class="extraction-card-header">
              <div>
                <h3>ROI ${escapeHtml(extraction.roi_id)}</h3>
                <p>${escapeHtml(extraction.series_instance_uid_roi)}</p>
              </div>
              <span>Image ${escapeHtml(extraction.image_number)}</span>
            </div>
            <div class="extraction-features">
              ${features
                .map(
                  (feature) => `
                    <div class="extraction-feature-row">
                      <span class="extraction-feature-labels">
                        <span class="extraction-feature-name">
                          ${escapeHtml(getExtractionFeatureName(feature))}
                        </span>
                        <span class="extraction-feature-snomed">
                          SNOMED CT: ${escapeHtml(getExtractionSnomedTerm(feature))}
                        </span>
                      </span>
                      <span class="extraction-feature-value">
                        ${escapeHtml(formatFeatureValue(feature.value))}
                      </span>
                    </div>
                  `,
                )
                .join("")}
            </div>
          </div>
        </article>
      `;
    })
    .join("");

  extractionsData.forEach(drawExtractionPreview);
}

async function refreshExtractions() {
  isExtractionsLoading = true;
  extractionsError = "";
  renderExtractions();

  try {
    extractionsData = await loadExtractions(apiBaseUrl);
    extractionsLoaded = true;
  } catch (error) {
    console.error("Could not load stored extractions.", error);
    extractionsData = [];
    extractionsError = `Failed to load stored extractions: ${error.message}`;
  } finally {
    isExtractionsLoading = false;
    renderExtractions();
  }
}

function renderMetadataRows(rows) {
  metadataContent.innerHTML = rows
    .map(
      ([label, value]) => `
        <div class="metadata-row">
          <span>${escapeHtml(label)}</span>
          <span>${escapeHtml(getDisplayValue(value))}</span>
        </div>
      `,
    )
    .join("");
}

function setMetadataTab(tab) {
  activeMetadataTab = tab;

  metadataSeriesTab.classList.toggle("active", tab === "series");
  metadataPatientTab.classList.toggle("active", tab === "patient");
}

function renderSeriesMetadata(series) {
  setMetadataTab("series");
  renderMetadataRows([
    [getSeriesFieldLabel(["SeriesInstanceUID", "series_instance_uid"], "Series UID"), series.seriesUid],
    [getSeriesFieldLabel(["StudyInstanceUID", "StudyInstanceUID_series", "study_instance_uid_series"], "Study UID"), series.studyUid],
    [getSeriesFieldLabel(["PatientID", "PatientID_study", "patient_id_study"], "Patient ID"), series.patientId],
    [getSeriesFieldLabel(["Modality", "modality"], "Modality"), normalizeModality(series.modality)],
    [getSeriesFieldLabel(["BodyPartExamined", "body_part_examined"], "Body Part"), series.bodyPart],
    [getSeriesFieldLabel(["SeriesDescription", "series_description"], "Description"), series.description],
    [getSeriesFieldLabel(["ProtocolName", "protocol_name"], "Protocol"), series.protocolName],
    [getSeriesFieldLabel(["SeriesDate", "series_date"], "Series Date"), series.seriesDate],
    [getSeriesFieldLabel(["ImageCount", "image_count"], "Number of Images"), series.numImages],
    [getSeriesFieldLabel(["Collection", "CollectionName_study", "collection_name_study"], "Collection"), series.collection],
    [getSeriesFieldLabel(["Manufacturer", "manufacturer"], "Manufacturer"), series.manufacturer],
    [getSeriesFieldLabel(["ManufacturerModelName", "manufacturer_model_name"], "Model"), series.manufacturerModelName],
  ]);
}

function renderPatientMetadata(series, patient = null) {
  setMetadataTab("patient");
  renderMetadataRows([
    [getPatientFieldLabel(["PatientID", "PatientId", "patient_id"], "Patient ID"), patient?.id ?? series.patientId],
    [getPatientFieldLabel(["PatientSex", "patient_sex"], "Sex"), patient?.sex ?? series.patientSex],
    [getPatientFieldLabel(["PatientAge", "patient_age"], "Age"), getPatientAgeDisplayValue(patient?.age ?? series.patientAge)],
    [getPatientFieldLabel(["EthnicGroup", "ethnic_group"], "Ethnic Group"), patient?.ethnic_group ?? series.patientEthnicGroup],
    [getSeriesFieldLabel(["Collection", "CollectionName_study", "collection_name_study"], "Collection"), series.collection],
  ]);
}

function renderPatientMetadataLoading(series) {
  setMetadataTab("patient");
  renderMetadataRows([
    [getPatientFieldLabel(["PatientID", "PatientId", "patient_id"], "Patient ID"), series.patientId],
    [getPatientFieldLabel(["PatientSex", "patient_sex"], "Sex"), "Loading..."],
    [getPatientFieldLabel(["PatientAge", "patient_age"], "Age"), "Loading..."],
    [getPatientFieldLabel(["EthnicGroup", "ethnic_group"], "Ethnic Group"), "Loading..."],
    [getSeriesFieldLabel(["Collection", "CollectionName_study", "collection_name_study"], "Collection"), series.collection],
  ]);
}

async function showPatientMetadata() {
  if (!activeViewerSeries) {
    return;
  }

  renderPatientMetadataLoading(activeViewerSeries);

  try {
    const patient = await loadPatient(
      apiBaseUrl,
      activeViewerSeries.patientId,
      activeViewerSeries.collection,
    );
    renderPatientMetadata(activeViewerSeries, patient);
  } catch (error) {
    console.warn("Could not load patient metadata. Showing series fallback.", error);
    renderPatientMetadata(activeViewerSeries);
  }
}

async function handleCollectionDownload(collectionName, button) {
  try {
    button.disabled = true;
    button.textContent = "Downloading...";

    await downloadAvailableCollection(apiBaseUrl, collectionName);

    button.textContent = "Refreshing...";

    const { collections: loadedCollections, seriesData: loadedSeries } =
      await loadMockData(apiBaseUrl);

    collections = loadedCollections;
    seriesData = loadedSeries;

    selectedCollections = new Set(
      collections.map((collection) => collection.id),
    );

    syncAvailableCollectionStatus();
    resetAvailableCollectionsPage();
    renderCollections();
    renderModalityFilter();
    renderSeries();
    renderAvailableCollections();

    button.textContent = "Downloaded";
    button.classList.add("downloaded");
  } catch (error) {
    console.error("Collection download failed", error);

    button.disabled = false;
    button.textContent = "Failed — Retry";
  }
}

function openViewer(series) {
  activeViewerSeries = normalizeViewerSeries(series);
  lastSearchScrollY = window.scrollY;
  updateBackToTopButton();
  appShell.classList.add("viewer-mode");

  searchPage.classList.remove("active");
  viewerPage.classList.add("active");

  viewerTitle.textContent = `${normalizeModality(activeViewerSeries.modality)} series`;
  viewerSubtitle.textContent = `${activeViewerSeries.patientId} · ${getDisplayValue(
    activeViewerSeries.bodyPart,
  )}`;
  viewerModality.textContent = normalizeModality(activeViewerSeries.modality);

  if (getSeriesSource(activeViewerSeries) === "NIfTI") {
    viewerImages.textContent = "NIfTI volume";
  } else {
    viewerImages.textContent = `${activeViewerSeries.numImages} images`;
  }

  imageSlider.max = activeViewerSeries.numImages || 1;
  imageSlider.value = Math.ceil((activeViewerSeries.numImages || 1) / 2);

  renderSeriesMetadata(activeViewerSeries);
  if (!activeViewerSeries.seriesUid) {
    setViewerError("Missing series UID. Unable to load viewer.");
    return;
  }

  loadViewerForSeries(activeViewerSeries);
}

function closeViewer() {
  activeViewerSeries = null;
  appShell.classList.remove("viewer-mode");

  viewerPage.classList.remove("active");
  searchPage.classList.add("active");
  resetViewerState();

  requestAnimationFrame(() => {
    window.scrollTo({
      top: lastSearchScrollY,
      left: 0,
      behavior: "auto",
    });
    updateBackToTopButton();
  });
}

function updateBackToTopButton() {
  backToTopButton.classList.toggle("visible", window.scrollY > 650);
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: "smooth",
  });
}

searchInput.addEventListener("input", () => {
  resetSeriesPage();
  renderSeries();
});

modalityFilter.addEventListener("change", () => {
  resetSeriesPage();
  renderSeries();
});
backButton.addEventListener("click", closeViewer);
imageSlider.addEventListener("input", () => {
  if (activeImageObjects.length > 0) {
    showImageSlice(Number(imageSlider.value) - 1);
  }
});
openRoiButton?.addEventListener("click", openSelectedImageInRoi);
window.addEventListener("scroll", updateBackToTopButton);
backToTopButton.addEventListener("click", scrollToTop);

metadataSeriesTab.addEventListener("click", () => {
  if (activeViewerSeries) {
    renderSeriesMetadata(activeViewerSeries);
  }
});

metadataPatientTab.addEventListener("click", showPatientMetadata);

selectAllCollectionsButton.addEventListener("click", () => {
  selectedCollections = new Set(collections.map((collection) => collection.id));
  resetSeriesPage();
  renderCollections();
  renderModalityFilter();
  renderSeries();
});

clearCollectionsButton.addEventListener("click", () => {
  selectedCollections.clear();
  resetSeriesPage();
  renderCollections();
  renderModalityFilter();
  renderSeries();
});

const queryParams = new URLSearchParams(window.location.search);
const apiBaseUrl = queryParams.get("apiBaseUrl") ?? window.location.origin;

async function initializeData() {
  collections = [];
  seriesData = [];
  availableCollectionsData = [];
  isSeriesLoading = true;
  isAvailableCollectionsLoading = true;

  selectedCollections = new Set(collections.map((collection) => collection.id));

  renderCollections();
  renderModalityFilter();
  renderSeries();
  renderAvailableCollections();

  const seriesLoad = loadMockData(apiBaseUrl)
    .then(({ collections: loadedCollections, seriesData: loadedSeries }) => {
      collections = loadedCollections;
      seriesData = loadedSeries;
      selectedCollections = new Set(
        collections.map((collection) => collection.id),
      );
    })
    .catch((error) => {
      console.warn(
        "Could not load downloaded collections/series from backend. Starting empty.",
        error,
      );
    })
    .finally(() => {
      isSeriesLoading = false;
      syncAvailableCollectionStatus();
      resetAvailableCollectionsPage();
      renderCollections();
      renderModalityFilter();
      renderSeries();
      renderAvailableCollections();
    });

  const availableLoad = loadAvailableCollections(apiBaseUrl)
    .then((loadedAvailableCollections) => {
      availableCollectionsData = loadedAvailableCollections;
    })
    .catch((error) => {
      console.warn(
        "Could not load available collections from backend. Using fallback data.",
        error,
      );

      availableCollectionsData = [...fallbackAvailableCollections];
    })
    .finally(() => {
      isAvailableCollectionsLoading = false;
      syncAvailableCollectionStatus();
      resetAvailableCollectionsPage();
      renderAvailableCollections();
    });

  await Promise.allSettled([ensureDicomFieldMappings(), seriesLoad, availableLoad]);
}

seriesViewButton.addEventListener("click", () => {
  setMainView("series");
});

availableViewButton.addEventListener("click", () => {
  setMainView("available");
  renderAvailableCollections();
});

dicomViewButton.addEventListener("click", () => {
  setMainView("dicom");
  renderDicomExplorer();
});

extractionsViewButton.addEventListener("click", () => {
  setMainView("extractions");
  if (!extractionsLoaded && !isExtractionsLoading) {
    refreshExtractions();
  } else {
    renderExtractions();
  }
});

refreshExtractionsButton.addEventListener("click", refreshExtractions);

dicomSeriesModeButton.addEventListener("click", () => {
  setDicomSearchType("series");
});

dicomStudiesModeButton.addEventListener("click", () => {
  setDicomSearchType("studies");
});

dicomPatientsModeButton.addEventListener("click", () => {
  setDicomSearchType("patients");
});

dicomSearchButton.addEventListener("click", handleDicomSearch);

dicomCollectionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    handleDicomSearch();
  }
});

availableSearchInput.addEventListener("input", () => {
  resetAvailableCollectionsPage();
  renderAvailableCollections();
});

function setUploadModalStatus(message, type = "") {
  if (!uploadModalStatus) {
    return;
  }
  uploadModalStatus.textContent = message;
  uploadModalStatus.classList.toggle("error", type === "error");
  uploadModalStatus.classList.toggle("success", type === "success");
}

function getUploadZipFile() {
  return uploadInput?.files?.[0] ?? null;
}

function updateUploadTypeFields() {
  const isNifti = uploadDatasetType?.value === "nifti";
  uploadNiftiFields?.classList.toggle("hidden", !isNifti);
  if (!isNifti) {
    if (uploadMetadataFile) {
      uploadMetadataFile.value = "";
    }
    if (uploadColumnMapping) {
      uploadColumnMapping.value = "";
    }
  }
}

function updateUploadSubmitState() {
  const hasZip = Boolean(getUploadZipFile());
  const hasCollection = Boolean(uploadCollectionName?.value.trim());
  const hasDatasetType = Boolean(uploadDatasetType?.value);

  if (uploadSubmitButton) {
    uploadSubmitButton.disabled = !(hasZip && hasCollection && hasDatasetType);
  }
}

function setUploadFormDisabled(disabled) {
  [
    uploadDatasetType,
    uploadCollectionName,
    uploadDescription,
    uploadInput,
    uploadMetadataFile,
    uploadDescriptionSeriesMatching,
    uploadColumnMapping,
    uploadSubmitButton,
    uploadCancelButton,
    uploadModalClose,
  ].forEach((element) => {
    if (element) {
      element.disabled = disabled;
    }
  });
}

function resetUploadForm() {
  uploadForm?.reset();
  updateUploadTypeFields();
  updateUploadSubmitState();
  setUploadModalStatus("Choose a ZIP file to start.");
}

function openUploadModal() {
  resetUploadForm();
  uploadModal?.classList.remove("hidden");
  uploadCollectionName?.focus();
}

function closeUploadModal() {
  uploadModal?.classList.add("hidden");
}

function inferCollectionNameFromZip(file) {
  return file?.name?.replace(/\.zip$/i, "").trim() ?? "";
}

async function refreshDataAfterUpload() {
  const { collections: loadedCollections, seriesData: loadedSeries } =
    await loadMockData(apiBaseUrl);

  collections = loadedCollections;
  seriesData = loadedSeries;

  selectedCollections = new Set(
    collections.map((collection) => collection.id),
  );

  syncAvailableCollectionStatus();
  resetAvailableCollectionsPage();
  renderCollections();
  renderModalityFilter();
  renderSeries();
  renderAvailableCollections();
}

function getUploadPayload() {
  return {
    datasetType: uploadDatasetType.value,
    collectionName: uploadCollectionName.value.trim(),
    description: uploadDescription.value.trim(),
    zipFile: getUploadZipFile(),
    metadataFile:
      uploadDatasetType.value === "nifti"
        ? uploadMetadataFile?.files?.[0] ?? null
        : null,
    allowDescriptionSeriesMatching:
      uploadDatasetType.value === "nifti"
        ? Boolean(uploadDescriptionSeriesMatching?.checked)
        : false,
    columnMapping:
      uploadDatasetType.value === "nifti" ? uploadColumnMapping.value : "",
  };
}

if (uploadButton && uploadModal && uploadForm) {
  uploadButton.addEventListener("click", openUploadModal);
  uploadModalClose?.addEventListener("click", closeUploadModal);
  uploadCancelButton?.addEventListener("click", closeUploadModal);
  uploadModal.addEventListener("click", (event) => {
    if (event.target === uploadModal) {
      closeUploadModal();
    }
  });

  uploadDatasetType?.addEventListener("change", () => {
    updateUploadTypeFields();
    updateUploadSubmitState();
  });
  uploadCollectionName?.addEventListener("input", updateUploadSubmitState);
  uploadInput?.addEventListener("change", () => {
    const file = getUploadZipFile();
    if (file && !uploadCollectionName.value.trim()) {
      uploadCollectionName.value = inferCollectionNameFromZip(file);
    }
    setUploadModalStatus(file ? `Selected ${file.name}.` : "Choose a ZIP file to start.");
    updateUploadSubmitState();
  });

  uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = getUploadPayload();

    if (!payload.zipFile || !payload.collectionName) {
      setUploadModalStatus("Choose a ZIP file and collection name.", "error");
      updateUploadSubmitState();
      return;
    }

    try {
      setUploadFormDisabled(true);
      setUploadModalStatus(`Uploading ${payload.zipFile.name}...`);
      uploadStatus.textContent = `Uploading ${payload.zipFile.name}...`;

      await uploadDataset(apiBaseUrl, payload);

      setUploadModalStatus("Upload complete. Refreshing data...", "success");
      uploadStatus.textContent = "Upload complete. Refreshing data...";

      await refreshDataAfterUpload();

      uploadStatus.textContent = "Dataset loaded.";
      closeUploadModal();
    } catch (error) {
      console.error("Upload failed", error);
      const message = `Upload failed: ${error.message}`;
      setUploadModalStatus(message, "error");
      uploadStatus.textContent = message;
    } finally {
      setUploadFormDisabled(false);
      updateUploadSubmitState();
    }
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !uploadModal?.classList.contains("hidden")) {
    closeUploadModal();
  }
});

if (uploadForm) {
  updateUploadTypeFields();
  updateUploadSubmitState();
}

initializeData().catch((error) => {
  console.error("Failed to load mock data", error);
  resultCount.textContent = "Failed to load data";
});
