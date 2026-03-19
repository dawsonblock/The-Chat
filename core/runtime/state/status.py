"""Run and execution status constants (single authority for valid run states)."""

RUN_STATUSES = frozenset({'queued', 'running', 'waiting_approval', 'succeeded', 'failed', 'cancelled'})

FAILURE_CLASSES = frozenset({'retryable', 'user_error', 'infra', 'cancelled', 'timeout'})
