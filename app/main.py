from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from app.middleware import LoggingMiddleware
from app.routers import auth, books, borrows
from app.database import engine, Base, AsyncSessionLocal
from app.redis_client import ping_redis
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Library Management System",
    description="A RESTful API for managing library books, users, and borrow records.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(borrows.router)

Instrumentator().instrument(app).expose(app)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Library API is running"}


from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

@app.get("/health", tags=["Health"], summary="Service health check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Return operational status of the API, database, and Redis cache.

    Always returns HTTP 200 so load-balancers / test suites treat the app as
    alive even when a backing service is temporarily unavailable.
    The ``status`` field is ``"healthy"`` only when every dependency is up.
    """
    db_status = "ok"
    redis_status = "ok"

    # --- Database probe ---
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logging.getLogger(__name__).error("DB health-check failed: %s", exc)
        db_status = "unavailable"

    # --- Redis probe ---
    try:
        redis_ok = await ping_redis()
        if not redis_ok:
            redis_status = "degraded"
    except Exception as exc:
        logging.getLogger(__name__).warning("Redis health-check failed: %s", exc)
        redis_status = "degraded"

    overall = "healthy" if db_status == "ok" and redis_status == "ok" else "degraded"
    return JSONResponse(
        content={"status": overall, "database": db_status, "redis": redis_status},
        status_code=200,
    )
