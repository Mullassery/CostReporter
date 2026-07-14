# PyTokenCalc v0.7+ — Product Vision & Scope

**One thing, done perfectly: Unified token counting and cost calculation across 20+ LLM providers.**

---

## Core Mission

PyTokenCalc solves a single, critical problem in multi-provider LLM development:

> **Developers need ONE unified API to count tokens and calculate costs accurately across all LLM providers, without writing provider-specific integration code.**

### The Problem We Solve

1. **Token counting fragmentation**: Each LLM provider has a different tokenizer
   - OpenAI: tiktoken (public library)
   - Claude: API-only (no public tokenizer)
   - Gemini: API-only (proprietary)
   - Llama/Mistral: HF transformers (1000+ models)
   - Groq/DeepInfra: Model-specific, varies by provider

2. **Cost calculation complexity**: Each provider has unique billing logic
   - Claude: Simple input/output tokens
   - GPT-4o: Dual token model (full + mini tokens)
   - Gemini: Character-based (not tokens)
   - Groq: Speed-tiered pricing
   - DeepSeek: Batch-aware discounts

3. **Developer burden**: Integrate 10+ libraries and APIs manually
   - No unified interface
   - No intelligent routing (when to use local vs API)
   - No caching → expensive API calls
   - Different error handling per provider

### Our Solution

**PyTokenCalc provides:**
- ✅ **Unified API**: One function for all 20+ providers
- ✅ **Smart routing**: Local fast tokenizers + cached API calls
- ✅ **Accurate cost calculation**: 99%+ match vs official bills
- ✅ **Zero configuration**: Works out of the box
- ✅ **Extensible**: Easy to add new providers

---

## What PyTokenCalc IS

✅ **A Python library for:**
- Token counting (local + cached API)
- Cost calculation (provider-specific models)
- Batch operations
- Persistent storage (SQLite)
- Budget enforcement (hard limits)

✅ **Goals:**
- Single, clean API across all providers
- 99%+ accuracy vs official token counts
- <100ms latency (cached) for token counting
- Zero external service dependencies
- Minimal dependencies (pydantic core only)

✅ **Supported:**
- 20+ cloud LLM APIs (Anthropic, OpenAI, Google, Mistral, etc.)
- 10+ open-source inference APIs (Groq, DeepInfra, Together, etc.)
- Python 3.9+
- All operating systems

---

## What PyTokenCalc is NOT

❌ **NOT a service**: No backend, no web API, no database server
❌ **NOT a cost optimization platform**: We calculate costs per-request, we don't optimize or track them over time (that's OpenAnchor's job)
❌ **NOT an agent framework**: No LangChain, no automation, no orchestration
❌ **NOT a dashboard/UI**: Pure Python library for programmatic access
❌ **NOT a budget enforcement service**: No notifications, no alerts, no integrations (Slack, email, SMS)
❌ **NOT a forecasting engine**: No ML predictions, no anomaly detection, no recommendations
❌ **NOT a monitoring system**: No real-time dashboards, no alerting, no on-call integration

---

## Scope Boundaries (Prevent Creep)

### STRICTLY IN-SCOPE (v0.7+)

#### Phase 1: Token Counting (✅ DONE)
- ✅ OpenAI: tiktoken (local)
- ✅ Llama/Mistral: HF transformers (local)
- ✅ Caching: In-memory LRU + optional persistence
- ✅ Vision: Basic image/PDF support (placeholder for v0.8+)

#### Phase 2: Cloud API Integration (🚧 PLANNED)
- 🔜 Anthropic: Claude API token counting
- 🔜 Google: Gemini API token counting
- 🔜 Aggressive caching (reduce API calls 70-80%)

#### Phase 3: Vision/Multimodal (🚧 PLANNED)
- 🔜 Image token counting (Claude, GPT-4V, Gemini)
- 🔜 PDF token counting
- 🔜 Vision-specific pricing

#### Phase 4: Optimization (🚧 PLANNED)
- 🔜 System prompt assembly (dynamic, not static)
- 🔜 Batch API calls
- 🔜 RAG context optimization

### ⛔ STRICTLY OUT-OF-SCOPE (Will Not Implement)

#### Services & Backends
- ❌ REST API server
- ❌ Database server
- ❌ Message queue (Celery, RQ, etc.)
- ❌ Scheduled jobs/cron tasks
- ❌ Async workers

#### Integrations
- ❌ Slack notifications
- ❌ Email alerts
- ❌ SMS alerts (Twilio)
- ❌ PagerDuty/Oncall integration
- ❌ Webhook callbacks

#### Monitoring & Observability
- ❌ Real-time dashboards
- ❌ Metrics collection (Prometheus)
- ❌ Distributed tracing (Jaeger, DataDog)
- ❌ Log aggregation
- ❌ APM integration

#### Advanced Features (NOT LIBRARY SCOPE)
- ❌ ML-based cost forecasting
- ❌ Anomaly detection
- ❌ Cost optimization recommendations
- ❌ Model selection algorithms
- ❌ Provider comparison engine
- ❌ What-if scenarios

#### Business Logic
- ❌ Multi-tenant support
- ❌ User authentication
- ❌ Role-based access control (RBAC)
- ❌ Audit logging (compliance)
- ❌ Billing/invoicing
- ❌ Chargeback analysis

### RELATED BUT SEPARATE PROJECTS

These features belong in separate projects that *use* PyTokenCalc:

| Feature | Project | Status |
|---------|---------|--------|
| Cost optimization | [OpenAnchor](https://github.com/Mullassery/openanchor) | Active |
| Dashboard/UI | Future project | Planned |
| Service + alerts | Future project | Planned |
| Forecasting ML | Future project | Planned |

---

## Design Principles

### 1. Single Responsibility
PyTokenCalc does ONE thing: count tokens and calculate costs accurately.
All other features → separate projects or user code.

### 2. Zero External Dependencies
- Core: only `pydantic` (data validation)
- Optional: `tiktoken`, `transformers` (for local tokenizers)
- NO service dependencies: no SMTP, no Slack, no databases

### 3. Configurability Over Features
Let users extend PyTokenCalc rather than bloating the core:
- Custom providers: subclass `CostModel`
- Custom tokenizers: subclass `TokenCounter`
- Custom persistence: use `CostDatabase` API

### 4. Fail Fast, Not Gracefully
- No retry loops, no circuit breakers
- No graceful degradation (if local tokenizer fails, error out)
- No fallback logic (trust user to configure correctly)
- Error messages point to root cause, not workarounds

### 5. Pure Library Mentality
- No global state (except singletons for config)
- No side effects (no writing logs, no connecting to services)
- No implicit behavior (explicit APIs only)
- User controls everything (threading, async, batching, etc.)

---

## Roadmap: What's Next (v0.8 - v1.0)

### v0.8: Cloud API Integration
- Anthropic: `messages.count_tokens()` API
- Google: Gemini token counting API
- Aggressive caching: 70-80% API call reduction

### v0.9: Vision/Multimodal
- Image token counting for Claude, GPT-4V, Gemini
- PDF token counting
- Vision pricing models

### v1.0: Production Hardened
- Comprehensive error handling
- Full test coverage (100%)
- Performance benchmarks (local <10ms, cached <1ms)
- Documentation: API reference + provider guide

### Post-v1.0: Locked Scope
- No new providers without community request + review
- No service features (alerts, dashboards, etc.)
- No agent/orchestration features
- Focus: stability, performance, documentation

---

## For Future Contributors: Scope Check

Before proposing a feature, ask:

1. **Is this token counting or cost calculation?**
   - YES → In scope (if for an LLM provider)
   - NO → Out of scope

2. **Does this require a running service?**
   - YES → Out of scope (separate project)
   - NO → Maybe in scope

3. **Does this add a new external dependency (SMTP, Slack, DB server, etc.)?**
   - YES → Out of scope
   - NO → Maybe in scope

4. **Can this be done in user code instead?**
   - YES → Out of scope (provide an extension point instead)
   - NO → Maybe in scope

5. **Is this solving a library problem or a business problem?**
   - Library → In scope
   - Business → Out of scope (separate project)

---

## Version Contract

### v0.7.0 (Current)
- **Guarantee**: Token counting + cost calculation stable
- **API**: CostCalculatorV6, TokenCounterRegistry locked
- **Providers**: 6 cost models, 2 local tokenizers (tiktoken, HF)

### v0.8-v1.0
- **Guarantee**: Incremental improvements only
- **API**: Additive only (no breaking changes to v0.7)
- **Scope**: Cloud APIs + vision + optimization

### Post-v1.0
- **Guarantee**: Long-term stability
- **Breaking changes**: Only if critical
- **Scope**: Bug fixes + performance improvements only

---

## Why This Scope Matters

### 1. Clarity
Users know exactly what PyTokenCalc does: token counting + cost calculation.
Everything else is a separate project.

### 2. Maintainability
One focused library is easier to test, document, and maintain than a service platform.

### 3. Reliability
Pure library code is more stable than service code with external dependencies.

### 4. Performance
No I/O, no network calls (except optional API calls for cloud tokenizers).
Fast, predictable behavior.

### 5. Extensibility
Users can wrap PyTokenCalc with their own services (alerting, dashboards, etc.).
We provide the core; they build the platform.

---

## Examples: Feature Requests & How We'd Handle Them

### ❌ "Add Slack notifications when budget exceeded"
**Response**: Out of scope. Use PyTokenCalc's `BudgetExceededError` in your code to send Slack alerts.

### ✅ "Add support for Claude 4 token counting"
**Response**: In scope! File an issue with pricing details.

### ❌ "Build a web dashboard for cost tracking"
**Response**: Out of scope for PyTokenCalc. Consider building a separate project that uses PyTokenCalc.

### ✅ "Improve token counting accuracy for GPT-4o"
**Response**: In scope! Let's improve the test coverage.

### ❌ "Add machine learning to predict next month's costs"
**Response**: Out of scope. Belongs in a separate forecasting project.

### ✅ "Add support for Llama 2 quantization-aware token counting"
**Response**: In scope! Subclass `TokenCounter` and we'll review.

---

## Conclusion

**PyTokenCalc is a focused, stable, production-grade token counting and cost calculation library for multi-provider LLM development.**

Everything else is someone else's responsibility.

This keeps us sharp, reliable, and valuable.

---

*Last updated: 2026-07-15*  
*Maintainer: Georgi Mammen Mullassery*  
*Repository: https://github.com/Mullassery/PyTokenCalc*
