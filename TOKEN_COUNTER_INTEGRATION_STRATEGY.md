# PyTokenCalc: Token Counter Integration Strategy

## Executive Summary

Token counting across LLM providers is **fragmented and inconsistent**:
- **OpenAI (tiktoken)**: Public library, 100% accurate for GPT
- **Meta (Llama)**: Public SentencePiece, 100% accurate for Llama family
- **Anthropic (Claude)**: API-only, no public tokenizer
- **Google (Gemini)**: API-only proprietary tokenizer
- **Groq/DeepInfra**: Model-specific, varies by provider

**Problem**: Developers must choose between:
1. **Fast but inaccurate** (local estimates, 15-20% error on Claude)
2. **Slow but accurate** (API calls per request, 200-500ms latency, $$)
3. **Manual integration** (different code path per provider, maintenance nightmare)

**PyTokenCalc Solution**: Unified, intelligent routing—fast local tokenizers where available, cached API calls for proprietary models.

---

## Architecture: Hybrid Token Counting

```
Input: (model_id, text, images?)
    ↓
CostCalculatorV6.count_tokens()
    ↓
TokenCounterRegistry (route by provider)
    ├─ OpenAI/GPT → tiktoken (5ms, 100% accurate)
    ├─ Meta/Llama → HF transformers (10ms, 100% accurate)
    ├─ Google/Gemini → Cached API (200ms first call, 0ms cached)
    ├─ Anthropic/Claude → Cached API (200ms first call, 0ms cached)
    └─ Custom/Open-source → Model-specific tokenizer
    ↓
VisionTokenizer (if images)
    ├─ Claude vision formula
    ├─ GPT-4 vision formula
    ├─ Gemini vision formula
    └─ Cached API for unknowns
    ↓
TokenCache (hash-based)
    ├─ In-memory (current session)
    └─ Persistent (optional, for production)
    ↓
Output: {input_tokens, output_tokens, cached: bool, source: "local|api"}
```

---

## Implementation Phases

### Phase 1: Local Tokenizers (Week 1)
**Goal**: Fast estimates for 60% of models without API calls

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# GPT models (via tiktoken)
gpt_tokens = registry.count_tokens("gpt-4o", "Your prompt here")
# Result: 42 tokens (from tiktoken, 5ms)

# Llama models (via HF transformers)
llama_tokens = registry.count_tokens("llama-70b", "Your prompt here")
# Result: 45 tokens (from HF, 10ms)

# Mistral models (via HF)
mistral_tokens = registry.count_tokens("mistral-large", "Your prompt here")
# Result: 44 tokens (from HF, 8ms)
```

**Deliverables**:
- `pytokencalc/tokenizers/base.py` — Abstract `TokenCounter` class
- `pytokencalc/tokenizers/openai_counter.py` — tiktoken wrapper
- `pytokencalc/tokenizers/huggingface_counter.py` — HF transformers wrapper
- `pytokencalc/tokenizers/registry.py` — Intelligent routing
- Tests with real models

**Dependencies to add**:
```toml
dependencies = [
    "tiktoken>=0.5.0",  # OpenAI GPT tokenization
    "transformers>=4.30.0",  # Llama, Mistral, 1000+ models
    "sentencepiece>=0.1.99",  # Dependency for many HF models
]
```

---

### Phase 2: Cloud API Integration (Week 2)
**Goal**: Accurate counts for proprietary models (Claude, Gemini)

```python
from pytokencalc.tokenizers import TokenCounterRegistry
from pytokencalc.tokenizers.cache import TokenCounterCache

# Initialize with API credentials
registry = TokenCounterRegistry(
    anthropic_api_key="sk-ant-...",
    google_api_key="..."
)

# Claude (via Anthropic API)
claude_tokens = registry.count_tokens("claude-3-5-sonnet", "Your prompt")
# Result: 42 tokens (from API, 200ms first call, 0ms cached)

# Gemini (via Google API)
gemini_tokens = registry.count_tokens("gemini-2-flash", "Your prompt")
# Result: 38 tokens (from API, 300ms first call, 0ms cached)

# Check cache status
# cached=True → from cache (0ms)
# cached=False → from API (200-300ms)
```

**Deliverables**:
- `pytokencalc/tokenizers/anthropic_counter.py` — Anthropic API wrapper
- `pytokencalc/tokenizers/google_counter.py` — Google API wrapper
- `pytokencalc/tokenizers/cache.py` — Intelligent caching
- `pytokencalc/tokenizers/config.py` — API credential management

**Caching strategy**:
```python
# Cache key: hash(model_id + text[:100] + modality)
# TTL: 24 hours (token counts don't change)
# Size: 1M+ entries (LRU eviction)
# Persistence: Optional file-based backup

cache_hit_rate_expected = 60-70%  # Same prompts reused often
cost_reduction = 70-80%  # vs always calling API
latency_p95 = 10-50ms    # vs 200-500ms without cache
```

---

### Phase 3: Vision/Multimodal (Week 3)
**Goal**: Accurate vision token counting for images, PDFs, etc.

```python
from pytokencalc.tokenizers import TokenCounterRegistry
from pytokencalc.vision_tokenizers import VisionTokenCounter

registry = TokenCounterRegistry()

# Image token counting
# Claude: Automatic via API
claude_image_tokens = registry.count_tokens(
    "claude-3-5-sonnet",
    text="Analyze this image",
    image_path="/path/to/image.jpg",
    image_type="image"  # or "pdf"
)
# Result: 1258 tokens (image base + variable content tokens)

# GPT-4 Vision: Formula-based
gpt_image_tokens = registry.count_tokens(
    "gpt-4-vision",
    text="Analyze this image",
    image_url="https://example.com/image.png",
    image_type="url"
)
# Result: 85 + (4 * 4) * 170 = 2805 tokens (for 1024x1024)

# Gemini: Automatic via API
gemini_image_tokens = registry.count_tokens(
    "gemini-2-flash",
    text="Analyze this PDF",
    file_path="/path/to/document.pdf",
    image_type="pdf"
)
# Result: 2100 tokens (PDF-aware tokenization)
```

**Provider-specific vision formulas**:

| Provider | Formula | Base | Variable | Max Resolution |
|----------|---------|------|----------|-----------------|
| **Claude** | API-only | ~1200 | Content-based | 2576px |
| **GPT-4V** | 85 + (w/256 × h/256) × 170 | 85 | Size-based | 2048px |
| **Gemini** | API-only | ~258 | Content+model | 4096px |
| **Llama** | Base + patches | ~1000 | ~336×336 patches | 1024px |

**Deliverables**:
- `pytokencalc/tokenizers/vision_counter.py` — Vision-specific logic
- `pytokencalc/vision_tokenizers/claude_vision.py` — Claude formula
- `pytokencalc/vision_tokenizers/gpt_vision.py` — GPT-4V formula
- `pytokencalc/vision_tokenizers/gemini_vision.py` — Gemini formula
- `pytokencalc/vision_tokenizers/llama_vision.py` — LLaVA formula

---

### Phase 4: System Prompt + Tool Tokenization (Week 4)
**Goal**: Easy token counting for system prompts, tools, RAG context

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# System prompt tokenization
system_prompt = "You are a helpful assistant that..."
system_tokens = registry.count_tokens("claude-3-5-sonnet", system_prompt)

# Tool definitions tokenization
tools = [
    {"name": "search", "description": "Search the internet..."},
    {"name": "calculator", "description": "Perform calculations..."},
]
tool_tokens = registry.count_system_definition("claude-3-5-sonnet", tools)

# RAG context tokenization
rag_chunks = [
    "Document chunk 1...",
    "Document chunk 2...",
]
rag_tokens = registry.count_batch([
    {"model": "claude-3-5-sonnet", "text": chunk}
    for chunk in rag_chunks
])

# Batch API calls for cost optimization
# 10 prompts → 1 API call instead of 10 calls
```

**Deliverables**:
- `pytokencalc/tokenizers/batch_counter.py` — Batch tokenization API
- `pytokencalc/tokenizers/system_counter.py` — System prompt/tool counting
- Utilities for RAG context tokenization

---

## Integration with Current PyTokenCalc v0.6

### Updated CostCalculatorV6 Flow

```python
from pytokencalc import UsageData, CostCalculatorV6

calc = CostCalculatorV6()

# Method 1: Provide actual token counts (current, no change)
usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1_000_000,  # User provides
    output_tokens=500_000,
    task_type="analysis"
)
cost = calc.calculate(usage)

# Method 2: NEW - Auto-count tokens (v0.6+)
usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    text="Your prompt here",  # NEW: text instead of tokens
    image_path="/path/to/image.jpg",  # Optional
    output_tokens=500_000,  # Can mix text + provided tokens
    task_type="analysis"
)
cost = calc.calculate_with_auto_counting(usage)
```

### Changes to cost_models.py

```python
class CostModel(ABC):
    # Existing
    def calculate(self, usage: UsageData) -> float:
        """Calculate cost from provided token counts"""
        pass

    # NEW
    def calculate_with_counting(self, usage: UsageData, 
                               token_counter: TokenCounter) -> float:
        """Calculate cost with automatic token counting"""
        input_tokens = token_counter.count(
            usage.model,
            usage.text,
            usage.image_path
        ) if hasattr(usage, 'text') else usage.input_tokens
        
        output_tokens = usage.output_tokens
        
        usage.input_tokens = input_tokens
        return self.calculate(usage)
```

---

## API Design

### For End Users

```python
from pytokencalc import CostCalculatorV6, UsageData

calc = CostCalculatorV6(
    anthropic_api_key="...",  # Optional, for Claude
    google_api_key="...",     # Optional, for Gemini
    cache_file="~/.pytokencalc/cache.db"  # Optional persistence
)

# Auto-count tokens
tokens = calc.count_tokens(
    model="claude-3-5-sonnet",
    text="Your prompt here",
    images=["path/to/image1.jpg", "path/to/image2.jpg"],
    include_system_prompt=True,
    system_prompt="You are...",
    include_tools=True,
    tools=[{...}]
)
# Returns: TokenCount(
#   input_tokens=1500,
#   image_tokens=2000,
#   system_tokens=50,
#   tool_tokens=200,
#   total=3750,
#   cached=False,
#   source="api"
# )

# Calculate cost with auto-counting
usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    text="Your prompt here",
    system_prompt="...",
    tools=[...],
    output_tokens=250_000
)
cost = calc.calculate_with_counting(usage)
```

### For Library Developers

```python
from pytokencalc.tokenizers import TokenCounterRegistry, TokenCounter

# Create custom tokenizer for new provider
class MyProviderTokenCounter(TokenCounter):
    def count(self, text: str, model: str) -> int:
        # Your implementation
        pass
    
    def count_vision(self, image_path: str, model: str) -> int:
        # Your implementation
        pass

# Register it
registry = TokenCounterRegistry()
registry.register("myprovider", MyProviderTokenCounter())

# Use it
tokens = registry.count_tokens("myprovider-large", "Your text")
```

---

## Performance Targets

| Metric | Target | How | Fallback |
|--------|--------|-----|----------|
| **Local token count latency** | <10ms p95 | In-process, no I/O | N/A |
| **Cached API latency** | <1ms p95 | Memory lookup | <10ms p95 |
| **Fresh API latency** | <300ms p95 | Parallel API calls | None (must wait) |
| **Cache hit rate** | 60-70% | Aggressive caching | Lower with new prompts |
| **Cost reduction vs all-API** | 70-80% | Smart routing | 0% without caching |
| **Accuracy vs official** | >99% | Local for public, API for proprietary | 85-95% (tiktoken on Claude) |
| **Memory usage (cache)** | <500MB | LRU + compression | Unbounded growth without |
| **API calls/day** | <5% of requests | Caching + batching | 100% (no cache) |

---

## Roadmap

```
Week 1: Phase 1 - Local tokenizers (tiktoken, HF)
Week 2: Phase 2 - Cloud API integration (Anthropic, Google) + caching
Week 3: Phase 3 - Vision/multimodal token counting
Week 4: Phase 4 - System prompts, tools, RAG optimization

v0.7.0 Release: All phases + comprehensive tests + documentation
```

---

## Migration Path

### For Existing PyTokenCalc Users

**No breaking changes.** Old API still works:

```python
# Old (still works)
from pytokencalc import CostCalculatorV6, UsageData
usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1_000_000,
    output_tokens=500_000
)
cost = calc.calculate(usage)

# New (optional)
usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    text="Your prompt...",  # NEW
)
cost = calc.calculate_with_counting(usage)
```

---

## Competitive Advantage

| Aspect | tiktoken | HF Transformers | Cloud APIs | **PyTokenCalc** |
|--------|----------|-----------------|-----------|-----------------|
| **Providers supported** | 1 (OpenAI) | 1000+ (public) | 1 (each) | 20+ (unified) |
| **Speed** | Fast (5ms) | Moderate (10ms) | Slow (200ms) | Smart (5-200ms) |
| **Accuracy** | 100% (GPT) | 100% (matching) | 100% | >99% (unified) |
| **API-free** | Yes | Yes | No | Optional |
| **Vision** | No | Limited | Yes | Yes |
| **One import** | No | No | No | **Yes** |
| **Caching** | Manual | Manual | Manual | **Built-in** |
| **Batch API** | No | No | Limited | **Yes** |

---

## Files to Create

```
pytokencalc/
├── tokenizers/
│   ├── __init__.py
│   ├── base.py                    # Abstract TokenCounter
│   ├── registry.py                # TokenCounterRegistry + routing
│   ├── cache.py                   # TokenCounterCache (in-memory + persistent)
│   ├── config.py                  # API credential management
│   ├── openai_counter.py          # tiktoken wrapper
│   ├── huggingface_counter.py     # HF transformers wrapper
│   ├── anthropic_counter.py       # Anthropic API wrapper
│   ├── google_counter.py          # Google API wrapper
│   ├── vision_counter.py          # Vision-specific logic
│   ├── batch_counter.py           # Batch token counting
│   └── system_counter.py          # System prompt + tools
├── vision_tokenizers/
│   ├── __init__.py
│   ├── claude_vision.py           # Claude vision formulas
│   ├── gpt_vision.py              # GPT-4V vision formulas
│   ├── gemini_vision.py           # Gemini vision formulas
│   └── llama_vision.py            # LLaVA vision formulas
└── (existing cost_models.py integrates with tokenizers)

tests/
├── test_tokenizers_openai.py      # tiktoken tests
├── test_tokenizers_huggingface.py # HF tests
├── test_tokenizers_api.py         # API integration tests
├── test_tokenizers_cache.py       # Caching tests
├── test_vision_tokenizers.py      # Vision token tests
└── test_cost_with_tokenizers.py   # Integration with costs
```

---

## Success Metrics

After implementation, PyTokenCalc will provide:

1. **Unified Token Counting**
   - Single API for 20+ providers
   - 99%+ accuracy (matches official counts)
   - <100ms p95 latency (cached)

2. **Cost Savings**
   - 70-80% reduction in API token-counting calls
   - 60-70% cache hit rate from prompt reuse
   - $0-10/month vs $100-1000 without optimization

3. **Developer Experience**
   - Zero configuration for public models (tiktoken, HF)
   - Optional API keys for proprietary models
   - One import, one function call

4. **Competitive Advantage**
   - Only solution supporting 20+ providers + auto-counting
   - Intelligent routing (fast for public, accurate for proprietary)
   - Built-in caching (others require external Redis/memcached)

---

## Scope Boundaries: What's NOT Included

### ❌ NOT in Roadmap
- Cost optimization recommendations (belongs in separate project)
- Real-time dashboards (not a library feature)
- Alert/notification system (Slack, email, SMS)
- Machine learning forecasting
- Anomaly detection
- Multi-tenant support
- Web API / REST service

### ✅ What We Focus On
- Token counting accuracy (99%+ vs official)
- Cost calculation precision
- Performance (<10ms local, <1ms cached)
- Clean, extensible API
- Easy provider integration

### Why This Matters
PyTokenCalc is a **library**, not a **platform**. Our job is to provide the core building block; users and separate projects build the platform on top.

---

## Next Steps

1. **Phase 1 kickoff**: Start with tiktoken + HF transformers integration ✅ DONE
2. **Test with real models**: Validate accuracy against official counts ✅ DONE
3. **Document provider list**: Which tokenizer each provider uses ✅ DONE
4. **Implement caching**: Design and validate cache strategy ✅ DONE
5. **Phase 2-4**: Roll out API, vision, system prompt support 🚧 NEXT
