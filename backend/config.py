"""
Configuration and default rate cards for AI API Spends Tracker.
Prices are in USD per 1,000,000 tokens.
"""

from typing import Dict, Any

DEFAULT_RATE_CARDS: Dict[str, Dict[str, Any]] = {
    # OpenAI
    "gpt-4o": {
        "provider": "openai",
        "displayName": "GPT-4o",
        "tier": "frontier",
        "promptPricePerMillion": 2.50,
        "completionPricePerMillion": 10.00,
        "cachedPromptPricePerMillion": 1.25,
        "reasoningPricePerMillion": 0.0,
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "displayName": "GPT-4o Mini",
        "tier": "economy",
        "promptPricePerMillion": 0.15,
        "completionPricePerMillion": 0.60,
        "cachedPromptPricePerMillion": 0.075,
        "reasoningPricePerMillion": 0.0,
    },
    "o1": {
        "provider": "openai",
        "displayName": "OpenAI o1",
        "tier": "reasoning",
        "promptPricePerMillion": 15.00,
        "completionPricePerMillion": 60.00,
        "cachedPromptPricePerMillion": 7.50,
        "reasoningPricePerMillion": 60.00,
    },
    "o3-mini": {
        "provider": "openai",
        "displayName": "OpenAI o3-mini",
        "tier": "reasoning",
        "promptPricePerMillion": 1.10,
        "completionPricePerMillion": 4.40,
        "cachedPromptPricePerMillion": 0.55,
        "reasoningPricePerMillion": 4.40,
    },
    # Anthropic
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "displayName": "Claude 3.5 Sonnet",
        "tier": "frontier",
        "promptPricePerMillion": 3.00,
        "completionPricePerMillion": 15.00,
        "cachedPromptPricePerMillion": 0.30,
        "reasoningPricePerMillion": 0.0,
    },
    "claude-3-5-haiku": {
        "provider": "anthropic",
        "displayName": "Claude 3.5 Haiku",
        "tier": "economy",
        "promptPricePerMillion": 0.80,
        "completionPricePerMillion": 4.00,
        "cachedPromptPricePerMillion": 0.08,
        "reasoningPricePerMillion": 0.0,
    },
    # Google Gemini
    "gemini-1.5-pro": {
        "provider": "google",
        "displayName": "Gemini 1.5 Pro",
        "tier": "frontier",
        "promptPricePerMillion": 1.25,
        "completionPricePerMillion": 5.00,
        "cachedPromptPricePerMillion": 0.3125,
        "reasoningPricePerMillion": 0.0,
    },
    "gemini-1.5-flash": {
        "provider": "google",
        "displayName": "Gemini 1.5 Flash",
        "tier": "economy",
        "promptPricePerMillion": 0.075,
        "completionPricePerMillion": 0.30,
        "cachedPromptPricePerMillion": 0.01875,
        "reasoningPricePerMillion": 0.0,
    },
    "gemini-2.0-flash": {
        "provider": "google",
        "displayName": "Gemini 2.0 Flash",
        "tier": "economy",
        "promptPricePerMillion": 0.10,
        "completionPricePerMillion": 0.40,
        "cachedPromptPricePerMillion": 0.025,
        "reasoningPricePerMillion": 0.0,
    },
    # DeepSeek
    "deepseek-chat": {
        "provider": "deepseek",
        "displayName": "DeepSeek V3",
        "tier": "economy",
        "promptPricePerMillion": 0.14,
        "completionPricePerMillion": 0.28,
        "cachedPromptPricePerMillion": 0.014,
        "reasoningPricePerMillion": 0.0,
    },
    "deepseek-reasoner": {
        "provider": "deepseek",
        "displayName": "DeepSeek R1",
        "tier": "reasoning",
        "promptPricePerMillion": 0.55,
        "completionPricePerMillion": 2.19,
        "cachedPromptPricePerMillion": 0.14,
        "reasoningPricePerMillion": 2.19,
    },
    # Mistral
    "mistral-large": {
        "provider": "mistral",
        "displayName": "Mistral Large 2",
        "tier": "frontier",
        "promptPricePerMillion": 2.00,
        "completionPricePerMillion": 6.00,
        "cachedPromptPricePerMillion": 0.50,
        "reasoningPricePerMillion": 0.0,
    },
}

DEFAULT_BUDGETS = {
    "CustomerSupportBot": {"monthly_limit": 500.0, "alert_threshold": 80.0, "hard_cap": False},
    "DocSearchRAG": {"monthly_limit": 1200.0, "alert_threshold": 85.0, "hard_cap": False},
    "CodeGenAssistant": {"monthly_limit": 2000.0, "alert_threshold": 90.0, "hard_cap": True},
    "DataExtractionPipeline": {"monthly_limit": 400.0, "alert_threshold": 75.0, "hard_cap": False},
}
