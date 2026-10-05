"""
Database seeder for default rate cards, budgets, and realistic 30-day demo telemetry.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import init_db, SessionLocal, ModelRateCard, Budget, SpendEvent
from backend.config import DEFAULT_RATE_CARDS, DEFAULT_BUDGETS
from backend.pricing_engine import PricingEngine


def seed_database():
    """Seeds the database with initial models, budgets, and 30-day sample spends if empty."""
    init_db()
    db = SessionLocal()
    try:
        # 1. Seed Rate Cards
        for model_id, card in DEFAULT_RATE_CARDS.items():
            existing = db.query(ModelRateCard).filter(ModelRateCard.model_id == model_id).first()
            if not existing:
                db_card = ModelRateCard(
                    model_id=model_id,
                    display_name=card["displayName"],
                    provider=card["provider"],
                    tier=card["tier"],
                    prompt_price_per_million=card["promptPricePerMillion"],
                    completion_price_per_million=card["completionPricePerMillion"],
                    cached_prompt_price_per_million=card.get("cachedPromptPricePerMillion", 0.0),
                    reasoning_price_per_million=card.get("reasoningPricePerMillion", 0.0),
                )
                db.add(db_card)
        db.commit()

        # 2. Seed Budgets
        for proj_name, b_info in DEFAULT_BUDGETS.items():
            existing = db.query(Budget).filter(Budget.project_name == proj_name).first()
            if not existing:
                db_b = Budget(
                    project_name=proj_name,
                    monthly_limit_usd=b_info["monthly_limit"],
                    alert_threshold_percent=b_info["alert_threshold"],
                    hard_cap_enabled=b_info["hard_cap"]
                )
                db.add(db_b)
        db.commit()

        # 3. Seed 30-day historical Spend Events if none exist
        count = db.query(SpendEvent).count()
        if count < 50:
            print("Seeding 30-day sample AI spend events for demo...")
            projects = [
                ("CustomerSupportBot", ["gpt-4o", "gpt-4o-mini", "claude-3-5-haiku"]),
                ("DocSearchRAG", ["claude-3-5-sonnet", "gemini-1.5-pro", "gemini-1.5-flash"]),
                ("CodeGenAssistant", ["claude-3-5-sonnet", "o1", "deepseek-chat"]),
                ("DataExtractionPipeline", ["gemini-1.5-flash", "deepseek-chat", "gpt-4o-mini"]),
            ]
            
            now = datetime.utcnow()
            events = []

            for days_ago in range(30, -1, -1):
                day_time = now - timedelta(days=days_ago)
                # Generate 10 - 25 calls per day across projects
                calls_today = random.randint(12, 28)
                for _ in range(calls_today):
                    proj_name, allowed_models = random.choice(projects)
                    model_id = random.choice(allowed_models)
                    card = DEFAULT_RATE_CARDS[model_id]

                    # Token distributions based on model type
                    if card["tier"] == "reasoning":
                        prompt_tokens = random.randint(800, 3500)
                        completion_tokens = random.randint(400, 1500)
                        reasoning_tokens = random.randint(500, 2000)
                        cached_tokens = 0
                        latency = random.randint(2200, 8500)
                    elif card["tier"] == "economy":
                        prompt_tokens = random.randint(300, 2000)
                        completion_tokens = random.randint(100, 600)
                        reasoning_tokens = 0
                        cached_tokens = random.choice([0, 0, int(prompt_tokens * 0.6)])
                        latency = random.randint(300, 1200)
                    else:  # frontier
                        prompt_tokens = random.randint(1000, 4500)
                        completion_tokens = random.randint(300, 1200)
                        reasoning_tokens = 0
                        # 30% chance of cache hit
                        cached_tokens = int(prompt_tokens * 0.7) if random.random() < 0.35 else 0
                        latency = random.randint(900, 3200)

                    total_tokens = prompt_tokens + completion_tokens + reasoning_tokens
                    prompt_cost, comp_cost, total_cost, _ = PricingEngine.calculate_spend(
                        db, model_id, prompt_tokens, completion_tokens, cached_tokens, reasoning_tokens
                    )

                    event_time = day_time + timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59),
                        seconds=random.randint(0, 59)
                    )

                    event = SpendEvent(
                        project_name=proj_name,
                        environment=random.choice(["production", "production", "production", "staging"]),
                        provider=card["provider"],
                        model_id=model_id,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        cached_tokens=cached_tokens,
                        reasoning_tokens=reasoning_tokens,
                        total_tokens=total_tokens,
                        prompt_cost_usd=prompt_cost,
                        completion_cost_usd=comp_cost,
                        total_cost_usd=total_cost,
                        latency_ms=latency,
                        http_status_code=200,
                        feature_tag=random.choice(["chat_agent", "rag_retrieval", "auto_summary", "code_gen"]),
                        user_identifier=f"user_{random.randint(100, 999)}",
                        timestamp=event_time
                    )
                    events.append(event)

            db.bulk_save_objects(events)
            db.commit()
            print(f"Successfully seeded {len(events)} sample spend events!")
    finally:
        db.close()


def insert_single_event(
    project_name: str,
    environment: str,
    provider: str,
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
    reasoning_tokens: int = 0,
    latency_ms: int = 450,
    feature_tag: str = "interactive_simulation",
    http_status_code: int = 200,
    user_identifier: str = None,
    timestamp: datetime = None
) -> SpendEvent:
    """Inserts a single live telemetry spend event into the database."""
    db = SessionLocal()
    try:
        p_cost, c_cost, tot_cost, _ = PricingEngine.calculate_spend(
            db, model_id, prompt_tokens, completion_tokens, cached_tokens, reasoning_tokens
        )
        total_tokens = prompt_tokens + completion_tokens + reasoning_tokens
        event = SpendEvent(
            project_name=project_name,
            environment=environment,
            provider=provider,
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            total_tokens=total_tokens,
            prompt_cost_usd=p_cost,
            completion_cost_usd=c_cost,
            total_cost_usd=tot_cost,
            latency_ms=latency_ms,
            http_status_code=http_status_code,
            feature_tag=feature_tag,
            user_identifier=user_identifier,
            timestamp=timestamp or datetime.utcnow()
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    finally:
        db.close()

