from core.runtime.state.status import RUN_STATUSES

__all__ = ['RUN_STATUSES', 'build_event']


def build_event(event_type: str, **payload):
    return {'type': event_type, **payload}
