# DevExpert AI

Plataforma de gestión de partners desarrollada con **FastAPI**, **SQLAlchemy 2.0 async** y **PostgreSQL 16**. Proyecto del curso AI Expert.

## Descripción

DevExpert AI es una aplicación web que permite gestionar el ciclo completo de un programa de partners: registro, revisión, aprobación, entidades de facturación y facturas. Incluye un panel de administración interno con autenticación y un portal para que los propios partners consulten su información.

## Arquitectura

El proyecto sigue una separación estricta en tres capas:

```
router → repository → database
```

- **`models.py`** — Modelos ORM de SQLAlchemy (`InternalUser`, `Partner`, `BillingEntity`, `Invoice`). Los ENUMs de PostgreSQL (`InternalRole`, `PartnerStatus`, `InvoiceType`, `InvoiceStatus`) se definen aquí como objetos `PgEnum`.
- **`schemas/`** — Modelos Pydantic por entidad (`*Create`, `*Update`, `*Response`). `InternalUserResponse` omite intencionadamente `password_hash`.
- **`repositories/`** — Funciones de acceso a la BD (async). Reciben una `AsyncSession` y devuelven objetos ORM. Sin lógica de negocio.
- **`routers/`** — Instancias de `APIRouter` de FastAPI. Los routers JSON (`internal_user`, `partner`, `billing_entity`, `invoice`) usan `response_model` con esquemas Pydantic. El router `web` renderiza plantillas Jinja2 HTML para el flujo público `/register`.
- **`routers/admin.py`** — Panel de administración HTML en `/admin`. Usa `SessionMiddleware` (sesiones por cookie vía `itsdangerous`) y `passlib[bcrypt]` para autenticar `InternalUser`. La navegación lateral carga fragmentos de contenido vía htmx en `#content-area`.
- **`routers/partner_portal.py`** — Portal para partners en `/partner-portal`.
- **`database.py`** — Motor async único, factoría de sesiones `SessionLocal`, dependencia `get_db`.
- **`config.py`** — `pydantic-settings` lee la configuración desde `.env`.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| API | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| Driver BD | asyncpg |
| Base de datos | PostgreSQL 16 |
| Plantillas | Jinja2 |
| Frontend | htmx 2.0 + Bootstrap 5.3 |
| Autenticación | passlib[bcrypt] + itsdangerous |
| Configuración | pydantic-settings |
| Servidor | Uvicorn |

## Requisitos previos

- Python ≥ 3.13
- PostgreSQL 16
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes)

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Maegor/devexpertai.git
cd devexpertai

# Instalar dependencias (incluidas las de desarrollo)
uv sync --dev
```

## Configuración

Crea un fichero `.env` en la raíz del proyecto con las siguientes variables:

```env
DB_HOST=localhost
DB_NAME=dxpromoter
DB_USER=admin
DB_PASSWORD=tu_contraseña
```

Las tablas de la base de datos se crean automáticamente al arrancar la aplicación gracias a `Base.metadata.create_all` en el handler `lifespan` de `main.py`.

## Ejecución

```bash
# Iniciar el servidor de desarrollo
.venv/bin/uvicorn main:app --reload
```

La API estará disponible en `http://localhost:8000`.

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Health check |
| `*` | `/api/internal-users` | CRUD de usuarios internos |
| `*` | `/api/partners` | CRUD de partners |
| `*` | `/api/billing-entities` | CRUD de entidades de facturación |
| `*` | `/api/invoices` | CRUD de facturas |
| `GET` | `/register` | Formulario público de registro de partners |
| `*` | `/admin` | Panel de administración (requiere login) |
| `*` | `/partner-portal` | Portal de partners |

La documentación interactiva de la API (Swagger UI) está disponible en `http://localhost:8000/docs`.

## Tests

Los tests usan `httpx.AsyncClient` con `ASGITransport` (sin servidor HTTP real). El fixture `conftest.py` sobreescribe `get_db` con una sesión de test que apunta a la base de datos `dxpromoter` real y elimina los datos de test tras cada prueba.

```bash
# Ejecutar todos los tests
.venv/bin/pytest

# Ejecutar un fichero de tests concreto
.venv/bin/pytest tests/test_internal_users.py

# Ejecutar un test por nombre
.venv/bin/pytest tests/test_internal_users.py::test_crear_usuario
```

## Estructura del proyecto

```
devexpertai/
├── main.py                  # Punto de entrada de la aplicación
├── config.py                # Configuración vía pydantic-settings
├── database.py              # Motor async y factoría de sesiones
├── models.py                # Modelos ORM de SQLAlchemy
├── repositories/            # Acceso a datos (async)
├── routers/                 # Routers FastAPI (API JSON + HTML)
│   ├── admin.py             # Panel de administración
│   ├── partner_portal.py    # Portal de partners
│   └── web.py               # Flujo público de registro
├── schemas/                 # Modelos Pydantic de entrada/salida
├── seeds/                   # Scripts de inicialización de datos
├── templates/               # Plantillas Jinja2
│   ├── base.html            # Layout de páginas públicas
│   ├── admin/               # Plantillas del panel de administración
│   └── ...
└── tests/                   # Tests de integración
```
