---
name: retry_backoff_simulation_script
description: Simulation script project/simulate_429_529.py exercises retry/backoff logic
type: memory
---

project/simulate_429_529.py uses fake_create to raise configurable errors and run_scenario to call llm.with_retry, measuring wall-clock gaps between attempts. Demonstrated with MAX_RETRIES=10, BASE_DELAY_MS=500, MAX_CONSECUTIVE_529=3, MODEL_ID=deepseek-v4-flash, FALLBACK_MODEL_ID=deepseek-v4-flash. Expected backoff bases (s): [0.5, 1.0, 2.0, 4.0, 8.0].
