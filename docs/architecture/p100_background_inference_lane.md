# P100 Background Inference Lane

The first practical dual-GPU workload lane is a bounded `llama-server` lane
for the Qwen3 32B Q5_K_M GGUF. SillyTavern (or Grace) remains the frontend or
client; the backend owns the model file, context, GPU offload, and runtime.
The default endpoint is `http://127.0.0.1:18080`, which is OpenAI-compatible
through llama.cpp's server API.

The lane resolves the P100 from the canonical compute-resource inventory by
physical UUID (`GPU-6785b322-899d-8eec-e817-31d83279a414`) and verifies its
name, health, dispatch eligibility, and current CUDA/PyTorch ordinal before
launch. NVIDIA and CUDA ordinals are observations and may reverse; they are
never physical identity. The child is then restricted with the resolved
`CUDA_VISIBLE_DEVICES` value and uses its only visible device (`CUDA0`). This
prevents silent landing on the RTX 4090.

Default conservative settings are 42 GPU layers and context 4096. The model's
remaining work stays in system RAM/CPU. The P100 is classified as
`background_large_gguf`; primary interactive work remains explicitly assigned
to the RTX 4090. No autonomous GPU selection, retry loop, recovery, reset,
driver/CUDA change, or fallback is permitted.

Start with `tools/Start-P100BackgroundLane.ps1` after reviewing the generated
preflight. If P100 health/identity is lost, the lane must stop accepting new
work and be stopped by the operator; it must not restart in a loop. The
service-control state and diagnostic packet should report `DEGRADED/LOST`.
This lane is deliberately bounded and does not reproduce the heavy race or
crash conditions captured in [PL-0042](../../collaboration/parking_lot/PL-0042-dual-gpu-parallelism-stability-and-p100-crash-forensics.md).

Configuration is in `config/local_ai/p100_background_lane.json`. The optional
`multimodal` block enables llama.cpp's `--mmproj` path. The projector is not
selected by filename: preflight reads GGUF metadata and requires a Qwen3-VL
model, a `mmproj` artifact using `qwen3vl_merger`, a matching projection
dimension, and metadata identifying the same model family. Missing or
incompatible projectors fail closed.

The tested local projector is `A:\AI\Models\MMProj\mmproj-F16.gguf`, whose
metadata identifies Qwen3-VL 32B Instruct and a 5120-dimensional projection.
It is configured with projector GPU offload disabled because the resident text
model already uses approximately 15.6 GiB of the P100's 16 GiB. The tested
configuration remains 42 model GPU layers and context 4096; projector weights
remain in host memory. If future changes require projector GPU offload or
reduce headroom, lower model GPU layers conservatively and retest once.

For the OpenAI-compatible endpoint, send an image as a `data:image/...;base64,`
URL in a chat message content part alongside the text prompt. SillyTavern
must use its OpenAI-compatible connection against `http://127.0.0.1:18080`,
have image input enabled, and pass the image content through unchanged; no
SillyTavern UI modification is required by this lane. Stop testing immediately
if either GPU disappears from NVML/CUDA, the host becomes sluggish, or health
changes to `DEGRADED/LOST`; do not retry, reset, or invoke the PL-0042 crash
scenario.

## Multimodal acceptance record (2026-08-11)

- Model: `A:\AI\Models\GGUF\qwen3-32b-vl-instruct-polaris-hi16-heretic-uncensored-q5_k_m.gguf`
- Projector: `A:\AI\Models\MMProj\mmproj-F16.gguf`
- llama.cpp build: `9837 (b3fed31b9)`; interface: `--mmproj` and `--no-mmproj-offload`
- Target: Tesla P100, UUID `GPU-6785b322-899d-8eec-e817-31d83279a414`, resolved CUDA ordinal 1
- Tested settings: 42 GPU layers, context 4096, projector offload disabled
- `/v1/models`: returned `multimodal`; one small local image request returned a coherent image-aware response in 66.9 seconds
- Text regression before and after projector load: PASS
- Post-test P100: 15,684 / 16,384 MiB, 48°C, 42.38W; RTX 4090: 2,912 / 24,564 MiB, 53°C, 16.50W
- Both GPUs remained visible and healthy. No SDXL, benchmark, reset, driver/CUDA, or recovery action was performed.
