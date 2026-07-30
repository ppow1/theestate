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

The defaults are deliberately conservative. Do not reduce them casually: faster settings can increase temporary ChatGPT restrictions. Reports include total requests/actions, conversations opened, throttle events, retries, and total backoff time.
