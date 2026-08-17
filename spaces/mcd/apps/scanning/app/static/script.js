// Prefix the app is mounted under (e.g. "/scanning"), injected by the template
// as window.ROOT_PATH. Empty string in local dev, so all paths stay bare.
const API_BASE = (window.ROOT_PATH || "").replace(/\/$/, "");
function u(path) { return API_BASE + path; }

const ZONES = ["Kitchen - fry station", "Kitchen - grill station", "Beverage station", "Front counter", "Back room"];

const EQUIPMENT_ART = {
  "Deep fryer": '<rect x="28" y="34" width="44" height="40" rx="4" fill="#AEB1B5"/><rect x="28" y="34" width="44" height="10" rx="4" fill="#8A8D90"/><rect x="33" y="18" width="6" height="18" rx="2" fill="#6B6E71"/><rect x="61" y="18" width="6" height="18" rx="2" fill="#6B6E71"/><circle cx="40" cy="39" r="2.5" fill="#DA291C"/><circle cx="50" cy="39" r="2.5" fill="#FFC72C"/><rect x="30" y="74" width="40" height="6" rx="2" fill="#6B6E71"/>',
  "Fry holding bin": '<rect x="24" y="42" width="52" height="30" rx="4" fill="#B7B9BC"/><rect x="24" y="42" width="52" height="8" rx="4" fill="#8A8D90"/><rect x="44" y="22" width="12" height="20" rx="3" fill="#DA291C"/><ellipse cx="50" cy="22" rx="9" ry="4" fill="#FFC72C"/><rect x="28" y="72" width="44" height="5" rx="2" fill="#6B6E71"/>',
  "Ice cream machine": '<rect x="26" y="26" width="48" height="46" rx="6" fill="#D8D9D6"/><rect x="26" y="26" width="48" height="14" rx="6" fill="#8A8D90"/><rect x="36" y="58" width="6" height="14" rx="2" fill="#B7B9BC"/><rect x="58" y="58" width="6" height="14" rx="2" fill="#B7B9BC"/><path d="M50 40c3 0 5 2.5 5 5.5s-2 5-5 8.5c-3-3.5-5-5.5-5-8.5s2-5.5 5-5.5z" fill="#FFF6E8"/><circle cx="34" cy="33" r="2" fill="#DA291C"/><circle cx="42" cy="33" r="2" fill="#FFC72C"/>',
  "Beverage dispenser": '<rect x="24" y="24" width="52" height="34" rx="4" fill="#3C7CB5"/><rect x="24" y="24" width="52" height="10" rx="4" fill="#2C5C8A"/><rect x="30" y="58" width="6" height="10" fill="#8A8D90"/><rect x="46" y="58" width="6" height="10" fill="#8A8D90"/><rect x="62" y="58" width="6" height="10" fill="#8A8D90"/><path d="M40 70 h20 l-3 12 h-14 z" fill="#FFFFFF" stroke="#B7B9BC" stroke-width="2"/>',
  "Griddle": '<rect x="20" y="40" width="60" height="24" rx="3" fill="#5A5C5E"/><rect x="20" y="60" width="60" height="6" rx="2" fill="#3A3B3C"/><rect x="24" y="44" width="10" height="3" fill="#7A7C7E"/><rect x="40" y="44" width="10" height="3" fill="#7A7C7E"/><rect x="56" y="44" width="10" height="3" fill="#7A7C7E"/><rect x="20" y="30" width="60" height="6" rx="2" fill="#DA291C"/>',
  "Exhaust hood": '<path d="M28 24 h44 l8 20 h-60 z" fill="#B7B9BC"/><rect x="44" y="44" width="12" height="26" fill="#8A8D90"/><rect x="32" y="30" width="8" height="4" fill="#6B6E71"/><rect x="44" y="30" width="8" height="4" fill="#6B6E71"/><rect x="56" y="30" width="8" height="4" fill="#6B6E71"/>',
  "Fry warmer": '<rect x="26" y="30" width="48" height="42" rx="4" fill="#C7C9CC"/><rect x="26" y="30" width="48" height="8" rx="4" fill="#FFC72C"/><rect x="30" y="46" width="40" height="4" fill="#8A8D90"/><rect x="30" y="56" width="40" height="4" fill="#8A8D90"/><rect x="46" y="72" width="8" height="4" rx="2" fill="#6B6E71"/>',
  "Walk-in freezer unit": '<rect x="30" y="20" width="40" height="56" rx="4" fill="#8FA6B8"/><rect x="30" y="20" width="40" height="56" rx="4" fill="none" stroke="#5F7A8C" stroke-width="3"/><circle cx="62" cy="48" r="4" fill="#2C5C8A"/><path d="M40 30 v10 M46 28 v14" stroke="#FFFFFF" stroke-width="2" opacity="0.7"/>',
  "POS terminal": '<rect x="28" y="24" width="44" height="32" rx="4" fill="#2C2C2A"/><rect x="32" y="28" width="36" height="22" rx="2" fill="#4A90D9"/><rect x="42" y="56" width="16" height="6" fill="#6B6E71"/><rect x="34" y="62" width="32" height="6" rx="3" fill="#8A8D90"/><rect x="60" y="24" width="10" height="8" rx="2" fill="#DA291C"/>',
  "Milkshake mixer": '<rect x="34" y="22" width="10" height="26" rx="3" fill="#6B6E71"/><circle cx="39" cy="20" r="5" fill="#8A8D90"/><path d="M30 66 h26 l-4 14 h-18 z" fill="#FFFFFF" stroke="#B7B9BC" stroke-width="2"/><rect x="26" y="58" width="42" height="10" rx="4" fill="#DA291C"/>',
  "Grill": '<rect x="20" y="38" width="60" height="28" rx="3" fill="#4A4C4E"/><rect x="24" y="44" width="52" height="3" fill="#2C2C2A"/><rect x="24" y="52" width="52" height="3" fill="#2C2C2A"/><rect x="24" y="60" width="52" height="3" fill="#2C2C2A"/><rect x="20" y="28" width="60" height="6" rx="2" fill="#FFC72C"/>',
  "_default": '<rect x="26" y="30" width="48" height="40" rx="6" fill="#B7B9BC"/><circle cx="50" cy="50" r="10" fill="#8A8D90"/>'
};
function equipmentPhoto(type) {
  const icon = EQUIPMENT_ART[type] || EQUIPMENT_ART["_default"];
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">' +
    '<rect width="100" height="100" fill="#EDEBE4"/>' + icon + '</svg>';
  return "data:image/svg+xml;utf8," + encodeURIComponent(svg);
}

// Server-backed; this is a local copy so renders don't need a round trip.
let inventory = [];

function api(path, method, body) {
  return fetch(u(path), {
    method: method || "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined
  }).then(r => r.json().then(d => r.ok ? d : Promise.reject(new Error(d.detail || r.status))));
}

// Turn the stored filename back into a URL so it.photo works everywhere.
function fromServer(it) {
  it.photo = it.photo ? u("/captures/" + it.photo) : null;
  it.equipmentId = it.equipment_id || null;
  return it;
}

function loadInventory() {
  return api("/api/inventory")
    .then(d => { inventory = (d.items || []).map(fromServer); })
    .catch(() => { inventory = []; showToast("Could not reach the server"); });
}

// Update locally first so the UI stays snappy, then write through.
function saveItem(item, changes) {
  Object.assign(item, changes);
  if (!item.id) return Promise.resolve(item);
  return api("/api/inventory/" + item.id, "PATCH", changes)
    .catch(() => showToast("Could not save - check the server"));
}

let screen = "dashboard";
let pendingItems = [];
let nextIndex = 0;
let scanning = false;
let detectionTimer = null;
let cameraStream = null;
let selectedIndex = null;
let editing = false;
let toastTimer = null;
let zoneFilter = "All";
const app = document.getElementById("app");
const bar = document.getElementById("action-bar");
const toast = document.getElementById("toast");

function showToast(message) {
  if (!toast) return;
  const header = document.getElementById("header");
  const headerVisible = header && header.style.display !== "none";
  const topOffset = headerVisible ? Math.max(16, Math.round(header.getBoundingClientRect().bottom + 10)) : 16;
  toast.style.top = topOffset + "px";
  toast.innerHTML =
    '<span style="width:22px;height:22px;border-radius:50%;background:var(--success-solid);display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
      '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 12 9 18 20 6"></polyline></svg>' +
    '</span>' +
    '<span>' + message + '</span>';
  clearTimeout(toastTimer);
  toast.classList.add("show");
  toastTimer = setTimeout(() => { toast.classList.remove("show"); }, 3000);
}
const CONF_LABEL = { high: "Looks good", medium: "Double-check", low: "Couldn't read clearly" };
const CONF_ICON = { high: "ti-check", medium: "ti-alert-triangle", low: "ti-alert-circle" };
const CONF_COLOR = { high: "var(--success-solid)", medium: "var(--warning-solid)", low: "var(--danger-solid)" };

function outlinePill(color, icon, text) {
  return '<span class="pill" style="border:1px solid ' + color + ';color:' + color +
    ';background:transparent;"><i class="ti ' + icon + '"></i>' + text + "</span>";
}

function pill(bg, icon, label) { return '<span class="pill" style="background:' + bg + ';"><i class="ti ' + icon + '"></i>' + label + '</span>'; }
function badge(level) { return pill(CONF_COLOR[level], CONF_ICON[level], CONF_LABEL[level]); }
function statusBadge(status) { return status === "Verified" ? pill("var(--success-solid)", "ti-check", "Verified") : pill("var(--danger-solid)", "ti-alert-triangle", "Needs review"); }
function missingDetails(it) {
  if (it.type !== "Other") return false;
  return !(it.otherType && it.otherType.trim()) ||
         !(it.model && it.model.trim() && it.model.indexOf("not detected") === -1);
}

function needsReview(it) { return [it.typeConf, it.modelConf].includes("low") || it.type === "Other"; }
let photoSeq = 0;      // which uploaded/captured photo an item came from
let CATEGORIES = [];
let CATALOG = {};          // category -> [{mfr, model}]
fetch(u("/api/catalog")).then(r => r.json())
  .then(d => {
    CATALOG = d.categories || {};
    CATEGORIES = Object.keys(CATALOG);
  })
  .catch(() => { CATEGORIES = []; });
function typeOptions(sel) {
  const list = CATEGORIES.slice();
  if (list.indexOf("Other") === -1) list.push("Other");
  if (sel && list.indexOf(sel) === -1) list.unshift(sel);
  return list.map(t => '<option' + (t === sel ? " selected" : "") + '>' + t + '</option>').join("");
}
function zoneOptions(sel) { return ZONES.map(z => '<option' + (z === sel ? " selected" : "") + '>' + z + '</option>').join(""); }
function stopCamera() { if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; } }
function cameraFallback(message) {
  const video = document.getElementById("camera-video");
  const fallback = document.getElementById("camera-fallback");
  if (video) video.style.display = "none";
  if (!fallback) return;
  fallback.style.display = "flex";
  const note = fallback.querySelector(".cam-note");
  if (note) note.textContent = message;
}

function startCamera() {
  const video = document.getElementById("camera-video");
  const fallback = document.getElementById("camera-fallback");
  if (!video || !fallback) return;

  if (!window.isSecureContext && location.hostname !== "localhost"
      && location.hostname !== "127.0.0.1") {
    cameraFallback("Camera needs a secure page. Open http://localhost:" +
                   (location.port || "8000") + " (not " + location.hostname +
                   "), or use Upload photos.");
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraFallback("This browser has no camera API here. Use Upload photos.");
    return;
  }

  navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false })
    .then(stream => {
      cameraStream = stream;
      video.srcObject = stream;
      video.style.display = "block";
      fallback.style.display = "none";
    })
    .catch(err => {
      const why = {
        NotAllowedError: "Camera permission was blocked. Allow it in the address bar, then reopen this screen.",
        NotFoundError: "No camera found on this device.",
        NotReadableError: "The camera is in use by another app.",
        OverconstrainedError: "No rear camera available; try again or use Upload photos.",
      }[err && err.name] || "Camera unavailable (" + ((err && err.name) || "unknown") + ").";
      cameraFallback(why + " You can still use Upload photos.");
    });
}
function formatHeaderDate() {
  const d = new Date();
  const dateStr = d.toLocaleDateString("en-US", { weekday: "short", month: "long", day: "numeric", year: "numeric" });
  const timeStr = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  return dateStr + " • " + timeStr;
}
function updateChrome() {
  const showChrome = screen === "dashboard" || screen === "detail" || screen === "add" || screen === "needsReview";
  document.getElementById("header").style.display = showChrome ? "" : "none";
  document.querySelector(".content").style.paddingTop = showChrome ? "18px" : "calc(18px + env(safe-area-inset-top))";
  const title = screen === "detail" && inventory[selectedIndex] ? inventory[selectedIndex].type : screen === "add" ? "Add equipment" : screen === "needsReview" ? "Needs review" : "Equipment inventory";
  document.getElementById("header-title").textContent = title;
  document.getElementById("header-sub").textContent = formatHeaderDate();
}
function setActionBar(html, direction) {
  if (!html) { bar.style.display = "none"; bar.innerHTML = ""; return; }
  bar.style.display = "flex";
  bar.style.flexDirection = direction || "row";
  bar.innerHTML = html;
}
let lastScreen = null;

function render() {
  const changedScreen = screen !== lastScreen;
  const keepScroll = changedScreen ? 0 : window.scrollY;
  lastScreen = screen;
  updateChrome();
  if (screen === "dashboard") renderDashboard();
  else if (screen === "review") renderReview();
  else if (screen === "detail") renderDetail();
  else if (screen === "add") renderAddEquipment();
  else if (screen === "needsReview") renderNeedsReview();
  if (changedScreen) window.scrollTo(0, 0);
  else window.scrollTo(0, keepScroll);
}
function thumb(it, size) {
  return it.photo ?
    '<img src="' + it.photo + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:10px;display:block;flex-shrink:0;" />' :
    '<div style="width:' + size + 'px;height:' + size + 'px;border-radius:10px;background:var(--page-bg);display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="ti ti-tools" style="font-size:' + Math.round(size * 0.5) + 'px;color:var(--ink-muted);"></i></div>';
}

function renderDashboard() {
  const needReview = inventory.filter(i => i.status === "Needs review").length;
  const pct = inventory.length ? Math.round((needReview / inventory.length) * 100) : 0;
  const scannedToday = inventory.filter(i => i.scanned).length;
  app.innerHTML =
    '<div class="section-header"><span class="section-title"><i class="ti ti-clipboard-list"></i>Equipment overview</span><span class="section-meta">Updated just now</span></div>' +
    '<div class="metric-grid" style="grid-template-columns:repeat(2,1fr);">' +
      '<div class="metric-card"><p class="metric-label">Logged</p><p class="metric-value">' + inventory.length + '</p>' + (scannedToday > 0 ? '<span style="font-size:11px;color:var(--success-text);font-weight:700;display:flex;align-items:center;gap:3px;"><i class="ti ti-arrow-up-right" style="font-size:12px;"></i>+' + scannedToday + ' today</span>' : '<span style="font-size:11px;color:var(--ink-muted);">no change</span>') + '</div>' +
      '<div class="metric-card" id="needs-review-tile" style="cursor:pointer;"><p class="metric-label">Needs review</p><p class="metric-value">' + pct + '%</p>' + (needReview > 0 ? pill("var(--warning-solid)", "ti-alert-triangle", "Attention") : pill("var(--success-solid)", "ti-check", "All clear")) + '</div>' +
    '</div>' +
    '<div class="section-header"><span class="section-title"><i class="ti ti-list-details"></i>All equipment</span><span style="display:flex;align-items:center;gap:10px;"><span class="section-meta">' + inventory.length + ' items</span><button id="add-equipment-btn" class="icon-btn" aria-label="Add equipment" style="background:var(--brand-yellow);width:28px;height:28px;min-height:28px;min-width:28px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1A1A1A" stroke-width="3" stroke-linecap="round"><line x1="12" y1="4" x2="12" y2="20"></line><line x1="4" y1="12" x2="20" y2="12"></line></svg></button></span></div>' +
    '<div class="card">' +
      '<input id="search-input" type="text" placeholder="Search by type, model, or location" style="margin-bottom:10px;" />' +
      '<div id="zone-pills" style="display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;margin-bottom:12px;"></div>' +
      '<div id="inventory-list-container"></div>' +
    '</div>';
  const search = document.getElementById("search-input");
  search.oninput = () => renderInventoryList(search.value);
  renderZonePills();
  renderInventoryList("");
  document.getElementById("add-equipment-btn").onclick = () => { screen = "add"; render(); };
  document.getElementById("needs-review-tile").onclick = () => { screen = "needsReview"; render(); };
  setActionBar('<button id="start-scan" class="btn-primary"><i class="ti ti-camera"></i>Start equipment scan</button>');
  document.getElementById("start-scan").onclick = enterScan;
}

function renderZonePills() {
  const container = document.getElementById("zone-pills");
  if (!container) return;
  const options = ["All"].concat(ZONES);
  container.innerHTML = options.map(z =>
    '<button type="button" class="zone-pill' + (zoneFilter === z ? " active" : "") + '" data-zone="' + z + '">' + z + '</button>'
  ).join("");
  container.querySelectorAll("[data-zone]").forEach(btn => {
    btn.onclick = () => {
      zoneFilter = btn.getAttribute("data-zone");
      renderZonePills();
      const search = document.getElementById("search-input");
      renderInventoryList(search ? search.value : "");
    };
  });
}

function renderInventoryList(query) {
  const q = query.trim().toLowerCase();
  const filtered = inventory.filter(i => {
    const matchesQuery = !q || i.type.toLowerCase().includes(q) || i.model.toLowerCase().includes(q) || i.zone.toLowerCase().includes(q);
    const matchesFilter = zoneFilter === "All" ? true : zoneFilter === "Needs review" ? i.status === "Needs review" : i.zone === zoneFilter;
    return matchesQuery && matchesFilter;
  });
  const container = document.getElementById("inventory-list-container");
  container.innerHTML =
    '<div class="item-list">' + filtered.map(i => {
      const idx = inventory.indexOf(i);
      return '<div class="item-row" data-idx="' + idx + '">' + thumb(i, 46) +
        '<div class="item-row-text"><p class="item-row-title">' + i.type + '</p><p class="item-row-sub">' + i.model + ' &middot; ' + i.zone + '</p></div>' +
        statusBadge(i.status) +
      '</div>';
    }).join("") + '</div>' +
    (filtered.length === 0 ? '<p style="font-size:13px;color:var(--ink-muted);text-align:center;padding:12px 0;">No matches</p>' : "");
  container.querySelectorAll("[data-idx]").forEach(row => {
    row.onclick = () => { selectedIndex = Number(row.getAttribute("data-idx")); editing = false; screen = "detail"; render(); };
  });
}

function renderNeedsReview() {
  const entries = inventory.map((it, idx) => ({ it, idx })).filter(e => e.it.status === "Needs review");
  const arrowLeft = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>';
  const checkIcon = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 12 9 18 20 6"></polyline></svg>';
  let html = '<button id="back-btn" class="icon-btn" style="margin-bottom:12px;">' + arrowLeft + '</button>';
  if (entries.length === 0) {
    html +=
      '<div class="card" style="text-align:center;padding:2.5rem 1.25rem;">' +
        '<div style="width:56px;height:56px;border-radius:50%;background:var(--success-tint);display:flex;align-items:center;justify-content:center;margin:0 auto 14px;"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="var(--success-solid)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 12 9 18 20 6"></polyline></svg></div>' +
        '<p style="font-size:15px;font-weight:700;margin:0 0 4px;">Nothing needs review</p>' +
        '<p style="font-size:13px;color:var(--ink-secondary);margin:0;">Every item in inventory has been verified.</p>' +
      '</div>';
  } else {
    html += '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 12px;">' + entries.length + ' item' + (entries.length === 1 ? "" : "s") + ' need review</p>';
    html += entries.map(({ it, idx }) =>
      '<div class="card">' +
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">' + thumb(it, 52) +
          '<span style="flex:1;min-width:0;">' +
            '<span style="font-size:16px;font-weight:700;display:block;">' + it.type +
              (it.fromPhoto ? '<span style="font-size:10px;font-weight:700;color:var(--ink-muted);background:var(--page-bg);border-radius:6px;padding:2px 6px;margin-left:6px;vertical-align:middle;">photo ' + it.fromPhoto + '</span>' : "") +
            '</span>' +
            (it.why ? '<span style="font-size:11px;color:var(--ink-secondary);">' + it.why + '</span>' : "") +
            (it.source === "read_from_unit"
              ? '<span style="font-size:10px;font-weight:700;color:var(--warning-text);background:var(--warning-tint);border-radius:6px;padding:2px 6px;margin-left:6px;">read from unit - not in catalog</span>'
              : "") +
          '</span>' +
        '</div>' +
        '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 5px;font-weight:600;">Model</p>' +
        '<input type="text" data-fix-field="model" data-idx="' + idx + '" value="' + String(it.model).replace(/"/g, "&quot;") + '" style="margin-bottom:14px;" />' +
        '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 5px;font-weight:600;">Location</p>' +
        '<select data-fix-zone="' + idx + '" style="margin-bottom:14px;">' + zoneOptions(it.zone) + '</select>' +
        '<button data-mark-verified="' + idx + '" class="btn-secondary" style="width:100%;min-height:52px;border-radius:999px;font-weight:700;font-size:15px;display:flex;align-items:center;justify-content:center;gap:6px;">' + checkIcon + 'Mark as verified</button>' +
      '</div>'
    ).join("");
  }
  app.innerHTML = html;
  document.getElementById("back-btn").onclick = () => { screen = "dashboard"; render(); };
  app.querySelectorAll("[data-fix-field]").forEach(inp => {
    inp.oninput = () => { inventory[Number(inp.getAttribute("data-idx"))][inp.getAttribute("data-fix-field")] = inp.value; };
    inp.onchange = () => {
      const it = inventory[Number(inp.getAttribute("data-idx"))];
      saveItem(it, { [inp.getAttribute("data-fix-field")]: inp.value });
    };
  });
  app.querySelectorAll("[data-fix-zone]").forEach(sel => {
    sel.onchange = () => {
      const it = inventory[Number(sel.getAttribute("data-fix-zone"))];
      saveItem(it, { zone: sel.value });
    };
  });
  app.querySelectorAll("[data-mark-verified]").forEach(btn => {
    btn.onclick = () => {
      const idx = Number(btn.getAttribute("data-mark-verified"));
      const type = inventory[idx].type;
      saveItem(inventory[idx], { status: "Verified" }).then(() => {
        showToast(type + " marked as verified");
        renderNeedsReview();
      });
    };
  });
  setActionBar("");
}

function renderAddEquipment() {
  app.innerHTML =
    '<button id="back-btn" class="icon-btn" style="margin-bottom:12px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg></button>' +
    '<div class="card">' +
      '<img id="add-preview" src="' + equipmentPhoto("") + '" style="width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:16px;margin-bottom:14px;display:block;" />' +
      '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 4px;font-weight:600;">Type</p><input id="add-type" type="text" placeholder="e.g. Deep fryer" style="margin-bottom:12px;" />' +
      '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 4px;font-weight:600;">Model</p><input id="add-model" type="text" placeholder="e.g. Frymaster FPRE217" style="margin-bottom:12px;" />' +
      '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 4px;font-weight:600;">Location</p><select id="add-zone">' + zoneOptions(ZONES[0]) + '</select>' +
    '</div>';
  document.getElementById("back-btn").onclick = () => { screen = "dashboard"; render(); };
  document.getElementById("add-type").oninput = (e) => {
    document.getElementById("add-preview").src = equipmentPhoto(e.target.value.trim());
  };
  setActionBar('<button id="cancel-add" class="btn-secondary">Cancel</button><button id="save-add" class="btn-primary"><i class="ti ti-check"></i>Add equipment</button>');
  document.getElementById("cancel-add").onclick = () => { screen = "dashboard"; render(); };
  document.getElementById("save-add").onclick = () => {
    const typeInput = document.getElementById("add-type");
    const type = typeInput.value.trim();
    if (!type) { typeInput.focus(); return; }
    const model = document.getElementById("add-model").value.trim() || "Not specified";
    const zone = document.getElementById("add-zone").value;
    api("/api/inventory", "POST", [{ type, model, zone, status: "Verified", scanned: false }])
      .then(d => {
        inventory = (d.items || []).map(fromServer).concat(inventory);
        screen = "dashboard";
        render();
        showToast(type + " added to inventory");
      })
      .catch(() => showToast("Could not save - check the server"));
  };
}

function enterScan() {
  window.scrollTo(0, 0);
  screen = "scan";
  pendingItems = [];
  photoSeq = 0;
  nextIndex = 0;
  scanning = true;
  updateChrome();
  app.innerHTML =
    '<div class="scan-header"><span class="scan-title" style="display:flex;align-items:center;gap:6px;"><span class="live-dot"></span><span id="scan-status-label">Ready - tap the shutter</span></span><button id="exit-scan" class="icon-btn" aria-label="Exit scan"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button></div>' +
    '<div class="viewfinder">' +
      '<video id="camera-video" autoplay muted playsinline style="width:100%;height:100%;object-fit:cover;display:none;"></video>' +
      '<div id="camera-fallback" style="display:none;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#fff;gap:8px;padding:20px;text-align:center;">' +
        '<i class="ti ti-camera-off" style="font-size:28px;"></i>' +
        '<p class="cam-note" style="font-size:12px;margin:0;padding:0 12px;line-height:1.5;color:#ddd;">Camera unavailable or permission not granted</p>' +
      '</div>' +
      '<img id="camera-still" alt="" style="display:none;position:absolute;inset:0;width:100%;height:100%;object-fit:cover;" />' +
      '<div id="camera-cover" style="display:none;position:absolute;inset:0;background:#1A1A1A;color:#8A8A85;flex-direction:column;align-items:center;justify-content:center;gap:10px;">' +
        '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>' +
        '<span style="font-size:12px;font-weight:600;">Camera paused while analysing</span>' +
      '</div>' +
      '<div id="capture-flash"></div>' +
      '<div id="detect-label" class="detect-label"></div>' +
    '</div>' +
    '<p style="font-size:12px;color:var(--ink-secondary);margin:10px 0 4px;">Nothing is captured automatically. Tap the shutter to capture a station, or use the upload button to pick several photos at once. Everything lands in one list.</p>' +
    '<div class="zone-row"><label for="scan-zone">Station</label><select id="scan-zone">' + zoneOptions(ZONES[0]) + '</select></div>' +
    '<div class="shutter-row">' +
      '<button id="shutter" class="cap-btn cap-primary">' +
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>' +
        'Capture photo</button>' +
      '<button id="pick-photo" class="cap-btn cap-secondary">' +
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>' +
        'Upload photos</button>' +
    '</div>' +
    '<input type="file" id="photo-file" accept="image/*" multiple style="display:none;" />' +
    '<div id="capture-tray" class="capture-tray"></div>';
  document.getElementById("exit-scan").onclick = exitScan;
  document.getElementById("shutter").onclick = captureAndDetect;
  document.getElementById("pick-photo").onclick = () => document.getElementById("photo-file").click();
  document.getElementById("photo-file").onchange = e => {
    const files = Array.from(e.target.files || []);
    e.target.value = "";
    if (files.length) detectBatch(files);
  };
  startCamera();
  setActionBar("");
  renderTray();
}

function exitScan() {
  scanning = false;
  if (detectionTimer) clearTimeout(detectionTimer);
  stopCamera();
  pendingItems = [];
  screen = "dashboard";
  render();
}

let waitingForReview = false;
let stagedItems = [];

function revealStaged() {
  dedupeStaged();
  procHide();
  unfreezePreview();
  stagedItems.forEach(item => {
    pendingItems.push(item);
    renderTray(true);
    const container = document.getElementById("capture-tray");
    flyToTray(item, container ? container.lastElementChild : null);
  });
  stagedItems = [];
  updateScanActionBar();
}

function stopScanningAndReview() {
  scanning = false;
  if (detectionTimer) clearTimeout(detectionTimer);
  stopCamera();
  if (identifyPending()) {
    waitingForReview = true;
    procShow("Identifying models");
    procUpdate(70, "Comparing against reference images...");
    return;
  }
  screen = "review";
  render();
}

function grabFrame() {
  const video = document.getElementById("camera-video");
  if (video && video.style.display !== "none" && video.videoWidth) {
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.8);
  }
  return null;
}


function freezePreview(dataUrl) {
  const v = document.getElementById("camera-video");
  const still = document.getElementById("camera-still");
  const cover = document.getElementById("camera-cover");
  if (cover) cover.style.display = "flex";
  if (dataUrl) {
    if (still) { still.src = dataUrl; still.style.display = "block"; }
    const thumb = document.getElementById("proc-thumb");
    if (thumb) { thumb.src = dataUrl; thumb.style.display = "block"; }
  }

  if (v) { try { v.pause(); } catch (e) {} }
}

function unfreezePreview() {
  const v = document.getElementById("camera-video");
  const still = document.getElementById("camera-still");
  const cover = document.getElementById("camera-cover");
  if (cover) cover.style.display = "none";
  if (still) { still.style.display = "none"; still.removeAttribute("src"); }
  const thumb = document.getElementById("proc-thumb");
  if (thumb) { thumb.style.display = "none"; thumb.removeAttribute("src"); }
  if (v && v.srcObject) { try { v.play(); } catch (e) {} }
}

function procShow(title) {
  const p = document.getElementById("proc");
  document.getElementById("proc-title").textContent = title || "Analysing photo";
  document.getElementById("proc-sub").innerHTML = "Looking for equipment...";
  document.getElementById("proc-fill").style.width = "0%";
  document.getElementById("proc-count").textContent = "";
  if (p) p.classList.add("on");
}
function procUpdate(pct, sub, count) {
  const f = document.getElementById("proc-fill");
  if (f) f.style.width = Math.max(4, Math.min(100, pct)) + "%";
  if (sub !== undefined) document.getElementById("proc-sub").innerHTML = sub;
  if (count !== undefined) document.getElementById("proc-count").textContent = count;
}
function procFound() {
  const el = document.getElementById("proc-sub");
  if (!el) return;
  el.innerHTML = pendingItems.map(it => '<span class="found-chip">' + it.type + "</span>").join("")
    || "Identifying...";
}
function procHide() {
  const p = document.getElementById("proc");
  if (p) p.classList.remove("on");
}

function setShutter(enabled) {
  const b = document.getElementById("shutter");
  if (b) b.disabled = !enabled;
}

function setScanStatus(text) {
  const label = document.getElementById("scan-status-label");
  if (label) label.textContent = text;
}

// Must match SOURCE_SIDE in .env - crops are cut from whatever we upload,
// and at 1024 a control-panel badge lands ~30px wide and unreadable.
const UPLOAD_MAX_SIDE = 3072;

function downscale(dataUrl, cb) {
  let settled = false;
  const finish = v => { if (!settled) { settled = true; cb(v); } };
  const img = new Image();
  img.onload = () => {
    try {
      const sc = Math.min(1, UPLOAD_MAX_SIDE / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * sc); c.height = Math.round(img.height * sc);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      finish(c.toDataURL("image/jpeg", 0.85));
    } catch (e) { finish(dataUrl); }
  };
  img.onerror = () => finish(dataUrl);
  setTimeout(() => finish(dataUrl), 3000);      // backstop if decode stalls
  img.src = dataUrl;
}

function isHeicFile(file) {
  const n = (file.name || "").toLowerCase();
  if (n.endsWith(".heic") || n.endsWith(".heif")) return true;
  return (file.type || "").indexOf("hei") !== -1;
}

function readAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const rd = new FileReader();
    rd.onload = () => resolve(rd.result);
    rd.onerror = () => reject(new Error("could not read " + file.name));
    rd.readAsDataURL(file);
  });
}

function detectBatch(files) {
  if (!scanning) return;
  setShutter(false);
  let done = 0, failed = 0;
  const total = files.length;

  const POOL = 3;
  let cursor = 0;
  procShow(total === 1 ? "Analysing photo" : "Analysing " + total + " photos");
  freezePreview(null);          // pause and cover the camera straight away

  if (!isHeicFile(files[0])) {
    readAsDataUrl(files[0]).then(u => freezePreview(u)).catch(() => {});
  }
  const tick = () => {
    const n = done + failed;
    setScanStatus("Analysing " + Math.min(n + 1, total) + " of " + total + "...");
    procUpdate(total ? (n / total) * 100 : 0, undefined,
               n + " of " + total + " done  ·  " + pendingItems.length + " assets found");
  };
  const runOne = () => {
    if (cursor >= total) return Promise.resolve();
    const file = files[cursor++];
    const heic = isHeicFile(file);
    return readAsDataUrl(file)
      .then(url => heic ? url                       // server converts it
                        : new Promise(res => downscale(url, res)))
      .then(small => detectFrame(small, true))
      .then(() => { done += 1; tick(); })
      .catch(() => { failed += 1; tick(); })
      .then(runOne);
  };
  tick();
  Promise.all(Array.from({ length: Math.min(POOL, total) }, runOne)).then(() => {
    if (identifyPending()) {
      procUpdate(90, "Identifying models...");
    } else {
      setTimeout(() => { procHide(); unfreezePreview(); }, 300);
    }
    setShutter(true);
    setScanStatus(failed
      ? ("Processed " + (total - failed) + " of " + total + " - " + failed + " failed")
      : ("Captured " + pendingItems.length + " - next station, or done below"));
    if (failed) showDetectLabel(failed + " photo(s) could not be processed");
  });
}

function captureAndDetect() {
  const framePhoto = grabFrame();
  if (!framePhoto) { showDetectLabel("No camera - use the Upload photos button"); return; }
  freezePreview(framePhoto);
  detectFrame(framePhoto).then(unfreezePreview, unfreezePreview);
}

function detectFrame(framePhoto, inBatch) {
  if (!scanning) return Promise.resolve();
  if (!inBatch) { setShutter(false); setScanStatus("Detecting...");
                  procShow("Analysing photo"); procUpdate(35, "Looking for equipment..."); }
  return fetch(u("/api/detect"), { method: "POST", headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ image: framePhoto }) })
    .then(r => r.json())
    .then(d => {
      if (!inBatch) setShutter(true);
      const err = d.detail || d.error;
      if (err) {
        if (!inBatch) {
          procHide(); unfreezePreview();
          setScanStatus("Ready - tap the shutter");
          showDetectLabel(String(err).slice(0, 80));
        }
        throw new Error(err);
      }
      // The server decodes HEIC, so this is the first renderable version of
      // the photo the browser has seen.
      if (d.preview) freezePreview(d.preview);
      const items = d.items || [];
      if (!items.length) {
        if (!inBatch) {
          procHide(); unfreezePreview();
          setScanStatus("Ready - tap the shutter");
          showDetectLabel("No equipment recognised - try closer or square-on");
        }
        return;
      }
      return new Promise(resolve => {
        let settled = false;
        const go = im => { if (settled) return; settled = true;
                           addDetections(items, im, inBatch); resolve(); };
        const img = new Image();
        img.onload = () => go(img);
        img.onerror = () => go(null);
        setTimeout(() => go(null), 1200);
        // The server sends back a decoded preview, so HEIC uploads still get
        // real cropped thumbnails instead of a generic icon.
        img.src = d.preview || framePhoto;
      });
    })
    .catch(err => {
      if (!inBatch) {
        setShutter(true); procHide(); unfreezePreview();
        setScanStatus("Ready - tap the shutter");
        showDetectLabel("Server not reachable - is server.py running?");
        return;
      }
      throw err;
    });
}

const idQueue = [];
let idActive = 0;
const ID_POOL = 2;

function idPump() {
  while (idActive < ID_POOL && idQueue.length) {
    const it = idQueue.shift();
    idActive += 1;
    fetch(u("/api/identify"), { method: "POST", headers: { "Content-Type": "application/json" },
                         body: JSON.stringify({ image: it.photo, category: it.type,
                                                hint: [it.model, it.why].filter(Boolean).join(" ") }) })
      .then(r => r.json())
      .then(d => {
        if (it.modelEdited) return;      // operator has answered; leave it alone
        if (d && d.model) {
          it.model = d.model;
          it.equipmentId = d.equipment_id || null;
          it.source = d.source || null;
          // The matched record decides the category - detection put a UHC in
          // HLZ, and the catalog is the authority on what the machine is.
          if (d.category && d.category !== it.type) {
            it.type = d.category;
            it.typeConf = "high";
          }
          it.modelConf = d.source === "read_from_unit" ? "medium"
                       : d.confidence === "high" ? "high"
                       : d.confidence === "medium" ? "medium" : "low";
          it.why = d.why || it.why;
          if (screen === "review") render();
        }
      })
      .catch(() => {})
      .then(() => {
        it.identifying = false;
        idActive -= 1;
        idPump();
        if (!identifyPending()) {
          revealStaged();
          procFound();
          showDetectLabel(pendingItems.length === 1
            ? (pendingItems[0].type + " detected")
            : (pendingItems.length + " assets detected"));
        }
        if (screen === "scan" && waitingForReview && !identifyPending()) {
          waitingForReview = false;
          procHide();
          unfreezePreview();
          screen = "review";
          render();
        }
      });
  }
}

function refineModels() {
  stagedItems.forEach(it => {
    if (it._refined || it.modelEdited || !it.photo || it.type === "Other") return;
    if (it.model && it.modelConf === "high") return;
    it._refined = true;
    it.identifying = true;
    idQueue.push(it);
  });
  idPump();
}

function boxesTouch(a, b, gap) {
  const g = gap === undefined ? 0.06 : gap;
  return !(a[2] + g < b[0] || b[2] + g < a[0] ||
           a[3] + g < b[1] || b[3] + g < a[1]);
}

function dedupeStaged() {
  const seen = {};
  let keep = stagedItems.filter(it => {
    if (!it.equipmentId) return true;
    if (seen[it.equipmentId]) return false;
    seen[it.equipmentId] = it;
    return true;
  });
  keep = keep.filter(it => {
    if (it.equipmentId || it.modelEdited) return true;
    return !keep.some(other => other !== it && other.equipmentId &&
                               it.box && other.box && boxesTouch(it.box, other.box));
  });
  stagedItems = keep;
}

function identifyPending() {
  return stagedItems.some(it => it.identifying);
}

function cropBox(img, box) {
  const x = box[0] * img.width, y = box[1] * img.height;
  const w = (box[2] - box[0]) * img.width, h = (box[3] - box[1]) * img.height;
  const c = document.createElement("canvas");
  const side = Math.max(w, h, 1);
  c.width = side; c.height = side;
  const g = c.getContext("2d");
  g.fillStyle = "#EDEBE4"; g.fillRect(0, 0, side, side);
  g.drawImage(img, x, y, w, h, (side - w) / 2, (side - h) / 2, w, h);
  return c.toDataURL("image/jpeg", 0.85);
}

function addDetections(items, img, inBatch) {
  const zoneSel = document.getElementById("scan-zone");
  const zone = zoneSel ? zoneSel.value : ZONES[0];
  photoSeq += 1;
  const src = photoSeq;
  items.forEach(det => {
    const item = {
      type: det.category,
      typeConf: det.category === "Other" ? "low" : "high",
      model: det.model || "not detected - manual entry needed",
      modelConf: det.model ? "medium" : "low",
      zone: zone,
      why: det.why || "",
      fromPhoto: src,
      box: det.box,
      photo: det.crop || (img ? cropBox(img, det.box) : equipmentPhoto(det.category))
    };
    stagedItems.push(item);
  });
  refineModels();
  if (identifyPending()) {
    procUpdate(80, "Identifying models...");
  } else {
    revealStaged();
    procFound();
  }
  showDetectLabel("Identifying...");
  if (!inBatch) setScanStatus("Captured " + pendingItems.length + " - next station, or done below");
}

function showDetectLabel(text) {
  const label = document.getElementById("detect-label");
  if (!label) return;
  label.textContent = text;
  label.style.animation = "none";
  requestAnimationFrame(() => { label.style.animation = "labelFade 1.4s ease"; });
}

function flyToTray(item, targetEl) {
  const flash = document.getElementById("capture-flash");
  if (flash) {
    flash.style.animation = "none";
    requestAnimationFrame(() => { flash.style.animation = "flashFade 0.35s ease"; });
  }
  const viewfinder = document.querySelector(".viewfinder");
  if (!viewfinder || !targetEl) { if (targetEl) targetEl.style.opacity = "1"; return; }
  const vfRect = viewfinder.getBoundingClientRect();
  const targetRect = targetEl.getBoundingClientRect();
  const size = 120;
  const clone = document.createElement("div");
  clone.className = "flying-capture";
  clone.style.left = (vfRect.left + vfRect.width / 2 - size / 2) + "px";
  clone.style.top = (vfRect.top + vfRect.height / 2 - size / 2) + "px";
  clone.style.width = size + "px";
  clone.style.height = size + "px";
  clone.style.opacity = "1";
  clone.innerHTML = item.photo ?
    '<img src="' + item.photo + '" style="width:100%;height:100%;object-fit:cover;display:block;" />' :
    '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:var(--page-bg);"><i class="ti ti-tools" style="font-size:30px;color:var(--ink-muted);"></i></div>';
  document.body.appendChild(clone);
  requestAnimationFrame(() => {
    clone.style.left = targetRect.left + "px";
    clone.style.top = targetRect.top + "px";
    clone.style.width = targetRect.width + "px";
    clone.style.height = targetRect.height + "px";
    clone.style.opacity = "0.4";
  });
  setTimeout(() => {
    if (clone.parentNode) clone.parentNode.removeChild(clone);
    targetEl.style.opacity = "1";
  }, 560);
}

function renderTray(hideNewest) {
  const container = document.getElementById("capture-tray");
  if (!container) return;
  const total = pendingItems.length;
  const maxSlots = 5;
  const showCount = total > maxSlots ? maxSlots - 1 : total;
  let html = "";
  for (let i = 0; i < showCount; i++) {
    const it = pendingItems[i];
    const isNewestThumb = hideNewest && i === showCount - 1 && total <= maxSlots;
    const hideStyle = isNewestThumb ? ' style="opacity:0;"' : "";
    html += it.photo ?
      '<img class="tray-thumb"' + hideStyle + ' src="' + it.photo + '" />' :
      '<div class="tray-thumb-fallback"' + hideStyle + '><i class="ti ti-tools" style="font-size:20px;color:var(--ink-muted);"></i></div>';
  }
  if (total > maxSlots) {
    const hideStyle = hideNewest ? ' style="opacity:0;"' : "";
    html += '<div class="tray-overflow"' + hideStyle + '>+' + (total - showCount) + '</div>';
  }
  container.innerHTML = html;
}

function updateScanActionBar(complete) {
  if (pendingItems.length > 0) {
    const label = complete ? "Review captured items (" + pendingItems.length + ")" : "Done scanning (" + pendingItems.length + ")";
    const icon = complete ? "ti-list-check" : "ti-check";
    setActionBar('<button id="done-scan" class="btn-primary"><i class="ti ' + icon + '"></i>' + label + '</button>');
    document.getElementById("done-scan").onclick = stopScanningAndReview;
  } else {
    setActionBar("");
  }
}

function matchKnownModel(known, value) {
  if (!value) return "";
  const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, "");
  const v = norm(value);
  return known.find(k => norm(k) === v)
      || known.find(k => norm(k).indexOf(v) !== -1 || v.indexOf(norm(k)) !== -1)
      || "";
}

function modelControl(type, value, pickAttr, freeAttr, hint) {
  const known = (CATALOG[type] || []).map(m => m.display_name || (m.manufacturer + " " + m.model));
  const raw = value && value.indexOf("not detected") === -1 ? value : "";
  const val = matchKnownModel(known, raw) || raw;
  if (!known.length) {
    return '<input type="text" ' + freeAttr + ' placeholder="Manufacturer and model" value="' +
      String(val).replace(/"/g, "&quot;") + '" style="margin-bottom:6px;" />';
  }
  const showFree = val && known.indexOf(val) === -1;
  const opts = ['<option value="">- select a model -</option>']
    .concat(known.map(n => '<option' + (n === val ? " selected" : "") + ">" + n + "</option>"))
    .concat(['<option value="__other__"' + (showFree ? " selected" : "") +
             ">Not in this list...</option>"]);
  return '<select ' + pickAttr + ' style="margin-bottom:6px;">' + opts.join("") + "</select>" +
    '<input type="text" ' + freeAttr + ' placeholder="Manufacturer and model" value="' +
      String(showFree ? val : "").replace(/"/g, "&quot;") +
      '" style="margin-bottom:6px;display:' + (showFree ? "block" : "none") + ';" />' +
    (hint ? '<p style="font-size:11px;color:var(--warning-text);margin:0;">' + hint + "</p>" : "");
}

function modelField(idx, it) {
  const known = (CATALOG[it.type] || []).map(m => m.display_name || (m.manufacturer + " " + m.model));
  const val = it.model && it.model.indexOf("not detected") === -1 ? it.model : "";

  if (!known.length) {
    return reviewField(idx, "model", "Model", val, it.modelConf || "low", false);
  }
  const hint = it.modelConf === "high" && val
    ? "Matched a reference image - change it if this is wrong"
    : val
      ? "Not certain - confirm or pick another"
      : "Not recognised - pick from the " + known.length + " models on file";
  return '<div style="margin:0 0 14px;">' +
    '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 5px;font-weight:600;">Model</p>' +
    modelControl(it.type, val, 'data-model-pick="' + idx + '"',
                 'data-model-free="' + idx + '"', hint) +
  "</div>";
}

function updateConfirmBar() {
  const blocked = pendingItems.filter(missingDetails).length;
  const n = pendingItems.length;
  const label = blocked
    ? blocked + " item" + (blocked === 1 ? "" : "s") + " need details"
    : "Confirm and add " + n + " item" + (n === 1 ? "" : "s");
  setActionBar('<button id="confirm-all" class="btn-primary"' +
    (blocked ? ' style="opacity:0.55;"' : "") +
    '><i class="ti ti-check"></i>' + label + "</button>");
  const btn = document.getElementById("confirm-all");
  if (btn) btn.onclick = confirmAll;
}

function confirmAll() {
  if (pendingItems.some(missingDetails)) {
    showToast("Fill in the highlighted \'what is this?\' fields first");
    return;
  }
  pendingItems.forEach(it => {
    if (it.type === "Other" && it.otherType && it.otherType.trim()) {
      it.type = it.otherType.trim();      // use what the operator told us
      it.typeConf = "high";
    }
  });
  doConfirm();
}

function reviewField(idx, field, label, value, conf, mono) {
  const monoStyle = mono ? "font-family:var(--font-mono);" : "";
  const labelHtml = '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 5px;font-weight:600;">' + label + '</p>';
  if (conf === "high") {
    return '<div style="margin:0 0 14px;">' + labelHtml +
      '<p style="font-size:14px;margin:0 0 6px;' + monoStyle + '">' + value + '</p>' +
      badge(conf) +
    '</div>';
  }
  const hintColor = conf === "low" ? "var(--danger-text)" : "var(--warning-text)";
  const hintText = conf === "low" ? "Couldn't read clearly - edit to confirm" : "Double-check - edit to confirm";
  return '<div style="margin:0 0 14px;">' + labelHtml +
    '<input type="text" data-review-field="' + field + '" data-idx="' + idx + '" value="' + String(value).replace(/"/g, "&quot;") + '" style="' + monoStyle + 'margin-bottom:6px;" />' +
    '<p style="font-size:11px;color:' + hintColor + ';margin:0;">' + hintText + '</p>' +
  '</div>';
}

function renderReview() {
  app.innerHTML =
    '<div class="scan-header"><span class="scan-title">Review ' + pendingItems.length + ' detected item' + (pendingItems.length === 1 ? "" : "s") + '</span></div>' +
    (photoSeq > 1
      ? '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 12px;">From ' + photoSeq + ' photos - a single photo of a station often contains several machines.</p>'
      : "") +
    pendingItems.map((it, i) =>
      '<div class="card">' +
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">' + thumb(it, 52) +
          '<span style="flex:1;min-width:0;">' +
            '<span style="font-size:16px;font-weight:700;display:block;">' + it.type +
              (it.fromPhoto ? '<span style="font-size:10px;font-weight:700;color:var(--ink-muted);background:var(--page-bg);border-radius:6px;padding:2px 6px;margin-left:6px;vertical-align:middle;">photo ' + it.fromPhoto + '</span>' : "") +
            '</span>' +
            (it.why ? '<span style="font-size:11px;color:var(--ink-secondary);">' + it.why + '</span>' : "") +
            (it.source === "read_from_unit"
              ? '<span style="font-size:10px;font-weight:700;color:var(--warning-text);background:var(--warning-tint);border-radius:6px;padding:2px 6px;margin-left:6px;">read from unit - not in catalog</span>'
              : "") +
          '</span>' +
          '<button data-remove="' + i + '" aria-label="Remove item" class="icon-btn"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg></button>' +
        '</div>' +
        '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 5px;font-weight:600;">Equipment type</p>' +
        '<select data-type="' + i + '" style="margin-bottom:' + (it.type === "Other" ? "6px" : "14px") + ';">' + typeOptions(it.type) + '</select>' +
        (it.type === "Other"
          ? '<p style="font-size:11px;color:var(--danger-text);margin:0 0 10px;">Not recognised - pick the right type above, or describe it below</p>' +
            '<div style="background:var(--warning-tint);border-radius:14px;padding:12px;margin:0 0 14px;">' +
              '<p style="font-size:12px;font-weight:700;color:var(--warning-text);margin:0 0 8px;">Required - what is this?</p>' +
              '<input type="text" data-other-type="' + i + '" placeholder="Equipment type (e.g. Ice machine)" value="' +
                String(it.otherType || "").replace(/"/g, "&quot;") + '" style="margin-bottom:8px;" />' +
              '<input type="text" data-other-model="' + i + '" placeholder="Manufacturer and model" value="' +
                String(it.model && it.model.indexOf("not detected") === -1 ? it.model : "").replace(/"/g, "&quot;") + '" />' +
            "</div>"
          : "") +

        (it.type === "Other" ? "" : modelField(i, it)) +
        '<p style="font-size:12px;color:var(--ink-secondary);margin:0 0 5px;font-weight:600;">Location</p>' +
        '<select data-zone="' + i + '">' + zoneOptions(it.zone) + '</select>' +
      '</div>'
    ).join("");
  app.querySelectorAll("[data-remove]").forEach(btn => {
    btn.onclick = () => { pendingItems.splice(Number(btn.getAttribute("data-remove")), 1); render(); };
  });
  app.querySelectorAll("[data-zone]").forEach(sel => {
    sel.onchange = () => { pendingItems[Number(sel.getAttribute("data-zone"))].zone = sel.value; };
  });
  app.querySelectorAll("[data-type]").forEach(sel => {
    sel.onchange = () => {
      const idx = Number(sel.getAttribute("data-type"));
      const it = pendingItems[idx];
      it.type = sel.value;
      it.typeConf = "high";
      const valid = (CATALOG[it.type] || [])
        .some(m => (m.display_name || (m.manufacturer + " " + m.model)) === it.model);
      if (!valid) {
        it.model = "";
        it.modelConf = "low";
        it.modelEdited = false;
        it._refined = false;
        it.source = null;
      }
      render();
    };
  });
  app.querySelectorAll("[data-other-type]").forEach(inp => {
    inp.oninput = () => {
      const idx = Number(inp.getAttribute("data-other-type"));
      pendingItems[idx].otherType = inp.value;
      updateConfirmBar();
    };
  });
  app.querySelectorAll("[data-other-model]").forEach(inp => {
    inp.oninput = () => {
      const idx = Number(inp.getAttribute("data-other-model"));
      pendingItems[idx].model = inp.value;
      pendingItems[idx].modelConf = inp.value.trim() ? "high" : "low";
      updateConfirmBar();
    };
  });
  app.querySelectorAll("[data-model-pick]").forEach(sel => {
    sel.onchange = () => {
      const idx = Number(sel.getAttribute("data-model-pick"));
      const free = app.querySelector('[data-model-free="' + idx + '"]');
      if (sel.value === "__other__") {

        if (free) {
          if (!free.value) free.value = pendingItems[idx].model || "";
          free.style.display = "block";
          free.focus();
          free.select();
        }
        pendingItems[idx].modelConf = free && free.value ? "high" : "low";
        return;
      }
      if (free) free.style.display = "none";
      pendingItems[idx].model = sel.value;
      pendingItems[idx].modelConf = sel.value ? "high" : "low";
      pendingItems[idx].modelEdited = true;
      render();
    };
  });
  app.querySelectorAll("[data-model-free]").forEach(inp => {
    inp.oninput = () => {
      const idx = Number(inp.getAttribute("data-model-free"));
      pendingItems[idx].model = inp.value.trim();
      pendingItems[idx].modelConf = inp.value.trim() ? "high" : "low";
      pendingItems[idx].modelEdited = true;
    };
  });
  app.querySelectorAll("[data-review-field]").forEach(inp => {
    inp.oninput = () => {
      const idx = Number(inp.getAttribute("data-idx"));
      const field = inp.getAttribute("data-review-field");
      pendingItems[idx][field] = inp.value;
      pendingItems[idx][field + "Conf"] = "high";
      pendingItems[idx][field + "Edited"] = true;
    };
  });
  updateConfirmBar();
}

function doConfirm() {
  const payload = pendingItems.map(it => ({
    type: it.type,
    model: it.model && it.model.indexOf("not detected") === -1 ? it.model : "",
    zone: it.zone,
    status: needsReview(it) ? "Needs review" : "Verified",
    photo: it.photo && it.photo.indexOf("data:") === 0 ? it.photo : null,
    equipment_id: it.equipmentId || null,
    source: it.source || null,
    why: it.why || "",
    scanned: true
  }));
  setActionBar('<button class="btn-primary" disabled>Saving...</button>');
  api("/api/inventory", "POST", payload)
    .then(d => {
      const saved = (d.items || []).map(fromServer);
      saved.forEach(it => inventory.unshift(it));
      const flagged = saved.filter(i => i.status === "Needs review").length;
      const message = saved.length + (saved.length === 1 ? " item" : " items") +
        " added to inventory" + (flagged > 0 ? " - " + flagged + " need review" : "");
      pendingItems = [];
      photoSeq = 0;
      screen = "dashboard";
      render();
      showToast(message);
    })
    .catch(() => {
      showToast("Could not save - check the server");
      updateConfirmBar();
    });
}

function fieldRow(label, value, confLevel, edited, verified) {
  let mark = "";
  if (edited) {
    mark = pill("var(--success-solid)", "ti-check", "Confirmed");
  } else if (!verified && confLevel) {
    mark = badge(confLevel);
  }
  return '<div class="zone-row"><span style="font-size:13px;color:var(--ink-secondary);">' + label + '</span>' +
    '<span style="font-size:14px;font-weight:500;text-align:right;">' + value + ' ' + mark + '</span></div>';
}

function renderDetail() {
  const it = inventory[selectedIndex];
  const photoHtml = it.photo ?
    '<img src="' + it.photo + '" style="width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:16px;margin-bottom:14px;display:block;" />' :
    '<div style="width:100%;aspect-ratio:4/3;border-radius:16px;background:var(--page-bg);display:flex;align-items:center;justify-content:center;margin-bottom:14px;"><i class="ti ti-tools" style="font-size:36px;color:var(--ink-muted);"></i></div>';
  let inner = '<button id="back-btn" class="icon-btn" style="margin-bottom:12px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg></button>';
  if (!editing) {
    inner +=
      '<div class="card">' + photoHtml +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;"><h3 style="margin:0;font-size:17px;font-weight:800;">' + it.type + '</h3>' + statusBadge(it.status) + '</div>' +
      '<p style="font-size:12px;color:var(--ink-muted);margin:0 0 10px;">' + (it.scanned ? "Added via AI scan" : "Manually logged") + '</p>' +
      '<div class="zone-list">' +
        fieldRow("Model", it.model, it.modelConf, it.modelEdited, it.status === "Verified") +
        fieldRow("Location", it.zone, null, false, true) +
      '</div></div>';
  } else {
    inner +=
      '<div class="card">' + photoHtml +
      '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 4px;font-weight:600;">Equipment type</p>' +
        '<select id="edit-type" style="margin-bottom:12px;">' + typeOptions(it.type) + '</select>' +
      '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 4px;font-weight:600;">Model</p>' +
        '<div style="margin-bottom:12px;">' +
          modelControl(it.type, it.model, 'id="edit-model-pick"', 'id="edit-model-free"', "") +
        "</div>" +
      '<p style="font-size:13px;color:var(--ink-secondary);margin:0 0 4px;font-weight:600;">Location</p><select id="edit-zone">' + zoneOptions(it.zone) + '</select>' +
      '</div>';
  }
  app.innerHTML = inner;
  document.getElementById("back-btn").onclick = () => { screen = "dashboard"; render(); };
  if (!editing) {
    setActionBar('<button id="edit-btn" class="btn-primary"><i class="ti ti-edit"></i>Edit details</button>');
    document.getElementById("edit-btn").onclick = () => { editing = true; render(); };
  } else {
    // changing the type reloads the model list for that category
    const typeSel = document.getElementById("edit-type");
    if (typeSel) typeSel.onchange = () => {

      const p0 = document.getElementById("edit-model-pick");
      const f0 = document.getElementById("edit-model-free");
      const current = (p0 && p0.value && p0.value !== "__other__") ? p0.value
                    : (f0 ? f0.value.trim() : it.model);
      if (current) it.model = current;

      const prev = it.model;
      it.type = typeSel.value;
      const stillValid = (CATALOG[it.type] || [])
        .some(m => (m.display_name || (m.manufacturer + " " + m.model)) === prev);
      if (!stillValid) { it.modelConf = "low"; it.modelEdited = false; }
      render();
    };
    const pick = document.getElementById("edit-model-pick");
    const free = document.getElementById("edit-model-free");
    if (pick) pick.onchange = () => {
      if (pick.value === "__other__") {
        if (free) {
          if (!free.value) free.value = it.model || "";
          free.style.display = "block"; free.focus(); free.select();
        }
        return;
      }
      if (free) { free.style.display = "none"; free.value = ""; }
      it.model = pick.value;
    };
    if (free) free.oninput = () => { it.model = free.value.trim(); };
    setActionBar('<button id="cancel-btn" class="btn-secondary">Cancel</button><button id="save-btn" class="btn-primary"><i class="ti ti-check"></i>Save changes</button>');
    document.getElementById("cancel-btn").onclick = () => { editing = false; render(); };
    document.getElementById("save-btn").onclick = () => {
      const p = document.getElementById("edit-model-pick");
      const f = document.getElementById("edit-model-free");
      const newModel = (p && p.value && p.value !== "__other__") ? p.value
                     : (f ? f.value.trim() : it.model);
      if (newModel !== it.model) { it.modelEdited = true; }
      it.modelConf = newModel ? "high" : "low";
      saveItem(it, {
        type: document.getElementById("edit-type").value,
        model: newModel,
        zone: document.getElementById("edit-zone").value,
        status: "Verified"
      }).then(() => { editing = false; render(); });
    };
  }
}

loadInventory().then(render);