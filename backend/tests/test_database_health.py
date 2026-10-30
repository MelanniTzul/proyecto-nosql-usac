"""Integración real: requiere ambas bases activas y el .env local.

No usa mocks de controladores ni realiza escrituras. Ejecutar desde backend:
../.venv/bin/python -m unittest discover -s tests -v
"""

import io
import logging
import os
import socket
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


class DatabaseHealthTests(unittest.TestCase):
    def check_case(self, overrides, mongo_status, neo_status):
        logs = io.StringIO()
        handler = logging.StreamHandler(logs)
        logger = logging.getLogger()
        previous_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        try:
            with patch.dict(os.environ, overrides), TestClient(app) as client:
                response = client.get("/api/health/databases")
                expected_ok = mongo_status == neo_status == "ok"
                self.assertEqual(response.status_code, 200 if expected_ok else 503)
                data = response.json()
                self.assertEqual(data["status"], "ok" if expected_ok else "error")
                self.assertEqual(data["mongodb"]["status"], mongo_status)
                self.assertEqual(data["neo4j"]["status"], neo_status)
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(client.get("/api/health").json(), {
                    "status": "ok", "service": "usac-admisiones-api",
                })
                self.assertEqual(client.get("/api/health").status_code, 200)
                settings = client.app.state.databases.settings
                for secret in (settings.mongo_root_password, settings.neo4j_password):
                    self.assertNotIn(secret.get_secret_value(), response.text + logs.getvalue())
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)

    def test_both_databases_available(self):
        self.check_case({}, "ok", "ok")

    def test_mongo_wrong_password_preserves_neo4j_and_liveness(self):
        self.check_case({"MONGO_ROOT_PASSWORD": "invalid-test-password-mongo"}, "error", "ok")

    def test_neo4j_wrong_password_preserves_mongo_and_liveness(self):
        self.check_case({"NEO4J_PASSWORD": "invalid-test-password-neo4j"}, "ok", "error")

    def test_unreachable_databases_preserve_liveness(self):
        # Reservar puertos sin escuchar: no detenemos los servicios reales.
        with socket.socket() as mongo, socket.socket() as neo:
            mongo.bind(("127.0.0.1", 0))
            neo.bind(("127.0.0.1", 0))
            self.check_case({
                "MONGO_HOST": "127.0.0.1", "MONGO_PORT": str(mongo.getsockname()[1]),
                "NEO4J_HOST": "127.0.0.1", "NEO4J_PORT": str(neo.getsockname()[1]),
                "DB_TIMEOUT_SECONDS": "1",
            }, "error", "error")

    def test_invalid_configuration_has_safe_error(self):
        with patch.dict(os.environ, {"MONGO_PORT": "invalid-sensitive-input"}):
            with self.assertRaises(RuntimeError) as context:
                with TestClient(app):
                    pass
            self.assertNotIn("invalid-sensitive-input", str(context.exception))

    def test_env_path_does_not_depend_on_working_directory(self):
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                settings = Settings()
            finally:
                os.chdir(cwd)
        self.assertTrue(settings.mongo_root_password.get_secret_value())
        self.assertNotIn(settings.mongo_root_password.get_secret_value(), repr(settings))


if __name__ == "__main__":
    unittest.main()
