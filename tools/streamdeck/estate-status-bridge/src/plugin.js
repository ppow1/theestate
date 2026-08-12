import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ACTION_LIST, ACTIONS } from "./actions.js";
import { loadConfig } from "./config.js";
import { renderKeyImage } from "./icon.js";
import { getActionStatus, statusResult, writeDiagnostic } from "./status.js";

const config = loadConfig();
const contexts = new Map();
const presses = new Map();
const taps = new Map();
const ACTION_REGISTRY = new Map(ACTION_LIST.map((action) => [action.uuid, action]));
export const LONG_PRESS_MS = 1250;
export const DOUBLE_TAP_MS = 400;
let socket = null;
let polling = false;

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("-")) continue;
    const key = arg.replace(/^-+/, "");
    parsed[key] = argv[index + 1] && !argv[index + 1].startsWith("-") ? argv[++index] : true;
  }
  return parsed;
}
function send(event, context, payload = {}) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ event, context, payload }));
}
function register(event, uuid) { socket.send(JSON.stringify({ event, uuid })); }
function resolveAction(payload) { return ACTION_REGISTRY.get(payload.action) || contexts.get(payload.context) || null; }
async function updateContext(context, action) {
  const startedAt = Date.now();
  let status;
  try { status = await getActionStatus(action, config); }
  catch (error) { status = statusResult({ value: "ERR", color: "red", detail: error.message }); }
  writeDiagnostic(config, "status-transition", { context, action: action.key, value: status.value, color: status.color, durationMs: Date.now() - startedAt, detail: status.detail });
  send("setTitle", context, { title: "", target: 0 });
  send("setImage", context, { image: renderKeyImage(action, status), target: 0 });
}
function showTransient(context, action, value, color, detail) {
  const status = statusResult({ value, color, detail });
  send("setTitle", context, { title: "", target: 0 });
  send("setImage", context, { image: renderKeyImage(action, status), target: 0 });
}
async function pollVisibleContexts() {
  if (polling || contexts.size === 0) return;
  polling = true;
  try { await Promise.all(Array.from(contexts.entries()).map(([context, action]) => updateContext(context, action))); }
  finally { polling = false; }
}
export function buildCommandInvocation(commandPath) {
  return {
    command: "cmd.exe",
    args: ["/d", "/s", "/c", commandPath]
  };
}
function runCommand(commandPath) {
  if (!existsSync(commandPath)) { writeDiagnostic(config, "action-dispatch", { outcome: "missing-command", commandPath }); console.error(`Command not found: ${commandPath}`); return; }
  const invocation = buildCommandInvocation(commandPath);
  writeDiagnostic(config, "action-dispatch", { outcome: "dispatch", commandPath, command: invocation.command, args: invocation.args });
  const child = spawn(invocation.command, invocation.args, { detached: true, stdio: "ignore", windowsHide: true });
  child.unref();
}
function scheduleRefresh(context, action) {
  for (const delayMs of [1800, 5000, 9000, 14000]) {
    setTimeout(() => updateContext(context, action).catch((error) => {
      writeDiagnostic(config, "status-transition", { context, action: action.key, value: "ERR", durationMs: delayMs, detail: error.message });
    }), delayMs).unref();
  }
}
function clearPress(context) {
  const press = presses.get(context);
  if (press?.timer) clearTimeout(press.timer);
  presses.delete(context);
}
function clearTap(context) {
  const tap = taps.get(context);
  if (tap?.timer) clearTimeout(tap.timer);
  taps.delete(context);
}
function beginPress(context, action) {
  clearPress(context);
  const press = { action, longTriggered: false, timer: null };
  if (action.longPressCommandPath) {
    press.timer = setTimeout(() => {
      press.longTriggered = true;
      clearTap(context);
      showTransient(context, action, "STOPPING", "orange", `Stopping ${action.name}`);
      runCommand(action.longPressCommandPath);
      scheduleRefresh(context, action);
    }, LONG_PRESS_MS);
    showTransient(context, action, "HOLD", "yellow", "Hold 1.25 seconds to stop");
  }
  presses.set(context, press);
}
function runSingleTap(context, action) {
  showTransient(context, action, "STARTING", "blue", `Starting ${action.name}`);
  runCommand(action.commandPath);
  scheduleRefresh(context, action);
}
function runDoubleTap(context, action) {
  const commandPath = action.doublePressCommandPath || action.commandPath;
  showTransient(context, action, "OPENING", "blue", `Starting and opening ${action.name}`);
  runCommand(commandPath);
  scheduleRefresh(context, action);
}
function finishShortPress(context, action) {
  if (!action.doublePressCommandPath) { runSingleTap(context, action); return; }
  const existingTap = taps.get(context);
  if (existingTap) {
    clearTimeout(existingTap.timer);
    taps.delete(context);
    runDoubleTap(context, action);
    return;
  }
  const tap = { timer: setTimeout(() => { taps.delete(context); runSingleTap(context, action); }, DOUBLE_TAP_MS) };
  taps.set(context, tap);
  showTransient(context, action, "TAP?", "yellow", "Waiting briefly for second tap");
}
function endPress(context, action) {
  const press = presses.get(context);
  if (!press) return;
  if (press.timer) clearTimeout(press.timer);
  presses.delete(context);
  if (press.longTriggered) return;
  finishShortPress(context, action);
}
function handleMessage(message) {
  const payload = JSON.parse(message.data);
  const action = resolveAction(payload);
  if (payload.event === "willAppear") {
    if (action) { contexts.set(payload.context, action); updateContext(payload.context, action).catch(console.error); }
  } else if (payload.event === "willDisappear") {
    clearPress(payload.context); clearTap(payload.context); contexts.delete(payload.context);
  } else if (payload.event === "keyDown" && action) {
    beginPress(payload.context, action);
  } else if (payload.event === "keyUp" && action) {
    endPress(payload.context, action);
  }
}
export function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  if (!args.port || !args.pluginUUID || !args.registerEvent) { console.error("Missing Stream Deck launch arguments."); return; }
  socket = new WebSocket(`ws://127.0.0.1:${args.port}`);
  socket.addEventListener("open", () => register(args.registerEvent, args.pluginUUID));
  socket.addEventListener("message", handleMessage);
  socket.addEventListener("error", (event) => console.error("Stream Deck socket error", event.message || event));
  socket.addEventListener("close", () => process.exit(0));
  setInterval(() => pollVisibleContexts().catch(console.error), config.pollIntervalMs).unref();
}
if (process.argv[1] && path.resolve(fileURLToPath(import.meta.url)) === path.resolve(process.argv[1])) main();
function getRegisteredActionUuids() { return Array.from(ACTION_REGISTRY.keys()); }
export { ACTIONS, ACTION_REGISTRY, getRegisteredActionUuids, resolveAction };

