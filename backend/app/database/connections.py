"""Un cliente compartido por base; ninguna operación modifica datos."""

from neo4j import GraphDatabase, Query, READ_ACCESS
from neo4j.exceptions import DriverError, Neo4jError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.config import Settings


class DatabaseConnections:
    def __init__(self, settings: Settings):
        self.settings = settings
        timeout = settings.db_timeout_seconds
        self.mongo = MongoClient(
            host=settings.mongo_host,
            port=settings.mongo_port,
            username=settings.mongo_root_username.get_secret_value(),
            password=settings.mongo_root_password.get_secret_value(),
            authSource=settings.mongo_auth_source,
            connect=False,
            timeoutMS=int(timeout * 1000),
            serverSelectionTimeoutMS=int(timeout * 1000),
            connectTimeoutMS=int(timeout * 1000),
            socketTimeoutMS=int(timeout * 1000),
        )
        try:
            self.neo4j = GraphDatabase.driver(
                f"bolt://{settings.neo4j_host}:{settings.neo4j_port}",
                auth=(settings.neo4j_username.get_secret_value(),
                      settings.neo4j_password.get_secret_value()),
                connection_timeout=timeout,
                connection_acquisition_timeout=timeout,
                max_transaction_retry_time=0,
            )
        except Exception:
            self.mongo.close()
            raise RuntimeError("No se pudo configurar el cliente Neo4j.") from None

    def check_mongodb(self) -> bool:
        try:
            return self.mongo.admin.command("ping")["ok"] == 1
        except (PyMongoError, OSError):
            # No registrar la excepción: puede incluir datos de conexión.
            return False

    def check_neo4j(self) -> bool:
        try:
            with self.neo4j.session(
                database=self.settings.neo4j_database,
                default_access_mode=READ_ACCESS,
            ) as session:
                record = session.run(Query(
                    "RETURN 1 AS comprobacion",
                    timeout=self.settings.db_timeout_seconds,
                )).single()
                return record is not None and record["comprobacion"] == 1
        except (DriverError, Neo4jError, OSError):
            return False

    def close(self) -> None:
        try:
            self.mongo.close()
        finally:
            self.neo4j.close()
