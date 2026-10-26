# Cyber-DNA Backend API

This is the FastAPI backend for the Cyber-DNA Threat Detection Platform. It handles log ingestion from Windows (via PowerShell collector), parses and normalizes the data, detects suspicious activity through behavioral rules/ML, and serves structured alerts to the React dashboard.

## Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** SQLite (default) / PostgreSQL
- **ORM:** SQLAlchemy
- **Data Validation:** Pydantic

## Getting Started

1. **Set up a Virtual Environment:**
   It is highly recommended to run the backend within a virtual environment to isolate its dependencies.
   
   - **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup:**
   - The system defaults to SQLite (`cyberdna.db`) for testing and prototyping.
   - For PostgreSQL, copy `.env.example` to `.env` and update the credentials.

4. **Run the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Structure
- `app/api/endpoints/`: REST API endpoints grouped by domain (events, alerts, users, hosts, collector).
- `app/core/`: Configuration and environment variables.
- `app/db/`: Database connection and SQLAlchemy models (`events`, `alerts`, `users`, `computers`, `incidents`, `detection_rules`, `sessions`, `ml_analysis`).
- `app/schemas.py`: Pydantic models for data validation.

## Data Flow
1. **Windows Event** is collected and sent to `POST /api/collector/events`.
2. Stored in the **events** table.
3. **Detection Rules** / ML analyzes events.
4. If flagged, created as **alerts**.
5. Alerts are linked to multiple events via the **alert_events** junction table.
6. The Dashboard consumes data via `GET /api/alerts`, `GET /api/dashboard/overview`, etc.


## Vercel deployment notes

The repository root contains `vercel.json`, which routes `/api` and `/api/*` to this FastAPI service and all other paths to the Vite frontend. Import the repository root (`./`) into Vercel; do not set the project root to `backend/` or `frontend/`.

Set server-side `DATABASE_URI`, `OPENAI_API_KEY`, `AI_PROVIDER=openai`, `AI_MODEL`, and `CYBERDNA_COOKIE_SECURE=true` in Vercel Environment Variables. Use managed PostgreSQL because Vercel functions do not provide durable local SQLite storage. Never expose `OPENAI_API_KEY` through a `VITE_*` variable. Public demo login is optional and described in the root README; it must use an isolated demo tenant/database.
