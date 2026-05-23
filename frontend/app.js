const appShell = document.getElementById("app-shell");
const collectionsList = document.getElementById("collections-list");
const seriesTable = document.getElementById("series-table");
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

const seriesViewButton = document.getElementById("series-view-button");
const availableViewButton = document.getElementById("available-view-button");
const seriesBrowserSection = document.getElementById("series-browser-section");
const availableCollectionsSection = document.getElementById(
  "available-collections-section",
);
const availableSearchInput = document.getElementById("available-search-input");
const availableCollectionsList = document.getElementById(
  "available-collections-list",
);
const availableResultCount = document.getElementById("available-result-count");

const uploadInput = document.getElementById("dataset-upload-input");
const uploadButton = document.getElementById("dataset-upload-button");
const uploadStatus = document.getElementById("upload-status");

const collectionsCount = document.getElementById("collections-count");
const selectAllCollectionsButton = document.getElementById(
  "select-all-collections",
);
const clearCollectionsButton = document.getElementById("clear-collections");

let selectedCollections = new Set();

let availableCollectionsData = [];

function renderCollections() {
  collectionsList.innerHTML = "";

  collectionsCount.textContent = `${selectedCollections.size}/${collections.length}`;

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

      renderCollections();
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
      selectedModality === "all" || series.modality === selectedModality;

    const matchesSearch = Object.values(series).some((value) =>
      String(value).toLowerCase().includes(searchTerm),
    );

    return matchesCollection && matchesModality && matchesSearch;
  });
}

function renderSeries() {
  const filteredSeries = getFilteredSeries();

  seriesTable.innerHTML = "";
  resultCount.textContent = `${filteredSeries.length} results`;

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

  filteredSeries.forEach((series) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${series.seriesUid}</td>
      <td>${series.patientId}</td>
      <td><span class="modality-badge">${series.modality}</span></td>
      <td>${series.bodyPart}</td>
      <td>${series.description}</td>
      <td>${series.numImages}</td>
      <td>${series.collection}</td>
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

  seriesBrowserSection.classList.toggle("hidden", !showingSeries);
  availableCollectionsSection.classList.toggle("hidden", showingSeries);

  seriesViewButton.classList.toggle("active", showingSeries);
  availableViewButton.classList.toggle("active", !showingSeries);
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
  appShell.classList.add("viewer-mode");

  searchPage.classList.remove("active");
  viewerPage.classList.add("active");

  viewerTitle.textContent = `${series.modality} series`;
  viewerSubtitle.textContent = `${series.patientId} · ${series.bodyPart}`;
  viewerModality.textContent = series.modality;
  viewerImages.textContent = `${series.numImages} images`;

  imageSlider.max = series.numImages;
  imageSlider.value = Math.ceil(series.numImages / 2);

  metadataContent.innerHTML = `
    <div class="metadata-row">
      <span>Series UID</span>
      <span>${series.seriesUid}</span>
    </div>
    <div class="metadata-row">
      <span>Patient ID</span>
      <span>${series.patientId}</span>
    </div>
    <div class="metadata-row">
      <span>Modality</span>
      <span>${series.modality}</span>
    </div>
    <div class="metadata-row">
      <span>Body Part</span>
      <span>${series.bodyPart}</span>
    </div>
    <div class="metadata-row">
      <span>Description</span>
      <span>${series.description}</span>
    </div>
    <div class="metadata-row">
      <span>Number of Images</span>
      <span>${series.numImages}</span>
    </div>
    <div class="metadata-row">
      <span>Collection</span>
      <span>${series.collection}</span>
    </div>
  `;
}

function closeViewer() {
  appShell.classList.remove("viewer-mode");

  viewerPage.classList.remove("active");
  searchPage.classList.add("active");
}

searchInput.addEventListener("input", renderSeries);
modalityFilter.addEventListener("change", renderSeries);
backButton.addEventListener("click", closeViewer);

selectAllCollectionsButton.addEventListener("click", () => {
  selectedCollections = new Set(collections.map((collection) => collection.id));
  renderCollections();
  renderSeries();
});

clearCollectionsButton.addEventListener("click", () => {
  selectedCollections.clear();
  renderCollections();
  renderSeries();
});

const apiBaseUrl =
  new URLSearchParams(window.location.search).get("apiBaseUrl") ??
  window.location.origin;

async function initializeData() {
  collections = [];
  seriesData = [];

  try {
    const { collections: loadedCollections, seriesData: loadedSeries } =
      await loadMockData(apiBaseUrl);

    collections = loadedCollections;
    seriesData = loadedSeries;
  } catch (error) {
    console.warn(
      "Could not load downloaded collections/series from backend. Starting empty.",
      error,
    );
  }

  try {
    availableCollectionsData = await loadAvailableCollections(apiBaseUrl);
  } catch (error) {
    console.warn(
      "Could not load available collections from backend. Using fallback data.",
      error,
    );

    availableCollectionsData = [...fallbackAvailableCollections];
  }

  syncAvailableCollectionStatus();

  selectedCollections = new Set(collections.map((collection) => collection.id));

  renderCollections();
  renderSeries();
  renderAvailableCollections();
}

seriesViewButton.addEventListener("click", () => {
  setMainView("series");
});

availableViewButton.addEventListener("click", () => {
  setMainView("available");
  renderAvailableCollections();
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
