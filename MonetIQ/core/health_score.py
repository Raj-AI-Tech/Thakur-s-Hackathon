"""
core/health_score.py

Financial Health Intelligence Engine for MonetIQ
Computes a comprehensive, explainable Financial Health Score (0-100)
reflecting user's financial stability, resilience, and discipline.
"""

from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# ============================================================================
# 🔒 GLOBAL SAFE NUMERIC NORMALIZER (FIX)
# ============================================================================

def _to_number(value, default: float = 0.0) -> float:
    """
    Safely extract a numeric value from ints, floats, or nested dicts.

    Supported dict keys (checked in order):
    - monthly
    - amount
    - total
    - value

    This function is STREAMLIT-SAFE and NEVER raises.
    """
    try:
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, dict):
            for key in ("monthly", "amount", "total", "value"):
                if key in value and isinstance(value[key], (int, float)):
                    return float(value[key])
            return default

        return float(value) if value is not None else default

    except Exception:
        return default


# ============================================================================
# SCORING WEIGHTS CONFIGURATION
# ============================================================================

COMPONENT_WEIGHTS = {
    "savings_rate": 0.25,
    "budget_discipline": 0.20,
    "expense_stability": 0.15,
    "emergency_readiness": 0.20,
    "debt_burden": 0.12,
    "tax_pressure": 0.08
}

GRADE_THRESHOLDS = {
    80: "Excellent",
    65: "Good",
    50: "Fair",
    35: "Risky",
    0: "Critical"
}


# ============================================================================
# COMPONENT SCORE CALCULATIONS
# ============================================================================

def calculate_savings_rate_score(state: Dict) -> Tuple[float, Dict]:
    try:
        from core.expense_tracker import monthly_expense_summary

        now = datetime.now()
        summary = monthly_expense_summary(state, now.year, now.month)

        income = _to_number(state.get("monthly_income") or state.get("income"))

        if income <= 0:
            return 0.0, {
                "savings_rate": 0.0,
                "monthly_savings": 0.0,
                "status": "No income data"
            }

        expenses = _to_number(summary.get("total_expenses"))
        savings = income - expenses
        savings_rate = (savings / income) * 100

        if savings_rate >= 20:
            score = 100
        elif savings_rate >= 15:
            score = 80 + (savings_rate - 15) * 4
        elif savings_rate >= 10:
            score = 60 + (savings_rate - 10) * 4
        elif savings_rate >= 5:
            score = 40 + (savings_rate - 5) * 4
        elif savings_rate >= 0:
            score = 20 + savings_rate * 4
        else:
            score = max(0, 20 + savings_rate * 2)

        return min(100.0, max(0.0, score)), {
            "savings_rate": round(savings_rate, 2),
            "monthly_savings": round(savings, 2),
            "income": income,
            "expenses": expenses,
            "status": "healthy" if savings_rate >= 10 else "needs_improvement"
        }

    except Exception as e:
        return 50.0, {"error": str(e), "status": "calculation_failed"}


def calculate_budget_discipline_score(state: Dict) -> Tuple[float, Dict]:
    try:
        from analytics.overspending import detect_overspending

        overspending_data = detect_overspending(state)

        if not overspending_data:
            return 70.0, {"breach_count": 0, "status": "no_budget_set"}

        breached = overspending_data.get("breached_categories", [])
        safe = overspending_data.get("safe_categories", [])

        total = len(breached) + len(safe)
        if total == 0:
            return 70.0, {"status": "insufficient_data"}

        breach_count = len(breached)

        if breach_count == 0:
            score = 100
        elif breach_count == 1:
            score = 85
        elif breach_count == 2:
            score = 70
        else:
            score = max(0, 70 - (breach_count - 2) * 15)

        return score, {
            "breach_count": breach_count,
            "total_categories": total,
            "breached_categories": [c.get("category") for c in breached],
            "status": "disciplined" if breach_count <= 1 else "needs_attention"
        }

    except ImportError:
        return 70.0, {"status": "module_unavailable"}
    except Exception as e:
        return 70.0, {"error": str(e), "status": "calculation_failed"}


def calculate_expense_stability_score(state: Dict) -> Tuple[float, Dict]:
    try:
        from core.expense_tracker import monthly_expense_summary

        now = datetime.now()
        totals = []

        for i in range(3):
            d = now - timedelta(days=i * 30)
            summary = monthly_expense_summary(state, d.year, d.month)
            total = _to_number(summary.get("total_expenses"))
            if total > 0:
                totals.append(total)

        if len(totals) < 2:
            return 60.0, {"status": "insufficient_data"}

        mean = statistics.mean(totals)
        std = statistics.stdev(totals)

        cv = (std / mean) * 100 if mean else 0

        if cv < 10:
            score = 100
        elif cv < 20:
            score = 80 + (20 - cv)
        elif cv < 30:
            score = 60 + (30 - cv) * 2
        elif cv < 50:
            score = 40 + (50 - cv)
        else:
            score = max(0, 40 - (cv - 50) * 0.5)

        return score, {
            "volatility_cv": round(cv, 2),
            "months_analyzed": len(totals),
            "status": "stable" if cv < 20 else "volatile"
        }

    except Exception as e:
        return 60.0, {"error": str(e), "status": "calculation_failed"}


def calculate_emergency_readiness_score(state: Dict) -> Tuple[float, Dict]:
    try:
        from core.expense_tracker import monthly_expense_summary

        fund = _to_number(state.get("emergency_fund"))
        summary = monthly_expense_summary(state, datetime.now().year, datetime.now().month)
        expense = _to_number(summary.get("total_expenses"))

        if expense <= 0:
            return 50.0, {"status": "no_expense_data"}

        months = fund / expense

        if months >= 6:
            score = 100
        elif months >= 3:
            score = 70 + (months - 3) * 10
        elif months >= 1:
            score = 40 + (months - 1) * 15
        else:
            score = months * 40

        return score, {
            "months_coverage": round(months, 2),
            "recommended_fund": expense * 6,
            "status": "excellent" if months >= 6 else "needs_building"
        }

    except Exception as e:
        return 50.0, {"error": str(e), "status": "calculation_failed"}


def calculate_debt_burden_score(state: Dict) -> Tuple[float, Dict]:
    try:
        emi = _to_number(state.get("monthly_emi") or state.get("emi"))
        income = _to_number(state.get("monthly_income") or state.get("income"))

        if income <= 0:
            return 50.0, {"status": "no_income_data"}

        ratio = (emi / income) * 100

        if ratio == 0:
            score = 100
        elif ratio < 20:
            score = 90 + (20 - ratio) * 0.5
        elif ratio < 30:
            score = 70 + (30 - ratio) * 2
        elif ratio < 40:
            score = 50 + (40 - ratio) * 2
        elif ratio < 50:
            score = 30 + (50 - ratio) * 2
        else:
            score = max(0, 30 - (ratio - 50))

        return score, {
            "emi_to_income_ratio": round(ratio, 2),
            "status": "healthy" if ratio < 30 else "high_burden"
        }

    except Exception as e:
        return 50.0, {"error": str(e), "status": "calculation_failed"}


def calculate_tax_pressure_score(state: Dict) -> Tuple[float, Dict]:
    try:
        from tax.tax_estimator import estimate_annual_tax

        tax = _to_number(estimate_annual_tax(state).get("total_tax"))
        income = _to_number(state.get("monthly_income") or state.get("income"))

        annual_income = income * 12
        if annual_income <= 0:
            return 70.0, {"status": "no_income_data"}

        ratio = (tax / annual_income) * 100

        if ratio < 10:
            score = 100
        elif ratio < 15:
            score = 85 + (15 - ratio) * 3
        elif ratio < 20:
            score = 70 + (20 - ratio) * 3
        elif ratio < 25:
            score = 55 + (25 - ratio) * 3
        elif ratio < 30:
            score = 40 + (30 - ratio) * 3
        else:
            score = max(0, 40 - (ratio - 30) * 2)

        return score, {
            "tax_to_income_ratio": round(ratio, 2),
            "status": "optimized" if ratio < 20 else "high_pressure"
        }

    except ImportError:
        return 70.0, {"status": "module_unavailable"}
    except Exception as e:
        return 70.0, {"error": str(e), "status": "calculation_failed"}


# ============================================================================
# AGGREGATION, EXPLANATION & HISTORY (UNCHANGED)
# ============================================================================

# 🔒 Everything below runs cleanly now because numeric safety is guaranteed

def calculate_financial_health_score(state: Dict) -> Dict:
    """
    Calculate comprehensive financial health score with component breakdown.

    Args:
        state: Application state dictionary

    Returns:
        Dictionary with score, grade, components, strengths, and weaknesses
    """
    state = {
        k: _to_number(v) if isinstance(v, (int, float, dict)) else v
        for k, v in state.items()
    }

    def safe_get_number(value, default=0):
        """Safely extract number from value that might be dict or number."""
        if isinstance(value, dict):
            # Try common keys that might contain the actual number
            return value.get('monthly', value.get('amount', value.get('total', default)))
        try:
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default
    # Calculate all component scores
    savings_score, savings_details = calculate_savings_rate_score(state)
    discipline_score, discipline_details = calculate_budget_discipline_score(state)
    stability_score, stability_details = calculate_expense_stability_score(state)
    emergency_score, emergency_details = calculate_emergency_readiness_score(state)
    debt_score, debt_details = calculate_debt_burden_score(state)
    tax_score, tax_details = calculate_tax_pressure_score(state)

    # Calculate weighted score
    weighted_score = (
            savings_score * COMPONENT_WEIGHTS["savings_rate"] +
            discipline_score * COMPONENT_WEIGHTS["budget_discipline"] +
            stability_score * COMPONENT_WEIGHTS["expense_stability"] +
            emergency_score * COMPONENT_WEIGHTS["emergency_readiness"] +
            debt_score * COMPONENT_WEIGHTS["debt_burden"] +
            tax_score * COMPONENT_WEIGHTS["tax_pressure"]
    )

    final_score = round(weighted_score)

    # Determine grade
    grade = "Critical"
    for threshold, grade_name in sorted(GRADE_THRESHOLDS.items(), reverse=True):
        if final_score >= threshold:
            grade = grade_name
            break

    # Component breakdown
    components = {
        "savings_rate": {
            "score": round(savings_score, 2),
            "weight": COMPONENT_WEIGHTS["savings_rate"],
            "details": savings_details
        },
        "budget_discipline": {
            "score": round(discipline_score, 2),
            "weight": COMPONENT_WEIGHTS["budget_discipline"],
            "details": discipline_details
        },
        "expense_stability": {
            "score": round(stability_score, 2),
            "weight": COMPONENT_WEIGHTS["expense_stability"],
            "details": stability_details
        },
        "emergency_readiness": {
            "score": round(emergency_score, 2),
            "weight": COMPONENT_WEIGHTS["emergency_readiness"],
            "details": emergency_details
        },
        "debt_burden": {
            "score": round(debt_score, 2),
            "weight": COMPONENT_WEIGHTS["debt_burden"],
            "details": debt_details
        },
        "tax_pressure": {
            "score": round(tax_score, 2),
            "weight": COMPONENT_WEIGHTS["tax_pressure"],
            "details": tax_details
        }
    }

    # Identify strengths and weaknesses
    strengths = []
    weaknesses = []

    component_scores = {
        "Savings Rate": savings_score,
        "Budget Discipline": discipline_score,
        "Expense Stability": stability_score,
        "Emergency Readiness": emergency_score,
        "Debt Management": debt_score,
        "Tax Planning": tax_score
    }

    for component_name, score in component_scores.items():
        if score >= 80:
            strengths.append(component_name)
        elif score < 50:
            weaknesses.append(component_name)

    return {
        "health_score": final_score,
        "grade": grade,
        "components": components,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# EXPLANATION LAYER
# ============================================================================

def health_score_explanation(health_report: Dict) -> str:
    """
    Generate human-readable explanation of health score.

    Args:
        health_report: Output from calculate_financial_health_score

    Returns:
        Plain-English explanation string
    """
    score = health_report.get("health_score", 0)
    grade = health_report.get("grade", "Unknown")
    components = health_report.get("components", {})
    strengths = health_report.get("strengths", [])
    weaknesses = health_report.get("weaknesses", [])

    # Build explanation
    explanation_parts = []

    # Overall assessment
    explanation_parts.append(f"Your Financial Health Score is {score}/100, rated as '{grade}'.")

    # Grade-specific context
    if score >= 80:
        explanation_parts.append("You demonstrate excellent financial discipline and planning.")
    elif score >= 65:
        explanation_parts.append("Your financial health is good, with room for optimization.")
    elif score >= 50:
        explanation_parts.append("Your finances are fair but need attention in key areas.")
    elif score >= 35:
        explanation_parts.append("Your financial situation requires immediate improvements to avoid risks.")
    else:
        explanation_parts.append("Your financial health is critical. Urgent action needed.")

    # Strengths
    if strengths:
        explanation_parts.append(f"\n✅ Key Strengths: {', '.join(strengths)}")

        # Add specific strength details
        for strength in strengths:
            if strength == "Savings Rate":
                rate = components.get("savings_rate", {}).get("details", {}).get("savings_rate", 0)
                explanation_parts.append(f"   • You're saving {rate:.1f}% of your income - excellent!")
            elif strength == "Emergency Readiness":
                months = components.get("emergency_readiness", {}).get("details", {}).get("months_coverage", 0)
                explanation_parts.append(f"   • Your emergency fund covers {months:.1f} months of expenses.")
            elif strength == "Debt Management":
                explanation_parts.append("   • Your debt burden is well-managed.")

    # Weaknesses
    if weaknesses:
        explanation_parts.append(f"\n⚠️ Areas Needing Attention: {', '.join(weaknesses)}")

        # Add specific weakness details
        for weakness in weaknesses:
            if weakness == "Savings Rate":
                rate = components.get("savings_rate", {}).get("details", {}).get("savings_rate", 0)
                if rate < 0:
                    explanation_parts.append(
                        f"   • You're overspending by {abs(rate):.1f}% - reduce expenses urgently.")
                else:
                    explanation_parts.append(f"   • Your {rate:.1f}% savings rate is too low - aim for at least 15%.")
            elif weakness == "Emergency Readiness":
                months = components.get("emergency_readiness", {}).get("details", {}).get("months_coverage", 0)
                explanation_parts.append(f"   • Emergency fund only covers {months:.1f} months - build to 6 months.")
            elif weakness == "Debt Management":
                ratio = components.get("debt_burden", {}).get("details", {}).get("emi_to_income_ratio", 0)
                explanation_parts.append(f"   • EMI consumes {ratio:.1f}% of income - consider debt reduction.")
            elif weakness == "Budget Discipline":
                breaches = components.get("budget_discipline", {}).get("details", {}).get("breach_count", 0)
                explanation_parts.append(f"   • You exceeded budget in {breaches} categories this month.")

    # Recommendations
    explanation_parts.append("\n💡 Recommendations:")

    if score < 50:
        explanation_parts.append("   1. Start with emergency fund - save any small amount consistently")
        explanation_parts.append("   2. Track all expenses rigorously to identify leaks")
        explanation_parts.append("   3. Cut non-essential spending immediately")
    elif score < 70:
        explanation_parts.append("   1. Increase savings rate to at least 15%")
        explanation_parts.append("   2. Build emergency fund to 3-6 months")
        explanation_parts.append("   3. Stick to category budgets consistently")
    else:
        explanation_parts.append("   1. Maintain your discipline")
        explanation_parts.append("   2. Explore tax-saving investments")
        explanation_parts.append("   3. Consider long-term wealth building")

    return "\n".join(explanation_parts)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_health_score_history(state: Dict, months: int = 6) -> List[Dict]:
    """
    Get historical health scores (if tracked).

    Args:
        state: Application state dictionary
        months: Number of months to retrieve

    Returns:
        List of historical health score records
    """
    history = state.get("health_score_history", [])
    return history[-months:] if history else []


def save_health_score_to_history(state: Dict, health_report: Dict) -> Dict:
    """
    Save current health score to history.

    Args:
        state: Application state dictionary
        health_report: Health score report to save

    Returns:
        Updated state dictionary
    """
    if "health_score_history" not in state:
        state["health_score_history"] = []

    history_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "score": health_report.get("health_score"),
        "grade": health_report.get("grade"),
        "components": health_report.get("components")
    }

    state["health_score_history"].append(history_entry)

    # Keep only last 12 months
    state["health_score_history"] = state["health_score_history"][-12:]

    return state


def compare_health_scores(current_report: Dict, previous_report: Dict) -> Dict:
    """
    Compare two health score reports to show improvement/decline.

    Args:
        current_report: Current health score report
        previous_report: Previous health score report

    Returns:
        Comparison dictionary
    """
    current_score = current_report.get("health_score", 0)
    previous_score = previous_report.get("health_score", 0)

    change = current_score - previous_score
    change_percentage = (change / previous_score * 100) if previous_score > 0 else 0

    trend = "improved" if change > 0 else "declined" if change < 0 else "stable"

    return {
        "current_score": current_score,
        "previous_score": previous_score,
        "change": change,
        "change_percentage": round(change_percentage, 2),
        "trend": trend,
        "message": f"Score {trend} by {abs(change)} points ({abs(change_percentage):.1f}%)"
    }