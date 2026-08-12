export const PLUGIN_UUID = "com.estate.statusbridge";

const MVP_ROOT = "A:\\AI\\Tools\\EstateStreamDeckMVP";
const CORE_SERVICE_IDS = ["ollama", "resident_gateway", "open_webui"];

function mvpCommand(fileName) {
  return `${MVP_ROOT}\\${fileName}`;
}

export const ACTION_LIST = [
  {
    key: "estate",
    uuid: "com.estate.statusbridge.estate",
    label: "EST",
    name: "Estate Repository Status",
    kind: "estateRepo",
    commandPath: mvpCommand("01-Estate-Status.cmd"),
    icon: "images/estate",
    profilePosition: [0, 0]
  },
  {
    key: "estateSafeSync",
    uuid: "com.estate.statusbridge.estate.sync",
    label: "EST",
    name: "Estate Safe Sync",
    kind: "commandStatus",
    value: "SYNC",
    color: "blue",
    commandPath: mvpCommand("02-Estate-Safe-Sync.cmd"),
    icon: "images/estate",
    profilePosition: [1, 0]
  },
  {
    key: "cuemastery",
    uuid: "com.estate.statusbridge.cuemastery",
    label: "Q",
    name: "CueMastery Repository Status",
    kind: "cueMasteryRepo",
    commandPath: mvpCommand("03-CueMastery-Status.cmd"),
    icon: "images/cuemastery",
    profilePosition: [2, 0]
  },
  {
    key: "cueMasterySafeSync",
    uuid: "com.estate.statusbridge.cuemastery.sync",
    label: "Q",
    name: "CueMastery Safe Sync",
    kind: "commandStatus",
    value: "SYNC",
    color: "blue",
    commandPath: mvpCommand("04-CueMastery-Safe-Sync.cmd"),
    icon: "images/cuemastery",
    profilePosition: [3, 0]
  },
  {
    key: "workpackages",
    uuid: "com.estate.statusbridge.workpackages",
    label: "WP",
    name: "Work Packages Pending",
    kind: "workPackagesPending",
    commandPath: mvpCommand("05-WP-Pending.cmd"),
    icon: "images/workpackages",
    profilePosition: [4, 0]
  },
  {
    key: "validation",
    uuid: "com.estate.statusbridge.validation",
    label: "VAL",
    name: "Validation Status",
    kind: "validationStatus",
    commandPath: mvpCommand("06-Validation-Status.cmd"),
    icon: "images/validation",
    profilePosition: [5, 0]
  },
  {
    key: "readiness",
    uuid: "com.estate.statusbridge.readiness",
    label: "READY",
    name: "Operational Readiness Status",
    kind: "readinessStatus",
    commandPath: mvpCommand("07-Readiness-Status.cmd"),
    icon: "images/readiness",
    profilePosition: [6, 0]
  },
  {
    key: "runtimeStatus",
    uuid: "com.estate.statusbridge.runtime",
    label: "RUNTIME",
    name: "Estate Runtime Status",
    kind: "serviceHealth",
    commandPath: mvpCommand("13-Estate-Runtime-Status.cmd"),
    icon: "images/health",
    profilePosition: [7, 0]
  },
  {
    key: "gpu1",
    uuid: "com.estate.statusbridge.gpu.gpu1",
    label: "GPU1",
    name: "GPU1 Compute and VRAM Status",
    kind: "computeResourceStatus",
    logicalGpuId: "GPU1",
    resourceId: "DESKTOP-JA3RPNQ:nvidia:GPU-46f3fd00-5454-4536-4196-5d8b727e14f2",
    commandPath: "A:\\theestate\\tools\\operator-deck\\Open-GPU1-Office.cmd",
    icon: "images/health",
    profilePosition: [6, 2]
  },
  {
    key: "gpu2",
    uuid: "com.estate.statusbridge.gpu.gpu2",
    label: "GPU2",
    name: "GPU2 Compute and VRAM Status",
    kind: "computeResourceStatus",
    logicalGpuId: "GPU2",
    resourceId: "DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414",
    commandPath: "A:\\theestate\\tools\\operator-deck\\Open-GPU2-Office.cmd",
    icon: "images/health",
    profilePosition: [7, 2]
  },
  {
    key: "startEstateSurfaces",
    uuid: "com.estate.statusbridge.surfaces.start",
    label: "CORE",
    name: "Start Estate Core",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: CORE_SERVICE_IDS,
    commandPath: mvpCommand("Core\\Start-EstateCore.cmd"),
    icon: "images/health",
    profilePosition: [0, 1]
  },
  {
    key: "startResidentGateway",
    uuid: "com.estate.statusbridge.resident_gateway.start",
    label: "RGW",
    name: "Start Resident Gateway",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: ["resident_gateway"],
    commandPath: mvpCommand("Core\\Start-ResidentGateway.cmd"),
    longPressCommandPath: mvpCommand("Core\\Stop-ResidentGateway.cmd"),
    icon: "images/health",
    profilePosition: [1, 1]
  },
  {
    key: "startOffice",
    uuid: "com.estate.statusbridge.office.start",
    label: "OFFICE",
    name: "Start Office of Steward",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: ["office"],
    commandPath: mvpCommand("Core\\Start-Office.cmd"),
    longPressCommandPath: mvpCommand("Core\\Stop-Office.cmd"),
    icon: "images/health",
    profilePosition: [2, 1]
  },
  {
    key: "startOpenWebUI",
    uuid: "com.estate.statusbridge.open_webui.start",
    label: "WEBUI",
    name: "Start Open WebUI",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: ["open_webui"],
    commandPath: mvpCommand("Core\\Start-OpenWebUI.cmd"),
    longPressCommandPath: mvpCommand("Core\\Stop-OpenWebUI.cmd"),
    icon: "images/health",
    profilePosition: [3, 1]
  },
  {
    key: "startSillyTavern",
    uuid: "com.estate.statusbridge.sillytavern.start",
    label: "SILLY",
    name: "Start SillyTavern",
    kind: "p100SillyControl",
    operation: "start",
    value: "START",
    serviceIds: ["sillytavern"],
    commandPath: "A:\\theestate\\tools\\operator-deck\\Start-P100SillyTavern.cmd",
    longPressCommandPath: "A:\\theestate\\tools\\operator-deck\\Stop-P100SillyTavern.cmd",
    doublePressCommandPath: "A:\\theestate\\tools\\operator-deck\\Start-P100SillyTavern-And-Open.cmd",
    icon: "images/health",
    profilePosition: [4, 1]
  },
  {
    key: "startTextGen",
    uuid: "com.estate.statusbridge.textgen.start",
    label: "TEXT",
    name: "Start TextGen",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: ["textgen"],
    commandPath: mvpCommand("Core\\Start-TextGen.cmd"),
    longPressCommandPath: mvpCommand("Core\\Stop-TextGen.cmd"),
    doublePressCommandPath: mvpCommand("Core\\Start-TextGen-And-Open.cmd"),
    icon: "images/health",
    profilePosition: [5, 1]
  },
  {
    key: "startComfyUI",
    uuid: "com.estate.statusbridge.comfyui.start",
    label: "COMFY",
    name: "Start ComfyUI",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: ["comfyui"],
    commandPath: mvpCommand("Core\\Start-ComfyUI.cmd"),
    longPressCommandPath: mvpCommand("Core\\Stop-ComfyUI.cmd"),
    doublePressCommandPath: mvpCommand("Core\\Start-ComfyUI-And-Open.cmd"),
    icon: "images/health",
    profilePosition: [6, 1]
  },
  {
    key: "stopEstateSurfaces",
    uuid: "com.estate.statusbridge.surfaces.stop",
    label: "CORE",
    name: "Stop Estate Core",
    kind: "serviceControl",
    operation: "stop",
    value: "STOP",
    serviceIds: CORE_SERVICE_IDS,
    commandPath: mvpCommand("Core\\Stop-EstateCore.cmd"),
    icon: "images/health",
    profilePosition: [0, 2]
  },
  {
    key: "restartEstateSurfaces",
    uuid: "com.estate.statusbridge.surfaces.restart",
    label: "CORE",
    name: "Restart Estate Core",
    kind: "serviceControl",
    operation: "restart",
    value: "RESTART",
    serviceIds: CORE_SERVICE_IDS,
    commandPath: mvpCommand("Core\\Restart-EstateCore.cmd"),
    icon: "images/health",
    profilePosition: [1, 2]
  },
  {
    key: "health",
    uuid: "com.estate.statusbridge.health",
    label: "HEALTH",
    name: "Estate Service Health",
    kind: "serviceHealth",
    commandPath: mvpCommand("Core\\Get-EstateCoreHealth.cmd"),
    icon: "images/health",
    profilePosition: [2, 2]
  }
];

export const ACTIONS = Object.fromEntries(ACTION_LIST.map((action) => [action.key, action]));

export const PROFILE_ACTIONS = ACTION_LIST.filter((action) => Array.isArray(action.profilePosition));

export const ACTION_BY_UUID = Object.fromEntries(
  ACTION_LIST.map((action) => [action.uuid, action])
);



