"""
Anthropic Claude token counter.
Provides token counting for Claude 3 models (Opus, Sonnet, Haiku, 3.5-Sonnet).
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicTokenCounter(TokenCounter):
    """Anthropic Claude token counter using official API"""

    SUPPORTED_MODELS = {
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3.5-sonnet",
    }

    def __init__(self):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic is required for Claude token counting. "
                "Install: pip install anthropic"
            )
        self.client = Anthropic()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def supported_models(self) -> List[str]:
        return list(self.SUPPORTED_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using Anthropic's token counting API"""
        if not self.validate_model(model):
            raise ValueError(f"Unknown Claude model: {model}")

        start_time = time.time()

        try:
            response = self.client.messages.count_tokens(
                model=model,
                messages=[{"role": "user", "content": text}]
            )
            token_count = response.input_tokens
        except Exception as e:
            raise RuntimeError(f"Failed to count tokens for {model}: {e}")

        latency_ms = (time.time() - start_time) * 1000

        return TokenCountResult(
            input_tokens=token_count,
            cached=False,
            source="api",
            latency_ms=latency_ms,
            provider=self.provider_name,
            model=model,
        )

    def validate_model(self, model: str) -> bool:
        """Check if model is supported"""
        return model.lower() in self.SUPPORTED_MODELS

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({"library": "anthropic"})
        return info
