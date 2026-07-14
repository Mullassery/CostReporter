"""
PyTokenCalc v0.7: Multi-provider LLM token cost calculator.
Calculates accurate per-request costs using provider-specific token models.

SCOPE: Cost CALCULATION only
- What does this single request cost?
- Per-request precision with real-time pricing

COST TRACKING (aggregation, history, reporting) belongs in OpenAnchor.
"""

from typing import List
from .cost_models import UsageData, CostModelRegistry


class CostCalculatorV6:
    """
    PyTokenCalc v0.7: Multi-provider cost calculator with provider-specific token models.

    Calculates accurate per-request costs across 20+ cloud providers and 10+ open-source APIs.

    SCOPE: Cost CALCULATION only (per single request)
    - Accurate cost calculation using provider-specific token models
    - Real-time pricing data
    - Budget enforcement (hard cost limits)

    NOT IN SCOPE (see OpenAnchor):
    - Cost tracking (aggregate across many requests)
    - Cost reporting (breakdowns by provider/model/task)
    - Cost optimization (model/provider selection)
    - Historical cost analysis
    """

    def __init__(self):
        self.model_registry = CostModelRegistry()

    def calculate(self, usage: UsageData) -> float:
        """
        Calculate cost for a single request.

        Args:
            usage: UsageData with provider, model, and token counts

        Returns:
            Cost in USD (float)

        Example:
            calc = CostCalculatorV6()
            usage = UsageData(
                provider="anthropic",
                model="claude-3-5-sonnet",
                input_tokens=1_000_000,
                output_tokens=500_000
            )
            cost = calc.calculate(usage)  # $10.50
        """
        return self.model_registry.calculate_cost(usage)

    def calculate_batch(self, usages: List[UsageData]) -> List[float]:
        """
        Calculate costs for multiple requests.

        Args:
            usages: List of UsageData objects

        Returns:
            List of costs in USD

        Example:
            costs = calc.calculate_batch([usage1, usage2, usage3])
            total = sum(costs)
        """
        return [self.calculate(usage) for usage in usages]
