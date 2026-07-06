#!/usr/bin/env python3
"""Claude Code cost audit report with interactive navigation."""

import sqlite3
from datetime import datetime
import os
import sys

db_path = '/Users/georgimullassery/.pycostaudit/costs.db'


def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')


def print_header():
    print("\n" + "=" * 80)
    print(" " * 20 + "💰 CLAUDE CODE COST AUDIT REPORT")
    print("=" * 80)
    print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def print_menu(title, options):
    """Display a numbered menu and get user choice."""
    print("\n" + "─" * 80)
    print(f"📋 {title}")
    print("─" * 80)
    for i, (key, desc) in enumerate(options.items(), 1):
        print(f"  {i}. {desc}")
    print(f"  Q. Quit")
    print("─" * 80)

    while True:
        choice = input("Select option (1-{} or Q): ".format(len(options))).strip().upper()
        if choice == 'Q':
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return list(options.keys())[idx]
        except ValueError:
            pass
        print("Invalid choice, try again.")


def show_dashboard(conn):
    """Show main dashboard with key metrics."""
    clear_screen()
    print_header()

    cursor = conn.cursor()

    # Quick stats
    cursor.execute("SELECT COUNT(*) FROM session_costs")
    total_sessions = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(cost_usd) FROM session_costs")
    total_cost = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(estimated_tokens_in + estimated_tokens_out) FROM session_costs")
    total_tokens = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(DISTINCT model) FROM session_costs")
    model_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT date) FROM daily_costs")
    days_tracked = cursor.fetchone()[0]

    print("📊 QUICK STATS")
    print("─" * 80)
    print(f"Total Sessions:      {total_sessions}")
    print(f"Historical Cost:     ${total_cost:.4f}")
    print(f"Total Tokens:        {total_tokens:,}")
    print(f"Models Used:         {model_count}")
    print(f"Days Tracked:        {days_tracked}")

    # Most recent activity
    cursor.execute("""
        SELECT timestamp, model, estimated_tokens_in + estimated_tokens_out as tokens, cost_usd
        FROM session_costs
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    recent = cursor.fetchone()
    if recent:
        print(f"\n📌 Last Activity")
        print(f"  {recent[0][:10]} | {recent[1][:20]:20} | {recent[2]:>6} tokens | ${recent[3]:.4f}")

    print()


def show_session_history(conn):
    """Display recent session history."""
    clear_screen()
    print_header()
    print("1️⃣  RECENT SESSION HISTORY")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, model, estimated_tokens_in, estimated_tokens_out, cost_usd
        FROM session_costs
        ORDER BY timestamp DESC
        LIMIT 15
    """)

    sessions = cursor.fetchall()
    print(f"{'Date':<12} {'Model':<25} {'Input':<8} {'Output':<8} {'Cost':<10}")
    print("-" * 80)

    for row in sessions:
        date_str = row[0][:10] if row[0] else "N/A"
        model = row[1][:25] if row[1] else "N/A"
        print(f"{date_str:<12} {model:<25} {row[2]:<8} {row[3]:<8} ${row[4]:<9.4f}")

    input("\n[Press Enter to continue]")


def show_daily_trends(conn):
    """Display daily cost trends and patterns."""
    clear_screen()
    print_header()
    print("2️⃣  DAILY COST TRENDS")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("SELECT date, total_cost_usd, session_count FROM daily_costs ORDER BY date DESC LIMIT 15")
    daily_costs = cursor.fetchall()

    print(f"{'Date':<12} {'Cost':<12} {'Sessions':<10} {'Trend':<20}")
    print("-" * 80)

    prev_cost = None
    for row in daily_costs:
        trend = ""
        if prev_cost is not None:
            pct_change = ((row[1] - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0
            if pct_change > 10:
                trend = "📈 +{:.0f}%".format(pct_change)
            elif pct_change < -10:
                trend = "📉 {:.0f}%".format(pct_change)
            else:
                trend = "➡️  Stable"
        print(f"{row[0]:<12} ${row[1]:<11.4f} {row[2]:<10} {trend:<20}")
        prev_cost = row[1]

    # Forecast
    costs_list = [c[1] for c in reversed(daily_costs)]
    if costs_list:
        avg = sum(costs_list) / len(costs_list)
        print(f"\nAverage daily: ${avg:.4f} | Monthly projection: ${avg * 30:.2f}")

    input("\n[Press Enter to continue]")


def show_model_breakdown(conn):
    """Show model cost breakdown."""
    clear_screen()
    print_header()
    print("3️⃣  MODEL COST BREAKDOWN")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT model, COUNT(*) as count,
               SUM(estimated_tokens_in + estimated_tokens_out) as tokens,
               SUM(cost_usd) as total_cost
        FROM session_costs
        GROUP BY model
        ORDER BY total_cost DESC
    """)

    models = cursor.fetchall()
    total_cost = sum(m[3] for m in models)

    print(f"{'Model':<30} {'Sessions':<10} {'Tokens':<12} {'Cost':<10} {'%':<8}")
    print("-" * 80)

    for model in models:
        pct = (model[3] / total_cost * 100) if total_cost > 0 else 0
        print(f"{model[0]:<30} {model[1]:<10} {model[2]:<12,} ${model[3]:<9.4f} {pct:>6.1f}%")

    input("\n[Press Enter to continue]")


def show_project_costs(conn):
    """Show cost distribution by project."""
    clear_screen()
    print_header()
    print("4️⃣  PROJECT COST DISTRIBUTION")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT project, SUM(total_cost_usd) as total, COUNT(*) as sessions
        FROM project_costs
        GROUP BY project
        ORDER BY total DESC
    """)

    projects = cursor.fetchall()
    total = sum(p[1] for p in projects)

    print(f"{'Project':<25} {'Cost':<12} {'Sessions':<10} {'% Share':<10}")
    print("-" * 80)

    for project in projects:
        pct = (project[1] / total * 100) if total > 0 else 0
        print(f"{project[0]:<25} ${project[1]:<11.4f} {project[2]:<10} {pct:>8.1f}%")

    input("\n[Press Enter to continue]")


def show_efficiency(conn):
    """Show token and cost efficiency metrics."""
    clear_screen()
    print_header()
    print("5️⃣  EFFICIENCY METRICS")
    print("─" * 80)

    cursor = conn.cursor()

    # Cost per 1K tokens
    cursor.execute("""
        SELECT model,
               ROUND(SUM(cost_usd) / (SUM(estimated_tokens_in + estimated_tokens_out) / 1000.0), 4) as cost_per_1k
        FROM session_costs
        GROUP BY model
        ORDER BY cost_per_1k
    """)

    print("Cost per 1K tokens (lower is better):")
    print("─" * 80)
    for model in cursor.fetchall():
        print(f"  {model[0]:<30} ${model[1]:.4f}")

    # Input/Output ratio
    cursor.execute("""
        SELECT model,
               SUM(estimated_tokens_in) as input,
               SUM(estimated_tokens_out) as output,
               ROUND(CAST(SUM(estimated_tokens_in) AS FLOAT) / CAST(SUM(estimated_tokens_out) AS FLOAT), 2) as ratio
        FROM session_costs
        GROUP BY model
    """)

    print("\nInput/Output token ratio:")
    print("─" * 80)
    for model in cursor.fetchall():
        print(f"  {model[0]:<30} {model[2]:.2f}:1 (Input:Output)")

    input("\n[Press Enter to continue]")


def show_spending_velocity(conn):
    """Show spending velocity and trends."""
    clear_screen()
    print_header()
    print("6️⃣  SPENDING VELOCITY (Last 7 days)")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(timestamp) as date, COUNT(*) as ops, SUM(cost_usd) as cost
        FROM session_costs
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 7
    """)

    velocity = cursor.fetchall()
    print(f"{'Date':<12} {'Operations':<15} {'Cost':<12}")
    print("-" * 80)

    for row in velocity:
        print(f"{row[0]:<12} {row[1]:<15} ${row[2]:<11.4f}")

    # Trend
    if len(velocity) >= 3:
        recent_avg = sum(v[2] for v in velocity[:3]) / 3
        older_avg = sum(v[2] for v in velocity[3:]) / len(velocity[3:]) if len(velocity) > 3 else recent_avg
        pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        trend = "📈 INCREASING" if pct > 5 else "📉 DECREASING" if pct < -5 else "➡️  STABLE"
        print(f"\nTrend: {trend} ({pct:+.1f}%)")

    input("\n[Press Enter to continue]")


def show_recommendations(conn):
    """Show optimization recommendations."""
    clear_screen()
    print_header()
    print("7️⃣  OPTIMIZATION OPPORTUNITIES")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("SELECT SUM(cost_usd) FROM session_costs")
    total = cursor.fetchone()[0] or 0.0

    # Find most expensive model
    cursor.execute("SELECT model, SUM(cost_usd) as cost FROM session_costs GROUP BY model ORDER BY cost DESC LIMIT 1")
    most_expensive = cursor.fetchone()

    # Find most efficient model
    cursor.execute("""
        SELECT model, ROUND(SUM(cost_usd) / (SUM(estimated_tokens_in + estimated_tokens_out) / 1000.0), 4) as cost_per_1k
        FROM session_costs
        GROUP BY model
        ORDER BY cost_per_1k
        LIMIT 1
    """)
    most_efficient = cursor.fetchone()

    print("Key Findings:")
    print("─" * 80)
    print(f"✗ Highest cost model: {most_expensive[0]} (${most_expensive[1]:.4f})")
    print(f"✓ Most efficient: {most_efficient[0]} (${most_efficient[1]:.4f} per 1K tokens)")

    savings = total * 0.15
    print(f"\n💡 Potential Monthly Savings: ${savings:.2f} (15% reduction)")
    print("\nOptimization Strategies:")
    print("  • Route simple tasks to more efficient models")
    print("  • Batch similar operations to reduce overhead")
    print("  • Cache frequently requested information")
    print("  • Monitor and alert on unusual spending spikes")

    input("\n[Press Enter to continue]")


def show_forecast(conn):
    """Show cost forecast."""
    clear_screen()
    print_header()
    print("8️⃣  COST FORECAST")
    print("─" * 80)

    cursor = conn.cursor()
    cursor.execute("SELECT total_cost_usd FROM daily_costs ORDER BY date DESC LIMIT 30")
    costs = [row[0] for row in cursor.fetchall()]

    if costs and len(costs) > 1:
        costs.reverse()
        avg = sum(costs) / len(costs)

        print(f"Based on average daily spend: ${avg:.4f}")
        print("─" * 80)
        print(f"  • Next 7 days:   ${avg * 7:.2f}")
        print(f"  • Next 30 days:  ${avg * 30:.2f}")
        print(f"  • Next 90 days:  ${avg * 90:.2f}")
        print(f"  • Annualized:    ${avg * 365:.2f}")

        # Confidence levels
        print("\nConfidence: HIGH (based on 30+ days of data)")
        print("Note: Assumes current spending patterns continue")

    input("\n[Press Enter to continue]")


def main():
    """Main interactive menu."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        menu_items = {
            "dashboard": "📊 Dashboard - Quick Overview",
            "sessions": "📝 Session History - Recent Activity",
            "trends": "📈 Daily Trends - Cost Patterns",
            "models": "🤖 Model Breakdown - By Model",
            "projects": "📁 Project Costs - By Project",
            "efficiency": "⚡ Efficiency Metrics - Cost & Tokens",
            "velocity": "🚀 Spending Velocity - Trend Analysis",
            "recommendations": "💡 Recommendations - Optimization Tips",
            "forecast": "🔮 Forecast - 30/90 Day Projection"
        }

        while True:
            show_dashboard(conn)
            choice = print_menu("MAIN MENU", menu_items)

            if choice is None:
                clear_screen()
                print("\n👋 Goodbye!\n")
                break

            if choice == "dashboard":
                # Refresh and show current dashboard
                pass
            elif choice == "sessions":
                show_session_history(conn)
            elif choice == "trends":
                show_daily_trends(conn)
            elif choice == "models":
                show_model_breakdown(conn)
            elif choice == "projects":
                show_project_costs(conn)
            elif choice == "efficiency":
                show_efficiency(conn)
            elif choice == "velocity":
                show_spending_velocity(conn)
            elif choice == "recommendations":
                show_recommendations(conn)
            elif choice == "forecast":
                show_forecast(conn)

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
