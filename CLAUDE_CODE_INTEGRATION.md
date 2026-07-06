# Claude Code Integration Guide

PyCostAudit is built to integrate seamlessly into Claude Code's workflow. After every analysis completes, it shows you available next steps.

## How It Works

### The Interactive Loop

Every time you use PyCostAudit in Claude Code:

1. **You complete an analysis** (e.g., "Show me anomalies")
2. **Results appear** with the findings
3. **Options appear automatically** showing what you can do next
4. **You choose a next action** by typing a number (1-34) or asking a question
5. **Go to step 1**

### Example Flow

```
User: "4" (Run anomaly detection)
  ↓
Result: Anomalies found in your spending...
  ↓
Automatic prompt appears:
  "🎯 WHAT WOULD YOU LIKE TO EXPLORE NEXT?
  
   3. Which projects cost the most?
      → Identify focus areas
   
   6. Give me personalized recommendations
      → Get ROI targets
   
   20. Set a monthly budget
      → Lock spending limits"
  ↓
User: "6" (Get recommendations)
  ↓
[Repeat]
```

## Integration Points

### In Claude Code Terminal

```python
python3 << 'EOF'
from pycostaudit.cli_interactive import InteractiveCLI

cli = InteractiveCLI()
print(cli.welcome())  # Shows options immediately

# Process user input with contextual options
result = cli.process_user_input("4")  # Get anomalies
print(result)  # Includes next-step options automatically
EOF
```

### After Each Analysis

Every analysis wraps its result with relevant next actions:

```python
from pycostaudit.interactive_guide import (
    InteractiveGuide,
    AnalysisType,
    create_interactive_output
)

# Your analysis result
analysis = "Anomalies detected: 3 spikes found..."

# Automatically includes next-step options
output = create_interactive_output(
    analysis,
    AnalysisType.ANOMALIES,
    show_steps=True
)

print(output)  # Shows result + options
```

### Welcome Experience

First time users see:

```
🎯 PYCOSTAUDIT - WHAT WOULD YOU LIKE TO DO?

📊 GET STARTED (Recommended first 3):
  4. Detect anomalies → Find cost spikes
  3. Which projects cost most? → Identify focus areas
  6. Give recommendations → Get ROI targets

📈 QUICK ACCESS:
  20. Set a monthly budget
  10. 90-day forecast
  24. Slack alerts

📚 EXPLORE:
  "all" = See all 34 analyses
  "path" = Recommended learning sequence
```

### Error Handling with Options

Even when input is invalid, options appear:

```
⚠️  Didn't understand 'foobar'

💡 TRY ONE OF THESE:
  4 = Detect anomalies
  3 = Project breakdown
  6 = Save recommendations
  
  "all" = Full menu
  "path" = Learning sequence
```

## The 34 Analysis Options

After any analysis, you'll see contextual options like:

- **After anomaly detection** → See which projects are expensive
- **After project breakdown** → Get optimization recommendations  
- **After recommendations** → Set budget tracking
- **After budget tracking** → View 90-day forecast

## Special Commands

Available at any time:

- `all` → See all 34 options with descriptions
- `path` → Show the recommended first-time learning path
- `help` → Get help with available features
- `quit` or `exit` → Leave PyCostAudit
- `1-34` → Run specific analysis
- Any question → Ask anything about your costs (Claude handles it)

## Key Principles

### Always Show Options
✅ Welcome screen shows options  
✅ Analysis results show options  
✅ Errors show options  
✅ Every interaction ends with "what's next?"

### Context-Aware Navigation
✅ After anomalies → show investigation options  
✅ After projects → show optimization options  
✅ After recommendations → show implementation options

### Discoverable Features
✅ No hidden menus  
✅ No need to read documentation  
✅ Options always visible  
✅ Learning path for new users

## Usage in Claude Code

### Example Session

```bash
# 1. User starts PyCostAudit
$ python3 -m pycostaudit.cli_interactive

🎯 PYCOSTAUDIT - WHAT WOULD YOU LIKE TO DO?
[options shown]

✨ What next? → 4

# 2. Anomalies run and show next options
📊 ANOMALIES DETECTED: 3 patterns

[analysis results...]

🎯 WHAT WOULD YOU LIKE TO EXPLORE NEXT?
   3. Which projects cost most?
   6. Recommendations
   20. Set budget

✨ What next? → 6

# 3. Recommendations run and show next options
📊 PERSONALIZED RECOMMENDATIONS

[analysis results...]

🎯 WHAT WOULD YOU LIKE TO EXPLORE NEXT?
   24. Slack alerts
   20. Set budget
   23. Quarterly plan

✨ What next? → 20

[Loop continues...]
```

### In Python Scripts

```python
from pycostaudit.cli_interactive import InteractiveCLI

cli = InteractiveCLI()

# Start with welcome
print(cli.welcome())

# User gives input (from Claude Code conversation)
user_choice = "4"
result = cli.process_user_input(user_choice)
print(result)

# Result includes both data and next options
# User picks next action
next_choice = "6"
next_result = cli.process_user_input(next_choice)
print(next_result)
```

## Philosophy

**PyCostAudit is not a tool you "launch and find what to do"**

It's a **guided experience** where:
1. You never wonder what's available
2. Every result suggests the next logical action
3. Discovering features happens naturally
4. Learning happens by doing, not reading docs

## Related Docs

- `CAPABILITIES.md` — Full reference of all 34 analyses
- `USAGE.md` — Complete API documentation
- `README.md` — Product overview

---

**PyCostAudit v0.7.0** — Interactive by design, integrated with Claude Code
