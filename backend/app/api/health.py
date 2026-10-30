"""Comprobación de disponibilidad del proceso de la API."""

from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

router = APIRouter(tags=["Estado"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Confirma que la API responde, independientemente de las bases de datos."""
    return HealthResponse(status="ok", service="usac-admisiones-api")


class DatabaseStatus(BaseModel):
    status: Literal["ok", "error"]
    message: str


class DatabasesHealthResponse(BaseModel):
    status: Literal["ok", "error"]
    mongodb: DatabaseStatus
    neo4j: DatabaseStatus


@router.get(
    "/health/databases", response_model=DatabasesHealthResponse,
    responses={503: {"model": DatabasesHealthResponse, "description": "Una o ambas bases no disponibles"}},
)
def get_databases_health(request: Request, response: Response) -> DatabasesHealthResponse:
    """Comprueba ambas bases incluso si falla una. No expone errores del controlador."""
    databases = request.app.state.databases
    # Ruta síncrona: FastAPI ejecuta los controladores bloqueantes en un hilo.
    mongodb_ok = databases.check_mongodb()
    neo4j_ok = databases.check_neo4j()

    def result(available: bool) -> DatabaseStatus:
        return DatabaseStatus(
            status="ok" if available else "error",
            message="Conexión verificada." if available else "No se pudo verificar la conexión.",
        )

    available = mongodb_ok and neo4j_ok
    response.status_code = 200 if available else 503
    response.headers["Cache-Control"] = "no-store"
    return DatabasesHealthResponse(
        status="ok" if available else "error",
        mongodb=result(mongodb_ok), neo4j=result(neo4j_ok),
    )
