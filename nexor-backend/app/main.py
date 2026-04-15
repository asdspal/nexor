"""FastAPI application entrypoint.

Blueprint binding:
- Stack: FastAPI 0.111.x, SQLAlchemy 2.0 async, Postgres 16.x
- External services: PostgreSQL, Redis (Extraction 3.2)
- Endpoints: /api/health
- Constraints: CORS allow only frontend origin (Section 7.5)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import health_router, auth_router, credit_router, strategies_router, repayment_router, loans_router
from app.workers.cron_repay import start_scheduler
from app.core.limiter import _rate_limit_exceeded_handler, limiter


FRONTEND_ORIGINS = ["http://localhost:3000"]


app = FastAPI(title="Nexor API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(credit_router)
app.include_router(strategies_router)
app.include_router(repayment_router)
app.include_router(loans_router)


@app.on_event("startup")
async def _startup_scheduler() -> None:
    scheduler = start_scheduler()
    app.state.repay_scheduler = scheduler


@app.on_event("shutdown")
async def _shutdown_scheduler() -> None:
    scheduler = getattr(app.state, "repay_scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)
