'use strict';

const os = require('node:os');
const path = require('node:path');

const PROFILE_ID = 'estate-openwebui-operator-profile';
const PROFILE_ENV = 'ESTATE_OPENWEBUI_PROFILE';

function canonicalProfilePath(env = process.env, platform = process.platform) {
  const localAppData = platform === 'win32'
    ? (env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'))
    : (env.XDG_STATE_HOME || path.join(os.homedir(), '.local', 'state'));
  return path.resolve(localAppData, 'TheEstate', 'browser', 'openwebui-operator-profile');
}

function resolveProfilePath(explicitProfile, env = process.env, platform = process.platform) {
  return path.resolve(explicitProfile || env[PROFILE_ENV] || canonicalProfilePath(env, platform));
}

function profileEvidence(profilePath, env = process.env, platform = process.platform) {
  const resolved = resolveProfilePath(profilePath, env, platform);
  const canonical = canonicalProfilePath(env, platform);
  return {
    profile_id: resolved === canonical ? PROFILE_ID : 'explicit-estate-openwebui-operator-profile',
    persistence: resolved === canonical ? 'machine_local_outside_worktree' : 'explicit_external_path',
    authentication_state_reused: null
  };
}

module.exports = {PROFILE_ID, PROFILE_ENV, canonicalProfilePath, resolveProfilePath, profileEvidence};
