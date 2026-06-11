const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const previewCanvas = document.getElementById("previewCanvas");
const previewCtx = previewCanvas.getContext("2d");

const dialog = document.getElementById("dialog");
const yesBtn = document.getElementById("yesBtn");
const noBtn = document.getElementById("noBtn");
const roiBtn = document.getElementById("roiBtn");
const roiMenu = document.getElementById("roiMenu");
const zoomInBtn = document.getElementById("zoomInBtn");
const zoomOutBtn = document.getElementById("zoomOutBtn");

const featureBtn = document.getElementById("featureBtn");
const featureMenu = document.getElementById("featureMenu");
const selectAllBtn = document.getElementById("selectAllBtn");
const clearAllBtn = document.getElementById("clearAllBtn");

const loadStatus = document.getElementById("loadStatus");
const featuresStatus = document.getElementById("featuresStatus");
const featuresList = document.getElementById("featuresList");

const img = new Image();
let objectUrl = null;
let currentRenderSource = null;
let currentApiBaseUrl = "";
let currentSeriesUid = "";
let currentImageNumber = "1";

/* =========================================
   ROI STATE
========================================= */

let roiMode = "polygon";
let roiActive = false; // true solo dopo che l'utente ha scelto una modalità ROI
let roiClosed = false;
let points = [];
let freehandPath = [];
let isDrawing = false;
let ellipseCenter = null;
let ellipsePreview = null;

/* =========================================
   FEATURE STATE
========================================= */

let selectedFeatures = new Set();

/* =========================================
   TRANSFORM STATE
========================================= */

let fitScale = 1;
let zoomLevel = 1;
let offsetX = 0;
let offsetY = 0;

/* =========================================
   ZOOM-RECT SELECTION STATE
   Drag sul canvas → rettangolo tratteggiato
   → al mouseup, zoom sulla porzione scelta.
========================================= */

let isSelecting = false;
let selRect = null; // { startX, startY, endX, endY } in pixel canvas

/* =========================================
   INIT & RESIZE
========================================= */

img.onload = () => {
  previewCanvas.width = 400;
  previewCanvas.height = 400;
  initCanvas();
  resetAllROI();
  loadStatus.textContent = `Loaded ${img.width}×${img.height}`;
};

img.onerror = () => {
  loadStatus.textContent = "Failed to load image";
};

function initCanvas() {
  if (!img.naturalWidth) {
    return;
  }
  const container = document.getElementById("canvasContainer");
  canvas.width = container.clientWidth;
  canvas.height = container.clientHeight;

  fitScale = Math.min(canvas.width / img.width, canvas.height / img.height);
  zoomLevel = 1;

  offsetX = (canvas.width - img.width * fitScale) / 2;
  offsetY = (canvas.height - img.height * fitScale) / 2;

  drawBase();
}

function resizeCanvas() {
  if (!img.complete || !img.naturalWidth) return;
  const container = document.getElementById("canvasContainer");
  const newW = container.clientWidth;
  const newH = container.clientHeight;
  if (!newW || !newH) return;

  canvas.width = newW;
  canvas.height = newH;

  fitScale = Math.min(newW / img.width, newH / img.height);

  const ts = fitScale * zoomLevel;
  offsetX = (newW - img.width * ts) / 2;
  offsetY = (newH - img.height * ts) / 2;

  redrawAll();
}

const ro = new ResizeObserver(() => resizeCanvas());
ro.observe(document.getElementById("canvasContainer"));

/* =========================================
   IMAGE LOADING
========================================= */

function getRenderSourceFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const imageUrl = params.get("image_url");
  const objectName = params.get("object_name");
  const source = params.get("source");
  const seriesUid = params.get("series_uid") || "";
  const imageNumber = params.get("image_number") || "1";

  if (!imageUrl || !objectName || !source) {
    return null;
  }

  const renderSource = {
    source,
    object_name: objectName,
  };

  if (source === "NIfTI") {
    renderSource.axis = params.get("axis") || "z";
    renderSource.slice = Number(params.get("slice") || 0);
  } else {
    renderSource.frame = Number(params.get("frame") || 0);
  }

  return { imageUrl, renderSource, seriesUid, imageNumber };
}

async function loadRenderedImage(
  imageUrl,
  renderSource,
  seriesUid = "",
  imageNumber = "1",
) {
  loadStatus.textContent = "Loading image…";
  featuresStatus.textContent = "No features computed yet.";
  featuresList.innerHTML = "";

  try {
    currentApiBaseUrl = new URL(imageUrl, window.location.href).origin;
    const response = await fetch(imageUrl);
    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    const blob = await response.blob();
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
    }

    objectUrl = URL.createObjectURL(blob);
    currentRenderSource = renderSource;
    currentSeriesUid = seriesUid;
    currentImageNumber = imageNumber;
    img.src = objectUrl;
  } catch (error) {
    loadStatus.textContent = "Failed to load image";
    console.error("Failed to load image", error);
  }
}

const initialImage = getRenderSourceFromUrl();
if (initialImage) {
  loadRenderedImage(
    initialImage.imageUrl,
    initialImage.renderSource,
    initialImage.seriesUid,
    initialImage.imageNumber,
  );
} else {
  loadStatus.textContent = "Open a viewer slice from the main page.";
}

/* =========================================
   FRECCE — pan con tastiera
   Sposta la vista di PAN_STEP pixel
   per ogni pressione di freccia.
========================================= */

const PAN_STEP = 40;

document.addEventListener("keydown", (e) => {
  const map = {
    ArrowLeft: [PAN_STEP, 0],
    ArrowRight: [-PAN_STEP, 0],
    ArrowUp: [0, PAN_STEP],
    ArrowDown: [0, -PAN_STEP],
  };
  if (!map[e.key]) return;
  e.preventDefault();
  const [dx, dy] = map[e.key];
  offsetX += dx;
  offsetY += dy;
  redrawAll();
});

/* =========================================
   ROTELLA — zoom centrato sul cursore
   Il punto esatto sotto il mouse rimane fisso.
========================================= */

canvas.addEventListener(
  "wheel",
  (e) => {
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    zoomAtPoint(cx, cy, e.deltaY < 0 ? 1.1 : 0.909);
  },
  { passive: false },
);

/* =========================================
   ZOOM HELPERS
========================================= */

function zoomAtPoint(cx, cy, factor) {
  const newZoom = zoomLevel * factor;
  if (newZoom < 0.05 || newZoom > 100) return;

  const ts = fitScale * zoomLevel;
  const imgX = (cx - offsetX) / ts;
  const imgY = (cy - offsetY) / ts;

  zoomLevel = newZoom;

  const newTs = fitScale * zoomLevel;
  offsetX = cx - imgX * newTs;
  offsetY = cy - imgY * newTs;

  redrawAll();
}

function zoomAtCenter(factor) {
  zoomAtPoint(canvas.width / 2, canvas.height / 2, factor);
}

zoomInBtn.addEventListener("click", () => zoomAtCenter(1.2));
zoomOutBtn.addEventListener("click", () => zoomAtCenter(0.833));

/* =========================================
   ZOOM-TO-RECT
   Dato un selRect in coordinate canvas,
   ricalcola zoomLevel + offset per riempire
   il canvas con quella porzione.
========================================= */

function zoomToRect(r) {
  const x1 = Math.min(r.startX, r.endX);
  const y1 = Math.min(r.startY, r.endY);
  const rw = Math.abs(r.endX - r.startX);
  const rh = Math.abs(r.endY - r.startY);
  if (rw < 10 || rh < 10) return;

  const ts = fitScale * zoomLevel;
  const imgX1 = (x1 - offsetX) / ts;
  const imgY1 = (y1 - offsetY) / ts;
  const imgW = rw / ts;
  const imgH = rh / ts;

  const newTs = Math.min(canvas.width / imgW, canvas.height / imgH);
  zoomLevel = newTs / fitScale;

  offsetX = canvas.width / 2 - (imgX1 + imgW / 2) * newTs;
  offsetY = canvas.height / 2 - (imgY1 + imgH / 2) * newTs;

  redrawAll();
}

/* =========================================
   DISEGNO RETTANGOLO SELEZIONE (tratteggiato)
========================================= */

function drawSelectionRect() {
  if (!selRect) return;
  const x = Math.min(selRect.startX, selRect.endX);
  const y = Math.min(selRect.startY, selRect.endY);
  const w = Math.abs(selRect.endX - selRect.startX);
  const h = Math.abs(selRect.endY - selRect.startY);
  if (w < 2 || h < 2) return;

  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);

  ctx.fillStyle = "rgba(0, 140, 255, 0.08)";
  ctx.fillRect(x, y, w, h);

  ctx.strokeStyle = "rgba(255,255,255,0.7)";
  ctx.lineWidth = 2.5;
  ctx.setLineDash([]);
  ctx.strokeRect(x - 1, y - 1, w + 2, h + 2);

  ctx.strokeStyle = "rgba(0, 140, 255, 0.95)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([7, 4]);
  ctx.strokeRect(x, y, w, h);

  // Maniglie agli angoli
  const sz = 9;
  ctx.setLineDash([]);
  ctx.strokeStyle = "#0080ff";
  ctx.lineWidth = 2.5;
  [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]].forEach(
    ([cx2, cy2, sx, sy]) => {
      ctx.beginPath();
      ctx.moveTo(cx2 + sx * sz, cy2);
      ctx.lineTo(cx2, cy2);
      ctx.lineTo(cx2, cy2 + sy * sz);
      ctx.stroke();
    },
  );

  ctx.restore();
}

/* =========================================
   COORDINATE HELPER
========================================= */

function getImageCoords(e) {
  const rect = canvas.getBoundingClientRect();
  const ts = fitScale * zoomLevel;
  return {
    x: (e.clientX - rect.left - offsetX) / ts,
    y: (e.clientY - rect.top - offsetY) / ts,
  };
}

function getCanvasXY(e) {
  const rect = canvas.getBoundingClientRect();
  return { cx: e.clientX - rect.left, cy: e.clientY - rect.top };
}

/* =========================================
   DRAW BASE
========================================= */

function drawBase() {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!img.complete || !img.naturalWidth) {
    return;
  }
  const ts = fitScale * zoomLevel;
  ctx.setTransform(ts, 0, 0, ts, offsetX, offsetY);
  ctx.drawImage(img, 0, 0);
}

function redrawAll() {
  drawBase();
  if (roiMode === "polygon" && points.length > 0) {
    roiClosed ? drawPolygonClosed() : drawPolygonPreview();
  } else if (roiMode === "freehand" && freehandPath.length > 1) {
    drawFreehand();
  } else if (roiMode === "ellipse" && ellipseCenter) {
    if (ellipsePreview) drawEllipsePreview();
    else drawDot(ellipseCenter.x, ellipseCenter.y);
  }
}

/* =========================================
   RESET
========================================= */

function resetAllROI() {
  roiClosed = false;
  points = [];
  freehandPath = [];
  isDrawing = false;
  ellipseCenter = null;
  ellipsePreview = null;
  isSelecting = false;
  selRect = null;

  if (img.naturalWidth) {
    zoomLevel = 1;
    offsetX = (canvas.width - img.width * fitScale) / 2;
    offsetY = (canvas.height - img.height * fitScale) / 2;
  }
  roiActive = false;
  roiBtn.innerText = "ROI Decision ▾";

  drawBase();
  previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);
  dialog.style.display = "none";
  canvas.style.cursor = "crosshair";
}

/* =========================================
   PREVIEW
========================================= */

function drawPreviewScaled(sourceCanvas) {
  previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);
  const scale = Math.min(
    previewCanvas.width / sourceCanvas.width,
    previewCanvas.height / sourceCanvas.height,
  );
  const dw = sourceCanvas.width * scale;
  const dh = sourceCanvas.height * scale;
  previewCtx.drawImage(
    sourceCanvas,
    (previewCanvas.width - dw) / 2,
    (previewCanvas.height - dh) / 2,
    dw,
    dh,
  );
}

/* =========================================
   ROI MENU
========================================= */

roiBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  roiMenu.classList.toggle("hidden");
  featureMenu.classList.add("hidden");
});

document.querySelectorAll(".roi-option").forEach((opt) => {
  opt.addEventListener("click", () => {
    roiMode = opt.dataset.type;
    roiBtn.innerText = "ROI: " + opt.innerText.trim() + " ▾";
    roiMenu.classList.add("hidden");
    resetAllROI(); // resetta tutto (roiActive → false)
    roiActive = true; // riattiva il disegno DOPO il reset
  });
});

/* =========================================
   FEATURE MENU
========================================= */

featureBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  featureMenu.classList.toggle("hidden");
  roiMenu.classList.add("hidden");
});

featureMenu.querySelectorAll("input[type=checkbox]").forEach((cb) => {
  cb.addEventListener("change", () => {
    cb.checked ? selectedFeatures.add(cb.value) : selectedFeatures.delete(cb.value);
    updateFeatureBtn();
  });
});

selectAllBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  featureMenu.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.checked = true;
    selectedFeatures.add(cb.value);
  });
  updateFeatureBtn();
});

clearAllBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  featureMenu.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.checked = false;
  });
  selectedFeatures.clear();
  updateFeatureBtn();
});

function updateFeatureBtn() {
  const n = selectedFeatures.size;
  featureBtn.innerText = n === 0 ? "Feature Extraction ▾" : `Feature Extraction (${n}) ▾`;
}

function selectDefaultFeatures() {
  selectedFeatures.clear();
  featureMenu.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.checked = true;
    selectedFeatures.add(cb.value);
  });
  updateFeatureBtn();
}

selectDefaultFeatures();

/* =========================================
   CHIUDI MENU SU CLICK ESTERNO
========================================= */

document.addEventListener("click", () => {
  roiMenu.classList.add("hidden");
  featureMenu.classList.add("hidden");
});
roiMenu.addEventListener("click", (e) => e.stopPropagation());
featureMenu.addEventListener("click", (e) => e.stopPropagation());

/* =========================================
   MOUSE EVENTS

   MOUSEDOWN:
   • freehand → inizia disegno ROI
   • polygon / ellipse → inizia rettangolo selezione zoom

   MOUSEMOVE:
   • aggiorna freehand OPPURE rettangolo selezione
   • aggiorna anteprima polygon / ellipse

   MOUSEUP:
   • freehand → chiudi ROI
   • selezione → zoom-to-rect se > 20×20 px, altrimenti click normale

   CLICK:
   • polygon → aggiungi punto
   • ellipse → imposta centro / conferma
========================================= */

// Tiene traccia se il mouseup ha già gestito un drag
let wasDrag = false;

canvas.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  if (roiClosed) return;

  wasDrag = false;
  const { cx, cy } = getCanvasXY(e);

  if (roiMode === "freehand" && roiActive) {
    const { x, y } = getImageCoords(e);
    freehandPath = [{ x, y }];
    isDrawing = true;
    return;
  }

  // Rettangolo zoom-to-rect solo in modalità navigazione (nessuna ROI attiva)
  if (!roiActive) {
    isSelecting = true;
    selRect = { startX: cx, startY: cy, endX: cx, endY: cy };
  }
});

canvas.addEventListener("mousemove", (e) => {
  // Freehand drawing
  if (isDrawing && roiMode === "freehand") {
    const { x, y } = getImageCoords(e);
    freehandPath.push({ x, y });
    drawFreehand();
    return;
  }

  // Aggiorna rettangolo selezione
  if (isSelecting && selRect) {
    const { cx, cy } = getCanvasXY(e);
    selRect.endX = cx;
    selRect.endY = cy;
    const w = Math.abs(selRect.endX - selRect.startX);
    const h = Math.abs(selRect.endY - selRect.startY);
    if (w > 4 || h > 4) {
      wasDrag = true;
      redrawAll();
      drawSelectionRect();
    }
    return;
  }

  // Preview live per polygon / ellipse
  if (roiClosed) return;
  const { x, y } = getImageCoords(e);
  if (roiMode === "polygon") drawPolygonPreview(x, y);
  if (roiMode === "ellipse" && ellipseCenter) {
    ellipsePreview = { x, y };
    drawEllipsePreview();
  }
});

canvas.addEventListener("mouseup", (e) => {
  if (e.button !== 0) return;

  // Fine freehand
  if (isDrawing && roiMode === "freehand") {
    isDrawing = false;
    if (freehandPath.length > 1) {
      roiClosed = true;
      createFreehandROI();
      dialog.style.display = "block";
    }
    return;
  }

  // Fine selezione rettangolo
  if (isSelecting && selRect) {
    isSelecting = false;
    const w = Math.abs(selRect.endX - selRect.startX);
    const h = Math.abs(selRect.endY - selRect.startY);

    if (wasDrag && w > 20 && h > 20) {
      // Era un drag abbastanza grande → zoom alla zona
      zoomToRect(selRect);
      selRect = null;
      redrawAll();
    } else {
      // Era un click → lascia che l'evento "click" gestisca polygon/ellipse
      selRect = null;
      redrawAll();
    }
  }
});

canvas.addEventListener("mouseleave", () => {
  if (isSelecting && selRect && wasDrag) {
    const w = Math.abs(selRect.endX - selRect.startX);
    const h = Math.abs(selRect.endY - selRect.startY);
    if (w > 20 && h > 20) zoomToRect(selRect);
  }
  isSelecting = false;
  selRect = null;
  redrawAll();
});

/* =========================================
   CLICK — polygon & ellipse
   Si attiva solo se NON era un drag (wasDrag = false)
========================================= */

canvas.addEventListener("click", (e) => {
  if (!roiActive) return;
  if (roiClosed) return;
  if (wasDrag) {
    wasDrag = false;
    return;
  } // era uno zoom-to-rect, ignora

  const { x, y } = getImageCoords(e);

  if (roiMode === "polygon") {
    points.push({ x, y });
    drawPolygonPreview();
  }

  if (roiMode === "ellipse") {
    if (!ellipseCenter) {
      ellipseCenter = { x, y };
      return;
    }
    if (ellipsePreview) {
      roiClosed = true;
      createEllipseROI();
      dialog.style.display = "block";
    }
  }
});

canvas.addEventListener("contextmenu", (e) => {
  e.preventDefault();
  if (!roiActive || roiMode !== "polygon" || points.length < 3) return;
  roiClosed = true;
  drawPolygonClosed();
  createPolygonROI();
  dialog.style.display = "block";
});

/* =========================================
   STROKE / DOT HELPERS
========================================= */

function setStroke() {
  const ts = fitScale * zoomLevel;
  ctx.strokeStyle = "red";
  ctx.lineWidth = 2 / ts;
}

function drawDot(px, py) {
  const ts = fitScale * zoomLevel;
  ctx.beginPath();
  ctx.arc(px, py, 4 / ts, 0, Math.PI * 2);
  ctx.fillStyle = "red";
  ctx.fill();
}

/* =========================================
   POLYGON
========================================= */

function drawPolygonPreview(mouseX = null, mouseY = null) {
  drawBase();
  if (!points.length) return;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
  if (mouseX !== null) ctx.lineTo(mouseX, mouseY);
  setStroke();
  ctx.stroke();
  points.forEach((p) => drawDot(p.x, p.y));
}

function drawPolygonClosed() {
  drawBase();
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
  ctx.closePath();
  setStroke();
  ctx.stroke();
  points.forEach((p) => drawDot(p.x, p.y));
}

/* =========================================
   FREEHAND
========================================= */

function drawFreehand() {
  drawBase();
  if (freehandPath.length < 2) return;
  ctx.beginPath();
  ctx.moveTo(freehandPath[0].x, freehandPath[0].y);
  for (let i = 1; i < freehandPath.length; i++) ctx.lineTo(freehandPath[i].x, freehandPath[i].y);
  setStroke();
  ctx.stroke();
}

/* =========================================
   ELLIPSE
========================================= */

function drawEllipsePreview() {
  drawBase();
  if (!ellipseCenter || !ellipsePreview) return;
  const rx = Math.abs(ellipsePreview.x - ellipseCenter.x);
  const ry = Math.abs(ellipsePreview.y - ellipseCenter.y);
  ctx.beginPath();
  ctx.ellipse(ellipseCenter.x, ellipseCenter.y, rx, ry, 0, 0, Math.PI * 2);
  setStroke();
  ctx.stroke();
  drawDot(ellipseCenter.x, ellipseCenter.y);
}

/* =========================================
   CREATE ROI
========================================= */

function createPolygonROI() {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const p of points) {
    minX = Math.min(minX, p.x);
    minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x);
    maxY = Math.max(maxY, p.y);
  }
  const tc = document.createElement("canvas");
  tc.width = maxX - minX;
  tc.height = maxY - minY;
  const tx = tc.getContext("2d");
  tx.save();
  tx.beginPath();
  tx.moveTo(points[0].x - minX, points[0].y - minY);
  for (let i = 1; i < points.length; i++) tx.lineTo(points[i].x - minX, points[i].y - minY);
  tx.closePath();
  tx.clip();
  tx.drawImage(img, -minX, -minY);
  tx.restore();
  drawPreviewScaled(tc);
}

function createFreehandROI() {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const p of freehandPath) {
    minX = Math.min(minX, p.x);
    minY = Math.min(minY, p.y);
    maxX = Math.max(maxX, p.x);
    maxY = Math.max(maxY, p.y);
  }
  const tc = document.createElement("canvas");
  tc.width = maxX - minX;
  tc.height = maxY - minY;
  const tx = tc.getContext("2d");
  tx.save();
  tx.beginPath();
  tx.moveTo(freehandPath[0].x - minX, freehandPath[0].y - minY);
  for (let i = 1; i < freehandPath.length; i++)
    tx.lineTo(freehandPath[i].x - minX, freehandPath[i].y - minY);
  tx.closePath();
  tx.clip();
  tx.drawImage(img, -minX, -minY);
  tx.restore();
  drawPreviewScaled(tc);
}

function createEllipseROI() {
  const rx = Math.abs(ellipsePreview.x - ellipseCenter.x);
  const ry = Math.abs(ellipsePreview.y - ellipseCenter.y);
  const tc = document.createElement("canvas");
  tc.width = rx * 2;
  tc.height = ry * 2;
  const tx = tc.getContext("2d");
  tx.save();
  tx.beginPath();
  tx.ellipse(rx, ry, rx, ry, 0, 0, Math.PI * 2);
  tx.clip();
  tx.drawImage(img, -(ellipseCenter.x - rx), -(ellipseCenter.y - ry));
  tx.restore();
  drawPreviewScaled(tc);
}

/* =========================================
   ROI POINTS EXPORT
   Restituisce i punti della ROI confermata
   nel sistema di coordinate dell'immagine.
========================================= */

function getEllipsePoints(cx, cy, rx, ry) {
  // Approssimazione della circonferenza (Ramanujan)
  const perimeter =
    Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)));

  // ~1 punto ogni pixel
  const steps = Math.max(60, Math.ceil(perimeter));

  const pts = [];

  for (let i = 0; i < steps; i++) {
    const theta = (i / steps) * Math.PI * 2;

    pts.push({
      x: Math.round(cx + rx * Math.cos(theta)),
      y: Math.round(cy + ry * Math.sin(theta)),
    });
  }

  return pts;
}

function getROIPoints() {
  if (roiMode === "polygon") {
    return points.map((p) => ({ x: Math.round(p.x), y: Math.round(p.y) }));
  }

  if (roiMode === "freehand") {
    return freehandPath.map((p) => ({ x: Math.round(p.x), y: Math.round(p.y) }));
  }

  if (roiMode === "ellipse") {
    const rx = Math.abs(ellipsePreview.x - ellipseCenter.x);
    const ry = Math.abs(ellipsePreview.y - ellipseCenter.y);

    return getEllipsePoints(ellipseCenter.x, ellipseCenter.y, rx, ry);
  }

  return null;
}

function renderFeatures(features) {
  const entries = Object.entries(features ?? {});
  if (entries.length === 0) {
    featuresStatus.textContent = "No features returned.";
    featuresList.innerHTML = "";
    return;
  }
  featuresStatus.textContent = `Features (${entries.length})`;
  featuresList.innerHTML = entries
    .map(([key, value]) => {
      const formatted = typeof value === "number" ? value.toFixed(6) : "n/a";
      return `<div class="feature-item"><span>${key}</span><span>${formatted}</span></div>`;
    })
    .join("");
}

function buildStoredFeaturePayload(features) {
  return Object.entries(features ?? {})
    .map(([featureName, value]) => ({
      feature_name: featureName,
      value: Number(value),
    }))
    .filter((feature) => Number.isFinite(feature.value));
}

async function saveExtraction(roi, features) {
  if (!currentSeriesUid) {
    throw new Error("Missing series UID for saved extraction.");
  }

  const storedFeatures = buildStoredFeaturePayload(features);
  if (storedFeatures.length === 0) {
    throw new Error("No numeric features were returned for saving.");
  }

  const response = await fetch(`${currentApiBaseUrl}/api/addExtraction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_number: String(currentImageNumber),
      series_instance_uid: currentSeriesUid,
      features_extracted: storedFeatures,
      roi_coordinates: roi,
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Save failed (${response.status})`);
  }

  const payload = await response.json();
  if (payload.status_operation !== "success") {
    throw new Error(payload.error || "Save failed.");
  }

  return storedFeatures.length;
}

/* =========================================
   DIALOG
========================================= */

yesBtn.onclick = async () => {
  dialog.style.display = "none";

  if (!currentRenderSource) {
    featuresStatus.textContent = "Load an image before extracting features.";
    return;
  }

  const roi = getROIPoints();
  if (!roi || roi.length < 3) {
    featuresStatus.textContent = "Define a valid ROI before extracting features.";
    return;
  }

  const selectedFeatureList = Array.from(selectedFeatures);
  if (selectedFeatureList.length === 0) {
    featuresStatus.textContent = "Select at least one feature before extracting.";
    return;
  }

  featuresStatus.textContent = "Computing features…";
  featuresList.innerHTML = "";

  try {
    const response = await fetch(`${currentApiBaseUrl}/api/radiomics/extract`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        render_source: currentRenderSource,
        points: roi,
        selected_features: selectedFeatureList,
      }),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed (${response.status})`);
    }

    const payload = await response.json();
    renderFeatures(payload.features);

    try {
      const savedCount = await saveExtraction(roi, payload.features);
      featuresStatus.textContent = `Features (${savedCount}) saved`;
    } catch (saveError) {
      featuresStatus.textContent = "Features computed, but saving failed.";
      console.error("Feature save failed", saveError);
    }
  } catch (error) {
    featuresStatus.textContent = "Failed to extract features.";
    console.error("Feature extraction failed", error);
  }
};

noBtn.onclick = () => resetAllROI();
