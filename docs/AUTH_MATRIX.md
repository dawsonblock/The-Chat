# Auth and permissions (Operator One)

| Surface | Mechanism | Notes |
|---------|-----------|--------|
| **Browser app** | `POST /api/auth/login` → Bearer token; SSE uses `token_passthrough` query param | Session row in DB |
| **Runs / conversations / files** | `get_current_user` on `/api/*` routes | `user_id` on `runs`, `conversations`, uploads |
| **Run cancel / approve** | Same Bearer; [`require_run_for_user`](../core/auth/runs.py) on run routes; approvals must match path `run_id` | [`api/public/runs.py`](../api/public/runs.py) |
| **Open WebUI `/v1`** | Bearer `OPENAI_PROXY_API_KEY` | Not tied to app `user_id` |
| **Internal intake** | Header `X-Service-Token: SERVICE_TOKEN` | Service-to-service only |
| **Tool policy / approvals** | DB `tool_policies` + `approval_requests` | Gated tools pause run until approve/deny |

## Gaps (future)

- Centralized checks under `core/auth/` for tool invocation and artifact download.
- Role-based access (admin vs operator) is not modeled yet.
