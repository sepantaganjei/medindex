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

const seriesViewButton = document.getElementById("series-view-button");
const availableViewButton = document.getElementById("available-view-button");
const dicomViewButton = document.getElementById("dicom-view-button");
const seriesBrowserSection = document.getElementById("series-browser-section");
const availableCollectionsSection = document.getElementById(
  "available-collections-section",
);
const dicomExplorerSection = document.getElementById("dicom-explorer-section");
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

const uploadInput = document.getElementById("dataset-upload-input");
const uploadButton = document.getElementById("dataset-upload-button");
const uploadStatus = document.getElementById("upload-status");

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
let lastDicomCollectionName = "";
let dicomIsLoading = false;
let dicomError = "";
let activeViewerSeries = null;
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

  if (String(series?.modality ?? "").trim().toUpperCase() === "NIFTI") {
    return "NIfTI";
  }

  const collectionMeta = collections.find(
    (collection) => collection.id === series.collection,
  );

  if (collectionMeta?.source) {
    return collectionMeta.source;
  }

  return "DICOM";
}

function normalizeViewerSeries(series) {
  if (series?.seriesUid) {
    return {
      ...series,
      source: getSeriesSource(series),
    };
  }

  return {
    seriesUid: series.instance_uid ?? series.seriesUid ?? "",
    studyUid: series.study_instance_uid ?? "",
    patientId: series.patient_id ?? "Unknown",
    modality: series.modality ?? "Unknown",
    bodyPart: series.body_part ?? "",
    protocolName: series.protocol_name ?? "",
    seriesDate: series.series_date ?? "",
    description: series.series_description ?? "",
    numImages: series.image_count ?? 0,
    collection: series.collection ?? "",
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
  activeImageObjects = [];

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

  showImageSlice(0);
}

async function loadViewerForSeries(series) {
  resetViewerState();
  setViewerLoading("Loading image series...");

  try {
    const viewerInfo = await fetchSeriesViewer(
      apiBaseUrl,
      series.seriesUid,
      series.collection,
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

  seriesBrowserSection.classList.toggle("hidden", !showingSeries);
  availableCollectionsSection.classList.toggle("hidden", !showingAvailable);
  dicomExplorerSection.classList.toggle("hidden", !showingDicom);

  seriesViewButton.classList.toggle("active", showingSeries);
  availableViewButton.classList.toggle("active", showingAvailable);
  dicomViewButton.classList.toggle("active", showingDicom);
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
          </tr>
        </thead>
        <tbody>
          ${results
            .map(
              (series) => `
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
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </section>
  `;
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
    const patient = await loadPatient(apiBaseUrl, activeViewerSeries.patientId);
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

if (uploadButton && uploadInput) {
  uploadButton.addEventListener("click", () => {
    uploadInput.click();
  });

  uploadInput.addEventListener("change", async () => {
    const file = uploadInput.files[0];

    if (!file) {
      return;
    }

    uploadStatus.textContent = `Selected: ${file.name}`;

    try {
      if (typeof uploadDataset === "function") {
        uploadStatus.textContent = `Uploading ${file.name}...`;

        await uploadDataset(apiBaseUrl, file);

        uploadStatus.textContent = "Upload complete. Refreshing data...";

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

        uploadStatus.textContent = "Dataset loaded.";
      } else {
        uploadStatus.textContent =
          "File selected. Upload endpoint not connected yet.";
      }
    } catch (error) {
      console.error("Upload failed", error);
      uploadStatus.textContent = `Upload failed: ${error.message}`;
    }
  });
}

initializeData().catch((error) => {
  console.error("Failed to load mock data", error);
  resultCount.textContent = "Failed to load data";
});
