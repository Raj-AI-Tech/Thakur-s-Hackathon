"""
core/stress_index.py

Financial Stress Intelligence Engine for MonetIQ
Quantifies mental and financial pressure from money habits and cash-flow risks.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import calendar

# ============================================================================
# STRESS WEIGHTS CONFIGURATION
# ============================================================================

STRESS_WEIGHTS = {
    "budget_stress": 0.20,  # 20% - Budget breach frequency
    "expense_volatility_stress": 0.15,  # 15% - Spending fluctuations
    "survival_risk_stress": 0.25,  # 25% - End-of-month risk
    "savings_buffer_stress": 0.20,  # 20% - Emergency cushion
    "debt_pressure_stress": 0.15,  # 15% - Fixed obligations
    "goal_slippage_stress": 0.05  # 5% - Savings goal delays
}

STRESS_LEVEL_THRESHOLDS = {
    70: "Critical",
    50: "High",
    30: "Moderate",
    0: "Low"
}


# ============================================================================
# STRESS COMPONENT CALCULATIONS
# ============================================================================

def calculate_budget_stress(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate stress from budget breaches and overspending patterns.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (stress_score, details_dict)
    """
    try:
        from analytics.overspending import detect_overspending

        overspending_data = detect_overspending(state)

        if not overspending_data:
            return 0.0, {
                "breach_count": 0,
                "status": "no_budget_set"
            }

        breached_categories = overspending_data.get("breached_categories", [])
        breach_count = len(breached_categories)

        # Calculate severity of breaches
        total_breach_amount = 0
        critical_breaches = 0

        for breach in breached_categories:
            overspend_amount = breach.get("overspend_amount", 0)
            overspend_percentage = breach.get("overspend_percentage", 0)

            total_breach_amount += overspend_amount

            # Critical if >50% over budget
            if overspend_percentage > 50:
                critical_breaches += 1

        # Stress calculation
        base_stress = min(80, breach_count * 20)
        critical_stress = critical_breaches * 15

        total_stress = min(100, base_stress + critical_stress)

        return float(total_stress), {
            "breach_count": breach_count,
            "critical_breaches": critical_breaches,
            "total_breach_amount": round(total_breach_amount, 2),
            "breached_categories": [b["category"] for b in breached_categories],
            "status": "high_stress" if breach_count >= 3 else "manageable"
        }

    except ImportError:
        return 0.0, {"status": "module_unavailable"}
    except Exception as e:
        return 0.0, {"error": str(e), "status": "calculation_failed"}


def calculate_expense_volatility_stress(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate stress from unpredictable spending patterns.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (stress_score, details_dict)
    """
    try:
        from core.expense_tracker import monthly_expense_summary

        # Get last 3 months of expenses
        now = datetime.now()
        monthly_totals = []

        for months_back in range(3):
            target_date = now - timedelta(days=months_back * 30)
            summary = monthly_expense_summary(state, target_date.year, target_date.month)
            total = summary.get("total_expenses", 0)
            if total > 0:
                monthly_totals.append(total)

        if len(monthly_totals) < 2:
            return 0.0, {
                "volatility": 0.0,
                "status": "insufficient_data"
            }

        # Calculate coefficient of variation
        mean_expense = statistics.mean(monthly_totals)
        std_dev = statistics.stdev(monthly_totals) if len(monthly_totals) > 1 else 0

        if mean_expense == 0:
            return 0.0, {"volatility": 0.0, "status": "no_expenses"}

        cv = (std_dev / mean_expense) * 100

        # Stress calculation
        if cv < 10:
            stress = 0
        elif cv < 20:
            stress = 10 + (cv - 10) * 2
        elif cv < 30:
            stress = 30 + (cv - 20) * 2
        elif cv < 50:
            stress = 50 + (cv - 30) * 1.5
        else:
            stress = min(100, 80 + (cv - 50) * 0.5)

        return float(stress), {
            "volatility_cv": round(cv, 2),
            "mean_expense": round(mean_expense, 2),
            "std_deviation": round(std_dev, 2),
            "months_analyzed": len(monthly_totals),
            "status": "volatile" if cv > 30 else "stable"
        }

    except Exception as e:
        return 0.0, {"error": str(e), "status": "calculation_failed"}


def calculate_survival_risk_stress(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate stress from risk of running out of money before month-end.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (stress_score, details_dict)
    """
    try:
        from core.expense_tracker import expense_velocity

        # Get current financial state
        now = datetime.now()
        current_balance = state.get("current_balance", 0) or state.get("balance", 0) or 0
        income = state.get("monthly_income", 0) or state.get("income", 0) or 0

        # Get spending velocity
        daily_spend_rate = expense_velocity(state)

        # Days remaining in month
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_remaining = days_in_month - now.day

        # Projected expenses for rest of month
        projected_remaining_expenses = daily_spend_rate * days_remaining

        # Calculate survival buffer
        available_funds = current_balance
        survival_buffer = available_funds - projected_remaining_expenses

        # Days until funds exhaustion
        if daily_spend_rate > 0:
            days_until_exhaustion = available_funds / daily_spend_rate
        else:
            days_until_exhaustion = 999

        # Stress calculation
        if days_until_exhaustion < 5:
            stress = 100
        elif days_until_exhaustion < 10:
            stress = 80
        elif days_until_exhaustion < days_remaining:
            stress = 60
        elif survival_buffer < income * 0.1:
            stress = 40
        elif survival_buffer < income * 0.2:
            stress = 20
        else:
            stress = 0

        return float(stress), {
            "days_until_exhaustion": round(days_until_exhaustion, 1),
            "days_remaining_in_month": days_remaining,
            "survival_buffer": round(survival_buffer, 2),
            "daily_spend_rate": round(daily_spend_rate, 2),
            "current_balance": current_balance,
            "projected_remaining_expenses": round(projected_remaining_expenses, 2),
            "status": "critical" if stress >= 60 else "manageable"
        }

    except Exception as e:
        return 0.0, {"error": str(e), "status": "calculation_failed"}


def calculate_savings_buffer_stress(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate stress from inadequate emergency savings cushion.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (stress_score, details_dict)
    """
    try:
        from core.expense_tracker import monthly_expense_summary

        # Get emergency fund
        emergency_fund = state.get("emergency_fund", 0) or 0

        # Get average monthly expenses
        now = datetime.now()
        summary = monthly_expense_summary(state, now.year, now.month)
        monthly_expense = summary.get("total_expenses", 0)

        if monthly_expense <= 0:
            return 0.0, {
                "months_coverage": 0.0,
                "status": "no_expense_data"
            }

        # Calculate months of coverage
        months_coverage = emergency_fund / monthly_expense

        # Stress calculation
        if months_coverage < 0.5:
            stress = 100
        elif months_coverage < 1:
            stress = 80 + (1 - months_coverage) * 20
        elif months_coverage < 2:
            stress = 60 + (2 - months_coverage) * 20
        elif months_coverage < 3:
            stress = 40 + (3 - months_coverage) * 20
        elif months_coverage < 4:
            stress = 20 + (4 - months_coverage) * 20
        elif months_coverage < 6:
            stress = 10 + (6 - months_coverage) * 5
        else:
            stress = 0

        return float(stress), {
            "months_coverage": round(months_coverage, 2),
            "emergency_fund": emergency_fund,
            "monthly_expense": monthly_expense,
            "recommended_fund": monthly_expense * 6,
            "shortfall": max(0, monthly_expense * 3 - emergency_fund),
            "status": "critical" if months_coverage < 1 else "building"
        }

    except Exception as e:
        return 0.0, {"error": str(e), "status": "calculation_failed"}


def calculate_debt_pressure_stress(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate stress from fixed debt obligations (EMIs).

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (stress_score, details_dict)
    """
    try:
        # Get EMI and income
        total_emi = state.get("monthly_emi", 0) or state.get("emi", 0) or 0
        income = state.get("monthly_income", 0) or state.get("income", 0) or 0

        if income <= 0:
            return 0.0, {
                "emi_to_income_ratio": 0.0,
                "status": "no_income_data"
            }

        # Calculate EMI to income ratio
        emi_ratio = (total_emi / income) * 100

        # Stress calculation
        if emi_ratio < 20:
            stress = emi_ratio
        elif emi_ratio < 30:
            stress = 20 + (emi_ratio - 20) * 2
        elif emi_ratio < 40:
            stress = 40 + (emi_ratio - 30) * 2
        elif emi_ratio < 50:
            stress = 60 + (emi_ratio - 40) * 2
        else:
            stress = min(100, 80 + (emi_ratio - 50))

        return float(stress), {
            "emi_to_income_ratio": round(emi_ratio, 2),
            "total_emi": total_emi,
            "income": income,
            "disposable_income": income - total_emi,
            "status": "high_burden" if emi_ratio > 40 else "manageable"
        }

    except Exception as e:
        return 0.0, {"error": str(e), "status": "calculation_failed"}


def calculate_goal_slippage_stress(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate stress from falling behind savings goals.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (stress_score, details_dict)
    """
    try:
        from goals.savings_goals import get_savings_goals_progress

        # Get goals progress
        goals_data = get_savings_goals_progress(state)

        if not goals_data or not goals_data.get("goals"):
            return 0.0, {
                "goals_count": 0,
                "status": "no_goals_set"
            }

        goals = goals_data.get("goals", [])

        # Calculate slippage
        behind_schedule_count = 0
        total_goals = len(goals)
        max_slippage_percentage = 0

        for goal in goals:
            expected_progress = goal.get("expected_progress_percentage", 0)
            actual_progress = goal.get("current_progress_percentage", 0)

            slippage = expected_progress - actual_progress

            if slippage > 10:
                behind_schedule_count += 1
                max_slippage_percentage = max(max_slippage_percentage, slippage)

        if total_goals == 0:
            return 0.0, {"status": "no_goals"}

        # Stress calculation
        behind_ratio = behind_schedule_count / total_goals

        base_stress = behind_ratio * 60
        slippage_stress = min(40, max_slippage_percentage * 0.5)

        total_stress = min(100, base_stress + slippage_stress)

        return float(total_stress), {
            "total_goals": total_goals,
            "behind_schedule_count": behind_schedule_count,
            "max_slippage_percentage": round(max_slippage_percentage, 2),
            "status": "behind" if behind_schedule_count > 0 else "on_track"
        }

    except ImportError:
        return 0.0, {"status": "module_unavailable"}
    except Exception as e:
        return 0.0, {"error": str(e), "status": "calculation_failed"}


# ============================================================================
# AGGREGATION & LEVEL DETERMINATION
# ============================================================================

def calculate_financial_stress_index(state: Dict) -> Dict:
    """
    Calculate comprehensive financial stress index with component breakdown.

    Args:
        state: Application state dictionary

    Returns:
        Dictionary with stress index, level, components, stressors, and protective factors
    """
    # Calculate all stress components
    budget_stress, budget_details = calculate_budget_stress(state)
    volatility_stress, volatility_details = calculate_expense_volatility_stress(state)
    survival_stress, survival_details = calculate_survival_risk_stress(state)
    buffer_stress, buffer_details = calculate_savings_buffer_stress(state)
    debt_stress, debt_details = calculate_debt_pressure_stress(state)
    goal_stress, goal_details = calculate_goal_slippage_stress(state)

    # Calculate weighted stress index
    weighted_stress = (
            budget_stress * STRESS_WEIGHTS["budget_stress"] +
            volatility_stress * STRESS_WEIGHTS["expense_volatility_stress"] +
            survival_stress * STRESS_WEIGHTS["survival_risk_stress"] +
            buffer_stress * STRESS_WEIGHTS["savings_buffer_stress"] +
            debt_stress * STRESS_WEIGHTS["debt_pressure_stress"] +
            goal_stress * STRESS_WEIGHTS["goal_slippage_stress"]
    )

    final_stress = round(weighted_stress)

    # Determine stress level
    level = "Low"
    for threshold, level_name in sorted(STRESS_LEVEL_THRESHOLDS.items(), reverse=True):
        if final_stress >= threshold:
            level = level_name
            break

    # Component breakdown
    components = {
        "budget_stress": {
            "score": round(budget_stress, 2),
            "weight": STRESS_WEIGHTS["budget_stress"],
            "details": budget_details
        },
        "expense_volatility_stress": {
            "score": round(volatility_stress, 2),
            "weight": STRESS_WEIGHTS["expense_volatility_stress"],
            "details": volatility_details
        },
        "survival_risk_stress": {
            "score": round(survival_stress, 2),
            "weight": STRESS_WEIGHTS["survival_risk_stress"],
            "details": survival_details
        },
        "savings_buffer_stress": {
            "score": round(buffer_stress, 2),
            "weight": STRESS_WEIGHTS["savings_buffer_stress"],
            "details": buffer_details
        },
        "debt_pressure_stress": {
            "score": round(debt_stress, 2),
            "weight": STRESS_WEIGHTS["debt_pressure_stress"],
            "details": debt_details
        },
        "goal_slippage_stress": {
            "score": round(goal_stress, 2),
            "weight": STRESS_WEIGHTS["goal_slippage_stress"],
            "details": goal_details
        }
    }

    # Identify primary stressors and protective factors
    primary_stressors = []
    protective_factors = []

    component_scores = {
        "Budget Breaches": budget_stress,
        "Expense Volatility": volatility_stress,
        "End-of-Month Risk": survival_stress,
        "Low Emergency Fund": buffer_stress,
        "Debt Burden": debt_stress,
        "Goal Delays": goal_stress
    }

    for component_name, score in component_scores.items():
        if score >= 60:
            primary_stressors.append(component_name)
        elif score <= 20:
            protective_factors.append(component_name)

    return {
        "stress_index": final_stress,
        "level": level,
        "components": components,
        "primary_stressors": primary_stressors,
        "protective_factors": protective_factors,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# EXPLANATION LAYER
# ============================================================================

def stress_index_explanation(stress_report: Dict) -> str:
    """
    Generate empathetic, human-readable explanation of stress index.

    Args:
        stress_report: Output from calculate_financial_stress_index

    Returns:
        Plain-English explanation string
    """
    stress_index = stress_report.get("stress_index", 0)
    level = stress_report.get("level", "Unknown")
    components = stress_report.get("components", {})
    primary_stressors = stress_report.get("primary_stressors", [])
    protective_factors = stress_report.get("protective_factors", [])

    # Build empathetic explanation
    explanation_parts = []

    # Overall assessment
    explanation_parts.append(f"Your Financial Stress Index is {stress_index}/100, indicating '{level}' stress.")

    # Level-specific context
    if stress_index < 30:
        explanation_parts.append("Your financial situation is stable and manageable. Keep up the good work!")
    elif stress_index < 50:
        explanation_parts.append("You're experiencing moderate financial pressure. Some adjustments would help.")
    elif stress_index < 70:
        explanation_parts.append("Your financial stress is high. Immediate action needed to reduce pressure.")
    else:
        explanation_parts.append("You're under critical financial stress. Urgent intervention required.")

    # Primary stressors
    if primary_stressors:
        explanation_parts.append(f"\n🚨 Main Stress Sources: {', '.join(primary_stressors)}")

        # Add specific stressor details
        for stressor in primary_stressors:
            if stressor == "End-of-Month Risk":
                days = components.get("survival_risk_stress", {}).get("details", {}).get("days_until_exhaustion", 0)
                explanation_parts.append(f"   • You may run out of funds in {days:.0f} days at current spending rate")

            elif stressor == "Low Emergency Fund":
                months = components.get("savings_buffer_stress", {}).get("details", {}).get("months_coverage", 0)
                explanation_parts.append(f"   • Emergency fund only covers {months:.1f} months - very risky")

            elif stressor == "Budget Breaches":
                breaches = components.get("budget_stress", {}).get("details", {}).get("breach_count", 0)
                explanation_parts.append(f"   • You exceeded budget in {breaches} categories - losing control")

            elif stressor == "Expense Volatility":
                cv = components.get("expense_volatility_stress", {}).get("details", {}).get("volatility_cv", 0)
                explanation_parts.append(f"   • Spending fluctuates {cv:.0f}% - too unpredictable")

            elif stressor == "Debt Burden":
                ratio = components.get("debt_pressure_stress", {}).get("details", {}).get("emi_to_income_ratio", 0)
                explanation_parts.append(f"   • EMIs consume {ratio:.0f}% of income - leaving little flexibility")

            elif stressor == "Goal Delays":
                behind = components.get("goal_slippage_stress", {}).get("details", {}).get("behind_schedule_count", 0)
                explanation_parts.append(f"   • You're behind on {behind} savings goals - future plans at risk")

    # Protective factors
    if protective_factors:
        explanation_parts.append(f"\n✅ Strengths: {', '.join(protective_factors)}")

    # Actionable recommendations
    explanation_parts.append("\n💡 Stress Reduction Actions:")

    if stress_index >= 70:
        explanation_parts.append("   1. URGENT: Stop all non-essential spending immediately")
        explanation_parts.append("   2. Review and cut 3 highest discretionary expenses")
        explanation_parts.append("   3. Consider temporary income boost (freelance, sell unused items)")
        explanation_parts.append("   4. Set up daily expense alerts to track spending")
    elif stress_index >= 50:
        explanation_parts.append("   1. Build emergency fund - even ₹500/week helps")
        explanation_parts.append("   2. Stick strictly to category budgets")
        explanation_parts.append("   3. Reduce expense volatility - plan weekly spending")
        explanation_parts.append("   4. Review and renegotiate high EMIs if possible")
    elif stress_index >= 30:
        explanation_parts.append("   1. Continue building emergency fund to 6 months")
        explanation_parts.append("   2. Monitor budget breaches and adjust limits")
        explanation_parts.append("   3. Automate savings to stay on track with goals")
    else:
        explanation_parts.append("   1. Maintain your excellent discipline")
        explanation_parts.append("   2. Consider increasing investment allocation")
        explanation_parts.append("   3. Help others learn from your financial habits")

    # Empathetic closing
    if stress_index >= 70:
        explanation_parts.append(
            "\n💙 Remember: Financial stress is temporary. Small steps today lead to big relief tomorrow.")

    return "\n".join(explanation_parts)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_stress_index_history(state: Dict, months: int = 6) -> List[Dict]:
    """
    Get historical stress index records.

    Args:
        state: Application state dictionary
        months: Number of months to retrieve

    Returns:
        List of historical stress index records
    """
    history = state.get("stress_index_history", [])
    return history[-months:] if history else []


def save_stress_index_to_history(state: Dict, stress_report: Dict) -> Dict:
    """
    Save current stress index to history.

    Args:
        state: Application state dictionary
        stress_report: Stress index report to save

    Returns:
        Updated state dictionary
    """
    if "stress_index_history" not in state:
        state["stress_index_history"] = []

    history_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "stress_index": stress_report.get("stress_index"),
        "level": stress_report.get("level"),
        "components": stress_report.get("components")
    }

    state["stress_index_history"].append(history_entry)

    # Keep only last 12 months
    state["stress_index_history"] = state["stress_index_history"][-12:]

    return state


def compare_stress_indices(current_report: Dict, previous_report: Dict) -> Dict:
    """
    Compare two stress index reports to show improvement/decline.

    Args:
        current_report: Current stress index report
        previous_report: Previous stress index report

    Returns:
        Comparison dictionary
    """
    current_stress = current_report.get("stress_index", 0)
    previous_stress = previous_report.get("stress_index", 0)

    change = current_stress - previous_stress
    change_percentage = (change / previous_stress * 100) if previous_stress > 0 else 0

    # Note: For stress, lower is better
    trend = "improved" if change < 0 else "worsened" if change > 0 else "stable"

    return {
        "current_stress": current_stress,
        "previous_stress": previous_stress,
        "change": change,
        "change_percentage": round(change_percentage, 2),
        "trend": trend,
        "message": f"Stress {trend} by {abs(change)} points ({abs(change_percentage):.1f}%)"
    }


def get_stress_alerts(stress_report: Dict) -> List[Dict]:
    """
    Generate urgent alerts based on critical stress components.

    Args:
        stress_report: Stress index report

    Returns:
        List of alert dictionaries
    """
    alerts = []
    components = stress_report.get("components", {})

    # Survival risk alert
    survival_score = components.get("survival_risk_stress", {}).get("score", 0)
    if survival_score >= 80:
        days = components.get("survival_risk_stress", {}).get("details", {}).get("days_until_exhaustion", 0)
        alerts.append({
            "severity": "critical",
            "type": "survival_risk",
            "message": f"URGENT: Funds may run out in {days:.0f} days",
            "action": "Reduce spending immediately"
        })

    # Buffer alert
    buffer_score = components.get("savings_buffer_stress", {}).get("score", 0)
    if buffer_score >= 80:
        months = components.get("savings_buffer_stress", {}).get("details", {}).get("months_coverage", 0)
        alerts.append({
            "severity": "high",
            "type": "low_buffer",
            "message": f"Emergency fund only covers {months:.1f} months",
            "action": "Build emergency savings urgently"
        })

    # Budget breach alert
    budget_score = components.get("budget_stress", {}).get("score", 0)
    if budget_score >= 60:
        breaches = components.get("budget_stress", {}).get("details", {}).get("breach_count", 0)
        alerts.append({
            "severity": "medium",
            "type": "budget_breach",
            "message": f"Exceeded budget in {breaches} categories",
            "action": "Review and adjust spending patterns"
        })

    return alerts


def get_stress_trend_analysis(state: Dict) -> Dict:
    """
    Analyze stress index trends over time.

    Args:
        state: Application state dictionary

    Returns:
        Trend analysis dictionary
    """
    history = get_stress_index_history(state, months=6)

    if len(history) < 2:
        return {
            "trend": "insufficient_data",
            "direction": None,
            "average_stress": 0,
            "volatility": 0
        }

    stress_values = [entry.get("stress_index", 0) for entry in history]

    # Calculate trend direction
    first_half_avg = statistics.mean(stress_values[:len(stress_values) // 2])
    second_half_avg = statistics.mean(stress_values[len(stress_values) // 2:])

    if second_half_avg < first_half_avg - 5:
        direction = "improving"
    elif second_half_avg > first_half_avg + 5:
        direction = "worsening"
    else:
        direction = "stable"

    return {
        "trend": direction,
        "average_stress": round(statistics.mean(stress_values), 2),
        "volatility": round(statistics.stdev(stress_values), 2) if len(stress_values) > 1 else 0,
        "min_stress": min(stress_values),
        "max_stress": max(stress_values),
        "data_points": len(history)
    }


def get_stress_recommendations(stress_report: Dict) -> List[Dict]:
    """
    Generate personalized recommendations based on stress components.

    Args:
        stress_report: Stress index report

    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    components = stress_report.get("components", {})

    # Budget stress recommendations
    budget_score = components.get("budget_stress", {}).get("score", 0)
    if budget_score >= 40:
        recommendations.append({
            "category": "Budget Management",
            "priority": "high" if budget_score >= 60 else "medium",
            "action": "Review and adjust category budgets",
            "expected_impact": "Reduce stress by 10-15 points",
            "difficulty": "medium"
        })

    # Volatility recommendations
    volatility_score = components.get("expense_volatility_stress", {}).get("score", 0)
    if volatility_score >= 40:
        recommendations.append({
            "category": "Spending Stability",
            "priority": "medium",
            "action": "Create weekly spending plans to reduce fluctuations",
            "expected_impact": "Reduce stress by 8-12 points",
            "difficulty": "low"
        })

    # Survival risk recommendations
    survival_score = components.get("survival_risk_stress", {}).get("score", 0)
    if survival_score >= 60:
        recommendations.append({
            "category": "Cash Flow",
            "priority": "critical",
            "action": "Immediately cut non-essential spending to avoid fund depletion",
            "expected_impact": "Reduce stress by 20-25 points",
            "difficulty": "high"
        })

    # Buffer recommendations
    buffer_score = components.get("savings_buffer_stress", {}).get("score", 0)
    if buffer_score >= 60:
        recommendations.append({
            "category": "Emergency Fund",
            "priority": "high",
            "action": "Start emergency fund with automatic ₹500-1000 weekly transfers",
            "expected_impact": "Reduce stress by 15-20 points over 3 months",
            "difficulty": "medium"
        })

    # Debt recommendations
    debt_score = components.get("debt_pressure_stress", {}).get("score", 0)
    if debt_score >= 50:
        recommendations.append({
            "category": "Debt Management",
            "priority": "high",
            "action": "Explore debt consolidation or refinancing options",
            "expected_impact": "Reduce stress by 10-15 points",
            "difficulty": "high"
        })

    # Goal recommendations
    goal_score = components.get("goal_slippage_stress", {}).get("score", 0)
    if goal_score >= 40:
        recommendations.append({
            "category": "Savings Goals",
            "priority": "low",
            "action": "Reassess goal timelines and adjust monthly contributions",
            "expected_impact": "Reduce stress by 5-8 points",
            "difficulty": "low"
        })

    return sorted(recommendations, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]])


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def get_full_stress_analysis(state: Dict) -> Dict:
    """
    Get complete stress analysis including index, explanation, alerts, and recommendations.

    Args:
        state: Application state dictionary

    Returns:
        Comprehensive stress analysis dictionary
    """
    stress_report = calculate_financial_stress_index(state)
    explanation = stress_index_explanation(stress_report)
    alerts = get_stress_alerts(stress_report)
    recommendations = get_stress_recommendations(stress_report)
    trend = get_stress_trend_analysis(state)

    # Save to history
    state = save_stress_index_to_history(state, stress_report)

    return {
        "stress_report": stress_report,
        "explanation": explanation,
        "alerts": alerts,
        "recommendations": recommendations,
        "trend_analysis": trend,
        "generated_at": datetime.now().isoformat()
    }


def stress_color_code(stress_index: int) -> str:
    """
    Get color code for stress level visualization.

    Args:
        stress_index: Stress index value (0-100)

    Returns:
        Color code string
    """
    if stress_index >= 70:
        return "#E53E3E"  # Red - Critical
    elif stress_index >= 50:
        return "#DD6B20"  # Orange - High
    elif stress_index >= 30:
        return "#D69E2E"  # Yellow - Moderate
    else:
        return "#38A169"  # Green - Low


def is_stress_improving(state: Dict) -> Optional[bool]:
    """
    Check if stress is improving over time.

    Args:
        state: Application state dictionary

    Returns:
        True if improving, False if worsening, None if insufficient data
    """
    history = get_stress_index_history(state, months=3)

    if len(history) < 2:
        return None

    recent_stress = history[-1].get("stress_index", 0)
    old_stress = history[0].get("stress_index", 0)

    return recent_stress < old_stress