import fs from "node:fs/promises";
import { appendFileSync, existsSync, renameSync, statSync } from "node:fs";
import net from "node:net";
import path from "node:path";
import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";

const DIAGNOSTIC_MAX_BYTES = 256 * 1024;

export function writeDiagnostic(config, event, details = {}) {
  try {
    const logPath = config?.diagnosticLogPath || path.join(path.dirname(fileURLToPath(import.meta.url)), "estate-statusbridge-diagnostics.log");
    if (existsSync(logPath) && statSync(logPath).size >= DIAGNOSTIC_MAX_BYTES) {
      try { renameSync(logPath, `${logPath}.1`); } catch {}
    }
    appendFileSync(logPath, `${JSON.stringify({ at: new Date().toISOString(), event, ...details })}\n`, "utf8");
  } catch {}
}

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

async function checkGovernedService(service, config) {
  const statusScript = path.join(config.mvpRoot || "", "Core", "Get-EstateServiceStatus.ps1");
  const governedIds = new Set(["ollama", "resident_gateway", "office", "open_webui", "sillytavern", "textgen", "comfyui"]);
  if (!config.mvpRoot || !existsSync(statusScript) || !governedIds.has(service.id)) return null;
  const startedAt = Date.now();
  try {
    const result = await run("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", statusScript, "-ServiceId", service.id], { timeoutMs: Math.max(config.commandTimeoutMs || 3000, 20000) });
    const state = JSON.parse(result.stdout);
    writeDiagnostic(config, "probe", { probe: "governed-runtime", service: service.id, durationMs: Date.now() - startedAt, outcome: state.state, healthy: state.healthy === true });
    return {
      ...service,
      online: state.healthy === true,
      port: state.portOwners?.[0]?.port || null,
      healthUrl: state.healthyUrl || null,
      probe: "governed-runtime",
      runtimeState: state.state,
      identityHealthy: state.identityHealthy === true,
      foreignPortProcesses: state.foreignPortProcesses || [],
      ownedPortProcesses: state.ownedPortProcesses || []
    };
  } catch (error) {
    const timedOut = error.code === "ETIMEDOUT" || error.killed === true || error.signal === "SIGTERM";
    const runtimeState = timedOut ? "TIMEOUT" : "ERR";
    writeDiagnostic(config, "probe", { probe: "governed-runtime", service: service.id, durationMs: Date.now() - startedAt, outcome: runtimeState, error: error.stderr || error.message });
    return { ...service, online: false, port: null, healthUrl: null, probe: "governed-runtime", runtimeState, identityHealthy: false, error: error.stderr || error.message };
  }
}

export async function checkService(service, timeoutMs, config = {}) {
  const governed = await checkGovernedService(service, config);
  if (governed) return governed;
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
  const coreServices = selectCoreServices(config);
  const results = await Promise.all(coreServices.map((service) => checkService(service, config.tcpTimeoutMs, config)));
  const online = results.filter((service) => service.online).length;
  const timedOut = results.filter((service) => service.runtimeState === "TIMEOUT").map((service) => service.id);
  const detail = timedOut.length > 0
    ? `${online} of ${results.length} required core services healthy; probe timeout: ${timedOut.join(", ")}.`
    : `${online} of ${results.length} required core Estate services are healthy.`;
  return statusResult({
    value: `CORE ${online}/${results.length}`,
    color: summarizeCoreColor(online, results.length),
    detail,
    source: "127.0.0.1",
    raw: { services: results, online, total: results.length, scope: "core", aggregateColor: summarizeCoreColor(online, results.length), timedOut }
  });
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
    const results = await Promise.all(services.map((service) => checkService(service, config.tcpTimeoutMs, config)));
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

export async function getP100SillyControlStatus(action, config) {
  const scriptPath = path.join(config.estateRepo, "tools", "operator-deck", "Get-P100SillyTavernStatus.ps1");
  if (!existsSync(scriptPath)) return statusResult({ value: "ERR", color: "red", detail: `P100 status helper unavailable: ${scriptPath}`, source: scriptPath });
  try {
    const result = await run("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath], { timeoutMs: 15000 });
    const state = JSON.parse(result.stdout);
    if (state.state === "READY") return statusResult({ value: "READY", color: "green", detail: state.detail, source: scriptPath, raw: state });
    if (state.state === "OFF") return statusResult({ value: "OFF", color: "off", detail: state.detail, source: scriptPath, raw: state });
    return statusResult({ value: "ERR", color: "red", detail: state.detail || "P100/SillyTavern lane is not ready.", source: scriptPath, raw: state });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message, source: scriptPath });
  }
}

export async function getComputeResourceStatus(action, config) {
  try {
    const payload = await readJson(config.computeOperatorSummaryPath);
    const resources = payload.resources || [];
    const row = resources.find((resource) => resource.resource_id === action.resourceId);
    if (!row) return statusResult({ value: `${action.label} N/A`, color: "red", detail: `Configured physical GPU UUID/resource is not present: ${action.resourceId}.`, source: config.computeOperatorSummaryPath });
    if (row.logical_gpu_id !== action.logicalGpuId) {
      return statusResult({ value: `${action.label} ERR`, color: "red", detail: `Physical GPU identity mismatch: expected ${action.logicalGpuId}, found ${row.logical_gpu_id} for ${row.nvidia_uuid}.`, source: config.computeOperatorSummaryPath, raw: { row, expectedLogicalGpuId: action.logicalGpuId, expectedResourceId: action.resourceId } });
    }
    const health = String(row.health_state || "UNKNOWN").toUpperCase();
    const freshness = String(row.freshness || (health === "UNKNOWN" ? "unknown" : "current")).toLowerCase();
    const color = health === "HEALTHY" && freshness === "current" ? "green" : (health === "DEGRADED" ? "yellow" : "red");
    const compute = Number(row.utilization_percent);
    const used = Number(row.memory_used_mib);
    const total = Number(row.memory_total_mib);
    const vram = Number(row.vram_utilization_percent);
    const computeText = Number.isFinite(compute) ? `${compute.toFixed(0)}%` : "?%";
    const vramText = Number.isFinite(used) && Number.isFinite(total) ? `${(used / 1024).toFixed(1)}/${(total / 1024).toFixed(0)}G` : "?/?G";
    const vramPercentText = Number.isFinite(vram) ? ` ${vram.toFixed(0)}%` : "";
    return statusResult({ value: `${action.label} ${computeText} V${vramText}`, color, detail: `${row.name || action.name}: compute ${computeText}; VRAM ${vramText}${vramPercentText}; ${health}/${freshness}.`, source: config.computeOperatorSummaryPath, raw: { ...row, ringPercent: Number.isFinite(compute) ? Math.max(0, Math.min(100, compute)) : null } });
  } catch (error) {
    return statusResult({ value: `${action.label} N/A`, color: "red", detail: `GPU projection unavailable: ${error.message}`, source: config.computeOperatorSummaryPath });
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
    case "serviceControl":
      return getServiceControlStatus(action, config);
    case "p100SillyControl":
      return getP100SillyControlStatus(action, config);
    case "commandStatus":
      return getCommandStatus(action);
    case "computeResourceStatus":
      return getComputeResourceStatus(action, config);
    default:
      return statusResult({ value: "ERR", color: "red", detail: `Unsupported action kind: ${action.kind}` });
  }
}

