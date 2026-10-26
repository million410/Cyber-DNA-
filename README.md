# Development of an Intelligent Behavioral Analytics and Threat Detection Platform for Active Directory Environments

## Overview
This repository contains the source code and documentation for the **Development of an Intelligent Behavioral Analytics and Threat Detection Platform for Active Directory Environments**. This academic research project is designed to analyze Windows Event Logs and Active Directory context. The core thesis of this platform is to evaluate and compare traditional deterministic rule-based threat detection against probabilistic behavioral anomaly detection.

The platform processes telemetry from an isolated lab environment, evaluating data through independent Rule and Behavioral engines. It correlates these findings to generate explainable risk scores and visualizes entity timelines and alerts for SOC investigations.

## Academic Focus
- **Purpose:** To formally compare the effectiveness (Precision, Recall, F1-score) of Rule-based vs. Behavioral detection methodologies using a controlled lab and simulated ground truth.
- **Explainability:** All risk scores and generated alerts contain a traceable, human-readable justification. Black-box ML models are strictly avoided in favor of interpretable statistical methods (e.g., Isolation Forest, Z-Score).

## Architecture & Data Pipeline
The platform operates as a straightforward, modular pipeline:
1. **Collection:** Lightweight agents (Winlogbeat) forward core Windows Event Logs from a Domain Controller and client machines to a central ingestion API.
2. **Processing & Storage:** A Python (FastAPI) backend validates, normalizes, and stores the events in a PostgreSQL relational database.
3. **Detection (Asynchronous):** 
   - **Rule Engine:** Evaluates events against static, deterministic signatures (e.g., Account Created, Brute Force).
   - **Behavioral Engine:** Extracts features (e.g., login hours, frequency) and computes anomaly scores using statistical baselining.
4. **Correlation & Scoring:** Combines rule weights and anomaly scores based on the entity (User/Computer) to generate a final Risk Score and trigger necessary alerts.
5. **Presentation:** A React-based web dashboard displays generated alerts, entity timelines, and detection summaries.

## Technology Stack
- **Infrastructure:** Windows Server (Domain Controller), Windows 10/11 Clients
- **Log Collection:** Winlogbeat (Elastic)
- **Backend / API:** Python + FastAPI
- **Database:** PostgreSQL
- **Analytics & ML:** Python + Pandas + Scikit-Learn
- **Frontend:** React + TypeScript (Vite)

## Repository Structure
- `/docs/` - System architecture, detailed specifications, and academic research documentation.
- `/frontend/` - React + Vite UI dashboard for SOC alerts and investigation views.
- `/backend/` - FastAPI application handling log ingestion, normalization, and API endpoints.
- `/ML/` - Analytics components including the Rule Engine, Behavioral Engine (feature extraction, baseline models), and Risk Scorer.

## Group Members
- Million Birhanu (ID: 2210)
- Bereket Mamo (ID: 1513)
- Abraham Shimels (ID: 183)
- Bereketeab Sharew (ID: 2396)
- Eyosiyas Gezahegn (ID: 127)
- Amanuel Ayalew (ID: 4240)
- Samuel Alemu (ID: )

## Team Responsibilities
The project is modularly designed to support parallel development for a team of 7 students:
1. **AD Lab & Simulation:** Build the isolated virtual network and write traffic/attack simulation scripts.
2. **Collection & Ingestion:** Configure Winlogbeat and develop the FastAPI ingestion service.
3. **Data Schema & Storage:** Design the PostgreSQL relational schema and normalize raw logs.
4. **Rule Engine:** Write deterministic detection rules and severity weights.
5. **Behavioral Engine:** Implement feature extraction (Pandas) and baseline anomaly detection (Scikit-learn).
6. **Risk Scorer & API:** Correlate engine outputs and serve data via REST API to the frontend.
7. **Frontend UI:** Build the React dashboard and alert investigation visualizations.

**Live application (replace after deployment):** https://YOUR-PROJECT.vercel.app

## Getting Started
### Public demo login (read-only)

The optional public demo account is intentionally documented so visitors can try the app. **This is not an administrator account and must only be enabled against an isolated demo database, never a database containing real/customer telemetry.** If you enable the public demo through the environment variables below, use:

| Field | Public demo value |
|---|---|
| Username | `cyberdna.demo` |
| Password | `DemoOnly-CyberDNA-2026!` |

These credentials are public by design; do not reuse this password for any personal or administrator account. The demo account can read only its own demo organization and use the AI Analyst endpoint. It cannot change the shared password, manage accounts, modify alerts/settings, or run platform write operations. AI requests from everyone sharing this account are limited to **5 requests per rolling hour**. All other users need individually provisioned accounts.

### Deploy frontend and backend together on Vercel

This repository includes a root `vercel.json` that deploys `frontend/` as Vite and `backend/` as FastAPI under one shared URL. API calls use the same-origin relative base `/api/v1`; the browser never receives your OpenAI API key.

1. Create a **new GitHub repository** and upload the contents of this folder. The downloadable project archive excludes local `.git/`, `.env`, `node_modules`, and stale `dist/` build output.
2. In Vercel, choose **Add New → Project**, import the new GitHub repository, and set **Root Directory** to `./` (the repository root). Keep `vercel.json` next to `frontend/` and `backend/`.
3. In Vercel → Project → Settings → Environment Variables, add the variables below for **Production** (and Preview if you intend to use preview deployments). Use a managed PostgreSQL connection string from your provider; do not use SQLite for persistent production data.
4. Deploy. Your stable production URL is the Vercel project's production domain. Vercel redeploys it from the production branch on each push, so the README URL stays the same.
5. Replace `https://YOUR-PROJECT.vercel.app` in this README and set the same URL in GitHub's **About → Website** field once Vercel gives you the production domain.

Required Vercel environment variables:

| Variable | Value / instruction |
|---|---|
| `DATABASE_URI` | Managed PostgreSQL URL, e.g. `postgresql://USER:PASSWORD@HOST:5432/DB`; URL-encode special characters in credentials. |
| `OPENAI_API_KEY` | Your OpenAI API key. **Vercel backend environment variable only**—never add it to any `VITE_*` variable, frontend source, README, or GitHub. |
| `AI_PROVIDER` | `openai` |
| `AI_MODEL` | `gpt-6-luna` if your API project has access to it; otherwise use a model ID available to your account. |
| `CYBERDNA_COOKIE_SECURE` | `true` |
| `CYBERDNA_BOOTSTRAP_SECRET` | Generate a separate long random secret for first-admin bootstrap; keep it private and never document its value. |
| `CYBERDNA_DEMO_LOGIN_ENABLED` | `true` to enable the public demo account; `false` disables it. |
| `CYBERDNA_DEMO_USERNAME` | `cyberdna.demo` |
| `CYBERDNA_DEMO_PASSWORD` | `DemoOnly-CyberDNA-2026!` (public demo password only) |
| `CYBERDNA_DEMO_ORGANIZATION_NAME` | `Cyber DNA Public Demo` |
| `CYBERDNA_DEMO_AI_REQUESTS_PER_HOUR` | `5` (all demo visitors share this limit) |
| `AI_MAX_OUTPUT_TOKENS` | `900` |
| `ML_ENABLED` | `true` |
| `ML_MODEL_PATH` | `models/cyberdna_v25_isolation_forest.joblib` |
| `ML_CONFIG_PATH` | `models/cyberdna_v25_config.json` |
| `VITE_API_BASE_URL` | `/api/v1` |
| `VITE_DEMO_MODE` | `false` |

Vercel environment variables with no `VITE_` prefix stay on the backend and are not bundled into browser JavaScript. Never commit a real `.env` file. `frontend/.env.example` and `backend/.env.example` are templates only.

### AI model / API key flow

After logging into the public demo, open the **AI Analyst** panel in the dashboard. The browser sends the question to `POST /api/v1/analyst/ask`; FastAPI reads `OPENAI_API_KEY` from its server environment and calls the configured model. The key is not returned in the API response or sent to the frontend. The shared demo quota is enforced in PostgreSQL (concurrent requests are serialized for the demo account); the OpenAI API project may still incur charges within that limit, so configure provider-side spending/usage alerts as well. Since this demo starts with an isolated empty organization, evidence-based analysis needs you to ingest synthetic or authorized telemetry first.

### First platform administrator (separate from public demo)

The public demo credentials do not create or grant administrator access. To create your private platform admin, keep `CYBERDNA_BOOTSTRAP_SECRET` private and use the same production database. Set `CYBERDNA_BOOTSTRAP_URL=https://YOUR-PROJECT.vercel.app/api/v1/auth/bootstrap` and run `python create_first_admin.py`; the script prompts for the private bootstrap secret and admin password, not storing them in source. The bootstrap endpoint disables itself after the first `platform_admin` is created. Do not put admin credentials or the bootstrap secret in this public README.

### Continuous deployment and the live link

Once the GitHub repo is connected to Vercel, each push to the configured production branch builds and updates the same production domain. Add this to the top of the README after deployment:

`Live application: https://YOUR-PROJECT.vercel.app`

Then push README changes normally. The URL does not change on every redeployment. Preview branch deployments get separate preview URLs.

*(Further local setup instructions are available in `RUN_KALI.md` and `backend/README.md`.)*
