import fs from "node:fs/promises";
import { existsSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import { execFile } from "node:child_process";

const FINAL_READINESS_STATES = new Set([
  "accepted",
  "cancelled",
  "canceled",
  "closed",
  "complete",
  "completed",
  "done",
  "failed_final",
  "operationally_ready",
  "rejected",
  "resolved"
]);

export function statusResult({ value, color, detail = "", source = "", raw = {} }) {
  return { value, color, detail, source, raw, checkedAt: new Date().toISOString() };
}

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    execFile(
      command,
      args,
      {
        windowsHide: true,
        timeout: options.timeoutMs || 3000,
        maxBuffer: 1024 * 1024,
        cwd: options.cwd
      },
      (error, stdout, stderr) => {
        if (error) {
          error.stdout = stdout;
          error.stderr = stderr;
          reject(error);
          return;
        }
        resolve({ stdout, stderr });
      }
    );
  });
}

async function runGit(repoPath, args, timeoutMs) {
  const safePath = repoPath.replaceAll("\\", "/");
  return run("git", ["-c", `safe.directory=${safePath}`, "-C", repoPath, ...args], { timeoutMs });
}

export function summarizeGitState({ dirty, ahead, behind }) {
  if (ahead > 0 && behind > 0) {
    return statusResult({
      value: "DIV",
      color: "red",
      detail: `Diverged from upstream: ${ahead} ahead, ${behind} behind.`
    });
  }
  if (dirty) {
    return statusResult({ value: "DIRTY", color: "yellow", detail: "Working tree has local changes." });
  }
  if (behind > 0) {
    return statusResult({ value: `DOWN ${behind}`, color: "orange", detail: `Behind upstream by ${behind}.` });
  }
  if (ahead > 0) {
    return statusResult({ value: `UP ${ahead}`, color: "blue", detail: `Ahead of upstream by ${ahead}.` });
  }
  return statusResult({ value: "CLEAN", color: "green", detail: "Clean and synchronized with cached upstream state." });
}

export async function getRepositoryStatus(repoPath, options = {}) {
  const timeoutMs = options.timeoutMs || 3000;
  if (!existsSync(repoPath)) {
    return statusResult({ value: "ERR", color: "red", detail: `Repository path unavailable: ${repoPath}` });
  }

  try {
    await runGit(repoPath, ["rev-parse", "--is-inside-work-tree"], timeoutMs);
    const status = await runGit(repoPath, ["status", "--porcelain=v1", "--untracked-files=normal"], timeoutMs);
    const dirty = status.stdout.trim().length > 0;

    let ahead = 0;
    let behind = 0;
    try {
      const upstream = await runGit(repoPath, ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"], timeoutMs);
      const parts = upstream.stdout.trim().split(/\s+/).map((value) => Number.parseInt(value, 10));
      if (parts.length >= 2 && parts.every(Number.isFinite)) {
        ahead = parts[0];
        behind = parts[1];
      } else {
        return statusResult({ value: "ERR", color: "red", detail: "Malformed upstream count from Git." });
      }
    } catch (error) {
      if (dirty) {
        return statusResult({
          value: "DIRTY",
          color: "yellow",
          detail: `Working tree is dirty; upstream cache unavailable: ${error.stderr || error.message}`
        });
      }
      return statusResult({
        value: "ERR",
        color: "red",
        detail: `Cached upstream state unavailable: ${error.stderr || error.message}`
      });
    }

    return { ...summarizeGitState({ dirty, ahead, behind }), source: repoPath, raw: { dirty, ahead, behind } };
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message, source: repoPath });
  }
}

export async function getWorkPackagesPendingStatus(pendingDir) {
  try {
    const entries = await fs.readdir(pendingDir, { withFileTypes: true });
    const files = entries.filter((entry) => entry.isFile() && /^WP[-_].+\.md$/i.test(entry.name));
    const count = files.length;
    return statusResult({
      value: String(count),
      color: count === 0 ? "green" : "orange",
      detail: `${count} pending Markdown work-package file(s).`,
      source: pendingDir,
      raw: { count }
    });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.message, source: pendingDir });
  }
}

async function readJson(filePath) {
  const text = await fs.readFile(filePath, "utf8");
  return JSON.parse(text);
}

function countOpenObservations(dashboard) {
  const summary = dashboard?.summary || {};
  const observations = dashboard?.observations || {};
  const open = Number.isFinite(summary.open_observation_count)
    ? summary.open_observation_count
    : Array.isArray(observations.open)
      ? observations.open.length
      : 0;
  const defects = Number.isFinite(summary.confirmed_defect_count)
    ? summary.confirmed_defect_count
    : Array.isArray(observations.confirmed_defects)
      ? observations.confirmed_defects.length
      : 0;
  return { open, defects };
}

export async function getValidationStatus(config) {
  const latestPath = config.validationLatestPath;
  const dashboardPath = config.validationDashboardPath;
  let latest = null;
  let dashboard = null;
  const missing = [];

  try {
    latest = await readJson(latestPath);
  } catch (error) {
    if (error.code === "ENOENT") {
      missing.push(latestPath);
    } else {
      return statusResult({ value: "ERR", color: "red", detail: `Malformed latest validation source: ${error.message}`, source: latestPath });
    }
  }

  try {
    dashboard = await readJson(dashboardPath);
  } catch (error) {
    if (error.code === "ENOENT") {
      missing.push(dashboardPath);
    } else {
      return statusResult({ value: "ERR", color: "red", detail: `Malformed validation dashboard: ${error.message}`, source: dashboardPath });
    }
  }

  if (!latest && !dashboard) {
    return statusResult({ value: "N/A", color: "red", detail: `Validation sources unavailable: ${missing.join(", ")}` });
  }

  const { open, defects } = dashboard ? countOpenObservations(dashboard) : { open: 0, defects: 0 };
  if (defects > 0) {
    return statusResult({ value: `DEF ${defects}`, color: "red", detail: `${defects} confirmed validation defect(s).`, source: dashboardPath });
  }
  if (open > 0) {
    return statusResult({ value: `OBS ${open}`, color: "yellow", detail: `${open} open validation observation(s).`, source: dashboardPath });
  }

  const latestStatus = String(latest?.validation_status || "").toLowerCase();
  if (["passed", "pass"].includes(latestStatus)) {
    return statusResult({
      value: "OK",
      color: "green",
      detail: `Latest validation passed for ${latest.work_package_id || "unknown work package"}. Merged-but-unvalidated debt count is not exposed by current sources.`,
      source: latestPath,
      raw: { latestStatus, workPackageId: latest.work_package_id }
    });
  }
  if (["passed_with_findings", "conditional_pass"].includes(latestStatus)) {
    return statusResult({
      value: "FIND",
      color: "yellow",
      detail: `Latest validation completed with findings for ${latest.work_package_id || "unknown work package"}.`,
      source: latestPath,
      raw: { latestStatus, workPackageId: latest.work_package_id }
    });
  }
  if (["failed", "fail"].includes(latestStatus)) {
    return statusResult({
      value: "FAIL",
      color: "red",
      detail: `Latest validation failed for ${latest.work_package_id || "unknown work package"}.`,
      source: latestPath,
      raw: { latestStatus, workPackageId: latest.work_package_id }
    });
  }

  return statusResult({
    value: "UNK",
    color: "yellow",
    detail: `Latest validation status is not a pass/fail posture: ${latestStatus || "missing"}.`,
    source: latestPath,
    raw: { latestStatus, workPackageId: latest?.work_package_id }
  });
}

export function isReadinessCaseOpen(caseData) {
  const state = String(caseData?.state || caseData?.status || "").toLowerCase();
  if (!state) {
    return true;
  }
  return !FINAL_READINESS_STATES.has(state);
}

export async function getReadinessStatus(readinessDir) {
  try {
    const entries = await fs.readdir(readinessDir, { withFileTypes: true });
    let openCount = 0;
    let totalCount = 0;
    for (const entry of entries) {
      if (!entry.isFile() || !entry.name.toLowerCase().endsWith(".json")) {
        continue;
      }
      totalCount += 1;
      const data = await readJson(path.join(readinessDir, entry.name));
      if (isReadinessCaseOpen(data)) {
        openCount += 1;
      }
    }
    return statusResult({
      value: String(openCount),
      color: openCount === 0 ? "green" : "yellow",
      detail: `${openCount} open/non-final readiness case(s), ${totalCount} total case file(s).`,
      source: readinessDir,
      raw: { openCount, totalCount }
    });
  } catch (error) {
    const code = error instanceof SyntaxError ? "Malformed readiness source" : error.message;
    return statusResult({ value: "ERR", color: "red", detail: code, source: readinessDir });
  }
}

export function checkTcpPort(host, port, timeoutMs = 650) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    let done = false;
    const finish = (online) => {
      if (done) {
        return;
      }
      done = true;
      socket.destroy();
      resolve(online);
    };
    socket.setTimeout(timeoutMs);
    socket.on("connect", () => finish(true));
    socket.on("timeout", () => finish(false));
    socket.on("error", () => finish(false));
  });
}

async function checkHttpEndpoint(url, timeoutMs = 1000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      method: "GET",
      redirect: "manual",
      signal: controller.signal
    });
    return {
      ok: response.status >= 200 && response.status < 400,
      status: response.status,
      url
    };
  } catch (error) {
    return {
      ok: false,
      status: null,
      url,
      error: error.message
    };
  } finally {
    clearTimeout(timer);
  }
}

export async function checkService(service, timeoutMs) {
  if (Array.isArray(service.healthUrls) && service.healthUrls.length > 0) {
    for (const url of service.healthUrls) {
      const http = await checkHttpEndpoint(url, Math.max(timeoutMs, 1000));
      if (http.ok) {
        const matchedPort = service.ports.find((port) => url.includes(`:${port}`)) || service.ports[0] || null;
        return { ...service, online: true, port: matchedPort, healthUrl: url, probe: "http" };
      }
    }
  }
  for (const port of service.ports) {
    const online = await checkTcpPort(service.host, port, timeoutMs);
    if (online) {
      return { ...service, online: true, port, healthUrl: null, probe: "tcp" };
    }
  }
  return { ...service, online: false, port: null, healthUrl: null, probe: "none" };
}

function selectCoreServices(config) {
  const coreIds = new Set(config.coreServiceIds || []);
  return config.services.filter((service) => coreIds.has(service.id));
}

function summarizeCoreColor(online, total) {
  if (online === total) {
    return "green";
  }
  if (online > 0) {
    return "yellow";
  }
  return "red";
}

export async function getServiceHealthStatus(config) {
  try {
    const coreServices = selectCoreServices(config);
    const results = await Promise.all(coreServices.map((service) => checkService(service, config.tcpTimeoutMs)));
    const online = results.filter((service) => service.online).length;
    return statusResult({
      value: `CORE ${online}/${results.length}`,
      color: summarizeCoreColor(online, results.length),
      detail: `${online} of ${results.length} required core Estate services are healthy.`,
      source: "127.0.0.1",
      raw: { services: results, online, total: results.length, scope: "core", aggregateColor: summarizeCoreColor(online, results.length) }
    });
  } catch (error) {
    return statusResult({ value: "CORE 0/3", color: "red", detail: error.message, source: "127.0.0.1" });
  }
}

function summarizeServiceColor(operation, online, total) {
  if (operation === "stop") {
    return online === 0 ? "green" : online === total ? "orange" : "yellow";
  }
  if (operation === "restart") {
    return online === 0 ? "red" : online === total ? "blue" : "yellow";
  }
  return online === total ? "green" : online > 0 ? "yellow" : "red";
}

function selectServices(config, serviceIds = []) {
  const wanted = new Set(serviceIds);
  return config.services.filter((service) => wanted.has(service.id));
}

export async function getServiceControlStatus(action, config) {
  const services = selectServices(config, action.serviceIds);
  if (services.length === 0) {
    return statusResult({
      value: action.value || "RUN",
      color: "red",
      detail: `No configured services matched ${action.name}.`,
      source: action.commandPath,
      raw: { services: [] }
    });
  }

  try {
    const results = await Promise.all(services.map((service) => checkService(service, config.tcpTimeoutMs)));
    const online = results.filter((service) => service.online).length;
    const total = results.length;
    const aggregateColor = summarizeCoreColor(online, total);
    return statusResult({
      value: action.value || `${online}/${total}`,
      color: summarizeServiceColor(action.operation, online, total),
      detail: `${action.name}: ${online} of ${total} target service(s) currently reachable.`,
      source: action.commandPath,
      raw: { services: results, operation: action.operation, online, total, aggregateColor }
    });
  } catch (error) {
    return statusResult({
      value: action.value || "ERR",
      color: "red",
      detail: error.message,
      source: action.commandPath,
      raw: { services: [] }
    });
  }
}

export function getCommandStatus(action) {
  return statusResult({
    value: action.value || "RUN",
    color: action.color || "blue",
    detail: `${action.name} launches ${action.commandPath}.`,
    source: action.commandPath
  });
}

export async function getCanonicalRuntimeStatus(action) {
  try {
    const output = await run(
      "C:\\Python314\\python.exe",
      ["A:\\theestate-wp4233\\scripts\\canonical_webui_gateway.py", "status"],
      { timeoutMs: 5000 }
    );
    const raw = JSON.parse(output.stdout);
    const healthy = raw?.runtime?.healthy === true;
    return statusResult({
      value: healthy ? "READY" : "STOPPED",
      color: healthy ? "green" : "red",
      detail: healthy
        ? "Canonical Gateway/WebUI are semantically ready."
        : "Canonical runtime is " + (raw?.recorded_status?.state || raw?.runtime?.state || "unavailable") + ".",
      source: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway.py status",
      raw
    });
  } catch (error) {
    return statusResult({
      value: "ERR",
      color: "red",
      detail: error.message,
      source: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway.py status"
    });
  }
}

export async function getOperatorDeckDictationStatus(config) {
  let statePath = "";
  try {
    const observation = await getCachedOperatorDeckState(config);
    statePath = observation.statePath;
    const state = observation.state;
    const dictation = state?.dictation || {};
    if (dictation.state === "listening") {
      return statusResult({ value: "ON", color: "green", detail: "Windows Voice Typing is listening.", source: statePath, raw: { dictation } });
    }
    if (dictation.state === "off") {
      return statusResult({ value: "OFF", color: "off", detail: "Windows Voice Typing is not listening.", source: statePath, raw: { dictation } });
    }
    return statusResult({ value: "UNK", color: "yellow", detail: "Voice Typing state is unknown.", source: statePath, raw: { dictation } });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message, source: statePath });
  }
}
let operatorDeckStateCache = { expiresAt: 0, promise: null };

async function getCachedOperatorDeckState(config) {
  const now = Date.now();
  if (operatorDeckStateCache.promise && now < operatorDeckStateCache.expiresAt) {
    return operatorDeckStateCache.promise;
  }
  const scriptPath = path.join(config.estateRepo, "tools", "operator-deck", "Get-OperatorDeckState.ps1");
  const statePath = path.join(config.estateRepo, "tools", "operator-deck", "runtime", "operator-deck-state.json");
  if (!existsSync(scriptPath)) throw new Error(`Operator Deck state publisher not found: ${scriptPath}`);
  operatorDeckStateCache.expiresAt = now + 750;
  operatorDeckStateCache.promise = (async () => {
    await run("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath, "-NoClipboard", "-Quiet"], { timeoutMs: config.commandTimeoutMs });
    return { state: await readJson(statePath), statePath };
  })();
  try {
    return await operatorDeckStateCache.promise;
  } catch (error) {
    operatorDeckStateCache = { expiresAt: 0, promise: null };
    throw error;
  }
}

export async function getOperatorDeckSlotStatus(action, config) {
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const selection = state?.selection || {};
    const cycle = state?.cycle || {};
    if (!selection.armed || !selection.valid) {
      return statusResult({ value: "READY", color: "off", detail: `${action.name}: press to select the occupying window.`, source: statePath, raw: { selection, cycle } });
    }
    if (selection.source_slot === action.slot) {
      if (cycle.active && cycle.slot === action.slot) {
        return statusResult({ value: `${cycle.index}/${cycle.count}`, color: "yellow", detail: "Tap to cycle; hold to align the selected window in this quadrant.", source: statePath, raw: { selection, cycle } });
      }
      return statusResult({ value: "SELECT", color: "green", detail: "Tap again to align here; hold to enter window cycling.", source: statePath, raw: { selection, cycle } });
    }
    return statusResult({ value: "PLACE", color: "blue", detail: `Press to move the selected window to ${action.name}.`, source: statePath, raw: { selection, cycle } });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}
export async function getOperatorDeckControlStatus(action, config) {
  if (action.operation === "undo") {
    return statusResult({ value: "UNDO", color: "blue", detail: "Restore the most recent Operator Deck move or swap." });
  }
  if (action.operation === "selectActive") {
    return statusResult({ value: "SELECT", color: "blue", detail: "Arm the currently active window for placement." });
  }
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const armed = Boolean(state?.selection?.armed && state?.selection?.valid);
    return statusResult({ value: armed ? "CANCEL" : "CLEAR", color: armed ? "yellow" : "off", detail: armed ? "Cancel the armed window selection." : "No window selection is armed.", source: statePath });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}
export async function getOperatorDeckPlacementStatus(action, config) {
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const placement = state?.placement || {};
    const promotion = state?.promotion || {};
    if (action.placementType === "return") {
      const available = Boolean(promotion.available && promotion.valid);
      return statusResult({ value: available ? "RETURN" : "EMPTY", color: available ? "green" : "off", detail: available ? "Return the promoted window to its original rectangle." : "No promoted window is available.", source: statePath });
    }
    if (action.placementType === "monitor") {
      const selected = placement.monitor === action.placementValue;
      const hasShape = Boolean(placement.shape);
      return statusResult({ value: selected ? "ARMED" : (hasShape ? "PLACE" : action.label), color: selected ? "yellow" : (hasShape ? "blue" : "off"), detail: hasShape ? `Place the selected window on ${action.placementValue} using ${placement.shape}.` : `Place the selected window full-screen on ${action.placementValue}.`, source: statePath });
    }
    const selected = placement.shape === action.placementValue;
    const hasMonitor = Boolean(placement.monitor);
    return statusResult({ value: selected ? "ARMED" : (hasMonitor ? "PLACE" : action.label), color: selected ? "yellow" : (hasMonitor ? "blue" : "off"), detail: hasMonitor ? `Place the selected window on ${placement.monitor} using ${action.placementValue}.` : `Arm the ${action.placementValue} destination shape.`, source: statePath });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}

export async function getComputeResourceStatus(action, config) {
  try {
    const payload = await readJson(config.computeOperatorSummaryPath);
    const row = (payload.resources || []).find((resource) => resource.resource_id === action.resourceId);
    if (!row) return statusResult({ value: "N/A", color: "red", detail: "Configured physical compute resource is not present.", source: config.computeOperatorSummaryPath });
    const health = String(row.health_state || "unknown").toLowerCase();
    const stale = health === "stale" || health === "unknown";
    const color = health === "healthy" ? "green" : (health === "degraded" ? "yellow" : "red");
    const used = Number(row.memory_used_mib);
    const total = Number(row.memory_total_mib);
    const utilization = Number(row.utilization_percent);
    const value = Number.isFinite(used) && Number.isFinite(total) ? `${(used / 1024).toFixed(1)}/${(total / 1024).toFixed(0)}G` : "VRAM ?";
    return statusResult({ value, color, detail: `${row.name || action.label}: ${stale ? health.toUpperCase() : `${Number.isFinite(utilization) ? utilization : "?"}% GPU utilization`}.`, source: config.computeOperatorSummaryPath, raw: { ...row, ringPercent: stale || !Number.isFinite(utilization) ? null : Math.max(0, Math.min(100, utilization)) } });
  } catch (error) {
    return statusResult({ value: "N/A", color: "red", detail: `Compute projection unavailable: ${error.message}`, source: config.computeOperatorSummaryPath });
  }
}

export async function getActionStatus(action, config) {
  switch (action.kind) {
    case "estateRepo":
      return getRepositoryStatus(config.estateRepo, { timeoutMs: config.commandTimeoutMs });
    case "cueMasteryRepo":
      return getRepositoryStatus(config.cueMasteryRepo, { timeoutMs: config.commandTimeoutMs });
    case "workPackagesPending":
      return getWorkPackagesPendingStatus(config.pendingDir);
    case "validationStatus":
      return getValidationStatus(config);
    case "readinessStatus":
      return getReadinessStatus(config.readinessDir);
    case "serviceHealth":
      return getServiceHealthStatus(config);
    case "canonicalRuntimeStatus":
      return getCanonicalRuntimeStatus(action);
    case "serviceControl":
      return getServiceControlStatus(action, config);
    case "operatorDeckDictation":
      return getOperatorDeckDictationStatus(config);
    case "operatorDeckSlot":
      return getOperatorDeckSlotStatus(action, config);
    case "operatorDeckControl":
      return getOperatorDeckControlStatus(action, config);
    case "operatorDeckPlacement":
      return getOperatorDeckPlacementStatus(action, config);
    case "computeResourceStatus":
      return getComputeResourceStatus(action, config);
    case "commandStatus":
      return getCommandStatus(action);
    default:
      return statusResult({ value: "ERR", color: "red", detail: `Unsupported action kind: ${action.kind}` });
  }
}







