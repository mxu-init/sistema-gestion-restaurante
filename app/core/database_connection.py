from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings


#Es la conexión principal hacia PostgreSQL.
engine = create_engine (settings.database_url, echo=True)

#Es el generador de sesiones que luego usarán los endpoints para hablar con la DB
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# Es una dependencia de FastAPI que: abre sesión, la entrega al endpoint,
# y cierra la sesión automáticamente.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()