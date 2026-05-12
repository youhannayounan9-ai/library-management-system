# app/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager

from app.middleware import logging_middleware
from app.routers import auth, books, borrows, admin, default

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Library Management System...")
    try:
        from app.initial_data import seed_initial_data
        await seed_initial_data()  # ✅ Runs once on container/app start
    except Exception as e:
        logger.warning(f"⚠️  seed_initial_data skipped (DB unavailable): {e}")
    yield
    logger.info("🛑 Shutting down Library Management System...")

app = FastAPI(
    title="Library Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Logging Middleware
app.middleware("http")(logging_middleware)

# Include Routers
app.include_router(default.router, tags=["Default"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(borrows.router, prefix="/borrows", tags=["Borrows"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Prometheus Metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Mount Frontend at /ui to avoid conflicting with API routes
if os.path.exists("frontend"):
    app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
async def root():
    return {"message": "Library Management System API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)