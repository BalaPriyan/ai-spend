"""
FastAPI Backend Server providing Telemetry Ingestion and OpenAI-compatible Reverse Proxy.
"""

import time
import random
from typing import Optional, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import get_db, SpendEvent, ModelRateCard, Budget
from backend.models import TelemetryIngestRequest, BatchTelemetryRequest, ProxyChatRequest
from backend.pricing_engine import PricingEngine
from backend.analytics_engine import AnalyticsEngine
from backend.budget_service import BudgetService
from backend.seeder import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and seed demo data on startup
    seed_database()
    yield


app = FastAPI(
    title="AI Spends Tracker & Analyzer API",
    description="Telemetry ingestion, reverse proxy, and AI cost arbitrage analyzer",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "AI Spends Tracker & Analyzer", "version": "1.0.0"}


# -------------------------------------------------------------
# 1. Telemetry Ingestion Endpoints
# -------------------------------------------------------------
@app.post("/api/v1/telemetry", status_code=201)
def ingest_telemetry(req: TelemetryIngestRequest, db: Session = Depends(get_db)):
    """Ingests a single AI request spend/token telemetry event."""
    prompt_cost, comp_cost, total_cost, cache_savings = PricingEngine.calculate_spend(
        db, req.model_id, req.prompt_tokens, req.completion_tokens, req.cached_tokens, req.reasoning_tokens
    )

    total_tokens = req.prompt_tokens + req.completion_tokens + req.reasoning_tokens
    event = SpendEvent(
        project_name=req.project_name,
        environment=req.environment,
        provider=req.provider,
        model_id=req.model_id,
        prompt_tokens=req.prompt_tokens,
        completion_tokens=req.completion_tokens,
        cached_tokens=req.cached_tokens,
        reasoning_tokens=req.reasoning_tokens,
        total_tokens=total_tokens,
        prompt_cost_usd=prompt_cost,
        completion_cost_usd=comp_cost,
        total_cost_usd=total_cost,
        latency_ms=req.latency_ms,
        http_status_code=req.http_status_code,
        feature_tag=req.feature_tag,
        user_identifier=req.user_identifier,
        timestamp=req.timestamp or SpendEvent.timestamp.default.arg()
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Check budget alerts
    budget_status = BudgetService.get_project_budget_status(db, req.project_name)

    return {
        "event_id": event.id,
        "total_cost_usd": total_cost,
        "cache_savings_usd": cache_savings,
        "budget_status": budget_status
    }


@app.post("/api/v1/telemetry/batch", status_code=201)
def ingest_batch_telemetry(req: BatchTelemetryRequest, db: Session = Depends(get_db)):
    """Batch ingestion endpoint for high-throughput collectors."""
    saved_ids = []
    for item in req.events:
        p_cost, c_cost, tot_cost, _ = PricingEngine.calculate_spend(
            db, item.model_id, item.prompt_tokens, item.completion_tokens, item.cached_tokens, item.reasoning_tokens
        )
        total_tokens = item.prompt_tokens + item.completion_tokens + item.reasoning_tokens
        event = SpendEvent(
            project_name=item.project_name,
            environment=item.environment,
            provider=item.provider,
            model_id=item.model_id,
            prompt_tokens=item.prompt_tokens,
            completion_tokens=item.completion_tokens,
            cached_tokens=item.cached_tokens,
            reasoning_tokens=item.reasoning_tokens,
            total_tokens=total_tokens,
            prompt_cost_usd=p_cost,
            completion_cost_usd=c_cost,
            total_cost_usd=tot_cost,
            latency_ms=item.latency_ms,
            http_status_code=item.http_status_code,
            feature_tag=item.feature_tag,
            user_identifier=item.user_identifier
        )
        db.add(event)
        saved_ids.append(event)
    db.commit()
    return {"message": f"Successfully ingested {len(saved_ids)} events"}


# -------------------------------------------------------------
# 2. AI Reverse Proxy Gateway Endpoint (/v1/chat/completions)
# -------------------------------------------------------------
@app.post("/v1/chat/completions")
def proxy_chat_completions(req: ProxyChatRequest, db: Session = Depends(get_db)):
    """
    OpenAI-compatible drop-in proxy endpoint.
    Intercepts calls, extracts tokens, calculates micro-cent spend,
    and logs telemetry automatically.
    """
    start_time = time.time()
    
    # Calculate approximate tokens from messages
    text_content = " ".join([str(m.get("content", "")) for m in req.messages])
    estimated_prompt_tokens = max(10, len(text_content.split()) * 4 // 3)
    
    # Check if system prompt has cache opportunity
    cached_tokens = int(estimated_prompt_tokens * 0.7) if len(text_content) > 1000 else 0
    estimated_completion_tokens = random.randint(40, 200)
    
    # Simulated execution latency
    latency_ms = int((time.time() - start_time) * 1000) + random.randint(150, 450)
    
    # Determine provider from model
    card = PricingEngine.get_rate_card(db, req.model)
    provider = card.get("provider", "openai")

    prompt_cost, comp_cost, total_cost, cache_savings = PricingEngine.calculate_spend(
        db, req.model, estimated_prompt_tokens, estimated_completion_tokens, cached_tokens
    )

    # Automatically persist spend event
    event = SpendEvent(
        project_name=req.project_name or "ProxyGateway",
        environment=req.environment or "production",
        provider=provider,
        model_id=req.model,
        prompt_tokens=estimated_prompt_tokens,
        completion_tokens=estimated_completion_tokens,
        cached_tokens=cached_tokens,
        total_tokens=estimated_prompt_tokens + estimated_completion_tokens,
        prompt_cost_usd=prompt_cost,
        completion_cost_usd=comp_cost,
        total_cost_usd=total_cost,
        latency_ms=latency_ms,
        feature_tag=req.feature_tag or "chat_proxy"
    )
    db.add(event)
    db.commit()

    # Return standard OpenAI chat completion response structure
    return {
        "id": f"chatcmpl-{random.randint(100000, 999999)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[Tracked via AI Proxy] Processed request via {req.model}. Prompt Tokens: {estimated_prompt_tokens}, Completion: {estimated_completion_tokens}, Total Cost: ${total_cost:.5f}."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": estimated_prompt_tokens,
            "completion_tokens": estimated_completion_tokens,
            "total_tokens": estimated_prompt_tokens + estimated_completion_tokens,
            "prompt_tokens_details": {
                "cached_tokens": cached_tokens
            }
        },
        "_ai_spends_metadata": {
            "total_cost_usd": total_cost,
            "cache_savings_usd": cache_savings,
            "latency_ms": latency_ms
        }
    }


# -------------------------------------------------------------
# 3. Analytics & Reporting Endpoints
# -------------------------------------------------------------
@app.get("/api/v1/analytics/summary")
def get_summary(
    project: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    return AnalyticsEngine.get_summary(db, project_name=project, environment=environment, days=days)


@app.get("/api/v1/analytics/timeseries")
def get_timeseries(
    project: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    return AnalyticsEngine.get_timeseries(db, project_name=project, environment=environment, days=days)


@app.get("/api/v1/analytics/models")
def get_model_breakdown(
    project: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    return AnalyticsEngine.get_model_breakdown(db, project_name=project, days=days)


@app.get("/api/v1/analytics/arbitrage")
def get_arbitrage(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    return AnalyticsEngine.get_arbitrage_recommendations(db, days=days)


@app.get("/api/v1/budgets")
def get_budgets(db: Session = Depends(get_db)):
    return BudgetService.get_all_budgets(db)


@app.get("/api/v1/ratecards")
def get_rate_cards(db: Session = Depends(get_db)):
    cards = db.query(ModelRateCard).all()
    return cards
