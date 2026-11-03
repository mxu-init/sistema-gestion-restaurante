# sistema-gestion-restaurante

Backend del sistema de gestión para restaurantes (ERP / API REST).

---

## Configuración del entorno (.env)

El proyecto utiliza variables de entorno para gestionar credenciales y configuraciones sensibles según el entorno de ejecución (Tarea **SGR-43**).

### 1. Crear el archivo `.env` local

Copia la plantilla predefinida [`.env.example`](.env.example) a la raíz del proyecto como `.env`:

```bash
# En Linux / macOS / Git Bash:
cp .env.example .env

# En Windows (PowerShell):
Copy-Item .env.example .env
```

### 2. Parámetros requeridos

Edita el archivo `.env` recién creado con los valores correspondientes a tu entorno local:

#### Base de Datos (PostgreSQL)
* `DB_HOST`: Host del servidor PostgreSQL (ej. `localhost`).
* `DB_PORT`: Puerto de conexión a la base de datos (por defecto `5432`).
* `DB_NAME`: Nombre de la base de datos (ej. `sgr_db`).
* `DB_USER`: Usuario con permisos sobre la base de datos (ej. `sgr_user`).
* `DB_PASSWORD`: Contraseña del usuario de PostgreSQL.
* `DRIVER_NAME`: Driver de SQLAlchemy utilizado por la aplicación (`postgresql+psycopg`).

#### Autenticación y Seguridad (JWT)
* `SECRET_KEY`: Clave secreta aleatoria y segura utilizada para firmar los tokens JWT.
* `ALGORITHM`: Algoritmo de cifrado/firmado de tokens (por defecto `HS256`).
* `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de vida de los tokens de acceso en minutos (ej. `30`).

#### Integración Jira Cloud
* `JIRA_URL`: URL base de la instancia de Jira Cloud (ej. `https://tu-organizacion.atlassian.net`).
* `JIRA_USER_EMAIL`: Correo electrónico de la cuenta de Atlassian del desarrollador.
* `JIRA_API_TOKEN`: Token de API generado desde [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens).

---

## Herramientas de DX y Automatización con Jira

El proyecto cuenta con una utilidad CLI para la experiencia de desarrollo (DX) ubicada en [`scripts/jira_integration.py`](scripts/jira_integration.py). Esta herramienta interactúa con la API REST de Jira Cloud mediante la librería `atlassian-python-api` para sincronizar el estado de las tareas sin salir de la terminal.

### Comandos principales

#### 1. Asignar tarea (`assign`)
Asigna la incidencia indicada al usuario actualmente autenticado:
```bash
python scripts/jira_integration.py assign SGR-43
```

#### 2. Transicionar estado (`transition`)
Mueve el estado de una incidencia al estado o transición indicada (ej. `In Review`, `Done`, `In Progress`):
```bash
python scripts/jira_integration.py transition SGR-43 "In Review"
```

#### 3. Comentar enlace de Pull Request (`comment`)
Publica un comentario formateado en Jira con el enlace al Pull Request de GitHub y una nota opcional:
```bash
python scripts/jira_integration.py comment SGR-43 https://github.com/usuario/sistema-gestion-restaurante/pull/43 --note "Implementación de variables de entorno lista para revisión"
```

#### 4. Sincronización completa en un solo paso (`sync`)
Combina asignación, cambio de estado y publicación de PR en un único comando:
```bash
python scripts/jira_integration.py sync SGR-43 \
  --assign \
  --status "In Review" \
  --pr https://github.com/usuario/sistema-gestion-restaurante/pull/43 \
  --note "Listo para code review"
```

#### 5. Inspeccionar información de tarea (`info`)
Muestra el resumen, estado actual, asignado y transiciones disponibles de una tarea:
```bash
python scripts/jira_integration.py info SGR-43
```

> **Nota:** Puedes usar el argumento global `--env-file ruta/al/.env` si tu archivo de variables de entorno se encuentra en una ubicación personalizada.

### Pruebas Unitarias de DX

La suite de tests unitarios del script valida la carga de credenciales, transiciones, asignaciones, comentarios y control de errores HTTP. Para ejecutarla:

```bash
python -m unittest scripts/test_jira_integration.py
```

O utilizando `pytest`:
```bash
pytest scripts/test_jira_integration.py
```

---

## Guía de commits

Este repositorio está protegido por un **guardián de commits** construido con
[pre-commit](https://pre-commit.com/). El guardián se ejecuta en local en cada
`git commit` y **rechaza** cualquier mensaje que no cumpla las reglas siguientes,
para que el historial sea coherente y esté escrito en inglés.

### Instalar el guardián (una vez por clonación local)

```bash
pip install pre-commit
pre-commit install
```

### Formato del mensaje

```
<type>(<scope>): <asunto escrito en inglés, empieza en minúscula, máx 100 caracteres>
```

| Regla | Detalle |
| --- | --- |
| Formato | Conventional Commits: `type(scope): subject` |
| Tipos | `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test` |
| Asunto | empieza en minúscula, sin punto final, sin espacios al final, máximo **100** caracteres |
| Cuerpo | opcional; separado del asunto por una línea en blanco, máximo **100** caracteres por línea (los trailers como `Signed-off-by:` están exentos) |
| Idioma | **Solo inglés**: se rechazan palabras en español y caracteres con tilde (`á é í ó ú ü ñ ¿ ¡`) |
| Scope | opcional, en minúsculas con guiones (`auth`, `db`, `api-endpoints`) |
| Excepciones | los mensajes generados por git (`Merge ...` / `Revert "..."`) se aceptan tal cual |

### Ejemplos

**Aceptados**

```bash
git commit -m "feat(auth): add login endpoint"
git commit -m "fix(db): correct nullable column"
git commit -m "docs: update installation guide"
```

**Rechazados**

```bash
git commit -m "first commit"
git commit -m "feat: Add users."
git commit -m "fix: corrección del login"
git commit -m "arreglo: cosa rara"
```

### Validar un mensaje manualmente

```bash
pre-commit run commit-msg --hook-stage commit-msg --commit-msg-filename ruta/al/mensaje.txt
```

El guardián vive en [`scripts/check_commit_msg.py`](scripts/check_commit_msg.py)
y su configuración en [`.pre-commit-config.yaml`](.pre-commit-config.yaml).
