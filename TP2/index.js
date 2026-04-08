/* ─────────────────────────────────────────────
   Constants
───────────────────────────────────────────── */
const API = "http://127.0.0.1:5000";
const DESC_COLORS = {
  Color: "var(--c-color)",
  LBP: "var(--c-lbp)",
  GLCM: "var(--c-glcm)",
  HOG: "var(--c-hog)",
};
const METHOD_COLORS = {
  combinee: "#1D9E75",
  euclidienne: "#3B82F6",
  chi2: "#7C3AED",
  cosinus: "#D97706",
};

/* ─────────────────────────────────────────────
   State
───────────────────────────────────────────── */
let currentResults = []; // results from last search
let lastQueryFile = null; // the File object for re-running analysis
let selectedCard = null;
let analysisData = null; // { method: results[] }

/* ─────────────────────────────────────────────
   Init
───────────────────────────────────────────── */
window.addEventListener("DOMContentLoaded", () => {
  checkServer();
  renderCode();
});

/* ─────────────────────────────────────────────
   Server health check + stats
───────────────────────────────────────────── */
async function checkServer() {
  try {
    const r = await fetch(`${API}/api/stats`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!r.ok) throw new Error("Server offline");
    const d = await r.json();
    document.getElementById("statusDot").classList.remove("offline");
    document.getElementById("statusText").textContent = "Server running";
    document.getElementById("metaDb").textContent = d.db_size.toLocaleString();
    document.getElementById("metaDims").textContent = d.dims || "—";
  } catch {
    document.getElementById("statusDot").classList.add("offline");
    document.getElementById("statusText").textContent = "Server offline";
  }
}

/* ─────────────────────────────────────────────
   Upload
───────────────────────────────────────────── */
function onFileSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  lastQueryFile = file;
  const url = URL.createObjectURL(file);
  const thumb = document.getElementById("uploadThumb");
  thumb.src = url;
  thumb.style.display = "block";
  document.getElementById("uploadText").style.display = "none";
}

/* ─────────────────────────────────────────────
   Loading bar
───────────────────────────────────────────── */
function startBar() {
  const b = document.getElementById("loadingBar");
  b.style.transition = "none";
  b.style.width = "0";
  setTimeout(() => {
    b.style.transition = "width 0.8s ease";
    b.style.width = "75%";
  }, 50);
}
function endBar() {
  const b = document.getElementById("loadingBar");
  b.style.width = "100%";
  setTimeout(() => {
    b.style.width = "0";
  }, 300);
}

/* ─────────────────────────────────────────────
   Toast
───────────────────────────────────────────── */
function showToast(msg, isError = false) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast show" + (isError ? " error" : "");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => (t.className = "toast"), 3500);
}

/* ─────────────────────────────────────────────
   Search
───────────────────────────────────────────── */
async function doSearch() {
  if (!lastQueryFile) {
    document.getElementById("uploadZone").style.borderColor = "var(--c-hog)";
    setTimeout(
      () =>
        (document.getElementById("uploadZone").style.borderColor =
          "var(--accent)"),
      1200,
    );
    showToast("Please select a query image first.", true);
    return;
  }

  const btn = document.getElementById("searchBtn");
  btn.disabled = true;
  btn.textContent = "Searching…";
  startBar();

  const method = document.getElementById("distanceMethod").value;
  const k = document.getElementById("kSlider").value;
  const wColor = document.getElementById("wColor").value;
  const wLbp = document.getElementById("wLbp").value;
  const wGlcm = document.getElementById("wGlcm").value;
  const wHog = document.getElementById("wHog").value;

  const form = new FormData();
  form.append("image", lastQueryFile);
  form.append("method", method);
  form.append("k", k);
  form.append("w_color", wColor / 100);
  form.append("w_lbp", wLbp / 100);
  form.append("w_glcm", wGlcm / 100);
  form.append("w_hog", wHog / 100);

  try {
    const res = await fetch(`${API}/api/search`, {
      method: "POST",
      body: form,
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Search failed.", true);
      return;
    }

    currentResults = data.results;

    // Update metric cards
    document.getElementById("metaDb").textContent =
      data.db_size.toLocaleString();
    document.getElementById("metaDims").textContent = data.dims;
    document.getElementById("metaTime").textContent = data.elapsed;
    document.getElementById("metaBest").textContent = data.best_score ?? "—";

    renderResults(currentResults);
    closeDetail();
    await runAnalysis(); // fetch analysis for all 4 methods in background
  } catch (err) {
    showToast("Cannot reach server. Is app.py running?", true);
    console.error(err);
  } finally {
    endBar();
    btn.disabled = false;
    btn.textContent = "Rechercher ↗";
  }
}

/* ─────────────────────────────────────────────
   Render results
───────────────────────────────────────────── */
const PALETTE = [
  "#E05252",
  "#7C3AED",
  "#1D9E75",
  "#D97706",
  "#3B82F6",
  "#EC4899",
  "#0EA5E9",
  "#84CC16",
  "#F97316",
  "#8B5CF6",
  "#14B8A6",
  "#F43F5E",
];

function renderResults(results) {
  const grid = document.getElementById("resultsGrid");
  if (!results.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="icon">🔍</div><div>No results found in the database.</div></div>`;
    return;
  }
  const maxDist = Math.max(...results.map((r) => r.distance), 0.01);
  grid.innerHTML = results
    .map((r, i) => {
      const barW = Math.max(4, 100 - (r.distance / (maxDist * 1.2)) * 100);
      const thumb = r.thumbnail
        ? `<img class="card-thumb" src="${r.thumbnail}" alt="${r.name}" />`
        : `<div class="card-thumb-placeholder" style="background:${PALETTE[i % PALETTE.length]};">${r.name}</div>`;
      return `
    <div class="img-card" id="card-${i}" onclick="selectCard(${i})">
      <div class="rank-badge">#${r.rank}</div>
      ${thumb}
      <div class="card-body">
        <div class="card-name">${r.name}</div>
        <div class="card-dist">d = ${r.distance.toFixed(4)}</div>
        <div class="dist-bar-bg"><div class="dist-bar-fill" style="width:${barW}%;"></div></div>
        <span class="cat-tag">${r.category}</span>
      </div>
    </div>`;
    })
    .join("");
}

/* ─────────────────────────────────────────────
   Detail panel
───────────────────────────────────────────── */
function selectCard(i) {
  if (selectedCard !== null)
    document
      .getElementById(`card-${selectedCard}`)
      ?.classList.remove("selected");
  selectedCard = i;
  document.getElementById(`card-${i}`)?.classList.add("selected");

  const r = currentResults[i];
  document.getElementById("detailTitle").textContent =
    `${r.name} — rank #${r.rank}`;

  const bars = document.getElementById("descBars");
  bars.innerHTML = Object.entries(r.desc_sims)
    .map(([key, val]) => {
      const pct = Math.round(val * 100);
      return `
    <div class="desc-bar-row">
      <div class="desc-bar-label">${key}</div>
      <div class="desc-bar-track">
        <div class="desc-bar-fill" style="width:${pct}%; background:${DESC_COLORS[key]};"></div>
      </div>
      <div class="desc-bar-pct">${pct}%</div>
    </div>`;
    })
    .join("");

  const panel = document.getElementById("detailPanel");
  panel.classList.add("open");
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function closeDetail() {
  document.getElementById("detailPanel").classList.remove("open");
  if (selectedCard !== null) {
    document
      .getElementById(`card-${selectedCard}`)
      ?.classList.remove("selected");
    selectedCard = null;
  }
}

/* ─────────────────────────────────────────────
   Sort
───────────────────────────────────────────── */
function sortResults(by, btn) {
  document
    .querySelectorAll(".sort-btn")
    .forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  if (!currentResults.length) return;
  const sorted = [...currentResults].sort((a, b) =>
    by === "dist" ? a.distance - b.distance : a.name.localeCompare(b.name),
  );
  renderResults(sorted);
  closeDetail();
}

/* ─────────────────────────────────────────────
   Analysis — fetch all 4 methods
───────────────────────────────────────────── */
async function runAnalysis() {
  if (!lastQueryFile) return;
  const k = 3;
  const methods = ["combinee", "euclidienne", "chi2", "cosinus"];
  const results = {};

  await Promise.all(
    methods.map(async (m) => {
      const form = new FormData();
      form.append("image", lastQueryFile);
      form.append("method", m);
      form.append("k", k);
      try {
        const res = await fetch(`${API}/api/search`, {
          method: "POST",
          body: form,
        });
        if (!res.ok) throw new Error("Search failed");
        const data = await res.json();
        results[m] = data.results || [];
      } catch {
        results[m] = [];
      }
    }),
  );

  analysisData = results;
  renderAnalysis();
}

function renderAnalysis() {
  const grid = document.getElementById("analysisGrid");
  if (!analysisData) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="icon">📊</div><div>Run a search first to see the comparison</div></div>`;
    return;
  }
  const labels = {
    combinee: "Combinée",
    euclidienne: "Euclidienne",
    chi2: "Chi-carré",
    cosinus: "Cosinus",
  };
  grid.innerHTML = Object.entries(analysisData)
    .map(([m, results]) => {
      const color = METHOD_COLORS[m];
      const maxD = Math.max(...results.map((r) => r.distance), 0.01);
      const rows = results
        .map((r, i) => {
          const w = Math.round((r.distance / (maxD * 1.1)) * 100);
          return `
      <div class="ana-row">
        <div class="ana-rank">#${i + 1}</div>
        <div class="ana-bar-bg"><div class="ana-bar-fill" style="width:${w}%; background:${color};"></div></div>
        <div class="ana-val" title="${r.name}">${r.distance.toFixed(4)}</div>
      </div>`;
        })
        .join("");
      return `
    <div class="analysis-card">
      <h4>${labels[m]} — <span>top ${results.length} results</span></h4>
      ${rows || '<div style="color:var(--text-muted);font-size:11px;">No results</div>'}
    </div>`;
    })
    .join("");
}

/* ─────────────────────────────────────────────
   Re-index
───────────────────────────────────────────── */
async function doReindex() {
  showToast("Re-indexing database…");
  try {
    const res = await fetch(`${API}/api/index`, { method: "POST" });
    if (!res.ok) throw new Error("Re-index failed");
    const data = await res.json();
    showToast(`✓ Indexed ${data.indexed} images.`);
    checkServer();
  } catch {
    showToast("Re-index failed. Is app.py running?", true);
  }
}

/* ─────────────────────────────────────────────
   Tabs
───────────────────────────────────────────── */
function switchTab(name, btn) {
  document
    .querySelectorAll(".tab")
    .forEach((t) => t.classList.remove("active"));
  btn.classList.add("active");
  document
    .querySelectorAll(".tab-panel")
    .forEach((p) => p.classList.remove("active"));
  document.getElementById(`panel-${name}`).classList.add("active");
}

/* ─────────────────────────────────────────────
   Controls
───────────────────────────────────────────── */
function onMethodChange() {
  document.getElementById("weightsSection").style.display =
    document.getElementById("distanceMethod").value === "combinee"
      ? "block"
      : "none";
}
function updateSlider(id, v) {
  document.getElementById(id).textContent = v + "%";
}

/* ─────────────────────────────────────────────
   Code tab
───────────────────────────────────────────── */
function renderCode() {
  document.getElementById("codeBlock").innerHTML =
    `<span class="cm"># ── API Endpoints ──────────────────────────────────────────</span>
<span class="kw">GET</span>  <span class="str">http://localhost:5000/api/stats</span>        <span class="cm"># db size, dims, categories</span>
<span class="kw">GET</span>  <span class="str">http://localhost:5000/api/descriptors</span>  <span class="cm"># list active descriptors</span>
<span class="kw">POST</span> <span class="str">http://localhost:5000/api/search</span>       <span class="cm"># CBIR search (multipart/form-data)</span>
<span class="kw">POST</span> <span class="str">http://localhost:5000/api/index</span>        <span class="cm"># trigger re-indexing</span>

<span class="cm"># ── /api/search request parameters ─────────────────────────</span>
image    : <span class="str">File</span>    <span class="cm"># query image (jpg/png/bmp/webp)</span>
method   : <span class="str">str</span>     <span class="cm"># combinee | euclidienne | chi2 | cosinus</span>
k        : <span class="num">int</span>     <span class="cm"># number of results (1–20)</span>
w_color  : <span class="num">float</span>   <span class="cm"># weight for HSV color block</span>
w_lbp    : <span class="num">float</span>   <span class="cm"># weight for LBP texture block</span>
w_glcm   : <span class="num">float</span>   <span class="cm"># weight for GLCM texture block</span>
w_hog    : <span class="num">float</span>   <span class="cm"># weight for HOG shape block</span>

<span class="cm"># ── curl example ───────────────────────────────────────────</span>
<span class="fn">curl</span> -X POST <span class="str">http://localhost:5000/api/search</span> \
  -F <span class="str">"image=@query.jpg"</span> -F <span class="str">"method=combinee"</span> -F <span class="str">"k=6"</span>

<span class="cm"># ── Python descriptor signatures (moteur_recherche_images.py)</span>
<span class="kw">def</span> <span class="fn">extraire_histogramme_couleur</span>(img, bins=<span class="num">32</span>) -> np.ndarray: <span class="cm"># 96d</span>
<span class="kw">def</span> <span class="fn">extraire_lbp</span>(img, P=<span class="num">8</span>, R=<span class="num">1</span>)              -> np.ndarray: <span class="cm"># 10d</span>
<span class="kw">def</span> <span class="fn">extraire_glcm</span>(img)                         -> np.ndarray: <span class="cm">#  4d</span>
<span class="kw">def</span> <span class="fn">extraire_hog</span>(img, taille=(<span class="num">128</span>,<span class="num">128</span>))        -> np.ndarray: <span class="cm"># variable</span>
<span class="kw">def</span> <span class="fn">extraire_descripteurs</span>(img)                 -> np.ndarray: <span class="cm"># concat all</span>

<span class="cm"># ── Distance functions ──────────────────────────────────────</span>
<span class="kw">def</span> <span class="fn">distance_euclidienne</span>(a, b)        -> <span class="num">float</span>
<span class="kw">def</span> <span class="fn">distance_cosinus</span>(a, b)           -> <span class="num">float</span>
<span class="kw">def</span> <span class="fn">distance_chi2</span>(a, b)              -> <span class="num">float</span>
<span class="kw">def</span> <span class="fn">distance_combinee</span>(a, b,
        poids_couleur=<span class="num">0.4</span>, poids_lbp=<span class="num">0.2</span>,
        poids_glcm=<span class="num">0.1</span>, poids_hog=<span class="num">0.3</span>)  -> <span class="num">float</span>`;
}
