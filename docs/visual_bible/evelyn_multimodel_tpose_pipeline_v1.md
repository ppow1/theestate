# Evelyn Multimodel T-Pose Pipeline v1

This package installs a local, candidate-only pipeline for the supplied Evelyn
`version_1` source set. It verifies the immutable source manifest, creates
normalized gray-background derivatives, generates a deterministic front
OpenPose-style T-pose control image, validates ComfyUI profile compatibility,
and can run a bounded front T-pose comparison across compatible enabled SDXL
profiles.

The operator entry point is:

```powershell
scripts\visual_bibles\Invoke-EvelynTurnaroundV1.ps1 -Command inspect
scripts\visual_bibles\Invoke-EvelynTurnaroundV1.ps1 -Command prepare
scripts\visual_bibles\Invoke-EvelynTurnaroundV1.ps1 -Command validate-profiles
scripts\visual_bibles\Invoke-EvelynTurnaroundV1.ps1 -Command generate-front-tpose -SamplesPerProfile 1
```

All generated images remain candidates and are written under:

`data/visual_bibles/residents/evelyn/internal/capture_360/version_1/generated/evelyn_turnaround_v1/`

No source image is modified in place. Normalized derivatives and pose controls
are written under the same `version_1/derived` tree and carry SHA-256 manifests.

## Profile Rules

The registry lives at `config/visual_generation/evelyn_generation_profiles.yaml`.
The enabled profiles are SDXL checkpoint profiles using a local front T-pose
silhouette control image and the discovered ControlNet model. The package also
emits an OpenPose-style skeleton asset for provenance and future validation, but
the bounded run uses the silhouette control because the discovered
`diffusion_pytorch_model_promax.safetensors` asset behaved as a literal
structure control during integration testing.

IPAdapter identity-reference profiles are present but disabled because the
current ComfyUI runtime does not expose the installed IPAdapter files or
CLIP-ViT-H model through `object_info`.

The pipeline validates node and model visibility before running. A profile that
is enabled but missing a node or model is reported as incompatible and skipped.

## Steward Boundary

The bounded generation command intentionally ends with:

`Bounded front T-pose comparison complete; pause for Steward review before full campaign.`

Do not promote, canonize, or run the full turnaround campaign until the Steward
has reviewed the bounded comparison manifest and sheet.
