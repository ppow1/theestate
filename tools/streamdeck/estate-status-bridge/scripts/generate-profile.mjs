import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

import { PLUGIN_UUID, PROFILE_ACTIONS } from "../src/actions.js";

const PROFILE_UUID = "7D39C492-2807-4D7A-9850-312D8CF95C25";
const PAGE_UUID = "B40D6C81-8C58-4AB2-8A2F-A2CC76AF4B9D";

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg.startsWith("--")) {
      continue;
    }
    const key = arg.slice(2);
    const value = argv[index + 1] && !argv[index + 1].startsWith("--") ? argv[++index] : true;
    parsed[key] = value;
  }
  return parsed;
}

function uuidFromSeed(seed) {
  const bytes = Buffer.from(crypto.createHash("sha1").update(seed).digest().subarray(0, 16));
  bytes[6] = (bytes[6] & 0x0f) | 0x50;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = bytes.toString("hex");
  return [
    hex.slice(0, 8),
    hex.slice(8, 12),
    hex.slice(12, 16),
    hex.slice(16, 20),
    hex.slice(20)
  ].join("-");
}

async function writeJson(filePath, value) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function profileAction(action, pluginVersion) {
  const [x, y] = action.profilePosition;
  return {
    ActionID: uuidFromSeed(`${PROFILE_UUID}:${action.uuid}:${x},${y}`),
    LinkedTitle: false,
    Name: action.name,
    Plugin: {
      Name: "Estate Status Bridge",
      UUID: PLUGIN_UUID,
      Version: pluginVersion
    },
    Settings: {},
    State: 0,
    States: [
      {
        ShowTitle: false,
        Title: ""
      }
    ],
    UUID: action.uuid
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const outputRoot = args["output-root"];
  const profileName = args["profile-name"] || "Estate Operations v0.5 Plugin";
  const pluginVersion = args["plugin-version"] || "0.2.0";

  if (!outputRoot) {
    throw new Error("Missing --output-root");
  }

  const profileRoot = path.join(outputRoot, "Profiles", `${PROFILE_UUID}.sdProfile`);
  const pageRoot = path.join(profileRoot, "Profiles", PAGE_UUID);
  const actions = {};
  for (const action of PROFILE_ACTIONS) {
    const [x, y] = action.profilePosition;
    actions[`${x},${y}`] = profileAction(action, pluginVersion);
  }

  await writeJson(path.join(outputRoot, "package.json"), {
    AppVersion: "7.5.0.22885",
    DeviceModel: "20GAT9902",
    DeviceSettings: null,
    FormatVersion: 1,
    OSType: "Windows",
    OSVersion: "10.0.26300",
    RequiredPlugins: [PLUGIN_UUID]
  });

  await writeJson(path.join(profileRoot, "manifest.json"), {
    AppIdentifier: "*",
    Device: {
      Model: "20GAT9902",
      UUID: "608c6387-9038-4e77-a606-876ffdb47dde"
    },
    Name: profileName,
    Pages: {
      Current: "00000000-0000-0000-0000-000000000000",
      Default: PAGE_UUID.toLowerCase(),
      Pages: [PAGE_UUID.toLowerCase()]
    },
    Version: "3.0"
  });

  await writeJson(path.join(pageRoot, "manifest.json"), {
    Controllers: [
      {
        Actions: actions,
        Type: "Keypad"
      }
    ],
    Icon: "",
    Name: "Estate Operations"
  });

  const summary = PROFILE_ACTIONS.map((action) => ({
    position: action.profilePosition.join(","),
    uuid: action.uuid,
    name: action.name,
    commandPath: action.commandPath
  }));
  await writeJson(path.join(outputRoot, "profile-actions.json"), summary);
  console.log(`Generated ${summary.length} profile action(s) in ${outputRoot}`);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});



