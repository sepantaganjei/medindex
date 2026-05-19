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
const viewerSlices = document.getElementById("viewer-slices");
const sliceSlider = document.getElementById("slice-slider");
const metadataContent = document.getElementById("metadata-content");

const collectionsCount = document.getElementById("collections-count");
const selectAllCollectionsButton = document.getElementById(
  "select-all-collections",
);
const clearCollectionsButton = document.getElementById("clear-collections");

let selectedCollections = new Set(
  collections.map((collection) => collection.id),
);

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

  filteredSeries.forEach((series) => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${series.seriesUid}</td>
      <td>${series.patientId}</td>
      <td><span class="modality-badge">${series.modality}</span></td>
      <td>${series.bodyPart}</td>
      <td>${series.description}</td>
      <td>${series.numSlices}</td>
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

function openViewer(series) {
  appShell.classList.add("viewer-mode");

  searchPage.classList.remove("active");
  viewerPage.classList.add("active");

  viewerTitle.textContent = `${series.modality} series`;
  viewerSubtitle.textContent = `${series.patientId} · ${series.bodyPart}`;
  viewerModality.textContent = series.modality;
  viewerSlices.textContent = `${series.numSlices} slices`;

  sliceSlider.max = series.numSlices;
  sliceSlider.value = Math.ceil(series.numSlices / 2);

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
      <span>Number of Slices</span>
      <span>${series.numSlices}</span>
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

renderCollections();
renderSeries();
