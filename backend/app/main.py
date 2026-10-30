"""Punto de entrada: python -m uvicorn app.main:app --reload."""

from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="Análisis de Pruebas Específicas USAC",
    description="API del proyecto individual de Bases de Datos NoSQL.",
    version="0.1.0",
)
app.include_router(health_router, prefix="/api")
