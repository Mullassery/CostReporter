"""
PyTokenCalc v0.5: Multi-Provider LLM Token Cost Calculator

Unified cost calculation and tracking across 20+ cloud providers and 10+ open-source APIs.
This is the cost calculation core that powers OpenAnchor.

v0.5 Scope (Cost Calculation Only):
- CostCalculator: Calculate cost for any provider/model/tokens
- CostDatabase: Track operations and aggregate costs
- PricingManager: Provider pricing + daily updates
- Budget Enforcement: Hard limits to prevent cost overruns

NOT included in v0.5 (deferred to future versions):
- Forecasting/ML predictions
- Dashboards/web UI
- Compliance/audit tracking
- Recommendations (that's OpenAnchor's job)
- Advanced reporting/analytics

Documentation: https://github.com/Mullassery/PyTokenCalc
OpenAnchor (uses this): https://github.com/Mullassery/openanchor
"""

__version__ = "0.5.0"
__author__ = "Georgi Mammen Mullassery"

# Core cost calculation classes (v0.5 and v0.6)
from .cost_calculator import CostCalculator, CostCalculatorV6
from .cost_model import Cost, ProviderType
from .cost_models import (
    UsageData,
    CostModel,
    CostModelRegistry,
    ClaudeTokenModel,
    GPT4oTokenModel,
    GeminiCharacterModel,
    GroqSpeedTieredModel,
    DeepInfraTokenModel,
    TogetherAITokenModel,
)
from .pricing_manager import PricingManager
from .database import DatabaseManager
from .persistence import CostDatabase

# Safety feature: Hard budget enforcement
from ._budget_enforcement import (
    BudgetEnforcer,
    BudgetLimit,
    BudgetStatus,
    BudgetPeriod,
    EnforcementAction,
    BudgetExceededError,
    get_global_enforcer,
    set_budget_limit,
)

__all__ = [
    # Core v0.5 (backwards compatible)
    "CostCalculator",
    "Cost",
    "ProviderType",
    "PricingManager",
    "DatabaseManager",
    "CostDatabase",
    # v0.6 multi-provider (NEW)
    "CostCalculatorV6",
    "UsageData",
    "CostModel",
    "CostModelRegistry",
    "ClaudeTokenModel",
    "GPT4oTokenModel",
    "GeminiCharacterModel",
    "GroqSpeedTieredModel",
    "DeepInfraTokenModel",
    "TogetherAITokenModel",
    # Budget enforcement (safety feature)
    "BudgetEnforcer",
    "BudgetLimit",
    "BudgetStatus",
    "BudgetPeriod",
    "EnforcementAction",
    "BudgetExceededError",
    "get_global_enforcer",
    "set_budget_limit",
]
