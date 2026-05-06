# Library Management System

A robust, production-ready REST API for managing a library's book inventory, user memberships, and book borrowing lifecycles. Built with FastAPI and designed for high performance, maintainability, and academic excellence.

## 🏛 Architecture

```mermaid
flowchart LR
    Client([Client / Frontend])
    FastAPI[FastAPI Backend\n(Uvicorn)]
    PostgreSQL[(PostgreSQL)]
    Redis[(Redis Cache)]
    Prometheus[[Prometheus]]
    Grafana[[Grafana]]
    
    Client -- HTTP/REST --> FastAPI
    FastAPI -- Async SQL --> PostgreSQL
    FastAPI -- Cache-Aside --> Redis
    FastAPI -- /metrics --> Prometheus
    Prometheus -- Metrics --> Grafana
```

## 🚀 Setup & Execution

### Local Development (SQLite)
The application defaults to SQLite for local development to ensure a seamless developer experience.

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```
4. **Start the Application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Production Stack
To run the full orchestrated stack (API, PostgreSQL, Redis, Prometheus, Grafana):

```bash
docker compose up -d --build
```

## 📊 Monitoring Access
When running via Docker Compose, access the monitoring suite at:
- **Prometheus:** `http://localhost:9090`
- **Grafana:** `http://localhost:3000` (Login: `admin` / `admin`)
- **Swagger UI:** `http://localhost:8000/docs` 
## 🧪 Test Execution
The test suite utilizes `pytest` with `pytest-asyncio` for comprehensive coverage, using an isolated in-memory database and mocked Redis client to prevent state pollution.

```bash
pytest tests/ -v
```

## 👥 Team Roles & Git Branching Strategy

Our team adheres to a strict Gitflow-inspired branching strategy to ensure code quality and seamless collaboration:

- **Roles:**
  - **Lead Developer / Architect:** Defines schema and core APIs.
  - **Security Engineer:** Implements JWT, RBAC, and password hashing.
  - **DevOps / SRE:** Manages Docker, Redis cache, and Prometheus/Grafana.
  - **QA Engineer:** Authors the `pytest` suite and CI/CD validation.

- **Branching Strategy:**
  - `main`: Production-ready, fully tested code. Commits here are exclusively via merged PRs.
  - `develop`: Integration branch for ongoing features.
  - `feature/*`: Scoped branches for individual tasks (e.g., `feature/jwt-auth`, `feature/soft-deletes`).
  - **Flow:** `feature/*` → (Pull Request) → `develop` → (Release PR) → `main`

## 🔌 API Endpoints Table

| Method | Path | Auth | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/auth/register` | None | N/A | Register a new user (defaults to member). |
| **POST** | `/auth/login` | None | N/A | Authenticate user and receive JWT. |
| **GET** | `/books/` | JWT | Any | List all non-deleted books (supports pagination). |
| **GET** | `/books/{id}` | JWT | Any | Retrieve a specific book by ID. |
| **POST** | `/books/` | JWT | **Admin** | Create a new book. |
| **PUT** | `/books/{id}` | JWT | **Admin** | Update an existing book. |
| **DELETE** | `/books/{id}` | JWT | **Admin** | Soft-delete a book (removes from listings). |
| **POST** | `/borrows/{book_id}` | JWT | Any | Borrow a book (decrements copies). |
| **POST** | `/borrows/return/{id}`| JWT | Any | Return a book (calculates late fine). |
| **GET** | `/borrows/my-history` | JWT | Any | View authenticated user's borrow history. |
| **GET** | `/health` | None | N/A | Service health check (API, DB, Redis). |
| **GET** | `/metrics` | None | N/A | Prometheus metrics exposition. |

---
*Built with ❤️ for the Advanced Software Engineering Capstone.*

# Library Management System - FastAPI

## Team Members
- Youhanna (Backend + Redis + Monitoring)
- ...

## Features
- Full JWT Authentication + Role-Based Access (Admin / Member)
- Complete CRUD for Books with soft-delete
- Advanced Borrowing System with business rules
- Redis Caching (Cache-Aside)
- Structured Logging + Prometheus + Grafana Monitoring
- Comprehensive Test Suite
- Docker Support

## Tech Stack
- FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Redis, JWT, Pydantic v2
- Docker, Prometheus, Grafana

## Setup Instructions

### Local Development
```bash
docker-compose up -d
uvicorn app.main:app --reload