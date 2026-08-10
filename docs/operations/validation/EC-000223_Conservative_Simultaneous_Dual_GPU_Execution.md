# EC-000223 — Conservative Simultaneous Dual-GPU Execution

## Durable implementation

The read-only preflight utility is `tools/gpu-parallel-preflight.ps1`, with
deterministic fixture coverage in `tests/test_gpu_parallel_preflight.py`.
The utility does not launch workloads, unload models, stop or restart
processes/services, reset or reconfigure GPUs, mutate drivers/devices, or
reboot/shut down the host.

Physical identity is UUID-based and never ordinal-based:

| Resource | UUID | Lane | Port | Minimum free VRAM |
| --- | --- | --- | --- | ---: |
| RTX 4090 | `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2` | `qwen.local.text.4090` | 12409 | 8192 MiB |
| Tesla P100 | `GPU-6785b322-899d-8eec-e817-31d83279a414` | `qwen.local.text.p100-1` | 12100 | 4096 MiB |

The JSON contract reports `status`, `timestamp`, `host`, `resources`,
`reasons`, `policy`, and `exit_code`. Resource records include UUID, name,
PCI bus, PnP status, NVML visibility, VRAM, utilization, temperature, power,
compute PIDs and Windows process details, lane/port ownership, and readiness.
Ownership is `ESTATE_OWNED`, `EXTERNAL`, or `UNKNOWN`; unknown process or port
ownership blocks conservatively. External material compute and externally
owned or unknown lane ports block preflight. VRAM residency alone is not
material when no conflicting activity is observed.

Exit codes are 0 `PASS`, 2 `PRECHECK_BLOCKED`, 3 `GPU_HEALTH_FAILURE`, and 4
`PREFLIGHT_TOOL_ERROR`. Human-readable output is the default; `-Json` emits
the structured output.

## Validation

- Deterministic fixture tests: `10 passed`.
- PowerShell parser validation: passed.
- Mutation audit: passed; no prohibited mutation or workload-launch command
  is present.
- No live dual-GPU acceptance was run.

## Live basic health gate

The permitted read-only health observation was blocked before preflight:

- RTX 4090: present in NVML with the required UUID, but observed PCI
  `00000000:06:00.0` instead of required `00000000:07:00.0`; PnP was `OK`.
- Tesla P100: required UUID was absent from NVML and no matching PnP device
  was observed.

Because the basic health gate failed, the command
`powershell -ExecutionPolicy Bypass -File tools/gpu-parallel-preflight.ps1 -Json`
was not invoked. There is therefore no live preflight JSON or exit code for
this run. Live dual-GPU acceptance remains blocked, and no GPU workload was
launched.
