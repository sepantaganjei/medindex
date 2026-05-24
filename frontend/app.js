const appShell = document.getElementById("app-shell");
const collectionsList = document.getElementById("collections-list");
const seriesTable = document.getElementById("series-table");
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

const seriesPageSize = 100;

const modalityAliases = {
  "computed tomography": "CT",
  ct: "CT",
  "magnetic resonance": "MR",
  "magnetic resonance imaging": "MR",
  mr: "MR",
  mri: "MR",
  "positron emission tomography": "PET",
  pet: "PET",
  "digital radiography": "DX",
  radiography: "DX",
  dx: "DX",
  "computed radiography": "CR",
  cr: "CR",
  ultrasound: "US",
  us: "US",
  "single photon emission computed tomography": "SPECT",
  spect: "SPECT",
  segmentation: "SEG",
  seg: "SEG",
  "radiotherapy structure set": "RTSTRUCT",
  rtstruct: "RTSTRUCT",
  "secondary capture": "SC",
  sc: "SC",
};

function normalizeModality(value) {
  const rawValue = String(value ?? "").trim();

  if (!rawValue) {
    return "Unknown";
  }

  return modalityAliases[rawValue.toLowerCase()] ?? rawValue.toUpperCase();
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
      normalizeModality(series.modality) === selectedModality;

    const matchesSearch = Object.values(series).some((value) =>
      String(value).toLowerCase().includes(searchTerm),
    );

    return matchesCollection && matchesModality && matchesSearch;
  });
}

function resetSeriesPage() {
  seriesPage = 1;
}

function renderSeriesPagination(totalResults) {
  const totalPages = Math.max(1, Math.ceil(totalResults / seriesPageSize));

  if (isSeriesLoading || totalResults === 0 || totalPages === 1) {
    seriesPagination.innerHTML = "";
    return;
  }

  seriesPage = Math.min(seriesPage, totalPages);

  const startResult = (seriesPage - 1) * seriesPageSize + 1;
  const endResult = Math.min(seriesPage * seriesPageSize, totalResults);

  seriesPagination.innerHTML = `
    <div class="pagination-summary">
      Showing ${startResult}-${endResult} of ${totalResults}
    </div>
    <div class="pagination-actions">
      <button id="series-prev-page" type="button" ${
        seriesPage === 1 ? "disabled" : ""
      }>Previous</button>
      <span>Page ${seriesPage} of ${totalPages}</span>
      <button id="series-next-page" type="button" ${
        seriesPage === totalPages ? "disabled" : ""
      }>Next</button>
    </div>
  `;

  document.getElementById("series-prev-page").addEventListener("click", () => {
    seriesPage = Math.max(1, seriesPage - 1);
    renderSeries();
  });

  document.getElementById("series-next-page").addEventListener("click", () => {
    seriesPage = Math.min(totalPages, seriesPage + 1);
    renderSeries();
  });
}

function renderSeries() {
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
    new Set(visibleSeries.map((series) => normalizeModality(series.modality))),
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
    dicomResultsContainer.innerHTML = `
      <section class="table-card">
        <p class="empty-state">Searching remote DICOM metadata...</p>
      </section>
    `;
    return;
  }

  if (dicomError) {
    dicomResultsContainer.innerHTML = `
      <section class="table-card">
        <p class="empty-state">No results to show until the search succeeds.</p>
      </section>
    `;
    return;
  }

  if (dicomResults.length === 0) {
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

  if (activeDicomSearchType === "studies") {
    renderDicomStudiesTable(dicomResults);
    return;
  }

  if (activeDicomSearchType === "patients") {
    renderDicomPatientsTable(dicomResults);
    return;
  }

  renderDicomSeriesTable(dicomResults);
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
            <th>Series UID</th>
            <th>Patient</th>
            <th>Modality</th>
            <th>Body Part</th>
            <th>Description</th>
            <th>Images</th>
            <th>Collection</th>
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
            <th>Study UID</th>
            <th>Patient</th>
            <th>Date</th>
            <th>Description</th>
            <th>Series Count</th>
            <th>Collection</th>
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
            <th>Patient ID</th>
            <th>Sex</th>
            <th>Age</th>
            <th>Ethnic Group</th>
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
  renderDicomExplorer();

  try {
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
    availableCollectionsList.innerHTML = `
      <p class="empty-state">No available collections match the search.</p>
    `;
    return;
  }

  filteredCollections.forEach((collection) => {
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

  document
    .querySelectorAll(".download-button[data-collection-name]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        handleCollectionDownload(button.dataset.collectionName, button);
      });
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
    ["Series UID", series.seriesUid],
    ["Study UID", series.studyUid],
    ["Patient ID", series.patientId],
    ["Modality", normalizeModality(series.modality)],
    ["Body Part", series.bodyPart],
    ["Description", series.description],
    ["Protocol", series.protocolName],
    ["Series Date", series.seriesDate],
    ["Number of Images", series.numImages],
    ["Collection", series.collection],
    ["Manufacturer", series.manufacturer],
    ["Model", series.manufacturerModelName],
  ]);
}

function renderPatientMetadata(series, patient = null) {
  setMetadataTab("patient");
  renderMetadataRows([
    ["Patient ID", patient?.id ?? series.patientId],
    ["Sex", patient?.sex ?? series.patientSex],
    ["Age", getPatientAgeDisplayValue(patient?.age ?? series.patientAge)],
    ["Ethnic Group", patient?.ethnic_group ?? series.patientEthnicGroup],
    ["Collection", series.collection],
  ]);
}

function renderPatientMetadataLoading(series) {
  setMetadataTab("patient");
  renderMetadataRows([
    ["Patient ID", series.patientId],
    ["Sex", "Loading..."],
    ["Age", "Loading..."],
    ["Ethnic Group", "Loading..."],
    ["Collection", series.collection],
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
  activeViewerSeries = series;
  lastSearchScrollY = window.scrollY;
  updateBackToTopButton();
  appShell.classList.add("viewer-mode");

  searchPage.classList.remove("active");
  viewerPage.classList.add("active");

  viewerTitle.textContent = `${normalizeModality(series.modality)} series`;
  viewerSubtitle.textContent = `${series.patientId} · ${getDisplayValue(
    series.bodyPart,
  )}`;
  viewerModality.textContent = normalizeModality(series.modality);
  viewerImages.textContent = `${series.numImages} images`;

  imageSlider.max = series.numImages;
  imageSlider.value = Math.ceil(series.numImages / 2);

  renderSeriesMetadata(series);
}

function closeViewer() {
  activeViewerSeries = null;
  appShell.classList.remove("viewer-mode");

  viewerPage.classList.remove("active");
  searchPage.classList.add("active");

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

const apiBaseUrl =
  new URLSearchParams(window.location.search).get("apiBaseUrl") ??
  window.location.origin;

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
      renderAvailableCollections();
    });

  await Promise.allSettled([seriesLoad, availableLoad]);
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

availableSearchInput.addEventListener("input", renderAvailableCollections);

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
