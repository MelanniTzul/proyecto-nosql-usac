"""Respuestas de error seguras: no serializar excepciones ni entradas recibidas."""
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from neo4j.exceptions import DriverError, Neo4jError
from pymongo.errors import PyMongoError, ConnectionFailure
from starlette.exceptions import HTTPException

from app.services.errors import APIError


def response(status, code, message, details=None):
    return JSONResponse(status_code=status, content={
        'status': 'error', 'error': {'code': code, 'message': message, 'details': details or []}})


def install_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation(request, error):
        details = [{'campo': '.'.join(map(str, item['loc'])), 'mensaje': 'Valor inválido o parámetro no permitido.'}
                   for item in error.errors()]
        return response(422, 'INVALID_PARAMETERS', 'Revisa los parámetros enviados.', details)

    @app.exception_handler(APIError)
    async def application(request, error):
        return response(error.status, error.code, error.message)

    @app.exception_handler(HTTPException)
    async def http(request, error):
        return response(error.status_code, 'HTTP_ERROR', 'Ruta o método no disponible.')

    async def database(request, error):
        timed_out = ((getattr(error, 'timeout', False) and not isinstance(error, ConnectionFailure)) or
                     getattr(error, 'code', '') in ('Neo.ClientError.Transaction.TransactionTimedOut',
                                                    'Neo.TransientError.Transaction.TransactionTimedOut'))
        return response(504 if timed_out else 503,
                        'QUERY_TIMEOUT' if timed_out else 'DATABASE_UNAVAILABLE',
                        'La consulta excedió el tiempo permitido.' if timed_out else 'No se pudo consultar la base de datos.')

    app.add_exception_handler(PyMongoError, database)
    app.add_exception_handler(DriverError, database)
    app.add_exception_handler(Neo4jError, database)

    @app.exception_handler(ResponseValidationError)
    async def invalid_response(request, error):
        return response(500, 'INTERNAL_ERROR', 'No se pudo construir la respuesta.')

    @app.exception_handler(Exception)
    async def unexpected(request, error):
        return response(500, 'INTERNAL_ERROR', 'No se pudo completar la solicitud.')
