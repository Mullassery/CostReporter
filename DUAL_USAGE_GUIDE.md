# PyCostAudit: Dual Usage Patterns

PyCostAudit can be used in **two distinct ways**:

## 🎯 Pattern 1: Claude Code CLI (Integrated Mode)

Use PyCostAudit directly within Claude Code to monitor your coding costs in real-time.

### Setup
```bash
pip install pycostaudit
```

### CLI Commands

#### 1. **Run Cost Audit**
```bash
pycostaudit audit
# Output: Real-time cost breakdown of current Claude Code session

pycostaudit audit --period 30d
pycostaudit audit --period 7d --format json
pycostaudit audit --output report.json
```

#### 2. **Generate Forecast**
```bash
pycostaudit forecast
# Projects next 30 days of costs

pycostaudit forecast --days 60 --confidence 0.95
pycostaudit forecast --algorithm ensemble --output forecast.json
```

#### 3. **Compliance Report**
```bash
pycostaudit compliance --framework SOC2
pycostaudit compliance --framework HIPAA --export audit_trail.csv
pycostaudit compliance --verify
```

#### 4. **Budget Management**
```bash
pycostaudit budget set --amount 100 --period monthly
pycostaudit budget status
pycostaudit budget alert --threshold 75
```

#### 5. **Cost Breakdown**
```bash
pycostaudit breakdown
# By project: pycostaudit breakdown --group-by project
# By model: pycostaudit breakdown --group-by model
# By operation: pycostaudit breakdown --group-by operation
```

#### 6. **Alerts**
```bash
pycostaudit alerts
pycostaudit alerts acknowledge <alert_id>
pycostaudit alerts send-to-slack --webhook-url https://...
```

### Example: Integration with Claude Code Workflow

```bash
# At start of coding session
pycostaudit audit --format json | jq '.summary'

# During development
pycostaudit forecast --days 7  # Weekly forecast
pycostaudit breakdown --group-by project

# Before committing
pycostaudit compliance --verify

# Weekly report
pycostaudit audit --period 7d --output weekly_report.json
pycostaudit compliance --framework SOC2 --export compliance.pdf
```

---

## 📚 Pattern 2: Python Library (Programmatic Mode)

Use PyCostAudit as a Python library in your own applications.

### Installation
```bash
pip install pycostaudit
```

### 1. **Forecasting**

```python
from pycostaudit.ml_forecasting_service import TimeSeriesForecaster, ForecastAlgorithm

# Initialize forecaster
forecaster = TimeSeriesForecaster(history_days=90)

# Prepare historical data (date_string, cost_float)
daily_costs = [
    ("2024-06-01", 15.50),
    ("2024-06-02", 16.20),
    ("2024-06-03", 14.80),
    # ... more data
]

# Generate forecast
forecast = forecaster.forecast_costs(
    daily_costs=daily_costs,
    forecast_days=30,
    algorithm=ForecastAlgorithm.ENSEMBLE,  # or ARIMA, EXPONENTIAL_SMOOTHING, LINEAR_REGRESSION
    confidence_level=0.95
)

# Access results
print(f"Total Projected: ${forecast_summary['total_projected']:.2f}")
print(f"Trend: {forecast_summary['trend']}")
print(f"Accuracy: {(1 - forecast.mape) * 100:.1f}%")

# Get individual forecast points
for point in forecast.forecast_points:
    print(f"{point.date}: ${point.predicted_cost:.2f} "
          f"(${point.lower_bound:.2f} - ${point.upper_bound:.2f})")

# Detect anomalies
for date, score in forecast.anomalies:
    print(f"Anomaly on {date}: Z-score {score:.2f}")
```

### 2. **Cost Calculation**

```python
from pycostaudit.cost_calculator import CostCalculator

calculator = CostCalculator()

# Calculate from history
breakdown = calculator.get_cost_breakdown()
print(breakdown)
# {
#   'by_project': {'project1': 10.50, ...},
#   'by_model': {'claude-3-5-sonnet': 45.20, ...},
#   'by_operation': {'file_read': 5.10, ...},
#   'total': 50.30
# }

# Track individual operation
cost = calculator.track_operation(
    operation_type='api_call',
    tokens_input=1500,
    tokens_output=2000,
    model='claude-3-5-sonnet'
)
print(f"Operation cost: ${cost:.4f}")
```

### 3. **Compliance Management**

```python
from pycostaudit.compliance_reporting import ComplianceManager, ComplianceFramework

manager = ComplianceManager()

# Record audit events
manager.record_audit_event(
    event_type='COST_RECORDED',
    user_id='user123',
    resource_type='cost',
    action='create',
    resource_id='cost-xyz',
    new_values={'amount': 10.50, 'model': 'claude-3-5-sonnet'}
)

# Generate compliance report
report = manager.generate_compliance_report(
    framework=ComplianceFramework.SOC2,
    user_id='user123',
    organization='Acme Corp',
    period_days=30
)

# Verify compliance
compliance = manager.get_compliance_summary(report, ComplianceFramework.SOC2)
print(f"Compliance Score: {compliance['compliance_score']:.1f}%")
print(f"Status: {compliance['status']}")

# Export audit trail
audit_csv = manager.export_audit_trail_csv(report)
audit_json = manager.generate_audit_trail_json(report)
```

### 4. **Database Access**

```python
from pycostaudit.database import DatabaseManager

db = DatabaseManager("sqlite:///./pycostaudit.db")

# Get time series data
daily_costs = db.get_time_series(
    user_id="user123",
    granularity="daily",
    limit=90
)

# Get by provider
provider_costs = db.get_costs_by_provider("user123")

# Get alerts
alerts = db.get_alerts("user123", limit=50)
```

### 5. **Budget Tracking**

```python
from pycostaudit.database import DatabaseManager

db = DatabaseManager()

# Set budget
db.set_budget(
    user_id="user123",
    amount=500.00,
    period="monthly",
    alert_threshold_percent=0.75
)

# Get budget status
budget_status = db.get_budget_status("user123")
print(f"Budget: ${budget_status['budget_amount']:.2f}")
print(f"Spent: ${budget_status['spent']:.2f}")
print(f"Remaining: ${budget_status['remaining']:.2f}")
print(f"Used: {budget_status['percent_used']:.1f}%")
```

### 6. **Anomaly Detection**

```python
from pycostaudit.anomaly_detection import AnomalyDetector
from pycostaudit.database import DatabaseManager

db = DatabaseManager()
detector = AnomalyDetector(db)

# Detect anomalies
anomalies = detector.detect_anomalies(
    user_id="user123",
    sensitivity=1.0  # 0.5 = very sensitive, 2.0 = less sensitive
)

for anomaly in anomalies:
    print(f"Date: {anomaly.date}")
    print(f"Type: {anomaly.anomaly_type}")
    print(f"Score: {anomaly.anomaly_score:.2f}")
```

### 7. **Alerting**

```python
from pycostaudit.alerting import AlertPolicy, AlertSeverity, AlertType
from pycostaudit.alerts_service import AlertsService
from pycostaudit.database import DatabaseManager

db = DatabaseManager()
alerts_service = AlertsService(db)

# Create alert policy
policy = AlertPolicy(
    name="Budget Exceeded",
    alert_type=AlertType.BUDGET_EXCEEDED,
    severity=AlertSeverity.CRITICAL,
    budget_threshold_percent=0.90,
    slack_enabled=True,
    slack_channel="#cost-alerts"
)

# Evaluate budget against policy
alerts_triggered = alerts_service.evaluate_budget(
    user_id="user123",
    current_cost=450.00,
    period="monthly"
)

for alert in alerts_triggered:
    print(f"Alert: {alert.message}")
```

---

## 🔄 Hybrid Usage: CLI + Library

Combine both patterns for maximum flexibility:

```bash
#!/bin/bash
# batch_reporting.sh - Combine CLI and library approaches

# Use CLI to generate initial audit
pycostaudit audit --period 30d --output audit.json

# Use Python script to process and enhance
python << 'EOF'
import json
from pycostaudit.ml_forecasting_service import TimeSeriesForecaster

# Load CLI output
with open('audit.json') as f:
    audit_data = json.load(f)

# Enhance with ML forecasting
forecaster = TimeSeriesForecaster()
daily_costs = [
    (day, cost) 
    for day, cost in audit_data['daily_breakdown'].items()
]

forecast = forecaster.forecast_costs(daily_costs, forecast_days=30)

# Save combined report
report = {
    'audit': audit_data,
    'forecast': {
        'total_projected': forecast_summary['total_projected'],
        'trend': forecast_summary['trend']
    }
}

with open('combined_report.json', 'w') as f:
    json.dump(report, f, indent=2)
    
print("✅ Combined report generated: combined_report.json")
EOF

# Use CLI to export compliance
pycostaudit compliance --framework SOC2 --export compliance.csv
```

---

## 📊 Pattern Comparison

| Feature | CLI Mode | Library Mode |
|---------|----------|--------------|
| **Ease of Use** | Very easy | Requires Python knowledge |
| **Integration** | IDE / Shell | Custom Python apps |
| **Flexibility** | Limited to CLI commands | Full programmatic control |
| **Scripting** | Great with bash/sh | Great with Python |
| **Real-time** | Not ideal | Excellent |
| **Batch Processing** | Good | Excellent |
| **Learning Curve** | Minimal | Moderate |
| **Production Use** | Good | Excellent |

---

## 🎯 Use Case Examples

### Use Case 1: Monitor Claude Code Costs Daily (CLI)
```bash
# Add to crontab
0 9 * * * /usr/local/bin/pycostaudit audit --period 1d | mail -s "Daily Cost Report" user@example.com
```

### Use Case 2: Alert on Budget Threshold (Library)
```python
from pycostaudit.alerts_service import AlertsService
from pycostaudit.database import DatabaseManager

db = DatabaseManager()
alerts = AlertsService(db)

# Check daily and send Slack alert if threshold exceeded
alerts.evaluate_budget("user123", current_cost=95.50, period="daily")
```

### Use Case 3: Weekly Compliance Report (Hybrid)
```bash
#!/bin/bash
# weekly_compliance.sh

# Generate compliance report via CLI
pycostaudit compliance --framework HIPAA --export weekly_report.csv

# Process with Python
python weekly_processor.py weekly_report.csv

# Email result
mail -s "Weekly Compliance Report" security@company.com < weekly_report_processed.txt
```

### Use Case 4: Real-time Dashboard (Library + Web Framework)
```python
from flask import Flask, jsonify
from pycostaudit.ml_forecasting_service import TimeSeriesForecaster

app = Flask(__name__)
forecaster = TimeSeriesForecaster()

@app.route('/api/forecast')
def get_forecast():
    # Fetch costs from DB
    # Generate forecast
    # Return JSON
    return jsonify(forecast_data)
```

---

## 🚀 Recommended Approach by Use Case

| Scenario | Recommended |
|----------|------------|
| Personal cost monitoring | CLI (`pycostaudit audit`) |
| Automated reporting | CLI + cron jobs |
| Team dashboard | Library + Web Framework |
| Cost optimization | Library + ML models |
| Compliance auditing | Library + compliance module |
| Integration with other tools | Library (Python API) |
| Quick cost checks | CLI |
| Production monitoring | Library + API backend |

---

## 📖 Documentation

- **CLI Documentation:** `pycostaudit --help`
- **API Documentation:** http://localhost:8000/docs (when running backend)
- **Library Documentation:** See individual module docstrings
- **Dashboard Guide:** `pycostaudit/dashboard/README.md`

---

## 💡 Tips & Tricks

### Tip 1: Combine Multiple Reports
```bash
pycostaudit audit --period 7d > week.json
pycostaudit audit --period 30d > month.json
pycostaudit compliance --framework SOC2 > compliance.json

# Process together
python combine_reports.py week.json month.json compliance.json
```

### Tip 2: Continuous Monitoring
```python
# monitoring.py
import time
from pycostaudit.cost_calculator import CostCalculator

calculator = CostCalculator()

while True:
    breakdown = calculator.get_cost_breakdown()
    if breakdown['total'] > 100:  # Alert threshold
        print("⚠️ Cost exceeded threshold!")
        # Send alert
    time.sleep(3600)  # Check hourly
```

### Tip 3: Export for Analysis
```bash
# Export to CSV for Excel/Sheets
pycostaudit breakdown --group-by project --format csv > costs_by_project.csv

# Export to JSON for data pipeline
pycostaudit audit --period 30d --format json > historical_costs.json
```

---

## 🔗 Integration Examples

### With Slack
```python
from pycostaudit.alerts_service import AlertsService

# Configure Slack webhook
alerts = AlertsService(db)
alerts.evaluate_budget(user_id, current_cost, period)
# Automatically sends to Slack if threshold exceeded
```

### With Spreadsheets
```bash
# Generate CSV for Google Sheets
pycostaudit breakdown --group-by model --format csv > models.csv

# Upload to Google Drive
gdrive upload models.csv
```

### With Automation Tools (Zapier, IFTTT)
```bash
# Export JSON for webhooks
pycostaudit audit --period daily --format json \
  | curl -X POST -H 'Content-Type: application/json' \
    -d @- https://hooks.zapier.com/...
```

---

## ✅ Summary

- **Use CLI** for quick checks, monitoring, and automated scripts
- **Use Library** for custom applications, dashboards, and integrations
- **Combine both** for maximum flexibility and power
- Both patterns access the same underlying engine and data

Start with whatever fits your workflow best - you can always switch or combine them later!
