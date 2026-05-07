from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.middleware import logging_middleware
from app.routers import auth, books, borrows, admin, default

from fastapi.staticfiles import StaticFiles
import os

# Add this near the top of app/main.py
app = FastAPI(title="Library Management System", version="1.0.0")
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)

# ✅ Single prefix applied here. Routers inside must NOT have prefixes.
app.include_router(default.router, tags=["Default"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(borrows.router, prefix="/borrows", tags=["Borrows"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)