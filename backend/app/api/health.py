"""Comprobación de disponibilidad del proceso de la API."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Estado"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Confirma que la API responde; todavía no comprueba las bases de datos."""
    return HealthResponse(status="ok", service="usac-admisiones-api")
