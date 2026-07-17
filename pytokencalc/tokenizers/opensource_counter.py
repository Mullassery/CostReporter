"""
Open-source model token counter.
Supports DeepSeek, Falcon, PALM 2, and additional Llama/Mistral variants via HuggingFace.
"""

from typing import List, Dict, Any, Optional
import time

from .base import TokenCounter, TokenCountResult

try:
    from transformers import AutoTokenizer
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


class OpenSourceTokenCounter(TokenCounter):
    """Token counter for open-source models using HuggingFace"""

    MODEL_ALIASES = {
        # DeepSeek
        "deepseek-chat": "deepseek-ai/deepseek-coder-1.3b",
        "deepseek-coder": "deepseek-ai/deepseek-coder-7b",
        # Falcon
        "falcon-7b": "tiiuae/falcon-7b",
        "falcon-40b": "tiiuae/falcon-40b",
        # PALM 2
        "text-bison": "google/flan-t5-large",
        "code-bison": "google/flan-t5-large",
        # Additional Llama variants
        "llama-2-7b-hf": "meta-llama/Llama-2-7b-hf",
        "llama-2-13b-hf": "meta-llama/Llama-2-13b-hf",
        "llama-2-70b-hf": "meta-llama/Llama-2-70b-hf",
        "llama-3-8b": "meta-llama/Meta-Llama-3-8B",
        "llama-3-70b": "meta-llama/Meta-Llama-3-70B",
        # Mistral variants
        "mistral-7b": "mistralai/Mistral-7B-v0.1",
        "mistral-instruct": "mistralai/Mistral-7B-Instruct-v0.1",
        "mixtral-8x7b": "mistralai/Mixtral-8x7B",
    }

    def __init__(self):
        if not HF_AVAILABLE:
            raise ImportError(
                "transformers is required for open-source model token counting. "
                "Install: pip install transformers torch"
            )
        self.tokenizers = {}

    def _resolve_model_id(self, model: str) -> str:
        """Resolve model alias to HuggingFace model ID"""
        model_lower = model.lower()
        if model_lower in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model_lower]
        return model

    def _get_tokenizer(self, model: str):
        """Get or load tokenizer for model"""
        model_id = self._resolve_model_id(model)

        if model_id not in self.tokenizers:
            try:
                self.tokenizers[model_id] = AutoTokenizer.from_pretrained(model_id)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load tokenizer for {model_id}: {e}"
                )

        return self.tokenizers[model_id]

    @property
    def provider_name(self) -> str:
        return "opensource"

    @property
    def supported_models(self) -> List[str]:
        return list(self.MODEL_ALIASES.keys())

    def count(self, text: str, model: str) -> TokenCountResult:
        """Count tokens for open-source model"""
        if not self.validate_model(model):
            raise ValueError(f"Unknown open-source model: {model}")

        start_time = time.time()

        try:
            tokenizer = self._get_tokenizer(model)
            tokens = tokenizer.encode(text)
            token_count = len(tokens)
        except Exception as e:
            raise RuntimeError(f"Failed to count tokens for {model}: {e}")

        latency_ms = (time.time() - start_time) * 1000

        return TokenCountResult(
            input_tokens=token_count,
            cached=False,
            source="local",
            latency_ms=latency_ms,
            provider=self.provider_name,
            model=model,
        )

    def validate_model(self, model: str) -> bool:
        """Check if model can be loaded"""
        try:
            self._get_tokenizer(model)
            return True
        except Exception:
            return False

    def get_tokenizer_info(self) -> Dict[str, Any]:
        """Return tokenizer info"""
        info = super().get_tokenizer_info()
        info.update({
            "library": "transformers",
            "aliases": self.MODEL_ALIASES,
        })
        return info
