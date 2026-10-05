"""
Pricing calculation engine with rate card resolution and micro-cent precision.
"""

from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.database import ModelRateCard
from backend.config import DEFAULT_RATE_CARDS


class PricingEngine:

    @staticmethod
    def get_rate_card(db: Session, model_id: str) -> Dict[str, Any]:
        """Fetch rate card from DB, fall back to defaults, or generate heuristic rate."""
        # 1. Check DB
        db_card = db.query(ModelRateCard).filter(ModelRateCard.model_id == model_id).first()
        if db_card:
            return {
                "provider": db_card.provider,
                "displayName": db_card.display_name,
                "tier": db_card.tier,
                "promptPricePerMillion": db_card.prompt_price_per_million,
                "completionPricePerMillion": db_card.completion_price_per_million,
                "cachedPromptPricePerMillion": db_card.cached_prompt_price_per_million,
                "reasoningPricePerMillion": db_card.reasoning_price_per_million,
            }

        # 2. Check DEFAULT_RATE_CARDS
        clean_model = model_id.lower().strip()
        for key, card in DEFAULT_RATE_CARDS.items():
            if key in clean_model or clean_model in key:
                return card

        # 3. Heuristic fallback
        if "mini" in clean_model or "flash" in clean_model or "haiku" in clean_model or "small" in clean_model:
            return {
                "provider": "custom",
                "displayName": model_id,
                "tier": "economy",
                "promptPricePerMillion": 0.20,
                "completionPricePerMillion": 0.80,
                "cachedPromptPricePerMillion": 0.10,
                "reasoningPricePerMillion": 0.0,
            }
        else:
            return {
                "provider": "custom",
                "displayName": model_id,
                "tier": "frontier",
                "promptPricePerMillion": 2.50,
                "completionPricePerMillion": 10.00,
                "cachedPromptPricePerMillion": 1.25,
                "reasoningPricePerMillion": 0.0,
            }

    @classmethod
    def calculate_spend(
        cls,
        db: Session,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0
    ) -> Tuple[float, float, float, float]:
        """
        Returns:
            prompt_cost_usd, completion_cost_usd, total_cost_usd, cache_savings_usd
        """
        card = cls.get_rate_card(db, model_id)
        
        prompt_rate = card["promptPricePerMillion"] / 1_000_000.0
        cached_rate = card.get("cachedPromptPricePerMillion", prompt_rate * 0.5) / 1_000_000.0
        comp_rate = card["completionPricePerMillion"] / 1_000_000.0
        reasoning_rate = card.get("reasoningPricePerMillion", comp_rate) / 1_000_000.0

        # Uncached prompt tokens cost regular rate, cached tokens cost discounted rate
        uncached_prompt = max(0, prompt_tokens - cached_tokens)
        prompt_cost = (uncached_prompt * prompt_rate) + (cached_tokens * cached_rate)
        
        # Completion cost + optional separate reasoning tokens
        comp_cost = (completion_tokens * comp_rate) + (reasoning_tokens * reasoning_rate)
        total_cost = prompt_cost + comp_cost

        # Calculate what was saved via caching
        cache_savings = max(0.0, (cached_tokens * prompt_rate) - (cached_tokens * cached_rate))

        return round(prompt_cost, 6), round(comp_cost, 6), round(total_cost, 6), round(cache_savings, 6)
