// Tactical Audio Synthesis (Web Audio API)
let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) audioCtx = new AudioContextClass();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

function playBeep(freq = 1200, durationMs = 80, type = "sine") {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(0.08, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + durationMs / 1000);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + durationMs / 1000);
  } catch (e) {
    console.debug("Audio error", e);
  }
}

function playSuccessChirp() {
  playBeep(1200, 60, "sine");
  setTimeout(() => playBeep(1800, 100, "sine"), 60);
}

function playErrorChirp() {
  playBeep(600, 120, "sawtooth");
  setTimeout(() => playBeep(400, 160, "sawtooth"), 120);
}

// Global Modal System
let modalResolve = null;
function showConfirmDialog(title, message) {
  playBeep(900, 70);
  return new Promise((resolve) => {
    modalResolve = resolve;
    document.getElementById("modalTitle").innerText = title;
    document.getElementById("modalMessage").innerText = message;
    document.getElementById("modalOverlay").classList.add("active");
  });
}

function closeModal(result) {
  document.getElementById("modalOverlay").classList.remove("active");
  if (modalResolve) {
    modalResolve(result);
    modalResolve = null;
  }
}

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Navigation Tabs
document.querySelectorAll(".nav-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-view").forEach(v => v.classList.remove("active"));

    tab.classList.add("active");
    const activeView = document.getElementById(`view-${target}`);
    if (activeView) activeView.classList.add("active");
    playBeep(1400, 40);
  });
});

// PyWebView API Bridge Call Helper
async function callApi(funcName, ...args) {
  if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api[funcName] !== "function") {
    console.warn(`API method not available: ${funcName}`);
    return null;
  }
  try {
    return await window.pywebview.api[funcName](...args);
  } catch (err) {
    console.error(`API Call [${funcName}] Error:`, err);
    showToast(`Error in ${funcName}: ${err}`, "error");
    return null;
  }
}

// Window Callbacks called from Python evaluate_js
window.appendLog = function(level, message) {
  const terminal = document.getElementById("tocLiveTerminal");
  if (!terminal) return;

  const now = new Date();
  const timeStr = now.toTimeString().split(" ")[0];

  const entry = document.createElement("div");
  entry.className = "log-entry";
  
  let lvlClass = "log-lvl-info";
  if (level === "SUCCESS") lvlClass = "log-lvl-success";
  else if (level === "WARNING") lvlClass = "log-lvl-warn";
  else if (level === "ERROR" || level === "CRITICAL") lvlClass = "log-lvl-error";

  entry.innerHTML = `
    <span class="log-time">[${timeStr}]</span>
    <span class="${lvlClass}">[${level}]</span>
    <span class="log-msg">${escapeHtml(message)}</span>
  `;
  terminal.appendChild(entry);
  terminal.scrollTop = terminal.scrollHeight;
};

window.appendDriverLog = function(message) {
  const terminal = document.getElementById("driverVaultTerminal");
  if (!terminal) return;
  const line = document.createElement("div");
  line.style.whiteSpace = "pre-wrap";
  line.innerText = message;
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
};

window.updateDeployProgress = function(pct, statusMsg) {
  const fill = document.getElementById("deployProgressFill");
  const pctLbl = document.getElementById("deployProgressPct");
  const msgLbl = document.getElementById("deployProgressMsg");

  if (fill) fill.style.width = `${pct}%`;
  if (pctLbl) pctLbl.innerText = `${Math.round(pct)}%`;
  if (msgLbl && statusMsg) msgLbl.innerText = statusMsg;
};

window.updateTaskBadge = function(fname, statusText, statusClass) {
  const badge = document.querySelector(`.pkg-card[data-file="${fname}"] .pkg-status-badge`);
  if (badge) {
    badge.className = `pkg-status-badge ${statusClass}`;
    badge.innerText = statusText;
  }
};

window.setSuiteStatus = function(text, state = "ready") {
  const lbl = document.getElementById("statusText");
  const led = document.getElementById("statusLed");
  if (lbl) lbl.innerText = text;
  if (led) {
    led.className = "status-led";
    if (state === "busy") led.classList.add("busy");
    if (state === "error") led.classList.add("error");
  }
};

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// -------------------------------------------------------------
// DEPLOY VIEW LOGIC
// -------------------------------------------------------------
let cachedInstallers = [];

async function refreshDeployList() {
  const listContainer = document.getElementById("deployCardsList");
  listContainer.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Scanning deployment zone...</div>';
  
  const installers = await callApi("get_installers");
  cachedInstallers = installers || [];
  renderDeployCards(cachedInstallers);
  renderManageList(cachedInstallers);
}

function renderDeployCards(files) {
  const container = document.getElementById("deployCardsList");
  container.innerHTML = "";

  if (!files || files.length === 0) {
    container.innerHTML = `
      <div class="glass-card" style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
        <svg viewBox="0 0 24 24" style="width: 48px; height: 48px; fill: currentColor; opacity: 0.3; margin-bottom: 12px;">
          <path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/>
        </svg>
        <p style="font-size: 0.95rem; font-weight: 700; color: var(--text-main); margin-bottom: 6px;">Deployment zone is clear</p>
        <p style="font-size: 0.8rem;">Place your setup .exe or .msi packages in the 'installers/' directory to engage deployment.</p>
      </div>
    `;
    return;
  }

  files.forEach(pkg => {
    const card = document.createElement("div");
    card.className = "pkg-card";
    card.dataset.file = pkg.name;

    let engineClass = "engine-generic";
    const engLower = (pkg.engine || "").toLowerCase();
    if (engLower.includes("inno")) engineClass = "engine-inno";
    else if (engLower.includes("nsis")) engineClass = "engine-nsis";
    else if (engLower.includes("msi")) engineClass = "engine-msi";
    else if (engLower.includes("wix")) engineClass = "engine-wix";
    else if (engLower.includes("installshield")) engineClass = "engine-installshield";

    const flagsStr = (pkg.silent_args && pkg.silent_args.length > 0) ? pkg.silent_args.join(" ") : "(Interactive)";

    card.innerHTML = `
      <div class="pkg-info">
        <div class="pkg-title-row">
          <span class="pkg-name">${escapeHtml(pkg.name)}</span>
          <span class="pkg-size-badge">${pkg.size_mb} MB</span>
        </div>
        <div class="pkg-meta">
          <span class="engine-badge ${engineClass}">${escapeHtml(pkg.engine)}</span>
          <span>Flags: <code style="color: var(--accent-cyan);">${escapeHtml(flagsStr)}</code></span>
        </div>
      </div>
      <div>
        <span class="pkg-status-badge status-queued">QUEUED</span>
      </div>
    `;
    container.appendChild(card);
  });
}

async function engageDeployment() {
  if (!cachedInstallers || cachedInstallers.length === 0) {
    showToast("No installer packages found in 'installers/' folder.", "error");
    return;
  }

  const confirmed = await showConfirmDialog(
    "CONFIRM TACTICAL DEPLOYMENT",
    `Deploy and batch install ${cachedInstallers.length} packages automatically with smart silent fingerprinting?`
  );
  if (!confirmed) return;

  const btn = document.getElementById("btnDeployAll");
  btn.disabled = true;
  window.setSuiteStatus("DEPLOYING PACKAGES...", "busy");
  playBeep(1100, 100);

  const res = await callApi("start_deployment");
  btn.disabled = false;
  
  if (res && res.success) {
    playSuccessChirp();
    window.setSuiteStatus("MISSION ACCOMPLISHED", "ready");
    showToast("All packages deployed successfully!", "success");
  } else {
    playErrorChirp();
    window.setSuiteStatus("PARTIAL SUCCESS / RECON NEEDED", "error");
    showToast("Deployment completed with issues. Check TOC Comms log.", "error");
  }
}

async function openInstallersFolder() {
  await callApi("open_installers_folder");
}

// -------------------------------------------------------------
// WINGET ARMORY LOGIC
// -------------------------------------------------------------
async function initWingetArmory() {
  const status = await callApi("get_winget_status");
  const btn = document.getElementById("btnWingetStatus");
  if (status && status.ready) {
    btn.className = "btn btn-success";
    btn.innerText = `✔ WINGET READY (${status.version})`;
  } else {
    btn.className = "btn btn-primary";
    btn.innerText = "⚡ INSTALL WINGET (LTSC FIX)";
  }

  const presets = await callApi("get_presets");
  renderPresets(presets);
}

function renderPresets(presets) {
  const grid = document.getElementById("armoryPresetsGrid");
  if (!grid || !presets) return;
  grid.innerHTML = "";

  Object.entries(presets).forEach(([key, data]) => {
    const card = document.createElement("div");
    card.className = "preset-card";

    const tagsHtml = (data.packages || []).map(p => 
      `<span class="preset-tag">• ${escapeHtml(p.name)}</span>`
    ).join("");

    card.innerHTML = `
      <div>
        <div class="preset-title">${data.icon || "🎯"} ${escapeHtml(key)}</div>
        <div class="preset-desc">${escapeHtml(data.description)}</div>
        <div class="preset-tags">${tagsHtml}</div>
      </div>
      <button class="btn btn-primary" onclick="deployArmoryPreset('${escapeHtml(key)}')">
        DEPLOY ${escapeHtml(key.toUpperCase())}
      </button>
    `;
    grid.appendChild(card);
  });
}

async function triggerWingetBootstrap() {
  const status = await callApi("get_winget_status");
  const prompt = (status && status.ready)
    ? "Winget is already operational! Reinstall/repair official Microsoft LTSC bundle?"
    : "Winget not detected. Download and install official Microsoft Winget LTSC bundle (VCLibs + UI.Xaml + AppInstaller)?";

  const confirmed = await showConfirmDialog("WINGET LTSC BOOTSTRAP", prompt);
  if (!confirmed) return;

  const btn = document.getElementById("btnWingetStatus");
  btn.disabled = true;
  btn.innerText = "⏳ INSTALLING WINGET...";
  playBeep(1000, 100);

  const res = await callApi("bootstrap_winget_ltsc");
  btn.disabled = false;
  if (res && res.success) {
    playSuccessChirp();
    showToast("Winget installed successfully!", "success");
    initWingetArmory();
  } else {
    playErrorChirp();
    showToast(`Winget setup failed: ${res ? res.message : "Unknown error"}`, "error");
    initWingetArmory();
  }
}

async function deployArmoryPreset(key) {
  const confirmed = await showConfirmDialog(
    "CONFIRM ARMORY KIT DEPLOYMENT",
    `Deploy curated Kit '${key}' unattended via Winget?`
  );
  if (!confirmed) return;

  showToast(`Deploying kit: ${key}...`, "info");
  window.setSuiteStatus(`DEPLOYING ${key.toUpperCase()}...`, "busy");
  playBeep(1200, 100);

  const res = await callApi("deploy_preset", key);
  if (res && res.success) {
    playSuccessChirp();
    window.setSuiteStatus("ENTRY TEAM READY", "ready");
    showToast(`Kit '${key}' deployed successfully!`, "success");
  } else {
    playErrorChirp();
    window.setSuiteStatus("MISSION FAILED", "error");
    showToast(`Preset deployment finished with errors.`, "error");
  }
}

async function runWingetSearch() {
  const term = document.getElementById("wingetSearchInput").value.trim();
  if (!term) return;

  const resBox = document.getElementById("wingetSearchResults");
  resBox.innerHTML = `<span style="color: var(--accent-cyan);">Scanning Winget database for '${escapeHtml(term)}'...</span>`;
  playBeep(1100, 80);

  const output = await callApi("search_winget", term);
  resBox.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(output || "No output.")}</pre>`;
}

async function deploySingleWinget() {
  const pkgId = document.getElementById("wingetInstallInput").value.trim();
  if (!pkgId) {
    showToast("Please enter a valid Winget Package ID.", "error");
    return;
  }
  showToast(`Deploying Winget package: ${pkgId}...`, "info");
  window.setSuiteStatus(`DEPLOYING ${pkgId}...`, "busy");
  playBeep(1100, 100);

  const res = await callApi("deploy_single_winget", pkgId);
  if (res && res.success) {
    playSuccessChirp();
    window.setSuiteStatus("ENTRY TEAM READY", "ready");
    showToast(`Successfully deployed ${pkgId}!`, "success");
  } else {
    playErrorChirp();
    window.setSuiteStatus("MISSION FAILED", "error");
    showToast(`Failed to deploy ${pkgId}`, "error");
  }
}

async function triggerExportApps() {
  const savePath = await callApi("select_save_file", "Export Installed Applications", "winget-apps-backup.json");
  if (!savePath) return;

  showToast(`Exporting applications manifest...`, "info");
  playBeep(1000, 100);

  const res = await callApi("export_winget_apps", savePath);
  if (res && res.success) {
    playSuccessChirp();
    showToast("Application manifest exported successfully!", "success");
    window.appendLog("SUCCESS", `Exported installed apps to: ${savePath}`);
  } else {
    playErrorChirp();
    showToast(`Export failed: ${res ? res.message : "Error"}`, "error");
  }
}

async function triggerImportApps() {
  const filePath = await callApi("select_open_file", "Select Applications Backup Manifest");
  if (!filePath) return;

  const confirmed = await showConfirmDialog(
    "RESTORE APPLICATIONS",
    `Restore and batch install applications from manifest:\n${filePath}\n\nProceed?`
  );
  if (!confirmed) return;

  showToast("Restoring applications via Winget...", "info");
  playBeep(1200, 100);

  const res = await callApi("import_winget_apps", filePath);
  if (res && res.success) {
    playSuccessChirp();
    showToast("Applications restored successfully!", "success");
  } else {
    playErrorChirp();
    showToast(`Restoration failed: ${res ? res.message : "Error"}`, "error");
  }
}

// -------------------------------------------------------------
// DRIVER VAULT LOGIC
// -------------------------------------------------------------
async function initDriverVault() {
  const defaultDir = await callApi("get_default_driver_dir");
  if (defaultDir) {
    document.getElementById("driverBackupPath").value = defaultDir;
    document.getElementById("driverRestorePath").value = defaultDir;
    checkDriverStats();
  }
}

async function browseDriverBackupDir() {
  const current = document.getElementById("driverBackupPath").value;
  const dir = await callApi("select_folder", "Select Driver Backup Target Directory", current);
  if (dir) {
    document.getElementById("driverBackupPath").value = dir;
  }
}

async function browseDriverRestoreDir() {
  const current = document.getElementById("driverRestorePath").value;
  const dir = await callApi("select_folder", "Select Driver Source Directory", current);
  if (dir) {
    document.getElementById("driverRestorePath").value = dir;
    checkDriverStats();
  }
}

async function checkDriverStats() {
  const path = document.getElementById("driverRestorePath").value.trim();
  const badge = document.getElementById("driverStatsBadge");
  if (!path) return;

  const stats = await callApi("get_driver_stats", path);
  if (stats && stats.exists && stats.count > 0) {
    badge.innerText = `✔ Detected: ${stats.count} driver packages (${stats.size_mb} MB)`;
    badge.style.color = "var(--accent-green)";
  } else {
    badge.innerText = `ℹ No driver packages (.inf) found in this folder yet.`;
    badge.style.color = "var(--text-muted)";
  }
}

async function triggerDriverBackup() {
  const dest = document.getElementById("driverBackupPath").value.trim();
  if (!dest) {
    showToast("Please specify a valid backup directory.", "error");
    return;
  }

  const confirmed = await showConfirmDialog(
    "CONFIRM DRIVER BACKUP",
    `Export all installed third-party drivers to:\n${dest}\n\nThis may take 1-2 minutes. Proceed?`
  );
  if (!confirmed) return;

  const btn = document.getElementById("btnStartDriverBackup");
  btn.disabled = true;
  btn.innerText = "⏳ EXPORTING DRIVERS...";
  playBeep(1000, 100);

  const res = await callApi("backup_drivers", dest);
  btn.disabled = false;
  btn.innerText = "START DRIVER BACKUP";
  checkDriverStats();

  if (res && res.success) {
    playSuccessChirp();
    showToast(res.message, "success");
  } else {
    playErrorChirp();
    showToast(res ? res.message : "Driver backup failed", "error");
  }
}

async function triggerDriverRestore() {
  const src = document.getElementById("driverRestorePath").value.trim();
  const stats = await callApi("get_driver_stats", src);
  if (!stats || !stats.exists || stats.count === 0) {
    showToast("No .inf driver packages found in selected folder.", "error");
    return;
  }

  const confirmed = await showConfirmDialog(
    "CONFIRM DRIVER RESTORATION",
    `Install ${stats.count} driver packages (${stats.size_mb} MB) from:\n${src}\n\nProceed with automated driver deployment?`
  );
  if (!confirmed) return;

  const btn = document.getElementById("btnStartDriverRestore");
  btn.disabled = true;
  btn.innerText = "⏳ INSTALLING DRIVERS...";
  playBeep(1200, 100);

  const res = await callApi("restore_drivers", src);
  btn.disabled = false;
  btn.innerText = "RESTORE & INSTALL DRIVERS";

  if (res && res.success) {
    playSuccessChirp();
    showToast(res.message, "success");
  } else {
    playErrorChirp();
    showToast(res ? res.message : "Driver installation failed", "error");
  }
}

// -------------------------------------------------------------
// PACKAGE MANAGER LOGIC
// -------------------------------------------------------------
function renderManageList(files) {
  const container = document.getElementById("manageCardsList");
  if (!container) return;
  container.innerHTML = "";

  if (!files || files.length === 0) {
    container.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No installer files in deployment zone.</div>';
    return;
  }

  files.forEach(pkg => {
    const row = document.createElement("div");
    row.className = "pkg-card";
    row.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <input type="checkbox" class="manage-checkbox" data-file="${escapeHtml(pkg.name)}" style="width: 16px; height: 16px; cursor: pointer;">
        <span style="font-weight: 700; font-size: 0.88rem;">${escapeHtml(pkg.name)}</span>
      </div>
      <div style="display: flex; align-items: center; gap: 14px;">
        <span class="pkg-size-badge">${pkg.size_mb} MB</span>
        <button class="btn btn-sm btn-danger" onclick="deleteSinglePackage('${escapeHtml(pkg.name)}')">Delete</button>
      </div>
    `;
    container.appendChild(row);
  });
}

function selectAllManage(state) {
  document.querySelectorAll(".manage-checkbox").forEach(cb => cb.checked = state);
}

function getSelectedManageFiles() {
  const selected = [];
  document.querySelectorAll(".manage-checkbox:checked").forEach(cb => {
    selected.push(cb.dataset.file);
  });
  return selected;
}

async function importPackagesDialog() {
  const res = await callApi("import_packages_dialog");
  if (res && res.count > 0) {
    playSuccessChirp();
    showToast(`Imported ${res.count} packages to deployment zone!`, "success");
    refreshDeployList();
  }
}

async function deploySelectedManage() {
  const selected = getSelectedManageFiles();
  if (selected.length === 0) {
    showToast("Select at least one package to deploy.", "error");
    return;
  }
  document.querySelector('.nav-tab[data-tab="deploy"]').click();
  engageDeployment();
}

async function deleteSelectedManage() {
  const selected = getSelectedManageFiles();
  if (selected.length === 0) {
    showToast("Select at least one package to delete.", "error");
    return;
  }

  const confirmed = await showConfirmDialog(
    "CONFIRM DELETION",
    `Permanently delete ${selected.length} packages from installers folder?`
  );
  if (!confirmed) return;

  const res = await callApi("delete_packages", selected);
  if (res && res.success) {
    playSuccessChirp();
    showToast(`Deleted ${selected.length} packages.`, "info");
    refreshDeployList();
  }
}

async function deleteSinglePackage(fname) {
  const confirmed = await showConfirmDialog("CONFIRM DELETION", `Delete ${fname}?`);
  if (!confirmed) return;

  const res = await callApi("delete_packages", [fname]);
  if (res && res.success) {
    playSuccessChirp();
    showToast(`Deleted ${fname}`, "info");
    refreshDeployList();
  }
}

// -------------------------------------------------------------
// MISSION COMMS & BRIEFING LOGIC
// -------------------------------------------------------------
async function initMissionComms() {
  const notes = await callApi("load_briefing_notes");
  if (notes) {
    document.getElementById("briefingNotesArea").value = notes;
  }
}

async function saveBriefingNotes() {
  const content = document.getElementById("briefingNotesArea").value;
  const res = await callApi("save_briefing_notes", content);
  if (res && res.success) {
    playSuccessChirp();
    showToast("Briefing notes saved successfully!", "success");
  } else {
    playErrorChirp();
    showToast("Failed to save notes.", "error");
  }
}

function clearLiveTerminal() {
  const term = document.getElementById("tocLiveTerminal");
  if (term) term.innerHTML = "";
}

// Startup Sequence on PyWebView Ready
window.addEventListener("pywebviewready", async () => {
  console.log("Tactical HUD PyWebView engine ready.");
  playBeep(900, 70);
  
  await refreshDeployList();
  await initWingetArmory();
  await initDriverVault();
  await initMissionComms();

  window.appendLog("INFO", "TOC Command Center established. Initializing tactical HUD...");
  window.appendLog("SUCCESS", "Entry Team ready. Awaiting operational orders.");
});
