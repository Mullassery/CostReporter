# CostReporter Architecture: Agent-Native Cost Analysis Engine

## Core Principle

**CostReporter is NOT a dashboard. It's a Claude Code skill that Claude itself uses to diagnose and fix costs.**

```
User works in Claude Code
    ↓
CostReporter tracks operations silently
    ↓
User asks Claude: "How much am I spending?"
    ↓
Claude calls CostReporter API → gets structured cost data
    ↓
Claude analyzes + explains in natural language:
"Browser scrapes cost $45 this week (55x more than file reads).
Move 3 to disk. Saves $12/week. Should I do it?"
    ↓
User says: "Yes"
    ↓
Claude implements the fix using other tools (edit code, etc.)
```

**No dashboards. No CLIs. Just API + agent-friendly output.**

---

## Architecture Layers

### Layer 1: Rust Core (Silent Tracking)
**File:** `crates/cost-reporter/src/`

Runs in background, never bothers the user. Records:
- Every operation (API call, file read, MCP invocation)
- Session context (when it started, what it's doing, tags)
- Timestamps, tokens, model, cost

**No UI. No reporting. Just data collection.**

**Key Modules:**
```
cost_tracker.rs          → Record operations + calculate cost
session_tracker.rs       → Group operations by session context
file_format_profiler.rs  → Apply file source multipliers (36x variance)
operation_profiler.rs    → Categorize by operation type (55x variance)
mcp_profiler.rs          → Track MCP costs + trends
storage.rs               → SQLite backend (local, immutable)
```

---

### Layer 2: Agent-Friendly Output Format
**File:** `python/src/cost_reporter/__init__.py`

CostReporter exposes a Python API. Claude calls it. Output is structured JSON + explanation fields.

**Not for users. For Claude.**

```python
from cost_reporter import CostReporter

reporter = CostReporter()

# Method 1: Get session cost breakdown
session_analysis = reporter.analyze_session(session_id="debug-auth")
# Returns:
{
  "session_id": "debug-auth",
  "duration_seconds": 2400,
  "total_cost_usd": 12.40,
  "operations": 47,
  
  # Claude reads these to understand the diagnosis
  "cost_by_operation_type": {
    "file_read_url": {"count": 12, "cost": 5.40, "tokens": 4200, "explanation": "PDFs via URL cost 3.6x more than from disk"},
    "browser_scrape": {"count": 8, "cost": 4.20, "tokens": 2800, "explanation": "Browser scraping is 55x more expensive than file reads (parsing overhead)"},
    "mcp_invocation": {"count": 23, "cost": 2.20, "tokens": 1500, "explanation": "Web Search MCP (15 calls) and Code Execution (8 calls)"},
    "ai_call": {"count": 4, "cost": 0.60, "tokens": 200, "explanation": "Direct API calls are cheap baseline"}
  },
  
  # Claude understands the root cause
  "diagnosis": {
    "biggest_waste": {
      "type": "file_read_url",
      "cost": 5.40,
      "percentage": 44,
      "recommendation": "Move PDFs from URL to local disk",
      "savings_potential": 3.60  # 3.6x cost reduction
    },
    "second_biggest": {
      "type": "browser_scrape",
      "cost": 4.20,
      "percentage": 34,
      "recommendation": "Batch browser operations or use API instead",
      "savings_potential": 0.85  # 85% reduction via batching
    }
  },
  
  # Claude can act on this
  "actionable_recommendations": [
    {
      "rank": 1,
      "action": "Move 12 PDF reads from URL to local disk",
      "effort": "5 minutes",
      "savings": "$3.60 this session, ~$42/week",
      "implementation": "Change URL reads to disk.open() in session code"
    },
    {
      "rank": 2,
      "action": "Batch 8 browser scrapes into 2 operations",
      "effort": "15 minutes",
      "savings": "$2.80 this session, ~$30/week",
      "implementation": "Group similar scrape requests, call once per group"
    },
    {
      "rank": 3,
      "action": "Cache Web Search results (used 4 times)",
      "effort": "10 minutes",
      "savings": "$0.80 this session, ~$10/week",
      "implementation": "Check cache before calling Web Search"
    }
  ]
}
```

**Claude reads this and says:**
> "Your debug session cost $12.40 because:
> 1. You read 12 PDFs via URL (cost: $5.40) — move to disk and save $3.60
> 2. You did 8 browser scrapes (cost: $4.20) — batch them and save $2.80
> 3. Web Search was cached poorly (cost: $0.80) — add caching
> 
> Total: Fix these 3 things and save $42/week.
> 
> Want me to implement these changes?"

---

### Layer 3: Claude Code Integration (The Skill)
**File:** `claude_code_skill.py`

CostReporter is registered as a Claude Code **skill**. Claude can invoke it like any other tool.

```yaml
# Hypothetical skill definition
name: cost-reporter
description: Analyze LLM costs in this session
methods:
  - analyze_session(session_id)         → Session cost breakdown
  - analyze_daily()                     → Daily summary
  - analyze_mcp_costs()                 → Which MCPs cost most
  - get_optimization_recommendations()  → Top 5 cost-saving actions
  - detect_anomalies()                  → Unusual spending patterns
```

**Claude uses it like this:**
```
User: "Am I overspending?"
      ↓
Claude: "Let me check your costs..."
      ↓
Claude calls: cost_reporter.analyze_daily()
      ↓
Claude reads: "Browser ops are 55% of spend, trending up 40%"
      ↓
Claude: "Yes, your browser scraping cost $320 this week 
         (55x more expensive than file reads). 
         
         You could save $240/week by:
         1. Batching scrapes (effort: 2 hours)
         2. Using FileSystem API instead (effort: 1 hour)
         3. Caching results (effort: 30 min)
         
         Want me to implement these?"
```

---

## Output Format (Agent-Friendly Specifications)

### 1. Session Analysis Output
**Purpose:** Claude understands what cost money in this debugging session

```json
{
  "session_id": "string",
  "session_name": "string (user-provided tag)",
  "started_at": "ISO 8601 timestamp",
  "duration_seconds": "integer",
  "total_cost_usd": "float (2 decimals)",
  "total_tokens": "integer",
  
  "by_operation_type": {
    "operation_type": {
      "count": "integer",
      "cost_usd": "float",
      "tokens": "integer",
      "percentage_of_session": "float 0-100",
      "explanation": "string (why it costs this much)"
    }
  },
  
  "by_file_format": {
    "csv_local": {"count": 5, "cost": 0.05},
    "pdf_local": {"count": 3, "cost": 0.12},
    "pdf_url": {"count": 8, "cost": 1.44, "explanation": "3.6x multiplier for network download"},
    "image_url": {"count": 2, "cost": 0.34}
  },
  
  "by_mcp": {
    "web_search": {"calls": 12, "cost": 0.68, "avg_cost_per_call": 0.057},
    "code_execution": {"calls": 5, "cost": 0.35, "avg_cost_per_call": 0.070},
    "python_interpreter": {"calls": 3, "cost": 0.18, "avg_cost_per_call": 0.060}
  },
  
  "diagnosis": {
    "root_causes": [
      {
        "rank": 1,
        "type": "operation_type",
        "category": "file_read_url",
        "cost_usd": 1.44,
        "percentage": 44,
        "problem_statement": "You read 8 PDFs via URL. This costs 3.6x more than reading from disk.",
        "recommendation": "Move PDFs to local directory",
        "expected_savings_usd": 3.60,
        "effort_minutes": 5,
        "roi_weekly": "$42"
      },
      {
        "rank": 2,
        "type": "mcp_usage",
        "category": "web_search",
        "cost_usd": 0.68,
        "percentage": 20,
        "problem_statement": "Web Search was called 12 times. Some queries were duplicates.",
        "recommendation": "Cache search results for recurring queries",
        "expected_savings_usd": 0.34,
        "effort_minutes": 10,
        "roi_weekly": "$10"
      }
    ],
    "total_fixable_cost": 2.42,
    "total_fixable_percentage": 64,
    "claude_action_plan": "Should I fix these? I can implement all 3 recommendations in 30 minutes."
  }
}
```

**Claude parses this and explains:**
```
"Your session cost $12.40 total.

BIGGEST PROBLEMS:
1. (44% of cost) You read 8 PDFs via URL instead of disk
   → Move them to disk = $3.60 savings
   → Effort: 5 min

2. (20% of cost) Web Search called 12 times, some duplicates
   → Add caching = $0.34 savings
   → Effort: 10 min

3. (12% of cost) Browser scrapes aren't batched
   → Batch them = $0.60 savings
   → Effort: 15 min

FIX ALL 3 → Save $4.54 this session (~$65/week)
Effort: 30 minutes

Want me to implement?"
```

### 2. Daily/Weekly Summary Output
**Purpose:** Claude sees spending trends and anomalies

```json
{
  "period": "daily|weekly|monthly",
  "date_range": {"start": "ISO 8601", "end": "ISO 8601"},
  "total_cost_usd": "float",
  "total_tokens": "integer",
  
  "daily_breakdown": [
    {
      "date": "2026-07-05",
      "cost": 47.30,
      "trend": "↑ 12% higher than average",
      "drivers": ["browser_scrapes (48%)", "file_reads_url (35%)"]
    }
  ],
  
  "spending_pattern": {
    "average_daily": 42.50,
    "highest_day": {"date": "2026-07-05", "cost": 47.30},
    "lowest_day": {"date": "2026-07-02", "cost": 38.20},
    "trend_direction": "increasing",
    "trend_magnitude": "+12% week-over-week",
    "anomalies": [
      {
        "date": "2026-07-05",
        "cost": 47.30,
        "deviation": "+11%",
        "likely_cause": "Started 8 browser scrapes (new pattern) + 12 PDF URL reads"
      }
    ]
  },
  
  "top_cost_drivers": [
    {"type": "file_read_url", "cost": 156.80, "percentage": 48},
    {"type": "browser_scrape", "cost": 98.40, "percentage": 30},
    {"type": "mcp_web_search", "cost": 45.20, "percentage": 14}
  ],
  
  "opportunities": [
    {
      "name": "Move PDF reads to disk",
      "current_cost": 156.80,
      "projected_cost": 43.50,
      "savings_weekly": "$420",
      "effort": "1 hour"
    },
    {
      "name": "Batch browser scrapes",
      "current_cost": 98.40,
      "projected_cost": 18.90,
      "savings_weekly": "$240",
      "effort": "2 hours"
    }
  ]
}
```

**Claude says:**
```
"You spent $297 this week.

TREND: ↑ 12% higher than normal (caused by 8 browser scrapes you started Tuesday)

TOP 3 COSTS:
1. PDFs via URL — $156.80 (48%)
   → Move to disk = $113 savings/week
2. Browser scrapes — $98.40 (30%)
   → Batch them = $80 savings/week
3. Web Search MCPs — $45.20 (14%)
   → Cache results = $15 savings/week

POTENTIAL: Save $208/week ($10,800/year) with minimal changes."
```

### 3. MCP Cost Ranking Output
**Purpose:** Claude identifies which MCPs are budget killers

```json
{
  "period": "daily|weekly|monthly",
  "total_mcp_cost": "float",
  "mcp_ranking": [
    {
      "rank": 1,
      "name": "code_execution",
      "calls": 89,
      "cost_usd": 12.40,
      "percentage": 47,
      "avg_cost_per_call": 0.139,
      "trend": "↑ 8% higher than last week",
      "anomaly": "Friday spike: 34 calls ($6.20)",
      "caching_opportunity": "Detected 12 repeated commands",
      "recommendation": "Cache bash command outputs"
    },
    {
      "rank": 2,
      "name": "web_search",
      "calls": 156,
      "cost_usd": 8.90,
      "percentage": 34,
      "avg_cost_per_call": 0.057,
      "trend": "→ stable",
      "anomaly": "Tuesday spike: 42 calls ($2.40)",
      "caching_opportunity": "Detected 8 duplicate queries",
      "recommendation": "Enable result caching"
    },
    {
      "rank": 3,
      "name": "filesystem",
      "calls": 234,
      "cost_usd": 1.50,
      "percentage": 6,
      "avg_cost_per_call": 0.006,
      "trend": "→ stable",
      "recommendation": "Use more (cheapest option!)"
    }
  ],
  
  "claude_insight": "Code Execution is costing 8x more than Web Search per call ($0.139 vs $0.057). Consider caching command outputs or using FileSystem API instead."
}
```

**Claude says:**
```
"Your MCPs cost breakdown:

1. 🔴 Code Execution: $12.40 (47% of MCP spend)
   └─ 89 calls, avg $0.139 each
   └─ Friday spike detected (34 calls)
   └─ 12 repeated commands could be cached
   
2. 🟡 Web Search: $8.90 (34%)
   └─ 156 calls, avg $0.057 each
   └─ 8 duplicate queries detected
   └─ Add caching → save $3/week
   
3. 🟢 FileSystem: $1.50 (6%)
   └─ 234 calls, avg $0.006 each
   └─ Cheapest option! Use more of this.

ACTION: Cache Code Execution outputs + Web Search results = $8/week savings."
```

---

## Integration with Claude Code

### Method 1: Explicit User Query
```
User: "How much am I spending?"
↓
Claude invokes: cost_reporter.analyze_daily()
↓
Claude explains findings in natural language
↓
Claude offers: "Should I fix this? Here's the plan."
```

### Method 2: Proactive Alerts
```
CostReporter detects: "Session cost exceeded $50"
↓
CostReporter notifies Claude
↓
Claude: "Your session cost $52 (unusual). Here's why."
↓
Claude offers: "Optimize now or continue as-is?"
```

### Method 3: Agent-Driven Optimization
```
User: "Optimize my costs"
↓
Claude invokes: cost_reporter.get_optimization_recommendations()
↓
Claude receives: [
  {action: "Move PDFs to disk", savings: "$42/week", effort: "5min"},
  {action: "Cache Web Search", savings: "$10/week", effort: "10min"},
  ...
]
↓
Claude: "Found 5 optimizations. Implementing now..."
↓
Claude uses other tools to implement fixes
↓
Claude: "Done. You'll save $230/week."
```

---

## Key Design Principles

1. **Silent Tracking**
   - CostReporter runs in background
   - Never interrupts user
   - Just collects data

2. **Claude is the UI**
   - No dashboards to build
   - Claude is more intelligent than any dashboard
   - Claude can chain actions: analyze → explain → fix

3. **Structured Output for Claude**
   - JSON with explanation fields
   - Each object has "why" not just "what"
   - Ranked by impact (Claude sees top 3 issues first)

4. **Actionable Insights**
   - Every recommendation includes: effort estimate + savings + implementation hint
   - Claude can implement fixes using other tools

5. **No User-Facing UI**
   - Conversations are the UI
   - Claude explains findings conversationally
   - Claude recommends and implements fixes

---

## Implementation Phases

### Phase 1 (MVP)
- ✅ Silent cost tracking (Rust core)
- ✅ Session-based grouping
- ✅ File format multipliers
- ✅ Operation type categorization
- ✅ Python API with structured JSON output
- ✅ Basic Claude integration (single skill)

**Deliverable:** Claude can answer "What did this session cost and why?"

### Phase 2
- ✅ MCP cost profiling
- ✅ Optimization recommendations
- ✅ Anomaly detection
- ✅ Trend analysis

**Deliverable:** Claude can answer "How do I save money?"

### Phase 3
- ✅ Multi-channel tracking (Bedrock, Azure, GCP)
- ✅ Team cost attribution
- ✅ Budget enforcement
- ✅ Advanced forecasting

**Deliverable:** Claude can manage team costs

---

## Why This Architecture Wins

✅ **No dashboard maintenance** — Claude is the interface  
✅ **Agent-native** — Claude can chain actions: analyze → recommend → fix  
✅ **Scalable** — One API, infinite use cases (Claude decides how to use it)  
✅ **Private** — No cloud, all data local  
✅ **Integrated** — Works inside Claude Code, not a separate tool  

