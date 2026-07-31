// =====================================================================
// AI Glossary Tutor — frontend logic
// Calls the REAL backend (codebase/backend) — no mock data.
// If your backend runs on a different host/port, change API_BASE below.
// =====================================================================
const API_BASE = "http://127.0.0.1:8000";
const LEARNER_LEVEL = "coban"; // fixed to the simplest level, per product decision

// Real slide (page 13/29 of data/vlearn-pack/slides/d1-slide-hackathon.pdf,
// extracted with qpdf) rendered client-side via pdf.js. PNG is a fallback
// for when the pdf.js CDN can't be reached.
const SLIDE_PDF_URL = "assets/slide-d1-p13-token.pdf";
const SLIDE_PNG_FALLBACK = "assets/slide-d1-p13-token.png";
const PDFJS_WORKER_URL = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------
// state
// ---------------------------------------------------------------------
let sessionId = localStorage.getItem("vlearn_session_id") || null;
let savedTerms = [];
let lastLookups = Number(localStorage.getItem("vlearn_lookup_count") || 0);
let currentPayload = null;   // last successful /api/explain response
let currentContext = "";
let currentTerm = "";
let requestSeq = 0;          // guards against overlapping lookup() calls

// ---------------------------------------------------------------------
// boot
// ---------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  bindNav();
  renderSlidePage(); // fire-and-forget — doesn't block the rest of boot
  bindSelectionLookup();
  bindResultActions();

  await checkHealth();
  await ensureSession();
  await refreshSavedTerms();
  updateStatChips();
});

// ---------------------------------------------------------------------
// real slide rendering (pdf.js canvas + selectable text layer)
// ---------------------------------------------------------------------
async function renderSlidePage() {
  const wrap = $("slidePageWrap");
  const canvas = $("slideCanvas");
  const textLayerDiv = $("slideTextLayer");

  try {
    if (!window.pdfjsLib) throw new Error("pdf.js chưa sẵn sàng (CDN có thể bị chặn)");
    pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_URL;

    const pdf = await pdfjsLib.getDocument(SLIDE_PDF_URL).promise;
    const page = await pdf.getPage(1);

    const containerWidth = wrap.clientWidth || wrap.parentElement.clientWidth || 640;
    const unscaled = page.getViewport({ scale: 1 });
    const viewport = page.getViewport({ scale: containerWidth / unscaled.width });

    const ctx = canvas.getContext("2d");
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    wrap.style.height = viewport.height + "px";

    await page.render({ canvasContext: ctx, viewport }).promise;

    const textContent = await page.getTextContent();
    textLayerDiv.style.width = viewport.width + "px";
    textLayerDiv.style.height = viewport.height + "px";
    textLayerDiv.innerHTML = "";

    // pdf.js has renamed this param across versions (textContent → textContentSource)
    // — pass both so it works regardless of the exact 3.x build the CDN serves.
    const task = pdfjsLib.renderTextLayer({
      textContent,
      textContentSource: textContent,
      container: textLayerDiv,
      viewport,
      textDivs: [],
    });
    if (task && task.promise) await task.promise;
  } catch (e) {
    console.warn("Không render được slide PDF thật, dùng ảnh dự phòng:", e);
    wrap.innerHTML = `<img src="${SLIDE_PNG_FALLBACK}" alt="Slide: Token — model không đọc 'từ', model đọc mảnh chữ" style="display:block;width:100%;height:auto;">`;
  }
}

// ---------------------------------------------------------------------
// theme toggle
// ---------------------------------------------------------------------
function initTheme() {
  const saved = localStorage.getItem("vlearn_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  $("themeToggle").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("vlearn_theme", next);
  });
}

// ---------------------------------------------------------------------
// nav tabs (smooth scroll, active state)
// ---------------------------------------------------------------------
function bindNav() {
  document.querySelectorAll(".nav-link[data-tab]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      document.querySelectorAll(".nav-link[data-tab]").forEach((x) => x.classList.remove("active"));
      a.classList.add("active");
      document.getElementById(a.dataset.tab).scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

// ---------------------------------------------------------------------
// backend health check
// ---------------------------------------------------------------------
async function checkHealth() {
  const pill = $("statusPill");
  const dot = $("statusDot");
  const text = $("statusText");
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (!res.ok) throw new Error("health check failed");
    const data = await res.json();
    pill.className = "status-pill " + (data.groq_available ? "ok" : "warn");
    text.textContent = data.groq_available
      ? `Backend OK · ${data.primary_model}`
      : "Backend OK · thiếu GROQ_API_KEY";
    $("statModel").textContent = data.groq_available ? data.primary_model.split("-")[0] : "—";
  } catch (e) {
    pill.className = "status-pill err";
    text.textContent = "Không kết nối được backend";
  }
}

// ---------------------------------------------------------------------
// session management (persisted across reloads via localStorage)
// ---------------------------------------------------------------------
async function ensureSession() {
  if (sessionId) {
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
      if (res.ok) {
        $("statSession").textContent = sessionId.replace("sess_", "").slice(0, 6);
        return;
      }
    } catch (e) { /* fall through to create a new one */ }
  }
  try {
    const res = await fetch(`${API_BASE}/api/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ initial_level: LEARNER_LEVEL }),
    });
    const data = await res.json();
    sessionId = data.session_id;
    localStorage.setItem("vlearn_session_id", sessionId);
    $("statSession").textContent = sessionId.replace("sess_", "").slice(0, 6);
  } catch (e) {
    $("statSession").textContent = "lỗi";
  }
}

// ---------------------------------------------------------------------
// text selection → floating lookup icon (DDICT-style)
// ---------------------------------------------------------------------
function bindSelectionLookup() {
  const readerBody = $("readerBody");
  const icon = $("lookupIcon");
  let pending = null;

  document.addEventListener("mouseup", (e) => {
    if (e.target === icon) return;
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel.toString().trim();
      if (!text || text.length > 60 || !readerBody.contains(sel.anchorNode)) {
        icon.style.display = "none";
        return;
      }
      let ctx = "";
      const node = sel.anchorNode;
      const el = node && node.parentElement;
      const para = el ? el.closest("p") : null;
      if (para) {
        ctx = para.textContent.trim().replace(/\s+/g, " ");
      } else {
        // selection came from the PDF text layer (each word is its own <span>,
        // no wrapping <p>) — use the whole slide's text as context instead.
        const layer = el ? el.closest(".textLayer") : null;
        if (layer) ctx = layer.textContent.trim().replace(/\s+/g, " ").slice(0, 600);
      }

      pending = { text, ctx };

      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      const host = readerBody.getBoundingClientRect();
      icon.style.left = Math.min(rect.right - host.left + 6, readerBody.clientWidth - 40) + "px";
      icon.style.top = (rect.top - host.top - 40) + "px";
      icon.style.display = "flex";
    }, 10);
  });

  icon.addEventListener("click", () => {
    if (!pending) return;
    icon.style.display = "none";
    lookup(pending.text, pending.ctx);
    window.getSelection().removeAllRanges();
  });
}

// ---------------------------------------------------------------------
// main lookup flow → calls REAL /api/explain
// ---------------------------------------------------------------------
async function lookup(term, ctx) {
  // Bump the sequence for THIS call. If a newer lookup() starts before this
  // one finishes, its seq will be higher — so this call's async continuations
  // can detect they're stale and bail out instead of painting over (or racing)
  // the newer call's UI state (this is what caused the success card and the
  // "Không gọi được AI" error box to appear at the same time).
  const seq = ++requestSeq;

  currentTerm = term;
  currentContext = ctx;

  $("emptyState").hidden = true;
  $("result").hidden = true;
  $("errorState").hidden = true;
  const pl = $("pipeline");
  pl.hidden = false;
  ["pl1", "pl2", "pl3"].forEach((id) => $(id).classList.remove("run", "ok"));
  $("plTerm").textContent = `"${term}"`;

  $("pl1").classList.add("run");
  await sleep(280);
  if (seq !== requestSeq) return; // a newer lookup superseded this one
  $("pl1").classList.replace("run", "ok");
  $("pl2").classList.add("run");

  try {
    const res = await fetch(`${API_BASE}/api/explain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_text: term,
        surrounding_context: ctx,
        learner_level: LEARNER_LEVEL,
        session_id: sessionId,
      }),
    });

    if (seq !== requestSeq) return; // superseded while the request was in flight
    $("pl2").classList.replace("run", "ok");
    $("pl3").classList.add("run");
    await sleep(200);
    if (seq !== requestSeq) return;

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    $("pl3").classList.replace("run", "ok");

    currentPayload = data;
    lastLookups += 1;
    localStorage.setItem("vlearn_lookup_count", lastLookups);
    updateStatChips();

    renderResult(data);
  } catch (e) {
    if (seq !== requestSeq) return; // a newer lookup already took over the UI
    pl.hidden = true;
    $("result").hidden = true; // never show a stale success card behind the error
    $("errorState").hidden = false;
    $("errorMsg").textContent =
      "Lỗi: " + e.message + ". Kiểm tra backend đã chạy ở " + API_BASE + " và có GROQ_API_KEY chưa.";
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ---------------------------------------------------------------------
// render explain result
// ---------------------------------------------------------------------
function renderResult(data) {
  $("rTerm").textContent = data.term;
  $("rFull").textContent = data.expanded_form ? "— " + data.expanded_form : "";

  const tag = $("rConfidence");
  const map = { high: ["Đáng tin cậy", "high"], low: ["Chưa chắc chắn", "low"], insufficient: ["Thiếu căn cứ", "insufficient"] };
  const [label, cls] = map[data.confidence] || ["—", "low"];
  tag.textContent = label;
  tag.className = "confidence-tag " + cls;

  const isInsufficient = data.confidence === "insufficient";
  $("rExplainBox").hidden = isInsufficient;
  $("rExampleBox").hidden = isInsufficient || !data.example;
  $("rEvidenceBox").hidden = !data.evidence_span;
  $("rRelatedBox").hidden = isInsufficient || !(data.related_concepts || []).length;
  $("btnSave").hidden = isInsufficient;

  $("rExplain").textContent = data.plain_explanation || "";
  $("rExample").textContent = data.example || "";
  $("rEvidence").textContent = data.evidence_span ? `"${data.evidence_span}"` : "";

  const fb = $("rFallback");
  if (isInsufficient) {
    fb.hidden = false;
    fb.innerHTML =
      `⚠️ AI chưa đủ căn cứ để giải thích chắc chắn từ này trong ngữ cảnh hiện tại.` +
      (data.clarifying_question ? `<br><br><b>Câu hỏi gợi ý:</b> ${data.clarifying_question}` : "") +
      `<br><br>Không đoán bừa để tránh dạy sai kiến thức — bạn có thể hỏi trực tiếp tutor VLearn.`;
  } else {
    fb.hidden = true;
  }

  const chips = $("rChips");
  chips.innerHTML = "";
  (data.related_concepts || []).forEach((rc) => {
    const c = document.createElement("span");
    c.className = "chip";
    c.textContent = "🔗 " + rc.concept;
    c.title = rc.relationship || "";
    c.onclick = () => lookup(rc.concept, currentContext);
    chips.appendChild(c);
  });

  const btn = $("btnSave");
  btn.disabled = !!data.saved;
  btn.textContent = data.saved ? "✓ Đã lưu vào sổ tay" : "💾 Lưu để ôn tập";

  $("rModelTag").textContent = data.used_model ? "Trả lời bởi: " + data.used_model : "";
  $("statModel").textContent = data.used_model ? data.used_model.split("-")[0] : $("statModel").textContent;

  $("pipeline").hidden = true;
  $("result").hidden = false;
}

// ---------------------------------------------------------------------
// save / reset / retry
// ---------------------------------------------------------------------
function bindResultActions() {
  $("btnSave").addEventListener("click", async () => {
    if (!currentPayload || !sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/saved-terms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          term: currentPayload.term,
          expanded_form: currentPayload.expanded_form,
          meaning_in_context: currentPayload.meaning_in_context,
          plain_explanation: currentPayload.plain_explanation,
          example: currentPayload.example,
          evidence_span: currentPayload.evidence_span,
          learner_level: LEARNER_LEVEL,
        }),
      });
      if (!res.ok) throw new Error("save failed");
      currentPayload.saved = true;
      $("btnSave").disabled = true;
      $("btnSave").textContent = "✓ Đã lưu vào sổ tay";
      await refreshSavedTerms();
    } catch (e) {
      alert("Không lưu được — kiểm tra backend đang chạy.");
    }
  });

  $("btnReset").addEventListener("click", () => {
    $("result").hidden = true;
    $("pipeline").hidden = true;
    $("errorState").hidden = true;
    $("emptyState").hidden = false;
  });

  $("btnRetry").addEventListener("click", () => {
    if (currentTerm) lookup(currentTerm, currentContext);
  });
}

// ---------------------------------------------------------------------
// notebook (saved terms) — backed by real API
// ---------------------------------------------------------------------
async function refreshSavedTerms() {
  if (!sessionId) return;
  try {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/saved-terms`);
    if (!res.ok) return;
    const data = await res.json();
    savedTerms = data.terms || [];
    renderNotebook();
    updateStatChips();
  } catch (e) { /* silent — notebook just stays empty */ }
}

function renderNotebook() {
  const list = $("nbList");
  const empty = $("nbEmpty");
  const count = $("nbCount");
  count.textContent = savedTerms.length;
  $("avatarBadge").textContent = savedTerms.length;

  if (!savedTerms.length) {
    empty.hidden = false;
    list.innerHTML = "";
    return;
  }
  empty.hidden = true;
  list.innerHTML = "";
  savedTerms.forEach((t) => {
    const row = document.createElement("div");
    row.className = "nb-item";
    row.innerHTML = `
      <span class="n-term">${escapeHtml(t.term)}</span>
      <span class="n-meaning">${escapeHtml(t.plain_explanation || t.meaning_in_context || "")}</span>
      <span class="n-level">${t.learner_level || "coban"}</span>
      <button class="n-del" title="Xoá khỏi sổ tay">✕</button>
    `;
    row.querySelector(".n-meaning").parentElement.addEventListener("click", (e) => {
      if (e.target.classList.contains("n-del")) return;
      document.getElementById("notebook").scrollIntoView({ behavior: "smooth" });
    });
    row.querySelector(".n-del").addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await fetch(`${API_BASE}/api/sessions/${sessionId}/saved-terms/${t.term_id}`, { method: "DELETE" });
        await refreshSavedTerms();
      } catch (err) { /* noop */ }
    });
    list.appendChild(row);
  });
}

function updateStatChips() {
  $("statLookups").textContent = lastLookups;
  $("statSaved").textContent = savedTerms.length;
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}
