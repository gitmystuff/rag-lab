INFO 5707 — Data Modeling
Week 1 Starter: PostgreSQL → CRUD → FastAPI + Swagger (VS Code)

What you get
- PostgreSQL schema (documents + chunks) in sql/schema.sql
- FastAPI app in app/main.py
- Postgres connection helper in app/db.py (you only fill in your password)
- Minimal Pydantic models in app/models.py
- .gitignore and requirements.txt

Prerequisites
- PostgreSQL installed locally and running
- VS Code
- Python 3.10+

1) Create and activate a virtual environment (recommended)
Windows (PowerShell):
  python -m venv .venv
  .venv\Scripts\activate

macOS/Linux:
  python3 -m venv .venv
  source .venv/bin/activate

2) Install dependencies
  pip install -r requirements.txt

Note: This starter uses psycopg[binary] so you don't need to install libpq separately.

3) Create the database (one-time)
Option A (psql):
  psql -U postgres
  CREATE DATABASE rag_lab;
  \q

Option B (pgAdmin):
  Create a database named rag_lab

4) Apply the schema
  psql -U postgres -d rag_lab -f sql/schema.sql

5) Set your Postgres password
Open app/db.py and replace YOUR_PASSWORD with your local postgres password.
(If your username/port are different, update those fields too.)

6) Run the API
  uvicorn app.main:app --reload

7) Test in Swagger
Open:
  http://127.0.0.1:8000/docs

Endpoints included
- GET /
- POST /documents
- GET /documents
- GET /documents/{doc_id}
- DELETE /documents/{doc_id}

Mini-lab ideas (not implemented here)
- GET /documents/{doc_id}/chunks
- POST /chunks
- Pagination: limit/offset on GET /documents
- Search: GET /documents/search?q=...
