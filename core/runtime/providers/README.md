# Provider layer (v0.8 Agno pass)

`provider.py` holds the current minimal LLM client. During **v0.8 Pass 1**, add Agno-derived adapter modules **here** and route `generate` / streaming through them.

Rules:

- One outbound abstraction; no second run or event model.
- Streaming chunks must still become `RunEvent` records via `event_bus.publish`.

Suggested layout after absorption:

- `adapters/openai_compat.py` — adapted upstream patterns
- `router.py` — chooses adapter from settings
