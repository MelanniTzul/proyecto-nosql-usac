"""Punto de entrada: python -m uvicorn app.main:app --reload."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.api.health import router as health_router
from app.core.config import Settings, HTTPSettings
from app.core.errors import install_handlers
from app.api.analytics import router as analytics_router
from app.api.query_explorer import router as queries_router
from app.database.connections import DatabaseConnections


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = Settings()
    except ValidationError:
        raise RuntimeError("Configuración inválida: revisa las variables del backend y .env.") from None
    connections = DatabaseConnections(settings)
    app.state.databases = connections
    try:
        yield
    finally:
        connections.close()

def create_app() -> FastAPI:
    http = HTTPSettings()
    application = FastAPI(
        title="Análisis de Pruebas Específicas USAC",
        description="Consultas de solo lectura sobre evaluaciones y grafos de admisión.",
        version="0.5.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware, allow_origins=http.cors_origins,
        allow_credentials=False, allow_methods=["GET"], allow_headers=["Accept", "Content-Type"],
    )
    install_handlers(application)
    application.include_router(health_router, prefix="/api")
    application.include_router(analytics_router, prefix="/api")
    application.include_router(queries_router, prefix="/api")
    return application


app = create_app()
