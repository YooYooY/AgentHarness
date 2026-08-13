---
name: llm_retry_error_handling
description: Final retry/backoff behavior in harness/llm.py, including overload detection and log formats
type: memory
---

harness/llm.py with_retry retries up to MAX_RETRIES with exponential backoff. Rate-limit (429) and overload (529) errors are distinguished; consecutive 529s are tracked. Once MAX_CONSECUTIVE_529=3 is reached, current_model switches to FALLBACK_MODEL_ID. `_is_overloaded_error` uses `if isinstance(e, APIStatusError) and e.status_code == 529:`. Logs: `[Rate limit] Retries {attempt+1}/{MAX_RETRIES}, wait:{delay:.1f}s`; fallback logs use `Replace to backup model: {FALLBACK_MODEL_ID}` and `Empty backup model, please retry` when no fallback is configured. Observed retry gaps ~[0.594, 1.086, 2.412, 4.992]s for 429s and ~[0.566, 1.022, 2.022, 4.036]s for 529s.
