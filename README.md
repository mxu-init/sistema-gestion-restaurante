# 🍽️ Ratatouille ERP - Sistema de Gestión Operativa de Restaurantes

> Backend modular y escalable para un sistema **ERP (Enterprise Resource Planning)** especializado en la gestión operativa de restaurantes. Desarrollado en **Python** con **FastAPI** y **PostgreSQL**, implementando una arquitectura por capas limpia, control de alérgenos según normativa de la UE, cálculo dinámico de disponibilidad y documentación interactiva mediante **Swagger UI**.

---

## 📖 Descripción del Proyecto

**Ratatouille ERP** centraliza los procesos operativos de un restaurante en una API REST de alto rendimiento. En su versión actual correspondiente a la rama `dev`, el sistema proporciona una gestión integral de la carta gastronómica, categorización, catálogo de alérgenos y cálculo dinámico de la disponibilidad de menús en tiempo real.

### 🌟 Módulos y Funcionalidades Activas

- 📋 **Gestión de Carta y Alérgenos:**
  - Catálogo de platos clasificados por categorías fijas en base de datos (*Entrantes, Primeros, Segundos, Postres, Bebidas*).
  - Alertas automáticas (`has_allergens`) basadas en el catálogo oficial de los 14 alérgenos de declaración obligatoria de la Unión Europea.
  - Asignación flexible de alérgenos por ID mediante relaciones intermedias (`dish_allergens`).
  - Control de disponibilidad operativa por falta de ingredientes (`is_available`) sin alterar la persistencia del plato.
  - Soporte de subida y almacenamiento de imágenes en servidor local (`/static/uploads`).
  - Borrado lógico (*soft delete*) preservando la integridad referencial histórica.

- 📜 **Menús Dinámicos:**
  - Creación y composición de menús (diarios o especiales) integrados por platos existentes en la carta.
  - **Disponibilidad efectiva calculada en tiempo real:** si alguno de los platos que componen un menú se agota o se desactiva (`is_available = false`), el menú se marca automáticamente como no disponible.

- 🛡️ **Respuestas Uniformes y Control de Errores:**
  - Respuestas estandarizadas en español con manejo granular de códigos HTTP (`400`, `404`, `409`, `422`).
  - Validación tipada de esquemas en entrada y salida con Pydantic v2.

---

## 🛠️ Stack Tecnológico y Herramientas

El proyecto está construido bajo los estándares más modernos del ecosistema Python:

| Categoría | Tecnologías y Herramientas |
| :--- | :--- |
| **Backend & API** | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Starlette](https://img.shields.io/badge/Starlette-000000?style=for-the-badge&logo=starlette&logoColor=white) ![Uvicorn](https://img.shields.io/badge/uvicorn-%232D3748.svg?style=for-the-badge&logo=gunicorn&logoColor=white) |
| **Database & ORM** | ![PostgreSQL](https://img.shields.io/badge/postgresql-4169e1?style=for-the-badge&logo=postgresql&logoColor=white) ![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-%23D71F00.svg?style=for-the-badge&logo=sqlalchemy&logoColor=white) ![Alembic](https://img.shields.io/badge/alembic-4A154B?style=for-the-badge) ![Psycopg3](https://img.shields.io/badge/psycopg3-2F6792?style=for-the-badge&logo=postgresql&logoColor=white) |
| **Testing & BDD** | ![Pytest](https://img.shields.io/badge/pytest-%230A9EDC.svg?style=for-the-badge&logo=pytest&logoColor=white) ![BDD Gherkin](https://img.shields.io/badge/BDD-Gherkin-00A86B?style=for-the-badge) |
| **Documentation & Standards** | ![Swagger UI](https://img.shields.io/badge/Swagger_UI-85EA2D?style=for-the-badge&logo=swagger&logoColor=black) ![OpenAPI](https://img.shields.io/badge/OpenAPI_3.1-6BA539?style=for-the-badge&logo=openapiinitiative&logoColor=white) ![Clean Code](https://img.shields.io/badge/Design-Clean_Architecture-blue?style=for-the-badge) |
| **Control de Versiones & QA** | ![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![Pre-Commit](https://img.shields.io/badge/pre--commit-FAB040?style=for-the-badge&logo=pre-commit&logoColor=black) |

<br />

| Tecnología / Librería | Versión | Propósito en el Proyecto |
| :--- | :--- | :--- |
| **[FastAPI](https://fastapi.tiangolo.com/)** | `^0.162.0` | Framework web asíncrono para el desarrollo de APIs REST de alto rendimiento y tipado estricto. |
| **[Uvicorn](https://www.uvicorn.org/)** | `^0.54.0` | Servidor ASGI para ejecutar la aplicación en entornos locales y de producción. |
| **[PostgreSQL](https://www.postgresql.org/)** | `14+` | Sistema gestor de base de datos relacional para garantizar integridad referencial y transacciones ACID. |
| **[SQLAlchemy](https://www.sqlalchemy.org/)** | `^2.1.6` | ORM declarativo para modelado relacional y consultas estructuradas en base de datos. |
| **[Alembic](https://alembic.sqlalchemy.org/)** | `^1.20.1` | Control de versiones y migraciones automáticas del esquema de base de datos y datos fijos. |
| **[Pydantic v2](https://docs.pydantic.dev/)** | `^2.14.1` | Validación, parseo y serialización de datos de entrada y salida con esquemas tipados. |
| **[Psycopg 3](https://www.psycopg.org/psycopg3/)** | `^3.3.6` | Adaptador y driver nativo de alto rendimiento para la conexión con PostgreSQL. |
| **[Pytest & Pytest-BDD](https://pytest-bdd.readthedocs.io/)** | - | Framework de testing unitario y ejecución de pruebas de comportamiento basadas en escenarios Gherkin. |

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
1. **Borrado Lógico (*Soft Delete*):** Platos y menús no se eliminan físicamente; registran una marca temporal `deleted_at`. Toda consulta del sistema omite de forma transparente los elementos dados de baja.
2. **Desactivación vs. Eliminación:** Modificar `is_available` es una acción operativa reversible (ej. falta momentánea de un ingrediente o producto). La eliminación lógica marca el registro como retirado de forma permanente.
3. **Disponibilidad Computada:** La disponibilidad de un menú no se duplica estáticamente en base de datos; se evalúa dinámicamente según el estado de disponibilidad de cada uno de sus platos asociados.
4. **Respuestas de Error Uniformes:** Mensajes claros y contextualizados en español con códigos HTTP normalizados (`400` Bad Request, `404` Not Found, `409` Conflict, `422` Unprocessable Entity).

---

## 📂 Estructura del Repositorio

```text
gestion_restaurante/
├── alembic/                     # Control de versiones del esquema y datos
│   ├── versions/                # Revisiones: creación de tablas, relaciones y datos base
│   ├── env.py                   # Conexión de Alembic con los modelos de app/models
│   └── script.py.mako
├── app/
│   ├── api/                     # Rutas FastAPI (APIRouter) y documentación Swagger
│   │   ├── dish_routes.py       # CRUD de platos y asignación de alérgenos
│   │   ├── category_routes.py   # Endpoints de categorías de la carta
│   │   ├── allergen_routes.py   # Endpoints de consulta de alérgenos
│   │   ├── menu_routes.py       # Endpoints de gestión y consulta de menús
│   │   └── test_routes.py       # Endpoint de healthcheck y plantilla
│   ├── controllers/             # Orquestación de casos de uso
│   │   └── test_controller.py
│   ├── services/                # Lógica de negocio y consultas SQLAlchemy
│   │   ├── dish_service.py      # Lógica de platos, alérgenos asociados y carga optimizada
│   │   ├── category_service.py  # Lógica de categorías de la carta
│   │   ├── allergen_service.py  # Validación y consulta de alérgenos
│   │   ├── menu_service.py      # Lógica de menús y cálculo de disponibilidad
│   │   ├── image_service.py     # Manejo de subida y almacenamiento de imágenes
│   │   └── reference_service.py # Verificación y restauración de datos fijos al arrancar
│   ├── models/                  # Modelos relacionales ORM (SQLAlchemy)
│   │   ├── __init__.py          # Registro central de modelos y relaciones
│   │   ├── category_model.py    # Tabla categories
│   │   ├── dish_model.py        # Tabla dishes con deleted_at e is_available
│   │   ├── allergen_model.py    # Tabla allergens
│   │   ├── dish_allergen_model.py # Tabla intermedia dish_allergens
│   │   └── menu_model.py        # Tabla menus y relaciones con platos
│   ├── schemas/                 # Esquemas Pydantic (Create, Update, Response)
│   │   ├── dish_schema.py
│   │   ├── category_schema.py
│   │   ├── allergen_schema.py
│   │   └── menu_schema.py
│   ├── core/                    # Configuración global y conexiones
│   │   ├── config.py            # Variables de entorno y ajustes generales
│   │   ├── database_connection.py # Engine, sesión y get_db
│   │   ├── exceptions.py        # Excepciones de dominio (NotFoundError, ConflictError)
│   │   └── reference_data.py    # Categorías base y 14 alérgenos UE (fuente única)
│   └── main.py                  # Instancia FastAPI, lifespan y registro de routers
├── scripts/                     # Scripts de utilidad y validación
│   ├── seed_data.py             # Carga opcional de platos de ejemplo
│   └── check_commit_msg.py      # Verificador de Conventional Commits
├── tests/                       # Pruebas automáticas y escenarios BDD
│   ├── conftest.py              # Fixtures y base de datos SQLite en memoria
│   ├── test_dishes_bdd.py       # Steps BDD para platos y alérgenos
│   ├── test_menus_bdd.py        # Steps BDD para menús y disponibilidad
│   └── features/                # Archivos .feature en lenguaje Gherkin
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
Crea el archivo `.env` en la raíz del proyecto con los parámetros de conexión a tu base de datos:
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

### 6. Aplicar Migraciones y Cargar Datos Fijos
```bash
alembic upgrade head
```
Este comando crea el esquema relacional e inserta los **datos fijos**: las 5 categorías base (*Entrantes, Primeros, Segundos, Postres, Bebidas*) y los **14 alérgenos de declaración obligatoria** de la UE. Además, el servicio de referencia comprueba su existencia en cada arranque del servidor.

*(Opcional)* Carga de platos de ejemplo:
```bash
python -m scripts.seed_data
```

### 7. Iniciar el Servidor de Desarrollo
```bash
uvicorn app.main:app --reload
```

---

## 📚 Documentación Interactiva de la API

Una vez iniciado el servidor, accede a los exploradores interactivos autogenerados:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Comprobación de Estado (Health):** [http://localhost:8000/health](http://localhost:8000/health)
- **Health Check de Base de Datos:** [http://localhost:8000/health/db](http://localhost:8000/health/db)

---

## 🧪 Pruebas Automáticas y Escenarios BDD

El proyecto cuenta con una suite completa de pruebas automáticas escritas en **Gherkin (BDD)** e implementadas con **`pytest`** y **`pytest-bdd`**.

### Características de las pruebas:
- **Base de datos independiente:** Los tests se ejecutan sobre una base de datos SQLite en memoria (`sqlite:///:memory:` con `StaticPool`), completamente aislada de la base de datos de desarrollo (PostgreSQL).
- **Semilla automática:** Se inicializan las categorías base y alérgenos de forma automática en cada sesión de pruebas.
- **Escenarios Gherkin:** Los criterios de aceptación de platos y menús están documentados en archivos `.feature` dentro de `tests/features/` siguiendo la sintaxis *Dado / Cuando / Entonces* e incluyen casos de éxito y de error (`400`, `404`, `409`, `422`).

### Ejecución de los tests:

Ejecutar toda la suite de pruebas:
```bash
pytest
```

Ejecutar con salida detallada (*verbose*):
```bash
pytest -v
```

Ejecutar únicamente los escenarios de menús o de platos:
```bash
pytest tests/test_menus_bdd.py -v
pytest tests/test_dishes_bdd.py -v
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
git commit -m "fix(menus): recalculate availability when dishes are updated"
git commit -m "docs(api): update swagger descriptions for allergens"
```

---

## 🚀 Próximas Implementaciones (Roadmap)

En las siguientes iteraciones y sprints del proyecto se incorporarán los módulos y tecnologías que completan la visión integral del ERP. Cabe destacar que algunas de estas funcionalidades (como la autenticación) ya se encuentran desarrolladas en ramas de trabajo independientes y serán integradas en la rama principal próximamente:

- 🔐 **Autenticación y Control de Acceso (RBAC):**
  - Implementación de login seguro mediante OAuth2 con **JSON Web Tokens (JWT)** y hashing de contraseñas con **Argon2** (`pwdlib[argon2]`).
  - Roles jerárquicos: `super_admin`, `manager`, `staff` y comensal/público.
- 🪑 **Distribución y Gestión de Mesas:**
  - Administración de aforos según ubicación (*indoor* / *outdoor*), capacidad estándar y capacidad máxima admisible.
- 📅 **Motor de Reservas y Gestión de Capacidad:**
  - Máquina de estados para reservas (`pending`, `confirmed`, `waitlist`, `seated`, `cancelled`, `no_show`).
  - Prevención de duplicidades y solapamientos de reservas por mesa y teléfono en la misma franja horaria.
  - Gestión automatizada de listas de espera (*waitlist*) y detección de reservas no presentadas mediante tiempo de gracia.
- ⏰ **Gestión de Turnos y Horarios del Personal:**
  - Planificación de turnos de mañana/tarde y rotaciones de plantilla.

---

## 👥 Equipo de Desarrollo

El proyecto ha sido desarrollado por los siguientes integrantes (en orden alfabético):

| Foto | Colaborador | Perfil de GitHub |
| :---: | :--- | :--- |
| <img src="https://github.com/kvadrakola.png?size=64" width="50" height="50" style="border-radius: 50%;" alt="Kanstantsin Mlechka" /> | **Kanstantsin Mlechka** | [@kvadrakola](https://github.com/kvadrakola) |
| <img src="https://github.com/Marisa-Ruiz.png?size=64" width="50" height="50" style="border-radius: 50%;" alt="Marisa Ruiz" /> | **Marisa Ruiz** | [@Marisa-Ruiz](https://github.com/Marisa-Ruiz) |
| <img src="https://github.com/mxu-init.png?size=64" width="50" height="50" style="border-radius: 50%;" alt="Mauricio Rodríguez" /> | **Mauricio Rodríguez** | [@mxu-init](https://github.com/mxu-init) |
| <img src="https://github.com/moigarcia00.png?size=64" width="50" height="50" style="border-radius: 50%;" alt="Moisés García Sanz" /> | **Moisés García Sanz** | [@moigarcia00](https://github.com/moigarcia00) |
| <img src="https://github.com/simonlopez25.png?size=64" width="50" height="50" style="border-radius: 50%;" alt="Simón López" /> | **Simón López** | [@simonlopez25](https://github.com/simonlopez25) |

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia correspondiente al plan formativo y operativo de la organización. Todos los derechos reservados.
