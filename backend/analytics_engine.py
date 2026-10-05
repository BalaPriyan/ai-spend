"""
Analytics Engine for aggregations, time-series rollups, and AI cost arbitrage recommendations.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import SpendEvent, ModelRateCard
from backend.pricing_engine import PricingEngine


class AnalyticsEngine:

    @staticmethod
    def get_summary(
        db: Session,
        project_name: Optional[str] = None,
        environment: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculates executive KPI summary metrics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.query(SpendEvent).filter(SpendEvent.timestamp >= cutoff)

        if project_name and project_name != "All":
            query = query.filter(SpendEvent.project_name == project_name)
        if environment and environment != "All":
            query = query.filter(SpendEvent.environment == environment)

        events = query.all()

        total_spend = sum(e.total_cost_usd or 0.0 for e in events)
        total_tokens = sum(e.total_tokens or 0 for e in events)
        total_prompt_tokens = sum(e.prompt_tokens or 0 for e in events)
        total_cached_tokens = sum(e.cached_tokens or 0 for e in events)
        total_requests = len(events)

        # Cache metrics
        cache_hit_rate = (total_cached_tokens / total_prompt_tokens * 100.0) if total_prompt_tokens > 0 else 0.0
        
        # Estimate cache savings
        cache_savings = 0.0
        for e in events:
            if (e.cached_tokens or 0) > 0:
                card = PricingEngine.get_rate_card(db, e.model_id)
                prompt_rate = card["promptPricePerMillion"] / 1_000_000.0
                cached_rate = card.get("cachedPromptPricePerMillion", prompt_rate * 0.5) / 1_000_000.0
                cache_savings += e.cached_tokens * (prompt_rate - cached_rate)

        # Run rate projection
        daily_avg = (total_spend / max(1, days))
        projected_month_end = daily_avg * 30.0

        active_models = len({e.model_id for e in events})
        active_projects = len({e.project_name for e in events})
        avg_latency = (sum(e.latency_ms or 0 for e in events) / total_requests) if total_requests > 0 else 0.0

        return {
            "total_spend_usd": round(total_spend, 2),
            "projected_month_end_usd": round(projected_month_end, 2),
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "cache_savings_usd": round(cache_savings, 2),
            "cache_hit_rate_pct": round(cache_hit_rate, 1),
            "active_models_count": active_models,
            "active_projects_count": active_projects,
            "avg_latency_ms": round(avg_latency, 1),
        }

    @staticmethod
    def get_timeseries(
        db: Session,
        project_name: Optional[str] = None,
        environment: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Returns daily aggregated spends broken down by major providers."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.query(SpendEvent).filter(SpendEvent.timestamp >= cutoff)

        if project_name and project_name != "All":
            query = query.filter(SpendEvent.project_name == project_name)
        if environment and environment != "All":
            query = query.filter(SpendEvent.environment == environment)

        events = query.order_by(SpendEvent.timestamp.asc()).all()

        daily_map: Dict[str, Dict[str, Any]] = {}
        # Pre-populate all days in range so charts have smooth contiguous dates
        for d in range(days + 1):
            date_str = (cutoff + timedelta(days=d)).strftime("%Y-%m-%d")
            daily_map[date_str] = {
                "date": date_str,
                "total_spend": 0.0,
                "openai": 0.0,
                "anthropic": 0.0,
                "google": 0.0,
                "deepseek": 0.0,
                "other": 0.0,
                "tokens": 0,
                "requests": 0
            }

        for e in events:
            date_str = e.timestamp.strftime("%Y-%m-%d")
            if date_str not in daily_map:
                daily_map[date_str] = {
                    "date": date_str,
                    "total_spend": 0.0,
                    "openai": 0.0,
                    "anthropic": 0.0,
                    "google": 0.0,
                    "deepseek": 0.0,
                    "other": 0.0,
                    "tokens": 0,
                    "requests": 0
                }
            cost = e.total_cost_usd or 0.0
            daily_map[date_str]["total_spend"] += cost
            daily_map[date_str]["tokens"] += (e.total_tokens or 0)
            daily_map[date_str]["requests"] += 1

            prov = (e.provider or "other").lower()
            if "openai" in prov:
                daily_map[date_str]["openai"] += cost
            elif "anthropic" in prov:
                daily_map[date_str]["anthropic"] += cost
            elif "google" in prov:
                daily_map[date_str]["google"] += cost
            elif "deepseek" in prov:
                daily_map[date_str]["deepseek"] += cost
            else:
                daily_map[date_str]["other"] += cost

        # Format and round
        results = []
        for _, val in sorted(daily_map.items()):
            val["total_spend"] = round(val["total_spend"], 2)
            val["openai"] = round(val["openai"], 2)
            val["anthropic"] = round(val["anthropic"], 2)
            val["google"] = round(val["google"], 2)
            val["deepseek"] = round(val["deepseek"], 2)
            val["other"] = round(val["other"], 2)
            results.append(val)
        return results

    @staticmethod
    def get_model_breakdown(
        db: Session,
        project_name: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Returns spend, token count, and latency aggregated per model."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.query(SpendEvent).filter(SpendEvent.timestamp >= cutoff)

        if project_name and project_name != "All":
            query = query.filter(SpendEvent.project_name == project_name)

        events = query.all()
        total_all_spend = sum(e.total_cost_usd or 0.0 for e in events)

        model_map: Dict[str, Dict[str, Any]] = {}
        for e in events:
            mid = e.model_id
            if mid not in model_map:
                card = PricingEngine.get_rate_card(db, mid)
                model_map[mid] = {
                    "model_id": mid,
                    "display_name": card.get("displayName", mid),
                    "provider": card.get("provider", e.provider),
                    "tier": card.get("tier", "standard"),
                    "request_count": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cached_tokens": 0,
                    "total_tokens": 0,
                    "total_cost_usd": 0.0,
                    "total_latency": 0,
                }
            item = model_map[mid]
            item["request_count"] += 1
            item["prompt_tokens"] += (e.prompt_tokens or 0)
            item["completion_tokens"] += (e.completion_tokens or 0)
            item["cached_tokens"] += (e.cached_tokens or 0)
            item["total_tokens"] += (e.total_tokens or 0)
            item["total_cost_usd"] += (e.total_cost_usd or 0.0)
            item["total_latency"] += (e.latency_ms or 0)

        results = []
        for mid, data in model_map.items():
            reqs = data["request_count"]
            cost = data["total_cost_usd"]
            results.append({
                "model_id": mid,
                "display_name": data["display_name"],
                "provider": data["provider"],
                "tier": data["tier"],
                "request_count": reqs,
                "prompt_tokens": data["prompt_tokens"],
                "completion_tokens": data["completion_tokens"],
                "cached_tokens": data["cached_tokens"],
                "total_tokens": data["total_tokens"],
                "total_cost_usd": round(cost, 2),
                "percentage_of_total": round((cost / total_all_spend * 100.0) if total_all_spend > 0 else 0.0, 1),
                "avg_latency_ms": round((data["total_latency"] / reqs) if reqs > 0 else 0.0, 1)
            })

        results.sort(key=lambda x: x["total_cost_usd"], reverse=True)
        return results

    @staticmethod
    def get_arbitrage_recommendations(db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """
        Intelligently identifies cost optimization opportunities:
        1. Model downgrade for non-reasoning high-volume chat/RAG (e.g. GPT-4o -> Claude 3.5 Haiku or Gemini Flash).
        2. Prompt caching enablement for repetitive system prompts.
        3. Reasoning model arbitrage (e.g. o1 -> DeepSeek R1 or o3-mini).
        """
        breakdowns = AnalyticsEngine.get_model_breakdown(db, days=days)
        recommendations = []

        for item in breakdowns:
            mid = item["model_id"].lower()
            cost = item["total_cost_usd"]
            prompt_tokens = item["prompt_tokens"]
            cached_tokens = item["cached_tokens"]

            # Arbitrage Rule 1: GPT-4o high volume -> migrate to Claude 3.5 Haiku or Gemini 1.5 Flash
            if "gpt-4o" in mid and not ("mini" in mid) and cost > 20.0:
                # Estimate cost on Claude 3.5 Haiku ($0.80 / $4.00 per 1M)
                haiku_cost = (prompt_tokens * 0.80 / 1_000_000) + (item["completion_tokens"] * 4.00 / 1_000_000)
                savings = max(0.0, cost - haiku_cost)
                pct = (savings / cost * 100.0) if cost > 0 else 0.0
                recommendations.append({
                    "id": "rec_gpt4o_haiku",
                    "title": f"Migrate '{item['display_name']}' to Claude 3.5 Haiku or Gemini 1.5 Flash",
                    "description": f"You spent ${cost:,.2f} on {item['display_name']} across {item['request_count']:,} calls. Standard chat and summarization tasks yield comparable quality on economy models at ~75% lower cost.",
                    "current_model": item['display_name'],
                    "suggested_model": "Claude 3.5 Haiku / Gemini 1.5 Flash",
                    "estimated_monthly_savings_usd": round(savings, 2),
                    "savings_percentage": round(pct, 1),
                    "reasoning_type": "MODEL_DOWNGRADE",
                    "impact_level": "HIGH" if savings > 100 else "MEDIUM"
                })

            # Arbitrage Rule 2: OpenAI o1 -> migrate to DeepSeek R1 or o3-mini
            if "o1" in mid and not ("mini" in mid) and cost > 30.0:
                # Compare against o3-mini ($1.10 / $4.40 per 1M)
                o3_cost = (prompt_tokens * 1.10 / 1_000_000) + (item["completion_tokens"] * 4.40 / 1_000_000)
                savings = max(0.0, cost - o3_cost)
                pct = (savings / cost * 100.0) if cost > 0 else 0.0
                recommendations.append({
                    "id": "rec_o1_o3",
                    "title": f"Arbitrage '{item['display_name']}' with OpenAI o3-mini or DeepSeek R1",
                    "description": f"Reasoning tasks on {item['display_name']} accounted for ${cost:,.2f}. Transitioning to o3-mini preserves high math/code benchmarks while cutting token expenditure by ~85%.",
                    "current_model": item['display_name'],
                    "suggested_model": "OpenAI o3-mini / DeepSeek R1",
                    "estimated_monthly_savings_usd": round(savings, 2),
                    "savings_percentage": round(pct, 1),
                    "reasoning_type": "REASONING_ARBITRAGE",
                    "impact_level": "HIGH"
                })

            # Arbitrage Rule 3: High prompt volume with low cache rate
            if prompt_tokens > 200_000 and (cached_tokens / max(1, prompt_tokens)) < 0.15:
                card = PricingEngine.get_rate_card(db, item["model_id"])
                cache_discount = (card["promptPricePerMillion"] - card.get("cachedPromptPricePerMillion", 0.0)) / 1_000_000
                potential_savings = (prompt_tokens * 0.5) * cache_discount
                if potential_savings > 10.0:
                    recommendations.append({
                        "id": f"rec_cache_{mid}",
                        "title": f"Enable Prompt Caching for {item['display_name']}",
                        "description": f"Current prompt cache hit rate is only {round(cached_tokens/max(1, prompt_tokens)*100, 1)}%. Static system prompts over 1,024 tokens qualify for 50-80% discounts via prefix caching.",
                        "current_model": item['display_name'],
                        "suggested_model": f"{item['display_name']} (Cached Prefixes)",
                        "estimated_monthly_savings_usd": round(potential_savings, 2),
                        "savings_percentage": 45.0,
                        "reasoning_type": "PROMPT_CACHING",
                        "impact_level": "MEDIUM"
                    })

        return recommendations
