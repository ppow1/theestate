import assert from "node:assert/strict";
import fs from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { ACTION_LIST, ACTIONS, PROFILE_ACTIONS } from "../src/actions.js";
import { renderKeyImage } from "../src/icon.js";
import { ACTION_REGISTRY, getRegisteredActionUuids, resolveAction } from "../src/plugin.js";
import {
  getServiceControlStatus,
  getReadinessStatus,
  getServiceHealthStatus,
  getValidationStatus,
  getWorkPackagesPendingStatus,
  isReadinessCaseOpen,
  summarizeGitState
} from "../src/status.js";

async function tempDir(name) {
  return fs.mkdtemp(path.join(os.tmpdir(), `${name}-`));
}

test("pending work package count ignores README and non-WP markdown", async () => {
  const dir = await tempDir("estate-wp");
  await fs.writeFile(path.join(dir, "README.md"), "# ignore");
  await fs.writeFile(path.join(dir, "WP-0001_example.md"), "# one");
  await fs.writeFile(path.join(dir, "WP_0002_example.md"), "# two");
  await fs.writeFile(path.join(dir, "notes.md"), "# ignore");

  const status = await getWorkPackagesPendingStatus(dir);

  assert.equal(status.value, "2");
  assert.equal(status.color, "orange");
});

test("readiness cases count only non-final states", async () => {
  const dir = await tempDir("estate-readiness");
  await fs.writeFile(path.join(dir, "ready.json"), JSON.stringify({ state: "operationally_ready" }));
  await fs.writeFile(path.join(dir, "open.json"), JSON.stringify({ state: "observing" }));

  const status = await getReadinessStatus(dir);

  assert.equal(status.value, "1");
  assert.equal(status.color, "yellow");
  assert.equal(isReadinessCaseOpen({ state: "completed" }), false);
  assert.equal(isReadinessCaseOpen({ state: "blocked" }), true);
});

test("validation status reports latest pass without inventing debt count", async () => {
  const dir = await tempDir("estate-validation");
  const latest = path.join(dir, "latest.json");
  const dashboard = path.join(dir, "dashboard.json");
  await fs.writeFile(latest, JSON.stringify({ validation_status: "passed", work_package_id: "WP-TEST" }));
  await fs.writeFile(dashboard, JSON.stringify({ summary: { open_observation_count: 0, confirmed_defect_count: 0 } }));

  const status = await getValidationStatus({ validationLatestPath: latest, validationDashboardPath: dashboard });

  assert.equal(status.value, "OK");
  assert.equal(status.color, "green");
  assert.match(status.detail, /not exposed/);
});

test("validation defects override latest pass", async () => {
  const dir = await tempDir("estate-validation-defect");
  const latest = path.join(dir, "latest.json");
  const dashboard = path.join(dir, "dashboard.json");
  await fs.writeFile(latest, JSON.stringify({ validation_status: "passed", work_package_id: "WP-TEST" }));
  await fs.writeFile(dashboard, JSON.stringify({ summary: { open_observation_count: 0, confirmed_defect_count: 2 } }));

  const status = await getValidationStatus({ validationLatestPath: latest, validationDashboardPath: dashboard });

  assert.equal(status.value, "DEF 2");
  assert.equal(status.color, "red");
});

test("service health reports reachable localhost services", async () => {
  const server = net.createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const port = server.address().port;
    const status = await getServiceHealthStatus({
      tcpTimeoutMs: 250,
      coreServiceIds: ["test"],
      services: [{ id: "test", name: "Test", host: "127.0.0.1", ports: [port], core: true }]
    });
    assert.equal(status.value, "CORE 1/1");
    assert.equal(status.color, "green");
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("core health counts exactly three core services and ignores optional services", async () => {
  const server = net.createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const port = server.address().port;
    const status = await getServiceHealthStatus({
      tcpTimeoutMs: 250,
      coreServiceIds: ["one", "two", "three"],
      services: [
        { id: "one", name: "One", host: "127.0.0.1", ports: [port], core: true },
        { id: "two", name: "Two", host: "127.0.0.1", ports: [65001], core: true },
        { id: "three", name: "Three", host: "127.0.0.1", ports: [65002], core: true },
        { id: "optional", name: "Optional", host: "127.0.0.1", ports: [port], core: false }
      ]
    });
    assert.equal(status.value, "CORE 1/3");
    assert.equal(status.raw.services.length, 3);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("service control reports target service state while preserving command value", async () => {
  const server = net.createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const port = server.address().port;
    const status = await getServiceControlStatus(ACTIONS.startResidentGateway, {
      tcpTimeoutMs: 250,
      services: [{ id: "resident_gateway", name: "Resident Gateway", host: "127.0.0.1", ports: [port] }]
    });

    assert.equal(status.value, "START");
    assert.equal(status.color, "green");
    assert.equal(status.raw.services[0].online, true);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("segmented service status renders per-service bars", () => {
  const image = renderKeyImage(
    { label: "HEALTH" },
    {
      value: "1/2",
      color: "yellow",
      raw: { services: [{ online: true }, { online: false }] }
    }
  );
  const svg = Buffer.from(image.split(",")[1], "base64").toString("utf8");

  assert.match(svg, /y="116"/);
  assert.match(svg, /#18a558/);
  assert.match(svg, /#3f4652/);
});

test("start estate action renders perimeter segments for the three-service core", () => {
  const image = renderKeyImage(
    ACTIONS.startEstateSurfaces,
    {
      value: "START",
      color: "yellow",
      raw: {
        aggregateColor: "yellow",
        services: [{ online: true }, { online: false }, { online: true }]
      }
    }
  );
  const svg = Buffer.from(image.split(",")[1], "base64").toString("utf8");
  assert.match(svg, /x="46" y="14"/);
  assert.match(svg, /x="120" y="44"/);
  assert.match(svg, /x="14" y="44"/);
});

test("manifest, action list, and runtime registry expose the same 20 actions", async () => {
  const manifest = JSON.parse(await fs.readFile(new URL("../manifest.json", import.meta.url), "utf8"));
  const manifestUuids = new Set(manifest.Actions.map((action) => action.UUID));
  const runtimeUuids = new Set(getRegisteredActionUuids());

  assert.equal(manifest.Actions.length, ACTION_LIST.length);
  assert.equal(PROFILE_ACTIONS.length, 20);
  for (const action of ACTION_LIST) {
    assert.equal(manifestUuids.has(action.uuid), true, action.uuid);
    assert.equal(ACTION_REGISTRY.has(action.uuid), true, action.uuid);
    assert.equal(runtimeUuids.has(action.uuid), true, action.uuid);
  }
  assert.deepEqual(
    Object.fromEntries(PROFILE_ACTIONS.map((action) => [action.key, action.profilePosition.join(",")])),
    {
      estate: "0,0",
      estateSafeSync: "1,0",
      cuemastery: "2,0",
      cueMasterySafeSync: "3,0",
      workpackages: "4,0",
      validation: "5,0",
      readiness: "6,0",
      runtimeStatus: "7,0",
      startEstateSurfaces: "0,1",
      startResidentGateway: "1,1",
      startOffice: "2,1",
      startOpenWebUI: "3,1",
      startSillyTavern: "4,1",
      startTextGen: "5,1",
      startComfyUI: "6,1",
      stopEstateSurfaces: "0,2",
      restartEstateSurfaces: "1,2",
      health: "2,2",
      gpu4090: "6,2",
      gpuP100: "7,2"
    }
  );
});

test("runtime resolver recognizes the original six status actions and the newer control actions", () => {
  const originalSix = [
    "com.estate.statusbridge.estate",
    "com.estate.statusbridge.estate.sync",
    "com.estate.statusbridge.cuemastery",
    "com.estate.statusbridge.cuemastery.sync",
    "com.estate.statusbridge.workpackages",
    "com.estate.statusbridge.validation"
  ];
  const newerActions = [
    "com.estate.statusbridge.readiness",
    "com.estate.statusbridge.runtime",
    "com.estate.statusbridge.surfaces.start",
    "com.estate.statusbridge.resident_gateway.start",
    "com.estate.statusbridge.office.start",
    "com.estate.statusbridge.open_webui.start",
    "com.estate.statusbridge.sillytavern.start",
    "com.estate.statusbridge.textgen.start",
    "com.estate.statusbridge.surfaces.stop",
    "com.estate.statusbridge.surfaces.restart",
    "com.estate.statusbridge.health"
  ];

  for (const uuid of [...originalSix, ...newerActions]) {
    const action = resolveAction({ action: uuid, context: `ctx:${uuid}` });
    assert.equal(action?.uuid, uuid, uuid);
  }
});

test("core control actions map to stable operational scripts", () => {
  assert.equal(ACTIONS.startEstateSurfaces.commandPath, "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_start.cmd");
  assert.equal(ACTIONS.startResidentGateway.commandPath, "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_start.cmd");
  assert.equal(ACTIONS.startOpenWebUI.commandPath, "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_webui_open.cmd");
  assert.equal(ACTIONS.startOpenWebUI.doublePressCommandPath, "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_webui_open.cmd");
  assert.equal(ACTIONS.stopEstateSurfaces.commandPath, "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_stop.cmd");
  assert.equal(ACTIONS.restartEstateSurfaces.commandPath, "A:\\theestate-wp4233\\scripts\\canonical_webui_gateway_core_restart.cmd");
  assert.equal(ACTIONS.health.commandPath, "A:\\AI\\Tools\\EstateStreamDeckMVP\\Core\\Get-EstateCoreHealth.cmd");
});

test("generated profile suppresses native titles for every action", async () => {
  const manifest = JSON.parse(await fs.readFile(new URL("../manifest.json", import.meta.url), "utf8"));
  const dir = await tempDir("estate-profile");

  await fs.mkdir(dir, { recursive: true });
  const scriptPath = fileURLToPath(new URL("../scripts/generate-profile.mjs", import.meta.url));
  const { spawn } = await import("node:child_process");
  await new Promise((resolve, reject) => {
    const child = spawn(
      process.execPath,
      [scriptPath, "--output-root", dir, "--plugin-version", "0.2.0"],
      { stdio: "pipe" }
    );
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(stderr || `generate-profile failed with exit code ${code}`));
    });
    child.on("error", reject);
  });

  const packageManifest = JSON.parse(await fs.readFile(path.join(dir, "package.json"), "utf8"));
  assert.deepEqual(packageManifest.RequiredPlugins, ["com.estate.statusbridge"]);

  for (const action of manifest.Actions) {
    assert.equal(action.States.length, 1, action.UUID);
    assert.equal(action.States[0].TitleAlignment, "middle", action.UUID);
  }

  const pageManifest = JSON.parse(
    await fs.readFile(
      path.join(
        dir,
        "Profiles",
        "7D39C492-2807-4D7A-9850-312D8CF95C25.sdProfile",
        "Profiles",
        "B40D6C81-8C58-4AB2-8A2F-A2CC76AF4B9D",
        "manifest.json"
      ),
      "utf8"
    )
  );
  const pageActions = Object.values(pageManifest.Controllers[0].Actions);
  assert.equal(pageActions.length, 20);
  for (const action of pageActions) {
    assert.equal(action.States[0].ShowTitle, false, action.UUID);
    assert.equal(action.States[0].Title, "", action.UUID);
  }

  const image = renderKeyImage(ACTIONS.health, {
    value: "CORE 1/3",
    color: "yellow",
    detail: "example",
    raw: { services: [{ online: true }, { online: false }] }
  });
  const svg = Buffer.from(image.split(",")[1], "base64").toString("utf8");
  assert.match(svg, />HEALTH<\/text>/);
  assert.match(svg, />CORE 1\/3<\/text>/);
});

test("build script stages the manifest code path into the packaged plugin", async () => {
  const buildRoot = await tempDir("estate-build");
  const scriptPath = fileURLToPath(new URL("../scripts/build.ps1", import.meta.url));

  await new Promise((resolve, reject) => {
    const child = spawn(
      "pwsh",
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        scriptPath,
        "-BuildRoot",
        buildRoot
      ],
      { stdio: "pipe" }
    );
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(stderr || `build.ps1 failed with exit code ${code}`));
    });
    child.on("error", reject);
  });

  const manifest = JSON.parse(
    await fs.readFile(
      path.join(buildRoot, "dist", "com.estate.statusbridge.sdPlugin", "manifest.json"),
      "utf8"
    )
  );
  const codePath = manifest.CodePathWin || manifest.CodePath;
  assert.ok(codePath, "manifest must declare a Windows code path");

  const launcherPath = path.join(buildRoot, "dist", "com.estate.statusbridge.sdPlugin", ...codePath.split("/"));
  const launcher = await fs.readFile(launcherPath, "utf8");
  assert.match(launcher, /plugin\.js/);
  assert.match(launcher, /where\.exe node/);
});

test("git state summary maps required colors and compact values", () => {
  assert.deepEqual(summarizeGitState({ dirty: false, ahead: 0, behind: 0 }).value, "CLEAN");
  assert.deepEqual(summarizeGitState({ dirty: true, ahead: 0, behind: 0 }).color, "yellow");
  assert.deepEqual(summarizeGitState({ dirty: false, ahead: 0, behind: 1 }).value, "DOWN 1");
  assert.deepEqual(summarizeGitState({ dirty: false, ahead: 2, behind: 0 }).value, "UP 2");
  assert.deepEqual(summarizeGitState({ dirty: false, ahead: 1, behind: 1 }).value, "DIV");
});
