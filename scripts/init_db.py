"""Script de inicialización de la base de datos PostgreSQL.

Lee las credenciales desde `.env` (o configuración de la aplicación), se conecta
a la base de datos del sistema `postgres` en modo `AUTOCOMMIT`, verifica de forma
segura si la base de datos objetivo (`DB_NAME`) existe y la crea únicamente cuando
no está presente, sin eliminar ni modificar datos existentes.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import re
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("init_db")

_VALID_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def load_db_credentials(env_path: Path | None = None) -> dict[str, str | int]:
    """Carga las credenciales de conexión a PostgreSQL desde `.env`."""
    dotenv_file = env_path or (PROJECT_ROOT / ".env")
    load_dotenv(dotenv_path=dotenv_file, override=False)

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_user = os.getenv("DB_USER", "sgr_user")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_name = os.getenv("DB_NAME", "sgr_db")
    driver_name = os.getenv("DRIVER_NAME", "postgresql+psycopg")

    if not _VALID_DB_NAME_RE.match(db_name):
        raise ValueError(
            f"Nombre de base de datos inválido o inseguro: '{db_name}'"
        )

    return {
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_NAME": db_name,
        "DRIVER_NAME": driver_name,
    }


def init_database(env_path: Path | None = None) -> bool:
    """Verifica y crea la base de datos `DB_NAME` si no existe.

    Retorna `True` si la base de datos fue creada, o `False` si ya existía.
    """
    creds = load_db_credentials(env_path)
    db_name = str(creds["DB_NAME"])

    postgres_url = URL.create(
        drivername=str(creds["DRIVER_NAME"]),
        username=str(creds["DB_USER"]),
        password=str(creds["DB_PASSWORD"]),
        host=str(creds["DB_HOST"]),
        port=int(creds["DB_PORT"]),
        database="postgres",
    )

    logger.info(
        "Conectando a PostgreSQL en %s:%s (base del sistema 'postgres')...",
        creds["DB_HOST"],
        creds["DB_PORT"],
    )

    engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name},
            ).scalar()

            if exists:
                logger.info(
                    "La base de datos '%s' ya existe. No se realizaron modificaciones.",
                    db_name,
                )
                return False

            logger.info(
                "La base de datos '%s' no existe. Procediendo a crearla...",
                db_name,
            )
            connection.execute(text(f'CREATE DATABASE "{db_name}";'))
            logger.info(
                "Base de datos '%s' creada exitosamente.",
                db_name,
            )
            return True
    finally:
        engine.dispose()


if __name__ == "__main__":
    init_database()
