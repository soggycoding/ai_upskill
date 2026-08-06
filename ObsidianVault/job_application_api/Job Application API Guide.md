---
tags:
  - python
  - rest-api
  - fastapi
  - sqlite
  - sqlalchemy
  - job-tracker
date: 2026-08-05
status: complete
---

# Job Application Tracker REST API - Project Documentation

## 📌 Overview & Goal
Build a lightweight, performant **RESTful API** in Python backed by a **SQLite** database to track job applications and filter them by specific application statuses:
- ❌ **Rejected** (`rejected`)
- ⏳ **Follow Up** (`follow_up`)
- 📅 **Scheduled Interview** (`scheduled_interview`)
- 📝 **Additional Info Needed** (`additional_info_needed`)
- 📩 **Applied** (`applied`)

---

## 🛠️ Technology Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Auto OpenAPI/Swagger docs, high performance, Pydantic integration)
- **Database / ORM**: SQLite + [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Data Validation & Schemas**: Pydantic v2
- **Testing**: `pytest` & `Starlette TestClient` / `httpx`
- **Server**: Uvicorn (`python -m uvicorn`)

---

## 📂 Project Structure

Project folder: `c:\Users\user\Documents\ObsidianVault\job_application_api\`

| File | Purpose |
| :--- | :--- |
| `database.py` | Configures SQLite connection (`job_applications.db`), sessionmaker, and `get_db` FastAPI dependency. |
| `models.py` | Defines SQLAlchemy ORM `JobApplication` model and `ApplicationStatus` string enum. |
| `schemas.py` | Pydantic data schemas for API request validation, response serialization, and Swagger docs. |
| `crud.py` | Database helper functions for Create, Read, Update, Delete, Search, and Status filtering. |
| `main.py` | FastAPI application instance, REST routes, status filter endpoints, and auto table creation. |
| `requirements.txt` | Project dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `httpx`, `pytest`). |
| `test_api.py` | Automated test suite verifying CRUD workflows, status filtering, and search functionality. |

---

## 🗄️ Database Schema (`JobApplication`)

```sql
TABLE job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company VARCHAR(255) NOT NULL,
    position VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'applied',
    application_date DATE NOT NULL,
    job_url VARCHAR(500) NULL,
    location VARCHAR(255) NULL,
    salary_range VARCHAR(100) NULL,
    notes TEXT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

---

## 🚀 API Endpoints Overview

### Standard REST Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status metadata & supported filter tags |
| `POST` | `/api/applications/` | Create a new job application |
| `GET` | `/api/applications/` | List applications (Supports `?status=...` and `?search=...`) |
| `GET` | `/api/applications/{id}` | Get application details by ID |
| `PATCH` | `/api/applications/{id}` | Update status, notes, or details |
| `DELETE` | `/api/applications/{id}` | Delete a job application entry |

### Category Filter Shortcuts

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/applications/filter/rejected` | Filter & return all **REJECTED** applications |
| `GET` | `/api/applications/filter/follow-up` | Filter & return all applications for **FOLLOW UP** |
| `GET` | `/api/applications/filter/scheduled-interview` | Filter & return all **SCHEDULED INTERVIEW** applications |
| `GET` | `/api/applications/filter/additional-info-needed` | Filter & return all applications needing **ADDITIONAL INFO** |

---

## ⚡ How to Run & Test

### 1. Run the API Server
Open PowerShell / CMD in the project folder and run:

```powershell
cd "C:\Users\user\Documents\ObsidianVault\job_application_api"
python -m uvicorn main:app --reload
```

> 💡 **Tip**: Using `python -m uvicorn` avoids PowerShell `$env:PATH` execution errors when virtual environments are active.

### 2. Access Documentation
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 3. Run Automated Tests
```powershell
python test_api.py
```
*(All 8 test cases verify application creation, filter queries, status transitions, and search functions)*.

---

## 🧠 Key Learnings & Gotchas Tackled

1. **Clean Virtual Environment Setup**: Installed dependencies cleanly in `.venv` using `pip install -r requirements.txt`.
2. **PowerShell Path Executable Resolution**: Standardized terminal command invocations with `python -m uvicorn` instead of bare `uvicorn` to guarantee cross-shell reliability.
3. **Timezone-Aware Timestamps**: Used `datetime.now(timezone.utc)` for SQLite compatibility without Python 3.13 deprecation warnings.
4. **Self-Cleaning Tests**: Configured `test_api.py` to reset the test database file before test execution for 100% reproducible test suite runs.
