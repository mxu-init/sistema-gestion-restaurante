# 🍽️ Ratatouille ERP - Sistema de Gestión Operativa de Restaurantes

> Backend robusto y escalable para un sistema **ERP (Enterprise Resource Planning)** especializado en la gestión integral y operativa de restaurantes. Desarrollado en **Python** con **FastAPI** y **PostgreSQL**, implementando una arquitectura modular por capas, control de acceso basado en roles (**RBAC**), borrado lógico y documentación interactiva mediante **Swagger UI**.

---

## 📖 Descripción del Proyecto

**Ratatouille ERP** centraliza los flujos de trabajo críticos de un restaurante en una única plataforma backend orientada a servicios API REST. El sistema optimiza la administración de la carta gastronómica, el cálculo dinámico de menús, la asignación eficiente de mesas y el ciclo de vida de las reservas, asegurando integridad transaccional, trazabilidad y alta disponibilidad de datos.

### 🌟 Módulos y Funcionalidades Principales

- 📋 **Gestión de Carta y Alérgenos:**
  - Catálogo de platos clasificados por categorías fijas en base de datos (*Entrantes, Primeros, Segundos, Postres, Bebidas*).
  - Alertas automáticas (`has_allergens`) basadas en el catálogo oficial de los 14 alérgenos de declaración obligatoria.
  - Control de disponibilidad por falta de ingredientes (`is_available`) sin alterar la persistencia del plato.
  - Consulta pública accesible para comensales sin necesidad de autenticación.

- 📜 **Menús Dinámicos:**
  - Creación de menús especiales o diarios compuestos por platos existentes en la carta.
  - **Disponibilidad efectiva calculada en tiempo real:** si un plato integrante se desactiva o agota, el menú se desactiva de forma automática.

- 🪑 **Distribución de Mesas y Control de Aforos:**
  - Clasificación de mesas según ubicación (*indoor* / *outdoor*), capacidad estándar y capacidad máxima admisible.
  - Bloqueo de asignación para mesas temporalmente inactivadas.

- 📅 **Motor de Reservas y Gestión de Capacidad:**
  - Reservas configurables por franjas horarias (por defecto 1 hora en punto).
  - Prevención estricta de solapamiento: sin dobles reservas en una misma mesa ni duplicación de reserva por número telefónico.
  - **Máquina de estados de reserva:** `pending` ➔ `confirmed` ➔ `seated` (comensal sentado) / `cancelled` / `no_show`.
  - **Lista de espera (*Waitlist*):** Encolado automático sin mesa asignada cuando no existe aforo libre, con reasignación ágil al liberarse plazas.
  - **Tiempo de gracia y detección de no-shows:** Marcado de reservas no presentadas tras el margen de cortesía (5 minutos) liberando automáticamente la mesa para el servicio.

- 🔐 **Autenticación y Seguridad (RBAC):**
  - Autenticación OAuth2 basada en JSON Web Tokens (**JWT**) con expiración configurable.
  - Hash criptográfico de contraseñas mediante **Argon2**.
  - Jerarquía de roles: `super_admin` (acceso total y borrado lógico), `manager` (maître/jefe de cocina: carta, mesas y precios), `staff` (camareros: consulta y gestión de reservas) y acceso `público` (consulta de carta).

---

## 🛠️ Stack Tecnológico y Herramientas

El proyecto está construido bajo los estándares más modernos del ecosistema Python para APIs de alto rendimiento:

| Categoría | Tecnologías y Herramientas |
| :--- | :--- |
| **Backend & API** | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Starlette](https://img.shields.io/badge/Starlette-000000?style=for-the-badge&logo=starlette&logoColor=white) ![Uvicorn](https://img.shields.io/badge/uvicorn-%232D3748.svg?style=for-the-badge&logo=gunicorn&logoColor=white) |
| **Database & ORM** | ![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-%23D71F00.svg?style=for-the-badge&logo=sqlalchemy&logoColor=white) ![Alembic](https://img.shields.io/badge/alembic-4A154B?style=for-the-badge) ![Psycopg3](https://img.shields.io/badge/psycopg3-2F6792?style=for-the-badge&logo=postgresql&logoColor=white) |
| **Validation & Security** | ![Pydantic](https://img.shields.io/badge/Pydantic_v2-e92063?style=for-the-badge&logo=pydantic&logoColor=white) ![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens) ![Argon2](https://img.shields.io/badge/Argon2-Password_Hash-4B3263?style=for-the-badge) |
| **Documentation & Standards** | ![Swagger UI](https://img.shields.io/badge/Swagger_UI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black) ![OpenAPI](https://img.shields.io/badge/OpenAPI_3.1-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white) ![Clean Code](https://img.shields.io/badge/Design-Clean_Architecture-blue?style=for-the-badge) |
| **Control de Versiones & QA** | ![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![Pre-Commit](https://img.shields.io/badge/pre--commit-FAB040?style=for-the-badge&logo=pre-commit&logoColor=black) |

<br />

| Tecnología / Librería | Versión | Propósito en el Proyecto |
| :--- | :--- | :--- |
| **[FastAPI](https://fastapi.tiangolo.com/)** | `^0.162.0` | Framework web asíncrono para el desarrollo de APIs REST de alto rendimiento y tipado estricto. |
| **[Uvicorn](https://www.uvicorn.org/)** | `^0.54.0` | Servidor ASGI ultrarrápido para ejecutar la aplicación en entornos locales y de producción. |
| **[PostgreSQL](https://www.postgresql.org/)** | `14+` | Sistema de gestión de bases de datos relacional para garantizar integridad referencial y ACID. |
| **[SQLAlchemy](https://www.sqlalchemy.org/)** | `^2.1.6` | ORM declarativo para modelado relacional y consultas estructuradas en base de datos. |
| **[Alembic](https://alembic.sqlalchemy.org/)** | `^1.20.1` | Herramienta de control de versiones y migraciones de esquemas de base de datos. |
| **[Pydantic v2](https://docs.pydantic.dev/)** | `^2.14.1` | Validación, parseo y serialización de datos de entrada y salida con esquemas tipados. |
| **[PyJWT](https://pyjwt.readthedocs.io/) & Argon2** | - | Emisión y validación segura de tokens JWT para autenticación stateless y hash irreversible de credenciales. |
| **[Psycopg 3](https://www.psycopg.org/psycopg3/)** | `^3.3.6` | Adaptador y driver nativo de alto rendimiento para la conexión con PostgreSQL. |

---

## 🏛️ Arquitectura del Sistema y Patrones de Diseño

El backend adopta una arquitectura en capas desacoplada (**Layered Architecture**), donde cada nivel posee una responsabilidad única y aislada:

```
Petición Cliente
       │
       ▼
 ┌────────────┐
 │    api/    │  ➔ Enrutamiento FastAPI (APIRouter), documentación Swagger, validación de schemas de entrada
 └─────┬──────┘
       ▼
 ┌────────────┐
 │controllers/│  ➔ Orquestación de casos de uso y preparación de la respuesta HTTP
 └─────┬──────┘
       ▼
 ┌────────────┐
 │  services/ │  ➔ Lógica pura de negocio, reglas de validación y consultas a SQLAlchemy
 └─────┬──────┘
       ▼
 ┌────────────┐
 │   models/  │  ➔ Entidades SQLAlchemy mapeadas a tablas PostgreSQL con soporte de borrado lógico
 └─────┬──────┘
       ▼
  PostgreSQL
```

### Reglas Clave de Dominio
1. **Borrado Lógico (*Soft Delete*):** Platos, menús y usuarios nunca se eliminan físicamente; registran una marca temporal `deleted_at`. Toda consulta del sistema omite de forma transparente los elementos dados de baja.
2. **Desactivación vs. Eliminación:** Cambiar `is_available` o `is_active` es una operación operativa reversible (ej. falta puntual de un ingrediente). La eliminación lógica queda reservada con exclusividad al `super_admin`.
3. **Disponibilidad Computada:** La disponibilidad de una mesa o un menú no se duplica en base de datos; se evalúa dinámicamente según reservas activas y estado de los platos componentes.
4. **Respuestas de Error Uniformes:** Errores consistentes en español con códigos HTTP normalizados (`401` Unauthorized, `403` Forbidden, `404` Not Found, `409` Conflict, `422` Unprocessable Entity).

---

## 📂 Estructura del Repositorio

```text
sistema-gestion-restaurante/
├── alembic/                     # Control de versiones del esquema y datos
│   ├── versions/                # 8 revisiones: tablas, columna legacy y datos fijos
│   │   ├── c23d2bf3b75a_...     # elimina la columna legacy dishes.allergens
│   │   └── aacc49216385_...     # inserta categorías base y alérgenos UE
│   ├── env.py                   # Conecta Alembic con los modelos de app/models
│   └── script.py.mako
├── app/
│   ├── api/                     # Rutas FastAPI (APIRouter) y documentación Swagger
│   │   ├── dish_routes.py       # CRUD de platos y asignación de alérgenos
│   │   ├── category_routes.py   # Endpoints de categorías de carta
│   │   ├── allergen_routes.py   # Endpoints de alérgenos
│   │   └── test_routes.py       # Endpoint de plantilla
│   ├── controllers/             # Orquestación de casos de uso
│   │   └── test_controller.py
│   ├── services/                # Lógica de negocio y consultas SQLAlchemy
│   │   ├── dish_service.py      # Platos + allergen_ids + selectinload
│   │   ├── category_service.py
│   │   ├── allergen_service.py  # Validación y carga de alérgenos por ID
│   │   ├── image_service.py
│   │   └── reference_service.py # Restaura categorías y alérgenos en el arranque
│   ├── models/                  # Un archivo por tabla (SQLAlchemy)
│   │   ├── __init__.py          # Registro único de modelos (relaciones entre archivos)
│   │   ├── category_model.py    # categories
│   │   ├── dish_model.py        # dishes
│   │   ├── allergen_model.py    # allergens
│   │   ├── dish_allergen_model.py # dish_allergens (tabla intermedia)
│   │   └── test_model.py        # test (plantilla)
│   ├── schemas/                 # Esquemas Pydantic (Create, Update, Response)
│   │   ├── dish_schema.py
│   │   ├── category_schema.py
│   │   ├── allergen_schema.py
│   │   └── test_schema.py
│   ├── core/                    # Configuración global y conexión
│   │   ├── config.py            # Variables de entorno y ajustes generales
│   │   ├── database_connection.py # Engine, sesión y get_db
│   │   └── reference_data.py    # Categorías base y alérgenos UE (fuente única)
│   └── main.py                  # Instancia FastAPI, lifespan y registro de routers
├── scripts/                     # Scripts de utilidad y validación
│   ├── seed_data.py             # Carga opcional de los 15 platos de ejemplo
│   └── check_commit_msg.py      # Verificador de Conventional Commits
├── alembic.ini                  # Configuración de Alembic
├── .pre-commit-config.yaml      # Hooks de calidad y formato
├── requirements.txt             # Dependencias del proyecto
└── README.md                    # Documentación del proyecto
```

---

## ⚙️ Instalación y Puesta en Marcha Local

Sigue estos pasos para clonar, configurar y desplegar el backend en tu entorno local:

### 1. Requisitos Previos
- **Python 3.10** o versión superior instalada.
- Instancia activa de **PostgreSQL** (local o contenedor Docker).
- **Git** instalado.

### 2. Clonar el Repositorio
```bash
git clone https://github.com/tu-organizacion/gestion-restaurante.git
cd gestion-restaurante
```

### 3. Configurar el Entorno Virtual
- **En Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **En Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurar las Variables de Entorno
Crea el archivo `.env` en la raíz del proyecto con los valores correspondientes a tu base de datos y credenciales:
```env
APP_NAME="Ratatouille ERP"
APP_VERSION="1.0.0"
APP_DESCRIPTION="Sistema de gestion operativa de restaurantes"

# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=restaurante_erp_db
DB_USER=postgres
DB_PASSWORD=tu_password
DRIVER_NAME=postgresql+psycopg
```

### 6. Aplicar las Migraciones y los Datos Fijos
```bash
alembic upgrade head
```
Este comando crea el esquema e inserta los **datos fijos**: las 5 categorías base (*Entrantes, Primeros, Segundos, Postres, Bebidas*) y los **14 alérgenos de declaración obligatoria** de la UE. Además, el API los vuelve a comprobar en cada arranque por si faltara alguno.

Carga opcional de los 15 platos de ejemplo:
```bash
python -m scripts.seed_data
```

### 7. Iniciar el Servidor de Desarrollo
```bash
uvicorn app.main:app --reload
```

---

## 📚 Documentación Interactiva de la API

Una vez iniciado el servidor, accede a la documentación interactiva autogenerada para explorar y probar todos los endpoints:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)


> 💡 **Autenticación en Swagger:** Para consumir endpoints protegidos, pulsa el botón verde **Authorize** en Swagger UI e introduce el token JWT obtenido a través del endpoint `POST /auth/token`.

---

## Manejo Global de Excepciones y Errores (SGR-49)

La aplicación implementa una arquitectura centralizada de manejo de errores (`Transport-Agnostic`) que unifica el formato de respuesta HTTP, traduce errores de validación de Pydantic v2 y de PostgreSQL (`SQLSTATE`) al español, y evita filtraciones de trazas internas o datos sensibles.

### 1. Contrato estandarizado de respuesta (`ErrorResponse`)

Todas las respuestas de error (`4xx` y `5xx`, incluidas las validaciones `422`) devuelven un único esquema JSON estricto definido en [`app/schemas/errors.py`](app/schemas/errors.py):

```json
{
  "detail": "Error en el campo 'nombre': El campo es obligatorio"
}
```

Además, la generación del esquema OpenAPI 3.1 en [`app/main.py`](app/main.py) (`configure_openapi`) reemplaza automáticamente el `HTTPValidationError` por defecto de FastAPI por `#/components/schemas/ErrorResponse`.

### 2. Jerarquía de Excepciones de Dominio

Los servicios y casos de uso deben lanzar excepciones de dominio definidas en [`app/core/exceptions.py`](app/core/exceptions.py) (sin acoplarse a `fastapi.HTTPException`). Los manejadores globales en [`app/core/handlers.py`](app/core/handlers.py) las traducen al código de estado HTTP correspondiente:

| Excepción de Dominio | Código HTTP | Uso principal |
| --- | --- | --- |
| `NotFoundError` | `404 Not Found` | Recurso o entidad no encontrada |
| `ConflictError` | `409 Conflict` | Duplicados (`UNIQUE`) o conflicto de estado |
| `PermissionDeniedError` | `403 Forbidden` | Permisos insuficientes para la operación |
| `DomainValidationError` | `422 Unprocessable Content` | Reglas de negocio, claves foráneas (`FK`) o `CHECK` |
| `DatabaseRetryableError` | `503 Service Unavailable` | Deadlocks, timeouts o fallos transitorios de conexión |
| `InfrastructureError` | `500 Internal Server Error` | Fallos internos de infraestructura o configuración |

Ejemplo de uso en la capa de servicio:

```python
from app.core.exceptions import ConflictError, NotFoundError

if not mesa:
    raise NotFoundError("La mesa solicitada no existe.")
```

### 3. Traducción de errores SQLAlchemy / PostgreSQL y Rollback automático

El módulo [`app/core/error_translations.py`](app/core/error_translations.py) provee los gestores de contexto `handle_db_exceptions` (síncrono) y `handle_async_db_exceptions` (asíncrono) compatibles con `psycopg` v3 y `asyncpg`. Garantizan la ejecución de `session.rollback()` ante cualquier fallo y convierten códigos `SQLSTATE` (`23505`, `23503`, `23502`, `23514`, `40001`, `40P01`, etc.) en excepciones de dominio legibles en español:

```python
from app.core.error_translations import handle_db_exceptions

with handle_db_exceptions(session):
    session.add(nuevo_registro)
    session.commit()
```

### 4. Trazabilidad (`X-Request-ID`) y Logging Estructurado

En [`app/core/logging_config.py`](app/core/logging_config.py):
* **`CorrelationIdMiddleware`** (Pure ASGI): Lee o genera un identificador único en la cabecera `X-Request-ID` de cada petición/respuesta y lo propaga mediante `ContextVar` hacia todos los registros de log.
* **`redact_sensitive_data`**: Enmascara automáticamente contraseñas, tokens, claves API (`secret`, `password`, `token`, `authorization`) y cadenas de conexión DSN con `[REDACTED]` antes de escribir logs en formato JSON.

### 5. Ejecutar pruebas del sistema de errores

```bash
pytest tests/test_exception_handlers.py tests/test_db_exceptions.py
```

---

## 🛡️ Flujo de Contribución y Guía de Commits

Para preservar un historial de Git limpio y profesional, el repositorio implementa un hook de [pre-commit](https://pre-commit.com/) que valida el estándar **Conventional Commits**:

### 1. Activar el Guardián de Commits
```bash
pip install pre-commit
pre-commit install
```

### 2. Formato Requerido
```text
<type>(<scope>): <asunto en inglés, minúscula, imperativo y sin punto final>
```

| Tipo | Propósito |
| :--- | :--- |
| `feat` | Nueva funcionalidad incorporada |
| `fix` | Corrección de un fallo o bug |
| `refactor` | Reestructuración de código sin alterar su comportamiento externo |
| `test` | Incorporación o actualización de pruebas automáticas |
| `docs` | Actualización de documentación o estándares |
| `chore` | Tareas de configuración, scripts o mantenimiento de dependencias |

**Ejemplos de commits válidos:**
```bash
git commit -m "feat(dishes): add endpoint to toggle dish availability"
git commit -m "fix(reservations): prevent overlapping bookings on same table"
git commit -m "docs(api): update swagger descriptions for allergens"
```

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia correspondiente al plan formativo y operativo de la organización. Todos los derechos reservados.
