"""FastAPI application entry point for the Context Kernel API."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.chat import router as chat_router
from .routes.health import router as health_router
from .routes.sessions import router as sessions_router

app = FastAPI(
    title="Context Kernel API",
    description="Stateful AI runtime — context assembly, layered memory, retrieval, orchestration.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(health_router)
