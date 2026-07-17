"""
Cohere token counter.
Provides token counting for Cohere models (Command, Command Light, etc).
"""

from typing import List, Dict, Any
import time

from .base import TokenCounter, TokenCountResult

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


class CohereTokenCounter(TokenCounter):
    """Cohere token counter using official API"""

    SUPPORTED_MODELS = {
        "command",
        "command-light",
        "command-nightly",
        "command-r",
        "command-r-plus",
    }

    def __init__(self):
        if not COHERE_AVAILABLE:
            raise ImportError(
                "cohere is required for Cohere token counting. "
                "Install: pip install cohere"
            )
        self.client = cohere.Client()

    @property
    def provider_name(self) -> str:
        return "cohere"

    @property
    def supported_models(self) -> List[str]:
        return list(self.SUPPORTED_MODELS)

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens using Cohere's tokenize API"""
        if not self.validate_model(model):
            raise ValueError(f"Unknown Cohere model: {model}")

        start_time = time.time()

        try:
            response = self.client.tokenize(text=text)
            token_count = len(response.tokens)
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
        info.update({"library": "cohere"})
        return info
