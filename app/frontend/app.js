const collectionsList = document.getElementById("collections-list");
const seriesTable = document.getElementById("series-table");
const metadataContent = document.getElementById("metadata-content");
const searchInput = document.getElementById("search-input");

let selectedCollection = null;

function renderCollections() {
  collectionsList.innerHTML = "";

  collections.forEach(collection => {
    const card = document.createElement("div");
    card.className = "collection-card";
    card.innerHTML = `
      <strong>${collection.name}</strong>
      <p>${collection.source} · ${collection.seriesCount} series</p>
    `;

    card.addEventListener("click", () => {
      selectedCollection = collection.id;
      renderSeries();
    });

    collectionsList.appendChild(card);
  });
}

function renderSeries() {
  const searchTerm = searchInput.value.toLowerCase();

  let filteredSeries = seriesData;

  if (selectedCollection) {
    filteredSeries = filteredSeries.filter(
      item => item.collection === selectedCollection
    );
  }

  if (searchTerm) {
    filteredSeries = filteredSeries.filter(item =>
      Object.values(item).some(value =>
        String(value).toLowerCase().includes(searchTerm)
      )
    );
  }

  seriesTable.innerHTML = "";

  filteredSeries.forEach(series => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${series.seriesUid}</td>
      <td>${series.patientId}</td>
      <td>${series.modality}</td>
      <td>${series.bodyPart}</td>
      <td>${series.description}</td>
      <td>${series.numSlices}</td>
      <td>${series.collection}</td>
    `;

    row.addEventListener("click", () => {
      showMetadata(series);
    });

    seriesTable.appendChild(row);
  });
}

function showMetadata(series) {
  metadataContent.innerHTML = `
    <p><strong>Series UID:</strong> ${series.seriesUid}</p>
    <p><strong>Patient ID:</strong> ${series.patientId}</p>
    <p><strong>Modality:</strong> ${series.modality}</p>
    <p><strong>Body Part:</strong> ${series.bodyPart}</p>
    <p><strong>Description:</strong> ${series.description}</p>
    <p><strong>Number of slices:</strong> ${series.numSlices}</p>
    <p><strong>Source collection:</strong> ${series.collection}</p>
  `;
}

searchInput.addEventListener("input", renderSeries);

renderCollections();
renderSeries();