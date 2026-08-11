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

Configuration is in `config/local_ai/p100_background_lane.json`. SillyTavern
requires only a local OpenAI-compatible connection pointed at the endpoint;
no SillyTavern UI modification is needed.
