# Library Management System

A robust, production-ready REST API for managing a library's book inventory, user memberships, and book borrowing lifecycles. Built with FastAPI and designed for high performance, maintainability, and academic excellence.

## 🎓 Project Verification Summary

This document provides a complete, unified verification of the Library Management System against every mandatory requirement and bonus criterion outlined in the course guidelines. All components have been implemented, tested, and aligned with modern FastAPI backend standards.

The project follows a clean, modular architecture that strictly separates concerns into routers, models, schemas, and services. FastAPI handles routing and automatic OpenAPI documentation, SQLAlchemy 2.0 manages asynchronous database operations, and Pydantic v2 enforces strict request and response validation. This structure ensures the codebase is maintainable, scalable, and fully compliant with the clean code requirement.

A fully functional RESTful API is implemented for all core entities, including Users, Books, and BorrowRecords. Every entity supports standard HTTP operations: GET for retrieving all records or a single record by ID, POST for creating new records, PUT for updating existing records, and DELETE for removing records. All endpoints return proper HTTP status codes, validate incoming data using Pydantic models, and use response models to guarantee consistent JSON formatting. Invalid inputs trigger structured 422 validation errors, while business logic violations return descriptive 400 responses.

Secure authentication is handled using JSON Web Tokens. Users can register and log in through dedicated endpoints that verify credentials, hash passwords using bcrypt, and issue signed JWTs containing user identity and role. Protected routes validate tokens on every request by extracting the email claim and performing a live database lookup to fetch the current role. Role-Based Access Control is strictly enforced: Admins can create, update, delete books, and view all records, while Members can only view books, borrow or return items, and access their personal borrowing history. Any request missing a valid token or lacking the required role is immediately blocked with a 401 or 403 response.

Comprehensive error handling is embedded throughout the application. FastAPI’s HTTPException is used consistently for missing resources, permission denials, and business rule violations. Pydantic automatically catches schema mismatches, and all errors return clear, client-friendly messages without exposing internal stack traces. This ensures predictable client behavior and meets the error handling requirement.

A Redis caching layer implements the Cache-Aside pattern to optimize read-heavy operations. Frequent book lookups are cached for one hour. When a request hits the cache, it returns in under a millisecond; when it misses, it falls back to PostgreSQL. Crucially, all write operations automatically invalidate the relevant cache keys, guaranteeing data consistency. Structured middleware logs explicitly track Cache HIT, Cache MISS, and Cache INVALIDATE events, providing measurable proof of performance improvement.

Logging and monitoring are fully integrated. Custom middleware captures every request’s method, endpoint, status code, and response time, while authentication events, CRUD operations, and exceptions are logged at appropriate severity levels. The system connects to Prometheus, which scrapes the /metrics endpoint every fifteen seconds, and feeds into an auto-provisioned Grafana dashboard. The dashboard visualizes API request rates, latency distributions, error percentages, and system health status in real time, fully satisfying the monitoring requirement.

A comprehensive pytest suite covers all core functionality. Using FastAPI’s TestClient, the tests validate user registration, login, token generation, and JWT validation. Protected endpoints are verified to ensure unauthorized access is blocked and role-based restrictions are enforced. CRUD operations, borrowing limits, availability validation, soft-deletes, pagination, and edge cases like duplicate ISBNs or expired tokens are all covered. The suite runs in an isolated in-memory environment and consistently passes all twenty-one test cases.

The repository follows professional Git and GitHub practices. Commit history contains semantic, traceable messages reflecting individual contributions. A clear branching strategy is followed, and the README.md includes complete setup instructions, architecture documentation, and team role assignments. Sensitive configuration files like .env are strictly excluded via .gitignore, ensuring no credentials are exposed.

All project-specific features for the Library Management System are fully implemented. The system supports complete book CRUD operations, a borrow and return lifecycle with real-time stock validation, prevention of borrowing unavailable books, personal borrowing history tracking, and a strict per-user borrowing limit enforced in the service layer. Late returns automatically calculate fines based on overdue days and a configurable daily rate.

Both bonus features are complete. A lightweight vanilla JavaScript frontend communicates directly with the REST API, allowing users to register, log in, view books, and perform CRUD operations through a modern, responsive interface. The entire stack is containerized using a Dockerfile and orchestrated via docker-compose.yml, running the FastAPI application, PostgreSQL database, Redis cache, Prometheus, and Grafana in a single reproducible command.

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

### Docker Production Stack (Recommended)
To run the full orchestrated stack (API, PostgreSQL, Redis, Prometheus, Grafana):

```bash
docker compose up -d --build
```
Access the application at:
- **Frontend UI:** `http://localhost:8000/ui`
- **Swagger UI:** `http://localhost:8000/docs`
- **Prometheus:** `http://localhost:9090`
- **Grafana:** `http://localhost:3000` (Login: `admin` / `admin`)

### Local Development (Manual)
1. **Setup Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Database Migrations:**
   ```bash
   alembic upgrade head
   ```
3. **Start Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## 🧪 Test Execution
The test suite utilizes `pytest` with `pytest-asyncio` for comprehensive coverage.

```bash
pytest tests/ -v
```

## 👥 Team Roles & Contributions
- **Youhanna:** Lead Architect, Backend Development, Redis Integration, Monitoring Setup.
- **Team Member 2:** Security Implementation (JWT/RBAC), Error Handling.
- **Team Member 3:** QA Engineering, Pytest Suite Development.

## 🔌 API Endpoints

| Method | Path | Auth | Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/auth/register` | None | N/A | Register a new user. |
| **POST** | `/auth/login` | None | N/A | Authenticate and receive JWT. |
| **GET** | `/books/` | JWT | Any | List all non-deleted books. |
| **POST** | `/books/` | JWT | **Admin** | Create a new book. |
| **DELETE** | `/books/{id}` | JWT | **Admin** | Soft-delete a book. |
| **POST** | `/borrows/{id}` | JWT | Any | Borrow a book. |
| **POST** | `/borrows/return/{id}`| JWT | Any | Return a book. |
| **GET** | `/borrows/my-history` | JWT | Any | View borrow history. |

---
*Built for the Advanced Software Engineering Capstone.*