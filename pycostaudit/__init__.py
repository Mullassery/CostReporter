"""
PyCostAudit - Real-time LLM cost tracking and optimization
Tracks Claude Code costs across 15+ hidden dimensions and provides actionable recommendations.
"""

__version__ = "0.9.0"
__author__ = "Georgi Mammen Mullassery"

from . import (
    advanced_filters,
    custom_report_builder,
    detailed_token_classifier,
    detailed_recommendations,
    interactive_guide,
    user_context,
)

# CRITICAL: Hard budget enforcement (prevents runaway costs)
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
    "advanced_filters",
    "custom_report_builder",
    "detailed_token_classifier",
    "detailed_recommendations",
    "interactive_guide",
    "user_context",
    # Budget enforcement (v1.3.0+)
    "BudgetEnforcer",
    "BudgetLimit",
    "BudgetStatus",
    "BudgetPeriod",
    "EnforcementAction",
    "BudgetExceededError",
    "get_global_enforcer",
    "set_budget_limit",
]
