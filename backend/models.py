"""
Pydantic models and schemas for AI Spends Tracker.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TelemetryIngestRequest(BaseModel):
    project_name: str = Field(..., description="Target project/service name")
    environment: str = Field(default="production", description="Environment: production, staging, development")
    provider: str = Field(..., description="Provider name: openai, anthropic, google, deepseek, mistral")
    model_id: str = Field(..., description="Model identifier e.g. gpt-4o, claude-3-5-sonnet")
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    http_status_code: int = Field(default=200)
    feature_tag: str = Field(default="general")
    user_identifier: Optional[str] = None
    timestamp: Optional[datetime] = None


class BatchTelemetryRequest(BaseModel):
    events: List[TelemetryIngestRequest]


class ProxyChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    project_name: Optional[str] = "ProxyGateway"
    environment: Optional[str] = "production"
    feature_tag: Optional[str] = "chat_proxy"


class SpendSummaryResponse(BaseModel):
    total_spend_usd: float
    current_month_spend_usd: float
    projected_month_end_usd: float
    total_tokens: int
    total_requests: int
    cache_savings_usd: float
    cache_hit_rate_pct: float
    active_models_count: int
    active_projects_count: int
    avg_latency_ms: float
