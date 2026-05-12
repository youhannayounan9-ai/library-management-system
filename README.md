# 📚 Library Management System

A production-grade RESTful API built with **FastAPI**, featuring JWT authentication, Role-Based Access Control (RBAC), Redis caching, Prometheus + Grafana monitoring, and a fully Dockerised five-service stack.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ Postgres │    │  Redis   │    │   FastAPI (API)  │  │
│  │  :5432   │◄───│  :6379   │◄───│      :8000       │  │
│  └──────────┘    └──────────┘    └────────┬─────────┘  │
│                                           │             │
│  ┌──────────────┐    ┌──────────────────┐ │             │
│  │   Grafana    │◄───│   Prometheus     │◄┘             │
│  │    :3000     │    │      :9090       │               │
│  └──────────────┘    └──────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.111 + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 15 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Caching | Redis 7 (cache-aside pattern) |
| Monitoring | Prometheus + Grafana |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio + SQLite |
| Containerisation | Docker + Docker Compose |

---

## 👥 Team

| Name | Role |
|---|---|
| *(Team Member 1)* | Backend API & Auth |
| *(Team Member 2)* | Database & Migrations |
| *(Team Member 3)* | Caching & Monitoring |
| *(Team Member 4)* | Testing & Docker |

---

## 🚀 Quick Start

### Prerequisites
- Docker Desktop ≥ 4.x
- Python 3.12+ (for local test runs)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd library-management-system
cp .env.example .env          # edit JWT_SECRET_KEY before production
```

### 2. Build & Launch (5 containers)

```bash
docker compose up -d --build
```

Expected containers:

```
library_db         postgres:15-alpine    Up    0.0.0.0:5432->5432/tcp
library_redis      redis:7-alpine        Up    0.0.0.0:6379->6379/tcp
library_api        local build           Up    0.0.0.0:8000->8000/tcp
library_prometheus prom/prometheus       Up    0.0.0.0:9090->9090/tcp
library_grafana    grafana/grafana       Up    0.0.0.0:3000->3000/tcp
```

### 3. Run Database Migrations

```bash
docker exec library_api alembic upgrade head
```

### 4. Run Tests (Local)

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Expected result: **21 passed**

---

## 🌐 Service URLs

| Service | URL | Credentials |
|---|---|---|
| Swagger UI | http://localhost:8000/docs | Bearer token |
| ReDoc | http://localhost:8000/redoc | — |
| Frontend | http://localhost:8000/ui | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3000 | admin / admin |
| Health Check | http://localhost:8000/health | — |
| Metrics | http://localhost:8000/metrics | — |

---

## 🔐 Authentication Flow

1. **Register**: `POST /auth/register` → `{"email": "...", "password": "...", "role": "member|admin"}`
2. **Login**: `POST /auth/login` → returns `{"access_token": "...", "token_type": "bearer"}`
3. **Use token**: In Swagger, click **Authorize** → enter `Bearer <token>`

### Demo Credentials (seeded on startup)

| Email | Password | Role |
|---|---|---|
| admin@library.com | admin123 | admin |
| member@library.com | member123 | member |

---

## 📋 API Endpoints

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /auth/register | ❌ | Register new user |
| POST | /auth/login | ❌ | Login, receive JWT |

### Books
| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | /books/ | ✅ | Any | List books (paginated, cached) |
| GET | /books/{id} | ✅ | Any | Get book by ID (cached) |
| POST | /books/ | ✅ | Admin | Create book |
| PUT | /books/{id} | ✅ | Admin | Update book |
| DELETE | /books/{id} | ✅ | Admin | Soft-delete book |

### Borrows
| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| POST | /borrows/{book_id} | ✅ | Member | Borrow a book |
| POST | /borrows/return/{id} | ✅ | Member | Return a book |
| GET | /borrows/my-history | ✅ | Member | View borrow history (cached) |

### Admin
| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | /admin/users | ✅ | Admin | List all users |
| GET | /admin/borrows | ✅ | Admin | View all borrow records |

---

## ✅ Rubric Compliance Map

| Rubric Requirement | Implementation | File(s) |
|---|---|---|
| **JWT Authentication** | `python-jose` HS256 tokens; live DB lookup on every request (not JWT claims) | `app/dependencies.py`, `app/services/auth_service.py` |
| **RBAC** | `require_admin` dependency enforces `role == "admin"` at route level; `admin_required` alias used in books/admin routers | `app/dependencies.py`, `app/routers/books.py`, `app/routers/admin.py` |
| **Database (PostgreSQL)** | Async SQLAlchemy 2.0 engine + `async_sessionmaker`; Alembic migrations | `app/database.py`, `alembic/` |
| **Input Validation** | Pydantic v2 schemas with field validators; duplicate ISBN check; borrow limit enforcement | `app/schemas/`, `app/services/borrow_service.py` |
| **Caching (Redis)** | Cache-aside pattern on `GET /books/` and `GET /borrows/my-history`; invalidated on write | `app/redis_client.py`, `app/routers/books.py`, `app/routers/borrows.py` |
| **Monitoring** | `prometheus-fastapi-instrumentator` exposes `/metrics`; Grafana visualises request rate, latency, error rate | `app/main.py`, `prometheus.yml`, Grafana dashboard |
| **Testing** | 21 pytest tests across auth, books, RBAC; SQLite in-memory override; Redis mocked | `tests/`, `tests/conftest.py` |
| **Docker** | 5-service Compose stack: API, PostgreSQL, Redis, Prometheus, Grafana | `Dockerfile`, `docker-compose.yml` |
| **Frontend** | Static HTML/JS served at `/ui` via `StaticFiles` | `frontend/` |
| **Swagger UI** | Clean APIKeyHeader Bearer input (no OAuth2 modal); full OpenAPI schema at `/docs` | `app/dependencies.py`, `app/main.py` |

---

## 🗂️ Project Structure

```
library-management-system/
├── app/
│   ├── main.py              # FastAPI app, lifespan, middleware, routers
│   ├── config.py            # Pydantic Settings (env-driven)
│   ├── database.py          # Async SQLAlchemy engine & session
│   ├── dependencies.py      # JWT validation, get_current_user, require_admin
│   ├── initial_data.py      # Idempotent demo user seeder
│   ├── middleware.py        # Request/response logging
│   ├── redis_client.py      # Cache-aside helpers
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic v2 request/response schemas
│   ├── routers/             # auth, books, borrows, admin, default
│   └── services/            # auth_service, borrow_service
├── alembic/                 # Database migrations
├── tests/
│   ├── conftest.py          # SQLite override, Redis mock, fixtures
│   ├── test_auth.py         # 10 auth & RBAC tests
│   └── test_books.py        # 11 CRUD & cache tests
├── frontend/                # Static UI
├── prometheus.yml           # Scrape config
├── Dockerfile               # python:3.12-slim, uvicorn CMD
├── docker-compose.yml       # 5-service stack
├── pytest.ini               # asyncio=auto, SQLite test path
└── requirements.txt
```

---

## 🛑 Tear Down

```bash
docker compose down -v        # stops containers and removes volumes
```
