# Import audit: Agno

## Repo

- **name:** agno (upstream)
- **commit pinned:** _TBD — clone `agno-main` and record SHA here_
- **local path:** _e.g. `/path/to/agno-main`_

## Purpose (1–2 sentences)

Agno provides agent runtime patterns: tool contracts, provider adapters, streaming callbacks, and execution context—useful primitives to harden Operator One’s single run/event model without importing a second framework.

## Target destination in operator-one

- `core/runtime/`
- `core/tools/`
- `core/events/`
- `core/runtime/providers/`

## Directory classification

| Path | Purpose | Action | Destination | Notes |
|------|---------|--------|-------------|-------|
| _(inspect upstream)_ | tool base / registry | ADAPT | `core/tools/` | Map to `ToolDefinition`; no Agno-native run model |
| _(inspect upstream)_ | provider / model layer | ADAPT | `core/runtime/providers/` | Keep `runs` / `run_events` authoritative |
| _(inspect upstream)_ | hooks / streaming | ADAPT | `core/events/` | Must emit existing `RunEvent` shape |
| examples/, notebooks/ | demos | IGNORE | — | |
| upstream servers | second API | IGNORE | — | |

## Subsystems

### Tool system

- **Source paths:** _fill after tree audit_
- **Action:** ADAPT
- **Destination:** `core/tools/registry/`, `core/tools/dispatch/`
- **Replaces:** ad hoc schema handling if any remains after v0.7
- **Notes:** Single registry; policy stays in `tool_policies` + `effective_tool_policy`

### Runtime / execution

- **Source paths:** _TBD_
- **Action:** ADAPT
- **Destination:** `core/runtime/execution/`
- **Replaces:** weaker executor glue
- **Notes:** Must not introduce a parallel “Agno run” entity

### Provider / model layer

- **Source paths:** _TBD_
- **Action:** ADAPT
- **Destination:** `core/runtime/providers/`
- **Replaces:** `core/runtime/provider.py` minimal client when ready

## Conflict detection

- [ ] second run/job model
- [ ] second event system
- [ ] second workflow model
- [ ] second file/artifact system
- [ ] second auth/session model
- [ ] second API server

If YES → IGNORE or heavy ADAPT.

## Data mapping

| Upstream (conceptual) | operator-one |
|-----------------------|--------------|
| Tool call | `ToolCall` / dispatcher result |
| Tool output | `ToolResult` + artifacts |
| Stream chunk | `RunEvent` (`message.delta`, etc.) |

## Deletions triggered by this import

- Temporary provider shims superseded by imported adapters
- Duplicate callback helpers

## Integration checks

- [ ] Tool executes through `ToolDispatcher`
- [ ] SSE / `RunEvent` ordering unchanged
- [ ] No new run tables or parallel queues
