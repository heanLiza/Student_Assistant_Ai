"use strict";
const $ = (id) => document.getElementById(id);
const state = { task: "explain", busy: false, ctrl: null, keyHandler: null };
const JSON_TASKS = ["flashcards", "quiz", "practice"];
const MIN_CHARS = 20;
const SAMPLE = "Photosynthesis is the process by which plants, algae and some bacteria convert light energy into chemical energy. " +
  "It takes place in the chloroplasts, where chlorophyll absorbs sunlight. The plant uses water from the roots and carbon dioxide " +
  "from the air to produce glucose and oxygen. The overall equation is: 6CO2 + 6H2O + light -> C6H12O6 + 6O2. " +
  "The process has two stages: the light-dependent reactions, which make ATP and NADPH, and the Calvin cycle, which uses them to build sugar.";

const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
};
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text; // textContent = safe against HTML injection
  return e;
}

/* ---------- error toast ---------- */
let toastTimer;
function showError(msg) {
  const t = $("toast");
  clearTimeout(toastTimer);
  if (!msg) return t.classList.add("hidden");
  t.textContent = msg;
  t.classList.remove("hidden");
  toastTimer = setTimeout(() => t.classList.add("hidden"), 7000);
}

/* ---------- lesson input ---------- */
const lesson = $("lesson");
lesson.addEventListener("input", () => {
  $("counter").textContent = `${lesson.value.length} / ${lesson.maxLength}`;
  store.set("lesson", lesson.value);
});
lesson.value = store.get("lesson") || "";
lesson.dispatchEvent(new Event("input"));
$("clear").addEventListener("click", () => { lesson.value = ""; lesson.dispatchEvent(new Event("input")); lesson.focus(); });
$("sample").addEventListener("click", () => { lesson.value = SAMPLE; lesson.dispatchEvent(new Event("input")); });

/* ---------- task selection ---------- */
document.querySelectorAll(".task").forEach((b) =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".task").forEach((t) => { t.classList.remove("active"); t.setAttribute("aria-checked", "false"); });
    b.classList.add("active");
    b.setAttribute("aria-checked", "true");
    state.task = b.dataset.task;
    document.querySelectorAll(".nav-item[data-task]").forEach((n) => n.classList.toggle("active", n.dataset.task === state.task));
    $("countBox").classList.toggle("hidden", !JSON_TASKS.includes(state.task));
  })
);
document.querySelectorAll(".nav-item[data-task]").forEach((n) =>
  n.addEventListener("click", () => document.querySelector(`.task[data-task="${n.dataset.task}"]`).click()));
document.querySelectorAll("[data-click]").forEach((b) =>
  b.addEventListener("click", () => $(b.dataset.click).click()));

const clampCount = (v) => Math.max(1, Math.min(15, Number(v) || 5));
$("minus").addEventListener("click", () => { $("count").value = clampCount($("count").value - 1); });
$("plus").addEventListener("click", () => { $("count").value = clampCount(Number($("count").value) + 1); });

/* ---------- drag & drop / upload ---------- */
const drop = $("drop"), fileInput = $("file");
async function loadFile(file) {
  if (!file) return;
  const info = $("fileInfo");
  info.classList.remove("hidden");
  info.textContent = `Reading ${file.name} ...`;
  try {
    let text;
    if (/\.(txt|md|csv)$/i.test(file.name)) {
      text = await file.text();
    } else {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Upload failed.");
      text = data.text;
    }
    lesson.value = text.slice(0, lesson.maxLength);
    lesson.dispatchEvent(new Event("input"));
    info.textContent = `${file.name} loaded (${lesson.value.length} characters)`;
  } catch (e) {
    info.classList.add("hidden");
    showError(e.message || "Could not read the file.");
  }
  fileInput.value = "";
}
drop.addEventListener("click", () => fileInput.click());
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });
fileInput.addEventListener("change", () => loadFile(fileInput.files[0]));
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => loadFile(e.dataTransfer.files[0]));
["dragover", "drop"].forEach((ev) => window.addEventListener(ev, (e) => e.preventDefault()));

/* ---------- renderers ---------- */
function renderEmpty() {
  $("output").replaceChildren();
  $("actions").replaceChildren();
  $("info").classList.add("hidden");
  $("result").classList.add("hidden");
}

function renderText(out, text) {
  let ul = null;
  text.split("\n").forEach((line) => {
    if (/^\s*[-*•]\s+/.test(line)) {
      if (!ul) { ul = el("ul"); out.appendChild(ul); }
      ul.appendChild(el("li", null, line.replace(/^\s*[-*•]\s+/, "").replace(/\*\*/g, "")));
    } else {
      ul = null;
      if (line.trim()) out.appendChild(el("p", null, line.replace(/\*\*/g, "").replace(/^#+\s*/, "")));
    }
  });
  const btn = el("button", "copy", "Copy");
  btn.type = "button";
  btn.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(text); btn.textContent = "Copied"; }
    catch (e) { btn.textContent = "Select and copy manually"; }
    setTimeout(() => (btn.textContent = "Copy"), 1800);
  });
  $("actions").replaceChildren(btn);
}

function renderFlashcards(out, cards) {
  let i = 0;
  const bar = el("span"), prog = el("div", "progress");
  prog.appendChild(bar);
  const front = el("div", "face front"), back = el("div", "face back");
  const inner = el("div", "flip-inner");
  inner.append(front, back);
  const card = el("button", "flip");
  card.type = "button";
  card.setAttribute("aria-label", "Flip card");
  card.appendChild(inner);
  const prev = el("button", "btn", " មុន"), next = el("button", "btn main", "បន្ទាប់ ");
  prev.type = next.type = "button";
  const count = el("span", "hint");
  const nav = el("div", "fc-nav");
  nav.append(prev, count, next);
  function show() {
    card.classList.remove("is-flipped");
    front.textContent = cards[i].front;
    back.textContent = cards[i].back;
    bar.style.width = `${((i + 1) / cards.length) * 100}%`;
    count.textContent = `${i + 1} / ${cards.length}`;
    prev.disabled = i === 0;
    next.disabled = i === cards.length - 1;
  }
  const go = (d) => { i = Math.max(0, Math.min(cards.length - 1, i + d)); show(); };
  card.addEventListener("click", () => card.classList.toggle("is-flipped"));
  prev.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));
  state.keyHandler = (e) => {
    if (e.key === "ArrowRight") go(1);
    else if (e.key === "ArrowLeft") go(-1);
    else if (e.key === " ") { e.preventDefault(); card.classList.toggle("is-flipped"); }
  };
  out.append(prog, card, el("p", "hint", "Click or press Space to flip. Use the arrow keys to move."), nav);
  show();
}

function renderQuiz(out, items) {
  let i = 0, score = 0;
  const wrap = el("div", "q");
  out.appendChild(wrap);
  function show() {
    wrap.replaceChildren();
    const q = items[i];
    const head = el("div", "qhead");
    head.append(el("span", null, `សំណួរ ${i + 1} / ${items.length}`), el("span", null, `Score ${score}`));
    const prog = el("div", "progress"), bar = el("span");
    bar.style.width = `${(i / items.length) * 100}%`;
    prog.appendChild(bar);
    wrap.append(head, prog, el("h3", null, q.question));
    const expl = el("div", "expl hidden", q.explanation);
    const next = el("button", "btn main hidden", i === items.length - 1 ? "មើលពិន្ទុ" : "បន្ទាប់ ");
    next.type = "button";
    const btns = q.options.map((o, j) => {
      const b = el("button", "opt", `${"ABCD"[j]}. ${o}`);
      b.type = "button";
      b.addEventListener("click", () => {
        btns.forEach((x) => (x.disabled = true));
        btns[q.answer_index].classList.add("right");
        if (j === q.answer_index) score++; else b.classList.add("wrong");
        expl.classList.remove("hidden");
        next.classList.remove("hidden");
        next.focus();
      });
      wrap.appendChild(b);
      return b;
    });
    next.addEventListener("click", () => { i++; i < items.length ? show() : finish(); });
    wrap.append(expl, next);
  }
  function finish() {
    wrap.replaceChildren();
    const pct = Math.round((score / items.length) * 100);
    const ring = el("div", "ring");
    ring.style.setProperty("--p", pct);
    ring.appendChild(el("span", null, `${pct}%`));
    const msg = pct >= 80 ? "ល្អឥតខ្ចោះ! Excellent!" : pct >= 50 ? "ល្អ! Good job. Review and try again." : "បន្តព្យាយាម! Keep practicing.";
    const again = el("button", "btn main", "ធ្វើម្តងទៀត Retry");
    again.type = "button";
    again.addEventListener("click", () => { i = 0; score = 0; show(); });
    const box = el("div", "score");
    box.append(el("h3", null, `ពិន្ទុ Score: ${score} / ${items.length}`), ring, el("p", null, msg), again);
    wrap.appendChild(box);
  }
  show();
}

function renderPractice(out, items) {
  const all = el("button", "btn", "បើកទាំងអស់ Open all");
  all.type = "button";
  const list = items.map((q, i) => {
    const d = el("details");
    d.appendChild(el("summary", null, `${i + 1}. ${q.question}`));
    const a = el("p");
    a.append(el("strong", null, "ចម្លើយ: "), document.createTextNode(q.answer));
    d.append(a, el("div", "expl", q.explanation));
    out.appendChild(d);
    return d;
  });
  let open = false;
  all.addEventListener("click", () => {
    open = !open;
    list.forEach((d) => (d.open = open));
    all.textContent = open ? "បិទទាំងអស់ Close all" : "បើកទាំងអស់ Open all";
  });
  $("actions").replaceChildren(all);
}

/* ---------- API call ---------- */
let timer;
function setBusy(busy) {
  state.busy = busy;
  $("go").disabled = busy;
  $("loading").classList.toggle("hidden", !busy);
  clearInterval(timer);
  if (busy) {
    $("result").classList.remove("hidden");
    const t0 = Date.now();
    $("elapsed").textContent = "0s";
    timer = setInterval(() => ($("elapsed").textContent = `${Math.round((Date.now() - t0) / 1000)}s`), 500);
    $("output").replaceChildren();
    $("actions").replaceChildren();
    $("info").classList.add("hidden");
  }
}

async function generate() {
  if (state.busy) return;
  showError("");
  const text = lesson.value.trim();
  if (text.length < MIN_CHARS) {
    lesson.focus();
    return showError("សូមបញ្ចូលមេរៀនយ៉ាងហោចណាស់ ២០ តួអក្សរ។ Enter at least 20 characters.");
  }
  state.keyHandler = null;
  setBusy(true);
  const ctrl = (state.ctrl = new AbortController());
  const kill = setTimeout(() => ctrl.abort("timeout"), 150000);
  try {
    const res = await fetch("/api/study", {
      method: "POST",
      signal: ctrl.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task: state.task, text, count: clampCount($("count").value), language: $("language").value }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Request failed.");
    setBusy(false);
    const out = $("output");
    out.replaceChildren();
    $("info").classList.remove("hidden");
    $("info").textContent = `${data.model} · ${data.seconds}s` + (data.truncated ? " · used the first 8000 characters" : "");
    if (state.task === "flashcards") renderFlashcards(out, data.result);
    else if (state.task === "quiz") renderQuiz(out, data.result);
    else if (state.task === "practice") renderPractice(out, data.result);
    else renderText(out, data.result);
    $("result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    setBusy(false);
    renderEmpty();
    if (ctrl.signal.reason === "cancel") return;
    showError(ctrl.signal.reason === "timeout" ? "Timed out. Check your internet and try again." : e.message || "Network error.");
  } finally {
    clearTimeout(kill);
    setBusy(false);
  }
}
$("go").addEventListener("click", generate);
$("cancel").addEventListener("click", () => state.ctrl && state.ctrl.abort("cancel"));
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); generate(); return; }
  if (state.keyHandler && !/^(TEXTAREA|INPUT|SELECT)$/.test(document.activeElement.tagName)) state.keyHandler(e);
});

renderEmpty();