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
    kind: "canonicalRuntimeStatus",
    commandPath: mvpCommand("13-Estate-Runtime-Status.cmd"),
    icon: "images/health",
    profilePosition: [7, 0]
  },
  {
    key: "gpu4090",
    uuid: "com.estate.statusbridge.gpu.4090",
    label: "4090",
    name: "RTX 4090 Compute Status",
    kind: "computeResourceStatus",
    resourceId: "DESKTOP-JA3RPNQ:nvidia:GPU-46f3fd00-5454-4536-4196-5d8b727e14f2",
    icon: "images/health",
    profilePosition: [6, 2]
  },
  {
    key: "gpuP100",
    uuid: "com.estate.statusbridge.gpu.p100",
    label: "P100",
    name: "Tesla P100 Compute Status",
    kind: "computeResourceStatus",
    resourceId: "DESKTOP-JA3RPNQ:nvidia:GPU-6785b322-899d-8eec-e817-31d83279a414",
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
    commandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_start.cmd",
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
    commandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_start.cmd",
    longPressCommandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_stop.cmd",
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
    commandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_webui_open.cmd",
    longPressCommandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_webui_stop.cmd",
    doublePressCommandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_webui_open.cmd",
    icon: "images/health",
    profilePosition: [3, 1]
  },
  {
    key: "startSillyTavern",
    uuid: "com.estate.statusbridge.sillytavern.start",
    label: "SILLY",
    name: "Start SillyTavern",
    kind: "serviceControl",
    operation: "start",
    value: "START",
    serviceIds: ["sillytavern"],
    commandPath: mvpCommand("Core\\Start-SillyTavern.cmd"),
    longPressCommandPath: mvpCommand("Core\\Stop-SillyTavern.cmd"),
    doublePressCommandPath: mvpCommand("Core\\Start-SillyTavern-And-Open.cmd"),
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
    commandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_stop.cmd",
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
    commandPath: "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_restart.cmd",
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
  },
  {
    key: "operatorDeckDictation",
    uuid: "com.estate.statusbridge.operator_deck.dictation",
    label: "VOICE",
    name: "Operator Deck Voice Typing",
    kind: "operatorDeckDictation",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Toggle-VoiceTyping.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM1TOPLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m1_top_left",
    label: "M1 TL",
    name: "Operator Deck M1 Top Left",
    kind: "operatorDeckSlot",
    slot: "M1_TOP_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M1_TOP_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M1_TOP_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM1TOPRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m1_top_right",
    label: "M1 TR",
    name: "Operator Deck M1 Top Right",
    kind: "operatorDeckSlot",
    slot: "M1_TOP_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M1_TOP_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M1_TOP_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM1BOTTOMLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m1_bottom_left",
    label: "M1 BL",
    name: "Operator Deck M1 Bottom Left",
    kind: "operatorDeckSlot",
    slot: "M1_BOTTOM_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M1_BOTTOM_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M1_BOTTOM_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM1BOTTOMRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m1_bottom_right",
    label: "M1 BR",
    name: "Operator Deck M1 Bottom Right",
    kind: "operatorDeckSlot",
    slot: "M1_BOTTOM_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M1_BOTTOM_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M1_BOTTOM_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM2TOPLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m2_top_left",
    label: "M2 TL",
    name: "Operator Deck M2 Top Left",
    kind: "operatorDeckSlot",
    slot: "M2_TOP_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M2_TOP_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M2_TOP_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM2TOPRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m2_top_right",
    label: "M2 TR",
    name: "Operator Deck M2 Top Right",
    kind: "operatorDeckSlot",
    slot: "M2_TOP_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M2_TOP_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M2_TOP_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM2BOTTOMLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m2_bottom_left",
    label: "M2 BL",
    name: "Operator Deck M2 Bottom Left",
    kind: "operatorDeckSlot",
    slot: "M2_BOTTOM_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M2_BOTTOM_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M2_BOTTOM_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM2BOTTOMRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m2_bottom_right",
    label: "M2 BR",
    name: "Operator Deck M2 Bottom Right",
    kind: "operatorDeckSlot",
    slot: "M2_BOTTOM_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M2_BOTTOM_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M2_BOTTOM_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM3TOPLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m3_top_left",
    label: "M3 TL",
    name: "Operator Deck M3 Top Left",
    kind: "operatorDeckSlot",
    slot: "M3_TOP_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M3_TOP_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M3_TOP_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM3TOPRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m3_top_right",
    label: "M3 TR",
    name: "Operator Deck M3 Top Right",
    kind: "operatorDeckSlot",
    slot: "M3_TOP_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M3_TOP_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M3_TOP_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM3BOTTOMLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m3_bottom_left",
    label: "M3 BL",
    name: "Operator Deck M3 Bottom Left",
    kind: "operatorDeckSlot",
    slot: "M3_BOTTOM_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M3_BOTTOM_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M3_BOTTOM_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM3BOTTOMRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m3_bottom_right",
    label: "M3 BR",
    name: "Operator Deck M3 Bottom Right",
    kind: "operatorDeckSlot",
    slot: "M3_BOTTOM_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M3_BOTTOM_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M3_BOTTOM_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM4TOPLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m4_top_left",
    label: "M4 TL",
    name: "Operator Deck M4 Top Left",
    kind: "operatorDeckSlot",
    slot: "M4_TOP_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M4_TOP_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M4_TOP_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM4TOPRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m4_top_right",
    label: "M4 TR",
    name: "Operator Deck M4 Top Right",
    kind: "operatorDeckSlot",
    slot: "M4_TOP_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M4_TOP_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M4_TOP_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM4BOTTOMLEFT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m4_bottom_left",
    label: "M4 BL",
    name: "Operator Deck M4 Bottom Left",
    kind: "operatorDeckSlot",
    slot: "M4_BOTTOM_LEFT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M4_BOTTOM_LEFT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M4_BOTTOM_LEFT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSlotM4BOTTOMRIGHT",
    uuid: "com.estate.statusbridge.operator_deck.slot.m4_bottom_right",
    label: "M4 BR",
    name: "Operator Deck M4 Bottom Right",
    kind: "operatorDeckSlot",
    slot: "M4_BOTTOM_RIGHT",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Slots\\M4_BOTTOM_RIGHT.cmd",
    longPressCommandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Cycle\\M4_BOTTOM_RIGHT.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckUndo",
    uuid: "com.estate.statusbridge.operator_deck.undo",
    label: "UNDO",
    name: "Operator Deck Undo",
    kind: "operatorDeckControl",
    operation: "undo",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Controls\\Undo.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckClearSelection",
    uuid: "com.estate.statusbridge.operator_deck.clear_selection",
    label: "CLEAR",
    name: "Operator Deck Clear Selection",
    kind: "operatorDeckControl",
    operation: "clearSelection",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Controls\\ClearSelection.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckSelectActive",
    uuid: "com.estate.statusbridge.operator_deck.select_active",
    label: "SELECT",
    name: "Operator Deck Select Active",
    kind: "operatorDeckControl",
    operation: "selectActive",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Controls\\SelectActive.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckMonitorM1",
    uuid: "com.estate.statusbridge.operator_deck.monitor.m1",
    label: "M1",
    name: "Operator Deck Destination M1",
    kind: "operatorDeckPlacement",
    placementType: "monitor",
    placementValue: "M1",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Monitor-M1.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckMonitorM2",
    uuid: "com.estate.statusbridge.operator_deck.monitor.m2",
    label: "M2",
    name: "Operator Deck Destination M2",
    kind: "operatorDeckPlacement",
    placementType: "monitor",
    placementValue: "M2",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Monitor-M2.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckMonitorM3",
    uuid: "com.estate.statusbridge.operator_deck.monitor.m3",
    label: "M3",
    name: "Operator Deck Destination M3",
    kind: "operatorDeckPlacement",
    placementType: "monitor",
    placementValue: "M3",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Monitor-M3.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckMonitorM4",
    uuid: "com.estate.statusbridge.operator_deck.monitor.m4",
    label: "M4",
    name: "Operator Deck Destination M4",
    kind: "operatorDeckPlacement",
    placementType: "monitor",
    placementValue: "M4",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Monitor-M4.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckShapeFull",
    uuid: "com.estate.statusbridge.operator_deck.shape.full",
    label: "FULL",
    name: "Operator Deck Shape Full",
    kind: "operatorDeckPlacement",
    placementType: "shape",
    placementValue: "full",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Shape-Full.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckShapeLeft",
    uuid: "com.estate.statusbridge.operator_deck.shape.left",
    label: "LEFT",
    name: "Operator Deck Shape Left",
    kind: "operatorDeckPlacement",
    placementType: "shape",
    placementValue: "left",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Shape-Left.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckShapeRight",
    uuid: "com.estate.statusbridge.operator_deck.shape.right",
    label: "RIGHT",
    name: "Operator Deck Shape Right",
    kind: "operatorDeckPlacement",
    placementType: "shape",
    placementValue: "right",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Shape-Right.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckShapeTop",
    uuid: "com.estate.statusbridge.operator_deck.shape.top",
    label: "TOP",
    name: "Operator Deck Shape Top",
    kind: "operatorDeckPlacement",
    placementType: "shape",
    placementValue: "top",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Shape-Top.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckShapeBottom",
    uuid: "com.estate.statusbridge.operator_deck.shape.bottom",
    label: "BOTTOM",
    name: "Operator Deck Shape Bottom",
    kind: "operatorDeckPlacement",
    placementType: "shape",
    placementValue: "bottom",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Shape-Bottom.cmd",
    icon: "images/health"
  },
  {
    key: "operatorDeckReturn",
    uuid: "com.estate.statusbridge.operator_deck.return",
    label: "RETURN",
    name: "Operator Deck Return Promoted Window",
    kind: "operatorDeckPlacement",
    placementType: "return",
    placementValue: "return",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Placement\\Return.cmd",
    icon: "images/health"
  }
];

export const ACTIONS = Object.fromEntries(ACTION_LIST.map((action) => [action.key, action]));

export const PROFILE_ACTIONS = ACTION_LIST.filter((action) => Array.isArray(action.profilePosition));

export const ACTION_BY_UUID = Object.fromEntries(
  ACTION_LIST.map((action) => [action.uuid, action])
);






