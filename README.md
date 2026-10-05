# AI Spends Tracker & Cost Analyzer

An enterprise-ready, modular platform to track, monitor, analyze, and optimize multi-provider AI API token expenditures across **OpenAI**, **Anthropic Claude**, **Google Gemini**, **DeepSeek**, and **Mistral**.

Built with a clean decoupled architecture featuring a **FastAPI** telemetry ingestion & reverse proxy backend, an embedded **SQLite** data store with realistic 30-day historical data, and an interactive **Streamlit** executive analytics dashboard.

---

## Table of Contents

1. [Executive Overview & Token Economics](#executive-overview--token-economics)
2. [High-Level Architecture](#high-level-architecture)
3. [Repository File Structure](#repository-file-structure)
4. [Core Features in Detail](#core-features-in-detail)
   - [Spend Overview & Time-Series Visuals](#1-spend-overview--time-series-visuals)
   - [Data Management (List All & Add New)](#2-data-management-list-all--add-new)
   - [Intelligent AI Cost Arbitrage Engine](#3-intelligent-ai-cost-arbitrage-engine)
   - [Model Economics & Dynamic Rate Cards](#4-model-economics--dynamic-rate-cards)
   - [Project Budgets & Threshold Guardrails](#5-project-budgets--threshold-guardrails)
   - [AI Reverse Proxy & Simulator](#6-ai-reverse-proxy--simulator)
5. [Database Schema](#database-schema)
6. [Complete REST API Reference](#complete-rest-api-reference)
7. [Installation & Quick Start](#installation--quick-start)
8. [Screenshots Gallery](#screenshots-gallery)
9. [Development & Customization](#development--customization)

---

## Executive Overview & Token Economics

Engineering teams deploy LLMs across fragmented providers without unified cost attribution. This leads to:
- Unpredictable monthly invoices from multiple vendors.
- Lack of project-, environment-, or feature-level cost attribution.
- Inefficient token utilization: using expensive frontier models ($15-$60/1M tokens) on routine classification or chat tasks that economy models ($0.10-$0.40/1M tokens) handle with equivalent quality.
- Unmonitored prompt cache misses that forfeit 50% to 80% prompt discounts.

**AI Spends Tracker & Analyzer** solves this by centralizing token telemetry, enforcing budget quotas, providing a drop-in reverse proxy gateway, and generating automated cost arbitrage recommendations.

```
Total Cost = (Prompt Tokens - Cached Tokens) * Rate_prompt
           + Cached Tokens * Rate_cached
           + Completion Tokens * Rate_comp
           + Reasoning Tokens * Rate_reasoning
```

---

## High-Level Architecture

```mermaid
flowchart TD
    subgraph Clients["Client Applications & SDKs"]
        ClientApp["Backend Applications (Python / Node / Java)"]
        CurlClient["CLI / Direct REST Callers"]
        UIUser["Developers & Finance Ops"]
    end

    subgraph Ingestion["Ingestion & Proxy Layer"]
        Proxy["AI Reverse Proxy (/v1/chat/completions)"]
        TelemetryAPI["Telemetry Ingestion API (/api/v1/telemetry)"]
        BatchAPI["Batch Ingestion API (/api/v1/telemetry/batch)"]
    end

    subgraph Backend["Python Backend Engine (FastAPI & SQLAlchemy)"]
        PricingEngine["Dynamic Rate Card & Token Pricing Engine"]
        BudgetService["Budget Monitor & Velocity Guardrails"]
        AnalyticsEngine["Aggregation & Arbitrage Analyzer"]
        DataSeeder["30-Day Historical Data Seeder"]
    end

    subgraph Storage["Storage Layer"]
        DB[("Shared SQLite Database: data/ai_spends.db")]
    end

    subgraph Frontend["Streamlit Frontend Dashboard (Port 8501)"]
        DashboardKPIs["Spend KPIs & Plotly Trends"]
        DataExplorer["Data Explorer (List All Records & CSV Export)"]
        ManualForm["Add New Spend Event Form"]
        ArbitrageTab["Cost Arbitrage Recommendations"]
        ModelTable["Model Economics Breakdown"]
        BudgetMonitor["Project Budget Gauges"]
        ProxySimulator["Interactive Proxy Tester"]
    end

    ClientApp -->|OpenAI SDK Compatible Route| Proxy
    ClientApp -->|Async Telemetry Events| TelemetryAPI
    CurlClient -->|Batch Telemetry| BatchAPI
    UIUser --> Frontend

    Proxy --> PricingEngine
    TelemetryAPI --> PricingEngine
    BatchAPI --> PricingEngine

    PricingEngine --> DB
    PricingEngine --> BudgetService
    DataSeeder --> DB

    DB --> AnalyticsEngine
    AnalyticsEngine --> Frontend
    BudgetService --> Frontend
    ManualForm --> PricingEngine
```

---

## Repository File Structure

The project is structured into distinct, clean layers:

```
ai_spends/
├── backend/                             # Core Python Services & FastAPI Server
│   ├── __init__.py
│   ├── api.py                          # FastAPI application (REST endpoints & /v1/chat/completions)
│   ├── config.py                       # Provider rate cards & default budget thresholds
│   ├── database.py                     # SQLAlchemy models, SQLite connection, and session factory
│   ├── models.py                       # Pydantic schemas for request validation & API responses
│   ├── pricing_engine.py               # Micro-cent precision rate card calculation engine
│   ├── analytics_engine.py             # Rollups, time-series aggregations, and arbitrage heuristics
│   ├── budget_service.py               # Budget quota tracking, velocity checks, and alert statuses
│   ├── seeder.py                       # Realistic 30-day demo telemetry generator
│   └── run_backend.sh                  # Shell script to start the FastAPI server on port 8000
│
├── frontend/                            # Presentation & User Interface
│   ├── __init__.py
│   ├── app.py                          # Interactive Streamlit dashboard with Plotly charts
│   └── run_frontend.sh                 # Shell script to start the Streamlit UI on port 8501
│
├── data/                                # Persistent Storage Directory
│   └── ai_spends.db                    # SQLite database shared by backend and frontend
│
├── docs/                                # Documentation Assets
│   └── screenshots/                    # Dashboard page screenshots
│
├── run.sh                              # Unified master launcher script
├── pyproject.toml                      # Dependency definitions managed via uv
└── README.md                           # Comprehensive documentation
```

### Module Descriptions

| File | Purpose |
|---|---|
| `backend/api.py` | Exposes REST endpoints for telemetry ingestion, analytics queries, budget checks, and the OpenAI-compatible `/v1/chat/completions` proxy. |
| `backend/config.py` | Contains official per-million token pricing rate cards for OpenAI, Anthropic, Google, DeepSeek, and Mistral. |
| `backend/database.py` | Declares SQLAlchemy ORM models (`SpendEvent`, `ModelRateCard`, `Budget`) and manages the SQLite connection at `data/ai_spends.db`. |
| `backend/pricing_engine.py` | Applies micro-cent math to calculate prompt, completion, cached, and reasoning costs. |
| `backend/analytics_engine.py` | Computes time-series rollups, spend distribution by provider, model efficiency metrics, and identifies optimization candidates. |
| `backend/budget_service.py` | Compares monthly spend against project thresholds, returning `NORMAL`, `WARNING`, or `EXCEEDED` statuses. |
| `backend/seeder.py` | Automatically populates 600+ realistic events across 30 days on first boot. |
| `frontend/app.py` | Multi-tab interactive dashboard providing executive KPI cards, Plotly charts, data explorer with CSV export, manual data entry, and proxy testing. |

---

## Core Features in Detail

### 1. Spend Overview & Time-Series Visuals
- **Executive Metric Cards**:
  - **Total AI Spend**: Total expenditure in USD across selected projects and dates.
  - **Projected Monthly Run-Rate**: Projected 30-day invoice based on trailing velocity.
  - **Total Tokens Consumed**: Aggregate volume across prompt, completion, and reasoning tokens.
  - **Cache Savings**: Calculated dollar value saved through prompt caching discounts, alongside cache hit percentage.
- **Interactive Visualizations (Plotly)**:
  - **Daily Spend Trajectory**: Stacked bar chart showing expenditure broken down by major provider (OpenAI, Anthropic, Google, DeepSeek, Other).
  - **Token Volume Trajectory**: Area chart tracking prompt vs. completion volume trends over time.
- **Dynamic Scope Filters**: Filter by Project (`CustomerSupportBot`, `DocSearchRAG`, `CodeGenAssistant`, `DataExtractionPipeline`), Environment (`production`, `staging`, `development`), and Time Range (7 to 30 days).

---

### 2. Data Management (List All & Add New)
A comprehensive control panel for data auditing and manual record entry:
- **List All Data (Data Explorer)**:
  - Full tabular view of all spend records in the database.
  - Columns: `ID`, `Timestamp (UTC)`, `Project`, `Environment`, `Provider`, `Model`, `Prompt Tokens`, `Completion Tokens`, `Cached Tokens`, `Total Tokens`, `Total Cost ($)`, `Latency (ms)`, `Status`, `Feature Tag`, and `User`.
  - Filters by Project, Environment, and Model.
  - Configurable page view limits (`50`, `100`, `250`, `500`, `All`).
  - **CSV Export**: Download filtered records as a CSV file with a single click.
- **Add New Data Form**:
  - Select an existing project or enter a new project name.
  - Select Environment and Model target.
  - Enter Prompt Tokens, Completion Tokens, Cached Tokens, Reasoning Tokens, and Latency.
  - Set custom Event Date and Time.
  - Automatically calculates micro-cent token costs using active rate cards and persists the record to the shared SQLite database.

---

### 3. Intelligent AI Cost Arbitrage Engine
The analyzer automatically inspects spend profiles and flags cost-saving opportunities:
- **Frontier to Economy Model Downgrade**:
  - Identifies routine conversational and RAG tasks executing on high-cost models (e.g. GPT-4o at $2.50 / $10.00 per 1M) and computes savings if switched to economy models (e.g. Claude 3.5 Haiku at $0.80 / $4.00 or Gemini 1.5 Flash at $0.075 / $0.30).
  - Typical savings: **70% to 85%**.
- **Reasoning Model Arbitrage**:
  - Detects reasoning tasks routed to OpenAI o1 ($15.00 / $60.00 per 1M) and estimates cost reductions if routed to OpenAI o3-mini ($1.10 / $4.40 per 1M) or DeepSeek R1 ($0.55 / $2.19 per 1M).
  - Typical savings: **80% to 90%**.
- **Prompt Cache Miss Opportunity Detection**:
  - Flags queries with high prompt volumes (>200k tokens) and low cache hit rates (<15%).
  - Recommends restructuring repetitive system prompts over 1,024 tokens to qualify for prefix caching discounts (up to 80% discount on prompt tokens).

---

### 4. Model Economics & Dynamic Rate Cards
- **Performance & Spend Matrix**:
  - Tabular breakdown of each model's total requests, token volume, total cost, percentage share of total AI spend, and average response latency.
  - Spend distribution donut chart.
- **Active Provider Catalog (USD per 1,000,000 Tokens)**:

| Provider | Model ID | Tier | Prompt ($/1M) | Completion ($/1M) | Cached Prompt ($/1M) | Reasoning ($/1M) |
|---|---|---|---|---|---|---|
| OpenAI | `gpt-4o` | Frontier | $2.50 | $10.00 | $1.25 | - |
| OpenAI | `gpt-4o-mini` | Economy | $0.15 | $0.60 | $0.075 | - |
| OpenAI | `o1` | Reasoning | $15.00 | $60.00 | $7.50 | $60.00 |
| OpenAI | `o3-mini` | Reasoning | $1.10 | $4.40 | $0.55 | $4.40 |
| Anthropic | `claude-3-5-sonnet` | Frontier | $3.00 | $15.00 | $0.30 | - |
| Anthropic | `claude-3-5-haiku` | Economy | $0.80 | $4.00 | $0.08 | - |
| Google | `gemini-1.5-pro` | Frontier | $1.25 | $5.00 | $0.3125 | - |
| Google | `gemini-1.5-flash` | Economy | $0.075 | $0.30 | $0.0188 | - |
| Google | `gemini-2.0-flash` | Economy | $0.10 | $0.40 | $0.025 | - |
| DeepSeek | `deepseek-chat` (V3) | Economy | $0.14 | $0.28 | $0.014 | - |
| DeepSeek | `deepseek-reasoner` (R1) | Reasoning | $0.55 | $2.19 | $0.14 | $2.19 |
| Mistral | `mistral-large` | Frontier | $2.00 | $6.00 | $0.50 | - |

---

### 5. Project Budgets & Threshold Guardrails
- **Monthly Limit Tracking**: Configurable monthly dollar quotas for each project workspace.
- **Alert Status Lifecycle**:
  - `NORMAL`: Spend is within acceptable thresholds (< 80%).
  - `WARNING`: Spend has crossed the alert threshold (e.g. 80% to 99%).
  - `EXCEEDED`: Spend has reached or breached 100% of the monthly allocation.
- **Hard Cap Indicator**: Flags whether requests exceeding budget will be throttled.

---

### 6. AI Reverse Proxy & Simulator
- **OpenAI-Compatible Drop-In Proxy (`POST /v1/chat/completions`)**:
  - Client applications point their base URL to `http://localhost:8000/v1` without modifying their existing OpenAI SDK client code.
  - The proxy transparently intercepts the request, counts prompt and completion tokens, measures latency, calculates micro-cent spend, records the telemetry event to SQLite, and returns standard OpenAI JSON with custom spend metadata.
- **Interactive UI Testing Playground**: Test the reverse proxy directly in the browser to view the response payload and spend attribution in real time.

---

## Database Schema

The SQLite database (`data/ai_spends.db`) uses the following schema:

```mermaid
erDiagram
    MODEL_RATE_CARDS ||--o{ SPEND_EVENTS : "prices"
    BUDGETS ||--o{ SPEND_EVENTS : "tracks"

    SPEND_EVENTS {
        int id PK
        string project_name "Indexed"
        string environment
        string provider "Indexed"
        string model_id "Indexed"
        int prompt_tokens
        int completion_tokens
        int cached_tokens
        int reasoning_tokens
        int total_tokens
        float prompt_cost_usd
        float completion_cost_usd
        float total_cost_usd
        int latency_ms
        int http_status_code
        string feature_tag
        string user_identifier
        datetime timestamp "Indexed"
    }

    MODEL_RATE_CARDS {
        int id PK
        string model_id "Unique, Indexed"
        string display_name
        string provider
        string tier
        float prompt_price_per_million
        float completion_price_per_million
        float cached_prompt_price_per_million
        float reasoning_price_per_million
        datetime created_at
    }

    BUDGETS {
        int id PK
        string project_name "Unique, Indexed"
        float monthly_limit_usd
        float alert_threshold_percent
        boolean hard_cap_enabled
    }
```

---

## Complete REST API Reference

The FastAPI backend runs on port `8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### 1. Health Check
```bash
curl -X GET http://localhost:8000/
```
**Response:**
```json
{
  "status": "ok",
  "service": "AI Spends Tracker & Analyzer",
  "version": "1.0.0"
}
```

---

### 2. Ingest Single Telemetry Event
Endpoint: `POST /api/v1/telemetry`

```bash
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "CustomerSupportBot",
    "environment": "production",
    "provider": "openai",
    "model_id": "gpt-4o",
    "prompt_tokens": 1450,
    "completion_tokens": 320,
    "cached_tokens": 500,
    "latency_ms": 380,
    "feature_tag": "live_chat"
  }'
```
**Response:**
```json
{
  "event_id": 646,
  "total_cost_usd": 0.0062,
  "cache_savings_usd": 0.000625,
  "budget_status": {
    "project_name": "CustomerSupportBot",
    "monthly_limit_usd": 500.0,
    "current_spend_usd": 4.12,
    "percent_used": 0.8,
    "status": "NORMAL",
    "alert_threshold_percent": 80.0,
    "hard_cap_enabled": false
  }
}
```

---

### 3. AI Reverse Proxy (`/v1/chat/completions`)
Endpoint: `POST /v1/chat/completions`

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Explain prefix prompt caching in modern LLM architectures."}
    ],
    "project_name": "CustomerSupportBot",
    "environment": "production"
  }'
```
**Response:**
```json
{
  "id": "chatcmpl-491203",
  "object": "chat.completion",
  "created": 1791181200,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "[Tracked via AI Proxy] Processed request via gpt-4o. Prompt Tokens: 12, Completion: 110, Total Cost: $0.001130."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 110,
    "total_tokens": 122,
    "prompt_tokens_details": {
      "cached_tokens": 0
    }
  },
  "_ai_spends_metadata": {
    "total_cost_usd": 0.00113,
    "cache_savings_usd": 0.0,
    "latency_ms": 284
  }
}
```

---

### 4. Executive KPI Summary
Endpoint: `GET /api/v1/analytics/summary`

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/summary?days=30"
```
**Response:**
```json
{
  "total_spend_usd": 12.01,
  "projected_month_end_usd": 12.01,
  "total_tokens": 1553658,
  "total_requests": 646,
  "cache_savings_usd": 0.29,
  "cache_hit_rate_pct": 20.3,
  "active_models_count": 8,
  "active_projects_count": 4,
  "avg_latency_ms": 1522.6
}
```

---

### 5. Daily Time-Series Rollup
Endpoint: `GET /api/v1/analytics/timeseries`

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/timeseries?days=7"
```

---

### 6. Arbitrage Recommendations
Endpoint: `GET /api/v1/analytics/arbitrage`

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/arbitrage"
```
**Response:**
```json
[
  {
    "id": "rec_gpt4o_haiku",
    "title": "Migrate 'GPT-4o' to Claude 3.5 Haiku or Gemini 1.5 Flash",
    "description": "You spent $5.40 on GPT-4o across 185 calls. Standard chat and summarization tasks yield comparable quality on economy models at ~75% lower cost.",
    "current_model": "GPT-4o",
    "suggested_model": "Claude 3.5 Haiku / Gemini 1.5 Flash",
    "estimated_monthly_savings_usd": 4.15,
    "savings_percentage": 76.8,
    "reasoning_type": "MODEL_DOWNGRADE",
    "impact_level": "MEDIUM"
  }
]
```

---

### 7. Project Budgets
Endpoint: `GET /api/v1/budgets`

```bash
curl -X GET "http://localhost:8000/api/v1/budgets"
```

---

## Installation & Quick Start

### Prerequisites
- Python 3.12 or newer.
- Package manager: [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`.

### 1. Launch the Application

#### Option A: Launch the Streamlit Frontend (Default)
```bash
./run.sh
```
Or directly:
```bash
./frontend/run_frontend.sh
# or
uv run streamlit run frontend/app.py
```
Access the dashboard at **[http://localhost:8501](http://localhost:8501)**.

#### Option B: Launch the FastAPI Backend
```bash
./run.sh --backend
```
Or directly:
```bash
./backend/run_backend.sh
# or
uv run uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```
Access Swagger UI at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

#### Option C: Launch Both Frontend & Backend Concurrently
```bash
./run.sh --all
```

---

## Screenshots Gallery

Screenshots of each tab and page component are stored in `docs/screenshots/`:

| Screen | Description | File Path |
|---|---|---|
| **Spend Overview** | Executive KPI metric cards, daily spend trajectory stacked by provider, and token volume charts. | `docs/screenshots/01_spend_overview.png` |
| **Data Management (List)** | Interactive data explorer with filters, detailed token columns, and CSV export. | `docs/screenshots/02_data_management_list.png` |
| **Data Management (Add)** | Manual spend event entry form with real-time rate card calculation. | `docs/screenshots/03_data_management_add.png` |
| **Cost Arbitrage & Savings** | Intelligent recommendations for model downgrading, reasoning arbitrage, and caching. | `docs/screenshots/04_cost_arbitrage.png` |
| **Model Economics** | Performance breakdown by model, request volume, share of spend, and rate card catalog. | `docs/screenshots/05_model_economics.png` |
| **Budgets & Guardrails** | Project monthly quotas, progress bars, and alert status badges. | `docs/screenshots/06_budgets_guardrails.png` |
| **AI Reverse Proxy Simulator** | Drop-in proxy test interface with live token counts and micro-cent attribution. | `docs/screenshots/07_proxy_simulator.png` |

---

## Development & Customization

### Adding a New Model Rate Card
To register a new model or adjust prices, update `DEFAULT_RATE_CARDS` in `backend/config.py`:

```python
"custom-llm-v1": {
    "provider": "custom",
    "displayName": "Custom LLM v1",
    "tier": "economy",
    "promptPricePerMillion": 0.50,
    "completionPricePerMillion": 1.50,
    "cachedPromptPricePerMillion": 0.10,
    "reasoningPricePerMillion": 0.0,
}
```

### Adding a New Project Budget
To define a new project budget cap, update `DEFAULT_BUDGETS` in `backend/config.py`:

```python
"NewService": {
    "monthly_limit": 800.0,
    "alert_threshold": 80.0,
    "hard_cap": True
}
```

### Connecting to External PostgreSQL
To point the application to a production PostgreSQL database instead of local SQLite:
1. Install psycopg2 / asyncpg: `uv add psycopg2-binary`
2. Update `DATABASE_URL` in `backend/database.py`:
   ```python
   DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ai_spends")
   ```
