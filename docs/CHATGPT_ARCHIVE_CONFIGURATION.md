# ChatGPT archive configuration

The JSON configuration is merged with safe defaults. Timing values are milliseconds.

| Setting | Default | Purpose |
|---|---:|---|
| `backoffBaseMs` | `300000` | First throttle wait: 5 minutes |
| `backoffMaxMs` | `1800000` | Backoff cap: 30 minutes |
| `backoffJitterMs` | `30000` | Maximum random jitter added before the cap |
| `retryWindowMs` | `3600000` | Total unattended retry window: 1 hour |
| `backoffResetAfterMs` | `600000` | Sustained-success period before backoff count resets |
| `conversationOpenDelayMs` | `1500` | Minimum delay between conversation opens |
| `paginationDelayMs` | `500` | Delay between pagination/sidebar actions |
| `burstSize` | `8` | Actions before a longer cooldown |
| `burstCooldownMs` | `10000` | Cooldown after each burst |
| `conversationHydrationPollingIntervalMs` | `1200` | Wait after each upward hydration pass for lazy loading |
| `conversationHydrationStablePasses` | `4` | Consecutive stable passes required for completeness |
| `conversationHydrationMaxDurationMs` | `1800000` | 30-minute safety duration; never success by itself |
| `conversationHydrationMaxPasses` | `1200` | Safety pass ceiling; never success by itself |
| `conversationTopPositionTolerancePx` | `8` | Near-zero tolerance for the measured content container |
| `messageCountStabilityRequirement` | `4` | Required message-count stability policy |

The defaults are deliberately conservative. Do not reduce them casually: faster settings can increase temporary ChatGPT restrictions. Reports include total requests/actions, conversations opened, throttle events, retries, and total backoff time.

Hydration defaults favor correctness over speed. A ceiling before convergence yields an incomplete export and the index entry is not eligible for successful skip behavior.

Inventory and recovery settings include `inventoryPollingIntervalMs` (1200), `inventoryFallbackDelayMs` (5000), `inventoryBottomDwellMs` (10000), `inventoryRequiredStablePasses` (810), `inventoryMaxDurationMs` (2700000), `inventoryMaxPasses` (5000), `staleRunHeartbeatThresholdMs` (300000), `pdfGenerationTimeoutMs` (120000), `mhtmlGenerationTimeoutMs` (120000), and `validateArtifacts` (true). Safety ceilings never imply completeness. Use a separate low-ceiling configuration only for bounded validation.
