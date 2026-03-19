import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.internal.router import router as internal_router
from api.openai_compat.router import router as openai_compat_router
from api.public.router import router as public_router
from backend.config import settings
from core.observability import configure_logging
from core.runtime.execution.recovery import requeue_interrupted_runs
from core.runtime.worker import runtime_worker_loop
from storage.bootstrap import init_db

configure_logging(json_logs=os.environ.get('JSON_LOGS', '').lower() in {'1', 'true', 'yes'})


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info('application_startup')
    init_db()
    requeue_interrupted_runs()
    stop = asyncio.Event()
    worker_task = asyncio.create_task(runtime_worker_loop(stop))
    try:
        yield
    finally:
        stop.set()
        worker_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker_task


app = FastAPI(title='Operator One', version='0.7.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.cors_origins.split(',') if item.strip()],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/api/health')
def health():
    return {'ok': True, 'service': 'operator-one', 'version': '0.7.0'}


@app.get('/api/ready')
def ready():
    return {'ok': True, 'ready': True}


app.include_router(public_router)
app.include_router(internal_router)
app.include_router(openai_compat_router)
