import path from "node:path";

export const DEFAULT_CONFIG = {
  estateRepo: "A:\\theestate",
  cueMasteryRepo: "C:\\Users\\wille\\Documents\\GitHub\\CueMastery",
  pendingDir: "A:\\theestate\\collaboration\\work_packages\\pending",
  readinessDir: "A:\\theestate\\runtime\\operational_readiness\\cases",
  validationLatestPath: "A:\\theestate\\runtime\\validation\\work_packages\\latest.json",
  validationDashboardPath: "A:\\theestate\\runtime\\validation\\validation_metrics_dashboard.json",
  computeOperatorSummaryPath: "A:\\theestate\\runtime\\compute_resources\\operator_summary.json",
  mvpRoot: "A:\\AI\\Tools\\EstateStreamDeckMVP",
  pollIntervalMs: 5000,
  commandTimeoutMs: 3000,
  tcpTimeoutMs: 650,
  services: [
    {
      id: "ollama",
      name: "Ollama",
      host: "127.0.0.1",
      ports: [11434],
      healthUrls: ["http://127.0.0.1:11434/api/tags"],
      core: true
    },
    {
      id: "resident_gateway",
      name: "Resident Gateway",
      host: "127.0.0.1",
      ports: [11435],
      healthUrls: ["http://127.0.0.1:11435/v1/models"],
      core: true
    },
    {
      id: "office",
      name: "Office of Steward",
      host: "127.0.0.1",
      ports: [8765],
      healthUrls: ["http://127.0.0.1:8765/"],
      core: false
    },
    {
      id: "open_webui",
      name: "Open WebUI",
      host: "127.0.0.1",
      ports: [8080, 3000],
      healthUrls: ["http://127.0.0.1:8080/", "http://127.0.0.1:3000/"],
      core: true
    },
    {
      id: "sillytavern",
      name: "SillyTavern",
      host: "127.0.0.1",
      ports: [8000],
      healthUrls: ["http://127.0.0.1:8000/"],
      core: false
    },
    {
      id: "textgen",
      name: "TextGen",
      host: "127.0.0.1",
      ports: [7860, 5000, 5005, 7861],
      healthUrls: ["http://127.0.0.1:7860/", "http://127.0.0.1:5000/v1/models"],
      core: false
    },
    {
      id: "comfyui",
      name: "ComfyUI",
      host: "127.0.0.1",
      ports: [8188],
      healthUrls: ["http://127.0.0.1:8188/"],
      core: false
    }
  ],
  coreServiceIds: ["ollama", "resident_gateway", "open_webui"]
};

export function loadConfig(overrides = {}) {
  const estateRepo = process.env.ESTATE_STATUS_BRIDGE_ESTATE_REPO || DEFAULT_CONFIG.estateRepo;
  const mvpRoot = process.env.ESTATE_STATUS_BRIDGE_MVP_ROOT || DEFAULT_CONFIG.mvpRoot;

  return {
    ...DEFAULT_CONFIG,
    estateRepo,
    cueMasteryRepo: process.env.ESTATE_STATUS_BRIDGE_CUEMASTERY_REPO || DEFAULT_CONFIG.cueMasteryRepo,
    pendingDir:
      process.env.ESTATE_STATUS_BRIDGE_PENDING_DIR ||
      path.join(estateRepo, "collaboration", "work_packages", "pending"),
    readinessDir:
      process.env.ESTATE_STATUS_BRIDGE_READINESS_DIR ||
      path.join(estateRepo, "runtime", "operational_readiness", "cases"),
    validationLatestPath:
      process.env.ESTATE_STATUS_BRIDGE_VALIDATION_LATEST ||
      path.join(estateRepo, "runtime", "validation", "work_packages", "latest.json"),
    validationDashboardPath:
      process.env.ESTATE_STATUS_BRIDGE_VALIDATION_DASHBOARD ||
      path.join(estateRepo, "runtime", "validation", "validation_metrics_dashboard.json"),
    computeOperatorSummaryPath:
      process.env.ESTATE_STATUS_BRIDGE_COMPUTE_SUMMARY ||
      path.join(estateRepo, "runtime", "compute_resources", "operator_summary.json"),
    mvpRoot,
    services: DEFAULT_CONFIG.services,
    ...overrides
  };
}

