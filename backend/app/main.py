"""Punto de entrada: python -m uvicorn app.main:app --reload."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from app.api.health import router as health_router
from app.core.config import Settings
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

app = FastAPI(
    title="Análisis de Pruebas Específicas USAC",
    description="API del proyecto individual de Bases de Datos NoSQL.",
    version="0.2.0",
    lifespan=lifespan,
)
app.include_router(health_router, prefix="/api")
