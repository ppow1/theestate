# Lessons Learned

- Degree-only prompts are too abstract for reliable viewpoint control.
- Long identity-lock prompts can overpower or dilute the primary view instruction.
- Named viewpoints plus absolute angles improve results, but still require candidate selection.
- A clockwise sequential chain can work for several frames, then reverse, reset, or collapse into duplicate profiles.
- Re-running the same workflow produces materially different results; this variability is useful when deliberately managed as a pool.
- The 180-degree rear view requires explicit emphasis because many runs underproduce it.
- The 315-degree front-left view was initially weak but appeared reliably once three candidates per angle were generated.
- The gray spotlight/cloud backdrop is baked into generated pixels, not a transparency visualization.
- A standard SaveImage node does not make an opaque generated image transparent.
- BiRefNet plus mask inversion and JoinImageWithAlpha produces a genuine RGBA PNG.
- White clothing can survive background removal, but edge review remains mandatory.
