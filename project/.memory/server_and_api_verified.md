---
name: server_and_api_verified
description: API endpoints and uvicorn startup verified with HTTP tests.
type: project
---

uvicorn started on http://127.0.0.1:8123. Endpoints verified: /health 200; /themes 200; /themes/1 200; /themes/999 404; /passages 200 count 1; /passages?type=A 200 count 1; /passages?type=X 422; /passages/1 200 with sections=6, core_chunks=8, output_ladder=3; /passages/999 404; /passages/1/sections 200 count 6; /passages/999/sections 404.
