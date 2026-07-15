"""
PyTokenCalc v0.8: Multi-Provider LLM Token Counter

Unified token counting across 20+ cloud providers and 10+ open-source APIs.

Features:
- Local tokenizers (tiktoken for OpenAI, HuggingFace transformers for Llama/Mistral/etc.)
- Intelligent routing: auto-detect tokenizer per model
- Aggressive caching: 70-80% API call reduction
- Vision/multimodal support (images, PDFs)
- Workflow integration: CLI + REST API for automation platforms

Supported Providers:
- Cloud APIs: Anthropic Claude, OpenAI GPT, Google Gemini, Mistral, Groq, DeepInfra, Together, etc. (20+)
- Open-source APIs: Llama, DeepSeek, Qwen, GLM, MiniMax, etc. (10+)

Token Counting + Workflow Automation:
- Count tokens for any LLM provider
- Cache results to reduce API calls (70-80% fewer API calls)
- CLI: pytokencalc count, count-vision, providers, models, cache-stats
- REST API (Port 8005): n8n, Power Automate, Temporal, Airflow integration
- No external services or persistence
- No configuration needed

Repository: https://github.com/Mullassery/PyTokenCalc
"""

__version__ = "0.8.0"
__author__ = "Georgi Mammen Mullassery"

# Token counting (v0.7+: Multi-provider token counter)
try:
    from .tokenizers import (
        TokenCounter,
        TokenCountResult,
        TokenCounterRegistry,
        TokenCounterCache,
    )
    TOKENIZERS_AVAILABLE = True
except ImportError:
    TOKENIZERS_AVAILABLE = False

__all__ = [
    # Token counting interface
    "TokenCounter",
    "TokenCountResult",
    "TokenCounterRegistry",
    "TokenCounterCache",
]
