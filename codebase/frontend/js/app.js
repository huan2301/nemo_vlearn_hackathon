// =====================================================================
// AI Glossary Tutor — frontend logic
// Calls the REAL backend (codebase/backend) — no mock data.
// If your backend runs on a different host/port, change API_BASE below.
// =====================================================================
const API_BASE = "http://127.0.0.1:8000";
const LEARNER_LEVEL = "coban"; // fixed to the simplest level, per product decision

// Real slides are served by the backend from data/vlearn-pack/slides.
// The frontend loads them through the API so the PDF is shared from one place.
const SLIDE_PDF_URL = `${API_BASE}/api/slides/d1-slide-hackathon.pdf`;
const PDFJS_WORKER_URL =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

const $ = (id) => document.getElementById(id);

// ---------------------------------------------------------------------
// state
// ---------------------------------------------------------------------
let sessionId = localStorage.getItem("vlearn_session_id") || null;
let savedTerms = [];
let lastLookups = Number(localStorage.getItem("vlearn_lookup_count") || 0);
let currentPayload = null; // last successful /api/explain response
let currentContext = "";
let currentTerm = "";
let currentExplainStyle = "tomtat"; // tomtat | vidu | sosanh | chuyensau
let currentQuiz = null;
let requestSeq = 0; // guards against overlapping lookup() calls
let slidePageObserver = null;

// ---------------------------------------------------------------------
// boot
// ---------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  bindNav();
  renderAllSlidePages(); // fire-and-forget — doesn't block the rest of boot
  bindSelectionLookup();
  bindResultActions();
  bindStyleButtons();

  await checkHealth();
  await ensureSession();
  await refreshSavedTerms();
  await refreshProgress();
  await refreshDueFlashcards();
  updateStatChips();
});

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
      document
        .querySelectorAll(".nav-link[data-tab]")
        .forEach((x) => x.classList.remove("active"));
      a.classList.add("active");
      document
        .getElementById(a.dataset.tab)
        .scrollIntoView({ behavior: "smooth", block: "start" });
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
    $("statModel").textContent = data.groq_available
      ? data.primary_model.split("-")[0]
      : "—";
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
        $("statSession").textContent = sessionId
          .replace("sess_", "")
          .slice(0, 6);
        return;
      }
    } catch (e) {
      /* fall through to create a new one */
    }
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
// real slide rendering (pdf.js canvas + selectable text layer), all pages,
// scrollable — plus /api/terms/detect per page for the "thuật ngữ khó" chips.
// ---------------------------------------------------------------------
async function renderAllSlidePages() {
  const scroll = $("slideScroll");
  const indicator = $("slidePageIndicator");

  try {
    if (!window.pdfjsLib)
      throw new Error("pdf.js chưa sẵn sàng (CDN có thể bị chặn)");
    pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_URL;

    const pdf = await pdfjsLib.getDocument(SLIDE_PDF_URL).promise;
    const numPages = pdf.numPages;
    indicator.textContent = `Trang 1 / ${numPages}`;

    scroll.innerHTML = "";
    const blocks = [];
    for (let i = 1; i <= numPages; i++) {
      const block = document.createElement("div");
      block.className = "slide-page-block";
      block.dataset.page = String(i);
      block.innerHTML =
        '<div class="slide-page-wrap"><canvas></canvas><div class="textLayer"></div></div>' +
        '<div class="slide-terms"><span class="slide-terms-lbl">🔍 Đang quét thuật ngữ khó…</span>' +
        '<div class="chips terms-chips"></div></div>';
      scroll.appendChild(block);
      blocks.push(block);
    }

    if (slidePageObserver) slidePageObserver.disconnect();
    slidePageObserver = new IntersectionObserver(
      (entries) => {
        let best = null;
        entries.forEach((e) => {
          if (
            e.isIntersecting &&
            (!best || e.intersectionRatio > best.intersectionRatio)
          )
            best = e;
        });
        if (best)
          indicator.textContent = `Trang ${best.target.dataset.page} / ${numPages}`;
      },
      { root: scroll, threshold: [0.25, 0.5, 0.75] },
    );

    // Render sequentially (not all at once) — kinder to CPU and to the pdf.js worker.
    for (let i = 1; i <= numPages; i++) {
      slidePageObserver.observe(blocks[i - 1]);
      await renderOneSlidePage(pdf, i, blocks[i - 1]);
    }
  } catch (e) {
    console.warn("Không render được slide PDF thật:", e);
    scroll.innerHTML =
      '<div class="slide-loading">⚠️ Không tải được slide (pdf.js/CDN có thể bị chặn). ' +
      `<a href="${SLIDE_PDF_URL}" target="_blank" rel="noopener">Mở file PDF trực tiếp</a></div>`;
  }
}

async function renderOneSlidePage(pdf, pageNum, block) {
  const wrap = block.querySelector(".slide-page-wrap");
  const canvas = wrap.querySelector("canvas");
  const textLayerDiv = wrap.querySelector(".textLayer");

  const page = await pdf.getPage(pageNum);
  const containerWidth =
    wrap.clientWidth || wrap.parentElement.clientWidth || 640;
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

  const pageText = textContent.items
    .map((it) => it.str)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  block.dataset.pageText = pageText;
  await loadDifficultTermsForPage(pageText, block);
}

// ---------------------------------------------------------------------
// "Người học mở slide -> hệ thống tự nhận diện thuật ngữ khó" — /api/terms/detect
// ---------------------------------------------------------------------
async function loadDifficultTermsForPage(pageText, block) {
  const lbl = block.querySelector(".slide-terms-lbl");
  const chipsWrap = block.querySelector(".terms-chips");

  if (!pageText) {
    lbl.textContent = "Trang này không có chữ để quét.";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/terms/detect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        slide_text: pageText,
        learner_level: LEARNER_LEVEL,
        only_difficult: true,
        max_terms: 8,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data.terms || !data.terms.length) {
      lbl.textContent = "✓ Không có thuật ngữ khó nổi bật trên trang này.";
      chipsWrap.innerHTML = "";
      return;
    }

    lbl.textContent = "🔍 Thuật ngữ khó trên trang này — bấm để AI giải thích:";
    chipsWrap.innerHTML = "";
    const seen = new Set();
    data.terms.forEach((t) => {
      const key = t.term.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      const chip = document.createElement("span");
      chip.className = "chip difficult";
      chip.textContent = "⚠ " + t.term;
      chip.title = t.expanded_form || "";
      chip.onclick = () => {
        const ctx = pageText.slice(
          Math.max(0, t.start - 150),
          Math.min(pageText.length, t.end + 250),
        );
        lookup(t.term, ctx, currentExplainStyle);
      };
      chipsWrap.appendChild(chip);
    });
  } catch (e) {
    lbl.textContent = "Không quét được thuật ngữ khó (backend chưa chạy?).";
  }
}

// ---------------------------------------------------------------------
// text selection → floating lookup icon (DDICT-style), works across every
// rendered slide page since each has its own .textLayer inside #readerBody
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
        // selection came from a slide's PDF text layer (each word is its own
        // <span>, no wrapping <p>) — use that page's full text as context.
        const layer = el ? el.closest(".textLayer") : null;
        if (layer)
          ctx = layer.textContent.trim().replace(/\s+/g, " ").slice(0, 600);
      }

      pending = { text, ctx };

      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      const host = readerBody.getBoundingClientRect();
      icon.style.left =
        Math.min(rect.right - host.left + 6, readerBody.clientWidth - 40) +
        "px";
      icon.style.top = rect.top - host.top - 40 + "px";
      icon.style.display = "flex";
    }, 10);
  });

  icon.addEventListener("click", () => {
    if (!pending) return;
    icon.style.display = "none";
    lookup(pending.text, pending.ctx, currentExplainStyle);
    window.getSelection().removeAllRanges();
  });
}

// ---------------------------------------------------------------------
// style selector: Tóm tắt / Ví dụ / So sánh / Chuyên sâu
// ---------------------------------------------------------------------
function bindStyleButtons() {
  document.querySelectorAll(".style-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!currentTerm || btn.dataset.style === currentExplainStyle) return;
      lookup(currentTerm, currentContext, btn.dataset.style);
    });
  });
}

// ---------------------------------------------------------------------
// main lookup flow → calls REAL /api/explain
// ---------------------------------------------------------------------
async function lookup(term, ctx, style) {
  // Bump the sequence for THIS call. If a newer lookup() starts before this
  // one finishes, its seq will be higher — so this call's async continuations
  // can detect they're stale and bail out instead of racing the newer call's
  // UI state (success + error boxes showing at once).
  const seq = ++requestSeq;

  currentTerm = term;
  currentContext = ctx;
  currentExplainStyle = style || currentExplainStyle || "tomtat";

  $("emptyState").hidden = true;
  $("result").hidden = true;
  $("errorState").hidden = true;
  const pl = $("pipeline");
  pl.hidden = false;
  ["pl1", "pl2", "pl3"].forEach((id) => $(id).classList.remove("run", "ok"));
  $("plTerm").textContent = `"${term}"`;

  $("pl1").classList.add("run");
  await sleep(220);
  if (seq !== requestSeq) return;
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
        explain_style: currentExplainStyle,
        session_id: sessionId,
      }),
    });

    if (seq !== requestSeq) return;
    $("pl2").classList.replace("run", "ok");
    $("pl3").classList.add("run");
    await sleep(150);
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
      "Lỗi: " +
      e.message +
      ". Kiểm tra backend đã chạy ở " +
      API_BASE +
      " và có GROQ_API_KEY chưa.";
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

// ---------------------------------------------------------------------
// render explain result (incl. style/difficulty/comparison/quiz — new fields)
// ---------------------------------------------------------------------
function renderResult(data) {
  $("rTerm").textContent = data.term;
  $("rFull").textContent = data.expanded_form ? "— " + data.expanded_form : "";

  const tag = $("rConfidence");
  const map = {
    high: ["Đáng tin cậy", "high"],
    low: ["Chưa chắc chắn", "low"],
    insufficient: ["Thiếu căn cứ", "insufficient"],
  };
  const [label, cls] = map[data.confidence] || ["—", "low"];
  tag.textContent = label;
  tag.className = "confidence-tag " + cls;

  const isInsufficient = data.confidence === "insufficient";

  // AI đánh giá độ khó
  const diffBadge = $("rDifficulty");
  if (data.is_difficult) {
    diffBadge.hidden = false;
    $("rDifficultyReason").textContent =
      data.difficulty_reason || "AI đánh giá đây là thuật ngữ cần chú ý.";
  } else {
    diffBadge.hidden = true;
  }

  // giữ trạng thái active của 4 nút kiểu giải thích theo đúng style server trả về
  currentExplainStyle = data.explain_style || currentExplainStyle;
  document.querySelectorAll(".style-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.style === currentExplainStyle);
  });

  $("rExplainBox").hidden = isInsufficient;
  $("rExampleBox").hidden = isInsufficient || !data.example;
  $("rEvidenceBox").hidden = !data.evidence_span;
  $("rRelatedBox").hidden =
    isInsufficient || !(data.related_concepts || []).length;
  $("btnSave").hidden = isInsufficient;

  $("rExplain").textContent =
    data.styled_explanation || data.plain_explanation || "";
  $("rExample").textContent = data.example || "";
  $("rEvidence").textContent = data.evidence_span
    ? `"${data.evidence_span}"`
    : "";

  // So sánh với khái niệm đã biết
  const cmpBox = $("rComparisonBox");
  if (data.comparison_concept && data.comparison_concept.comparison) {
    cmpBox.hidden = false;
    $("rComparison").textContent =
      `${data.comparison_concept.concept}: ${data.comparison_concept.comparison}`;
  } else {
    cmpBox.hidden = true;
  }

  const fb = $("rFallback");
  if (isInsufficient) {
    fb.hidden = false;
    fb.innerHTML =
      `⚠️ AI chưa đủ căn cứ để giải thích chắc chắn từ này trong ngữ cảnh hiện tại.` +
      (data.clarifying_question
        ? `<br><br><b>Câu hỏi gợi ý:</b> ${data.clarifying_question}`
        : "") +
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
    c.onclick = () => lookup(rc.concept, currentContext, currentExplainStyle);
    chips.appendChild(c);
  });

  const btn = $("btnSave");
  btn.disabled = !!data.saved;
  btn.textContent = data.saved ? "✓ Đã lưu vào sổ tay" : "💾 Lưu để ôn tập";

  $("rModelTag").textContent = data.used_model
    ? "Trả lời bởi: " + data.used_model
    : "";
  $("statModel").textContent = data.used_model
    ? data.used_model.split("-")[0]
    : $("statModel").textContent;

  renderQuiz(data.quiz, data);

  $("pipeline").hidden = true;
  $("result").hidden = false;
}

// ---------------------------------------------------------------------
// Quiz 1 câu ("Active Recall") — sinh sẵn trong /api/explain, chấm qua /api/quiz/submit
// ---------------------------------------------------------------------
function renderQuiz(quiz, explainData) {
  const box = $("quizBox");
  const feedback = $("quizFeedback");
  feedback.hidden = true;
  feedback.className = "quiz-feedback";
  feedback.textContent = "";

  if (!quiz) {
    box.hidden = true;
    currentQuiz = null;
    return;
  }

  currentQuiz = quiz;
  box.hidden = false;
  $("quizQuestion").textContent = quiz.question;

  const optsWrap = $("quizOptions");
  optsWrap.innerHTML = "";
  quiz.options.forEach((opt) => {
    const b = document.createElement("button");
    b.className = "quiz-opt";
    b.dataset.key = opt.key;
    b.innerHTML = `<span class="k">${escapeHtml(opt.key)}.</span>${escapeHtml(opt.text)}`;
    b.addEventListener("click", () =>
      submitQuizAnswer(opt.key, quiz, explainData, optsWrap),
    );
    optsWrap.appendChild(b);
  });
}

async function submitQuizAnswer(selectedKey, quiz, explainData, optsWrap) {
  optsWrap.querySelectorAll(".quiz-opt").forEach((b) => (b.disabled = true));

  try {
    const needsNewCard = !explainData.term_id && !explainData.saved;
    const res = await fetch(`${API_BASE}/api/quiz/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        term: explainData.term,
        term_id: explainData.term_id || null,
        term_data: needsNewCard
          ? {
              term: explainData.term,
              expanded_form: explainData.expanded_form,
              meaning_in_context: explainData.meaning_in_context,
              plain_explanation: explainData.plain_explanation,
              example: explainData.example,
              evidence_span: explainData.evidence_span,
              learner_level: LEARNER_LEVEL,
              is_difficult: explainData.is_difficult || false,
            }
          : null,
        quiz,
        selected_key: selectedKey,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    optsWrap.querySelectorAll(".quiz-opt").forEach((b) => {
      if (b.dataset.key === data.correct_key) b.classList.add("correct");
      else if (b.dataset.key === selectedKey) b.classList.add("wrong");
    });

    const feedback = $("quizFeedback");
    feedback.hidden = false;
    feedback.className =
      "quiz-feedback " + (data.correct ? "correct" : "wrong");
    feedback.textContent =
      (data.correct ? "✓ Chính xác! " : "✗ Chưa đúng. ") +
      (data.explanation || "");

    updateProgressChips(data.progress);

    if (data.flashcard) {
      explainData.term_id = data.flashcard.term_id;
      explainData.saved = true;
      $("btnSave").disabled = true;
      $("btnSave").textContent = "✓ Đã lưu vào sổ tay";
      await refreshSavedTerms();
      await refreshDueFlashcards();
    }
  } catch (e) {
    const feedback = $("quizFeedback");
    feedback.hidden = false;
    feedback.className = "quiz-feedback wrong";
    feedback.textContent = "Không chấm được bài — kiểm tra backend đang chạy.";
  }
}

// ---------------------------------------------------------------------
// Learning Progress panel
// ---------------------------------------------------------------------
function updateProgressChips(progress) {
  if (!progress) return;
  $("pQuizScore").textContent =
    `${progress.quiz_correct_count}/${progress.quiz_attempted_count}`;
  $("pAccuracy").textContent = progress.quiz_attempted_count
    ? Math.round(progress.accuracy * 100) + "%"
    : "—";
  $("pStreak").textContent = progress.current_streak;
}

async function refreshProgress() {
  if (!sessionId) return;
  try {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/progress`);
    if (!res.ok) return;
    updateProgressChips(await res.json());
  } catch (e) {
    /* silent — panel just stays at defaults */
  }
}

// ---------------------------------------------------------------------
// save / reset / retry
// ---------------------------------------------------------------------
function bindResultActions() {
  $("btnSave").addEventListener("click", async () => {
    if (!currentPayload || !sessionId) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/sessions/${sessionId}/saved-terms`,
        {
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
            is_difficult: currentPayload.is_difficult || false,
          }),
        },
      );
      if (!res.ok) throw new Error("save failed");
      const savedCard = await res.json();
      currentPayload.saved = true;
      currentPayload.term_id = savedCard.term_id;
      $("btnSave").disabled = true;
      $("btnSave").textContent = "✓ Đã lưu vào sổ tay";
      await refreshSavedTerms();
      await refreshDueFlashcards();
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
    if (currentTerm) lookup(currentTerm, currentContext, currentExplainStyle);
  });
}

// ---------------------------------------------------------------------
// notebook (saved terms) — backed by real API
// ---------------------------------------------------------------------
async function refreshSavedTerms() {
  if (!sessionId) return;
  try {
    const res = await fetch(
      `${API_BASE}/api/sessions/${sessionId}/saved-terms`,
    );
    if (!res.ok) return;
    const data = await res.json();
    savedTerms = data.terms || [];
    renderNotebook();
    updateStatChips();
  } catch (e) {
    /* silent — notebook just stays empty */
  }
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
    row
      .querySelector(".n-meaning")
      .parentElement.addEventListener("click", (e) => {
        if (e.target.classList.contains("n-del")) return;
        document
          .getElementById("notebook")
          .scrollIntoView({ behavior: "smooth" });
      });
    row.querySelector(".n-del").addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await fetch(
          `${API_BASE}/api/sessions/${sessionId}/saved-terms/${t.term_id}`,
          { method: "DELETE" },
        );
        await refreshSavedTerms();
        await refreshDueFlashcards();
      } catch (err) {
        /* noop */
      }
    });
    list.appendChild(row);
  });
}

// ---------------------------------------------------------------------
// Flashcards due for review — "Nhắc ôn bằng Spaced Repetition"
// ---------------------------------------------------------------------
async function refreshDueFlashcards() {
  if (!sessionId) return;
  try {
    const res = await fetch(
      `${API_BASE}/api/sessions/${sessionId}/flashcards/due`,
    );
    if (!res.ok) return;
    const data = await res.json();
    renderDueList(data.terms || []);
  } catch (e) {
    /* silent — due section just stays empty */
  }
}

function renderDueList(terms) {
  const list = $("dueList");
  const empty = $("dueEmpty");
  const count = $("dueCount");
  count.textContent = terms.length;

  if (!terms.length) {
    empty.hidden = false;
    list.innerHTML = "";
    return;
  }
  empty.hidden = true;
  list.innerHTML = "";
  terms.forEach((t) => {
    const row = document.createElement("div");
    row.className = "due-item";
    row.innerHTML = `
      <span class="due-term">${escapeHtml(t.term)}</span>
      <div class="due-actions">
        <button type="button" data-quality="again">😵 Quên</button>
        <button type="button" data-quality="hard">😕 Khó</button>
        <button type="button" data-quality="good">🙂 Nhớ được</button>
        <button type="button" data-quality="easy">😄 Dễ</button>
      </div>
    `;
    row.querySelectorAll("button").forEach((b) => {
      b.addEventListener("click", () =>
        reviewFlashcard(t.term_id, b.dataset.quality, row),
      );
    });
    list.appendChild(row);
  });
}

async function reviewFlashcard(termId, quality, rowEl) {
  rowEl.querySelectorAll("button").forEach((b) => (b.disabled = true));
  try {
    const res = await fetch(
      `${API_BASE}/api/sessions/${sessionId}/flashcards/${termId}/review`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quality }),
      },
    );
    if (!res.ok) throw new Error("review failed");
    await refreshDueFlashcards();
    await refreshSavedTerms();
  } catch (e) {
    rowEl.querySelectorAll("button").forEach((b) => (b.disabled = false));
    alert("Không cập nhật được lịch ôn — kiểm tra backend đang chạy.");
  }
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
