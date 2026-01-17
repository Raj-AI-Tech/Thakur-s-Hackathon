"""
tax/tax_suggestions.py

Tax intelligence and optimization engine for MonetIQ.
Generates personalized tax-saving recommendations and actionable insights.
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# ============================================================================
# TAX CONSTANTS (Indian Tax System)
# ============================================================================

TAX_LIMITS = {
    "80C": 150000,
    "80D": {
        "self": 25000,
        "self_senior": 50000,
        "parents": 25000,
        "parents_senior": 50000
    },
    "80CCD_1B": 50000,  # NPS additional
    "80E": float('inf'),  # Education loan (no limit)
    "24B": 200000,  # Home loan interest
    "HRA": None  # Calculated based on salary
}

OLD_REGIME_SLABS = [
    (250000, 0),
    (500000, 0.05),
    (1000000, 0.20),
    (float('inf'), 0.30)
]

NEW_REGIME_SLABS = [
    (300000, 0),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float('inf'), 0.30)
]

STANDARD_DEDUCTION = 50000
CESS_RATE = 0.04

INVESTMENT_OPTIONS = {
    "80C": [
        {"name": "ELSS Mutual Funds", "risk": "medium", "returns": "12-15%", "lock_in": "3 years"},
        {"name": "PPF", "risk": "low", "returns": "7-8%", "lock_in": "15 years"},
        {"name": "EPF", "risk": "low", "returns": "8-9%", "lock_in": "retirement"},
        {"name": "NSC", "risk": "low", "returns": "7-8%", "lock_in": "5 years"},
        {"name": "Tax Saving FD", "risk": "low", "returns": "6-7%", "lock_in": "5 years"},
        {"name": "Life Insurance", "risk": "low", "returns": "5-6%", "lock_in": "varies"},
        {"name": "Sukanya Samriddhi", "risk": "low", "returns": "8%", "lock_in": "21 years"}
    ],
    "80D": [
        {"name": "Health Insurance", "coverage": "Self & Family", "benefit": "Tax deduction + coverage"},
        {"name": "Preventive Health Checkup", "coverage": "₹5,000", "benefit": "Within 80D limit"}
    ],
    "80CCD_1B": [
        {"name": "NPS (National Pension)", "risk": "medium", "returns": "10-12%", "lock_in": "retirement"}
    ]
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _normalize_amount(value: Any) -> float:
    """Convert any value to safe float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("₹", "").replace("$", "")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    return 0.0


def _safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safe division with zero protection."""
    try:
        if b == 0:
            return default
        return float(a) / float(b)
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def _percentage(part: float, whole: float) -> float:
    """Calculate percentage safely."""
    return _safe_divide(part, whole, 0) * 100


def _format_currency(amount: float) -> str:
    """Format amount as INR currency."""
    return f"₹{amount:,.0f}"


def _calculate_tax_old_regime(taxable_income: float, deductions: float) -> float:
    """Calculate tax under old regime."""
    income_after_deductions = max(0, taxable_income - deductions - STANDARD_DEDUCTION)

    tax = 0.0
    prev_limit = 0

    for limit, rate in OLD_REGIME_SLABS:
        if income_after_deductions <= prev_limit:
            break

        taxable_in_slab = min(income_after_deductions, limit) - prev_limit
        tax += taxable_in_slab * rate
        prev_limit = limit

    # Add cess
    tax_with_cess = tax * (1 + CESS_RATE)

    return round(tax_with_cess, 0)


def _calculate_tax_new_regime(taxable_income: float) -> float:
    """Calculate tax under new regime."""
    income_after_std_deduction = max(0, taxable_income - STANDARD_DEDUCTION)

    tax = 0.0
    prev_limit = 0

    for limit, rate in NEW_REGIME_SLABS:
        if income_after_std_deduction <= prev_limit:
            break

        taxable_in_slab = min(income_after_std_deduction, limit) - prev_limit
        tax += taxable_in_slab * rate
        prev_limit = limit

    # Add cess
    tax_with_cess = tax * (1 + CESS_RATE)

    # Rebate under 87A for income up to 7 lakhs
    if income_after_std_deduction <= 700000:
        rebate = min(tax_with_cess, 25000)
        tax_with_cess -= rebate

    return round(tax_with_cess, 0)


# ============================================================================
# DATA EXTRACTION
# ============================================================================

def get_income_details(state: Dict[str, Any]) -> Dict[str, float]:
    """Extract income information from state."""
    income_data = state.get("income", {})

    if isinstance(income_data, dict):
        monthly = _normalize_amount(income_data.get("monthly", 0))
    else:
        monthly = _normalize_amount(income_data)

    annual = monthly * 12

    return {
        "monthly": monthly,
        "annual": annual
    }


def get_expense_summary(state: Dict[str, Any]) -> Dict[str, float]:
    """Extract and categorize expenses."""
    expenses = state.get("expenses", [])

    if not isinstance(expenses, list):
        expenses = []

    categories = {
        "rent": 0.0,
        "health": 0.0,
        "education": 0.0,
        "insurance": 0.0,
        "discretionary": 0.0,
        "total": 0.0
    }

    discretionary_keywords = ["entertainment", "dining", "shopping", "travel", "leisure"]

    for expense in expenses:
        if not isinstance(expense, dict):
            continue

        amount = _normalize_amount(expense.get("amount", 0))
        category = str(expense.get("category", "")).lower()

        categories["total"] += amount

        if "rent" in category or "housing" in category:
            categories["rent"] += amount
        elif "health" in category or "medical" in category:
            categories["health"] += amount
        elif "education" in category or "tuition" in category:
            categories["education"] += amount
        elif "insurance" in category:
            categories["insurance"] += amount
        elif any(keyword in category for keyword in discretionary_keywords):
            categories["discretionary"] += amount

    return categories


def get_current_deductions(state: Dict[str, Any]) -> Dict[str, float]:
    """Extract currently claimed deductions."""
    tax_data = state.get("tax", {})

    if not isinstance(tax_data, dict):
        return {}

    deductions = {
        "80C": _normalize_amount(tax_data.get("80C", 0)),
        "80D": _normalize_amount(tax_data.get("80D", 0)),
        "80CCD_1B": _normalize_amount(tax_data.get("80CCD_1B", 0)),
        "80E": _normalize_amount(tax_data.get("80E", 0)),
        "24B": _normalize_amount(tax_data.get("24B", 0)),
        "HRA": _normalize_amount(tax_data.get("HRA", 0))
    }

    return deductions


def get_user_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user profile information."""
    user_data = state.get("user", {})

    return {
        "name": user_data.get("name", ""),
        "age": user_data.get("age", 30),
        "is_senior": user_data.get("age", 30) >= 60,
        "dependents": user_data.get("dependents", 0),
        "city_tier": user_data.get("city_tier", "metro")
    }


# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

def analyze_tax_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze complete tax profile of user."""
    income = get_income_details(state)
    expenses = get_expense_summary(state)
    deductions = get_current_deductions(state)
    profile = get_user_profile(state)

    annual_income = income["annual"]
    total_deductions = sum(deductions.values())

    # Calculate current tax liability
    tax_old = _calculate_tax_old_regime(annual_income, total_deductions)
    tax_new = _calculate_tax_new_regime(annual_income)

    # Determine current regime (lower tax)
    current_regime = "Old" if tax_old <= tax_new else "New"
    current_tax = min(tax_old, tax_new)

    # Calculate tax efficiency
    potential_deductions = TAX_LIMITS["80C"] + TAX_LIMITS["80D"]["self"] + TAX_LIMITS["80CCD_1B"]
    deduction_utilization = _safe_divide(total_deductions, potential_deductions, 0) * 100

    return {
        "annual_income": annual_income,
        "total_deductions": total_deductions,
        "current_tax": current_tax,
        "current_regime": current_regime,
        "tax_old": tax_old,
        "tax_new": tax_new,
        "deduction_utilization": deduction_utilization,
        "expenses": expenses,
        "profile": profile
    }


def calculate_unused_deductions(state: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Calculate unused deduction limits for each section."""
    current_deductions = get_current_deductions(state)
    profile = get_user_profile(state)

    unused = {}

    # Section 80C
    used_80c = current_deductions.get("80C", 0)
    unused["80C"] = {
        "limit": TAX_LIMITS["80C"],
        "used": used_80c,
        "remaining": max(0, TAX_LIMITS["80C"] - used_80c)
    }

    # Section 80D
    max_80d = TAX_LIMITS["80D"]["self_senior" if profile["is_senior"] else "self"]
    used_80d = current_deductions.get("80D", 0)
    unused["80D"] = {
        "limit": max_80d,
        "used": used_80d,
        "remaining": max(0, max_80d - used_80d)
    }

    # Section 80CCD(1B) - NPS
    used_nps = current_deductions.get("80CCD_1B", 0)
    unused["80CCD_1B"] = {
        "limit": TAX_LIMITS["80CCD_1B"],
        "used": used_nps,
        "remaining": max(0, TAX_LIMITS["80CCD_1B"] - used_nps)
    }

    # Section 24(b) - Home Loan
    used_home_loan = current_deductions.get("24B", 0)
    unused["24B"] = {
        "limit": TAX_LIMITS["24B"],
        "used": used_home_loan,
        "remaining": max(0, TAX_LIMITS["24B"] - used_home_loan)
    }

    return unused


def generate_sectionwise_suggestions(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate section-wise tax saving suggestions."""
    unused = calculate_unused_deductions(state)
    income = get_income_details(state)
    expenses = get_expense_summary(state)
    profile = get_user_profile(state)

    suggestions = []

    # Section 80C Suggestions
    if unused["80C"]["remaining"] > 0:
        remaining = unused["80C"]["remaining"]
        tax_saved = remaining * 0.30  # Assuming 30% tax bracket

        # Determine risk profile based on age
        risk_appetite = "high" if profile["age"] < 35 else "medium" if profile["age"] < 50 else "low"

        if risk_appetite == "high":
            recommendation = "ELSS Mutual Funds"
            reason = "Best for young investors with higher risk appetite and shorter lock-in period (3 years)"
        elif risk_appetite == "medium":
            recommendation = "PPF + ELSS combination"
            reason = "Balanced approach with stability (PPF) and growth potential (ELSS)"
        else:
            recommendation = "PPF or NSC"
            reason = "Safe, government-backed instruments suitable for conservative investors"

        suggestions.append({
            "section": "80C",
            "title": f"Maximize 80C Deduction - Save up to {_format_currency(tax_saved)}",
            "message": f"You have {_format_currency(remaining)} unused in Section 80C. Investing this amount can save you approximately {_format_currency(tax_saved)} in taxes.",
            "recommendation": recommendation,
            "reason": reason,
            "potential_savings": tax_saved,
            "investment_required": remaining,
            "action": f"Invest {_format_currency(remaining)} before March 31st",
            "priority": "HIGH" if remaining > 50000 else "MEDIUM",
            "options": INVESTMENT_OPTIONS["80C"]
        })

    # Section 80D Suggestions
    if unused["80D"]["remaining"] > 0:
        remaining = unused["80D"]["remaining"]
        tax_saved = remaining * 0.30

        suggestions.append({
            "section": "80D",
            "title": f"Health Insurance Tax Benefit - Save up to {_format_currency(tax_saved)}",
            "message": f"You can claim up to {_format_currency(remaining)} more under Section 80D for health insurance premiums.",
            "recommendation": "Comprehensive Health Insurance",
            "reason": "Dual benefit of tax savings and financial protection against medical emergencies",
            "potential_savings": tax_saved,
            "investment_required": remaining,
            "action": "Purchase or upgrade health insurance policy",
            "priority": "HIGH",
            "options": INVESTMENT_OPTIONS["80D"]
        })

    # Section 80CCD(1B) - NPS Suggestions
    if unused["80CCD_1B"]["remaining"] > 0:
        remaining = unused["80CCD_1B"]["remaining"]
        tax_saved = remaining * 0.30

        if profile["age"] < 50:
            suggestions.append({
                "section": "80CCD(1B)",
                "title": f"NPS Additional Deduction - Save {_format_currency(tax_saved)}",
                "message": f"Invest {_format_currency(remaining)} in NPS for additional tax savings beyond 80C limit.",
                "recommendation": "National Pension System",
                "reason": "Extra ₹50,000 deduction exclusively for NPS, builds retirement corpus",
                "potential_savings": tax_saved,
                "investment_required": remaining,
                "action": "Open NPS account and invest before March 31st",
                "priority": "MEDIUM",
                "options": INVESTMENT_OPTIONS["80CCD_1B"]
            })

    # HRA Optimization
    if expenses["rent"] > 0 and profile["city_tier"] == "metro":
        monthly_rent = expenses["rent"]
        monthly_income = income["monthly"]

        # HRA exemption calculation
        hra_exempt = min(
            monthly_rent * 12,
            monthly_rent * 12 - (0.10 * monthly_income * 12),
            0.50 * monthly_income * 12  # 50% for metro
        )

        if hra_exempt > 0:
            tax_saved = hra_exempt * 0.30

            suggestions.append({
                "section": "HRA",
                "title": f"HRA Exemption Available - Save {_format_currency(tax_saved)}",
                "message": f"Your rent payments of {_format_currency(monthly_rent * 12)} annually qualify for HRA exemption of approximately {_format_currency(hra_exempt)}.",
                "recommendation": "Claim HRA Exemption",
                "reason": "You're already paying rent, ensure you claim the tax benefit",
                "potential_savings": tax_saved,
                "investment_required": 0,
                "action": "Ensure rent receipts and landlord PAN are available for ITR filing",
                "priority": "HIGH"
            })

    # Home Loan Interest Deduction
    if unused["24B"]["remaining"] > 0:
        suggestions.append({
            "section": "24(b)",
            "title": "Home Loan Interest Deduction Available",
            "message": f"If you have a home loan, you can claim up to {_format_currency(TAX_LIMITS['24B'])} as interest deduction under Section 24(b).",
            "recommendation": "Claim Home Loan Interest",
            "reason": "Reduce taxable income through home loan interest payments",
            "potential_savings": TAX_LIMITS["24B"] * 0.30,
            "investment_required": 0,
            "action": "Obtain interest certificate from bank and include in ITR",
            "priority": "MEDIUM"
        })

    return suggestions


def analyze_lifestyle_tradeoffs(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify opportunities to redirect discretionary spending to tax-saving investments."""
    expenses = get_expense_summary(state)
    unused = calculate_unused_deductions(state)

    tradeoffs = []

    discretionary = expenses["discretionary"]
    unused_80c = unused["80C"]["remaining"]

    if discretionary > 10000 and unused_80c > 0:
        # Calculate what percentage of discretionary spend could cover unused 80C
        redirect_amount = min(discretionary * 0.20, unused_80c)
        tax_saved = redirect_amount * 0.30

        tradeoffs.append({
            "type": "discretionary_to_investment",
            "title": "Smart Spending Opportunity",
            "message": f"Redirecting just {_percentage(redirect_amount, discretionary):.0f}% of your discretionary spending ({_format_currency(redirect_amount)}) to tax-saving investments could save you {_format_currency(tax_saved)} in taxes.",
            "current_spending": discretionary,
            "redirect_amount": redirect_amount,
            "tax_savings": tax_saved,
            "net_benefit": tax_saved,
            "action": "Consider reducing non-essential expenses and investing in ELSS or PPF",
            "priority": "MEDIUM"
        })

    return tradeoffs


def compare_tax_regimes(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compare old vs new tax regime for user."""
    income = get_income_details(state)
    current_deductions = get_current_deductions(state)
    unused = calculate_unused_deductions(state)

    annual_income = income["annual"]
    total_current_deductions = sum(current_deductions.values())

    # Calculate with current deductions
    tax_old_current = _calculate_tax_old_regime(annual_income, total_current_deductions)
    tax_new = _calculate_tax_new_regime(annual_income)

    # Calculate with maximum possible deductions
    max_deductions = (
            TAX_LIMITS["80C"] +
            TAX_LIMITS["80D"]["self"] +
            TAX_LIMITS["80CCD_1B"]
    )
    tax_old_max = _calculate_tax_old_regime(annual_income, max_deductions)

    comparison = {
        "old_regime": {
            "with_current_deductions": tax_old_current,
            "with_max_deductions": tax_old_max,
            "deductions_used": total_current_deductions,
            "max_possible_deductions": max_deductions
        },
        "new_regime": {
            "tax": tax_new,
            "deductions_allowed": STANDARD_DEDUCTION
        },
        "recommendation": "",
        "reason": "",
        "savings_difference": 0
    }

    # Determine recommendation
    if tax_old_current < tax_new:
        comparison["recommendation"] = "Old Regime"
        comparison[
            "reason"] = f"With your current deductions of {_format_currency(total_current_deductions)}, old regime saves you {_format_currency(tax_new - tax_old_current)} compared to new regime."
        comparison["savings_difference"] = tax_new - tax_old_current
    else:
        comparison["recommendation"] = "New Regime"
        comparison[
            "reason"] = f"New regime is better as you save {_format_currency(tax_old_current - tax_new)} without needing to make investments for deductions."
        comparison["savings_difference"] = tax_old_current - tax_new

    # Additional insight for maximizing old regime
    if tax_old_max < tax_new and total_current_deductions < max_deductions:
        additional_investment = max_deductions - total_current_deductions
        additional_savings = tax_old_current - tax_old_max

        comparison["optimization_opportunity"] = {
            "message": f"By maximizing deductions (investing additional {_format_currency(additional_investment)}), you could save {_format_currency(additional_savings)} more in the old regime.",
            "additional_investment": additional_investment,
            "additional_savings": additional_savings
        }

    return comparison


def estimate_total_tax_savings(state: Dict[str, Any]) -> Dict[str, float]:
    """Estimate total potential tax savings across all recommendations."""
    suggestions = generate_sectionwise_suggestions(state)

    total_potential = sum(s.get("potential_savings", 0) for s in suggestions)
    total_investment_required = sum(s.get("investment_required", 0) for s in suggestions)

    return {
        "total_potential_savings": total_potential,
        "total_investment_required": total_investment_required,
        "roi": _safe_divide(total_potential, total_investment_required, 0) * 100
    }


def generate_deadlines_and_reminders(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate tax-related deadlines and action reminders."""
    current_month = datetime.now().month
    unused = calculate_unused_deductions(state)

    reminders = []

    # Financial year end reminder
    if current_month >= 1 and current_month <= 3:
        total_unused = sum(u["remaining"] for u in unused.values())

        if total_unused > 0:
            reminders.append({
                "title": "Financial Year End Approaching",
                "message": f"You still have {_format_currency(total_unused)} in unused tax-saving limits. Act before March 31st!",
                "deadline": "March 31",
                "urgency": "HIGH"
            })

    # ITR filing reminder
    if current_month >= 4 and current_month <= 7:
        reminders.append({
            "title": "ITR Filing Window Open",
            "message": "File your Income Tax Return before July 31st to avoid penalties and claim refunds.",
            "deadline": "July 31",
            "urgency": "HIGH"
        })

    # Advance tax reminder
    if current_month in [6, 9, 12, 3]:
        reminders.append({
            "title": "Advance Tax Payment Due",
            "message": "If your tax liability exceeds ₹10,000, advance tax payment is required this quarter.",
            "deadline": f"15th {datetime.now().strftime('%B')}",
            "urgency": "MEDIUM"
        })

    return reminders


def prioritize_suggestions(suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prioritize suggestions based on impact and urgency."""
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    sorted_suggestions = sorted(
        suggestions,
        key=lambda x: (
            priority_order.get(x.get("priority", "LOW"), 3),
            -x.get("potential_savings", 0)
        )
    )

    return sorted_suggestions


# ============================================================================
# PUBLIC API
# ============================================================================

def get_tax_suggestions_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate complete tax suggestions report.

    Args:
        state: Application state dictionary

    Returns:
        Comprehensive tax suggestions report
    """
    # Analyze tax profile
    profile_analysis = analyze_tax_profile(state)

    # Generate suggestions
    suggestions = generate_sectionwise_suggestions(state)
    tradeoffs = analyze_lifestyle_tradeoffs(state)

    # Prioritize suggestions
    prioritized_suggestions = prioritize_suggestions(suggestions)

    # Calculate potential savings
    savings_estimate = estimate_total_tax_savings(state)

    # Compare regimes
    regime_comparison = compare_tax_regimes(state)

    # Get unused deductions
    unused_deductions = calculate_unused_deductions(state)

    # Generate reminders
    deadlines = generate_deadlines_and_reminders(state)

    # Build comprehensive report
    report = {
        "summary": {
            "current_tax": profile_analysis["current_tax"],
            "potential_savings": savings_estimate["total_potential_savings"],
            "recommended_regime": regime_comparison["recommendation"],
            "deduction_utilization": profile_analysis["deduction_utilization"],
            "total_investment_required": savings_estimate["total_investment_required"]
        },
        "suggestions": prioritized_suggestions,
        "lifestyle_tradeoffs": tradeoffs,
        "unused_deductions": unused_deductions,
        "regime_comparison": regime_comparison,
        "deadlines": deadlines,
        "profile": profile_analysis,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_suggestions": len(prioritized_suggestions),
            "high_priority_count": sum(1 for s in suggestions if s.get("priority") == "HIGH")
        }
    }

    return report


def get_quick_wins(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get quick win tax-saving opportunities (no investment required).

    Args:
        state: Application state dictionary

    Returns:
        List of quick win opportunities
    """
    suggestions = generate_sectionwise_suggestions(state)

    quick_wins = [
        s for s in suggestions
        if s.get("investment_required", float('inf')) == 0
    ]

    return quick_wins


def get_investment_roadmap(state: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create a prioritized investment roadmap for tax savings.

    Args:
        state: Application state dictionary

    Returns:
        Roadmap with immediate, short-term, and long-term actions
    """
    suggestions = generate_sectionwise_suggestions(state)

    roadmap = {
        "immediate": [],  # Can be done now, high impact
        "short_term": [],  # Within 3 months
        "long_term": []  # Planning for next year
    }

    for suggestion in suggestions:
        investment_req = suggestion.get("investment_required", 0)
        priority = suggestion.get("priority", "LOW")

        if priority == "HIGH" and investment_req < 50000:
            roadmap["immediate"].append(suggestion)
        elif investment_req < 100000:
            roadmap["short_term"].append(suggestion)
        else:
            roadmap["long_term"].append(suggestion)

    return roadmap


def calculate_tax_efficiency_score(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate user's tax efficiency score (0-100).

    Args:
        state: Application state dictionary

    Returns:
        Score and breakdown
    """
    profile = analyze_tax_profile(state)
    unused = calculate_unused_deductions(state)

    # Calculate utilization score (40% weight)
    utilization_score = profile["deduction_utilization"]

    # Calculate planning score (30% weight) - based on regime choice
    regime_comp = compare_tax_regimes(state)
    is_optimal_regime = (
            (profile["current_regime"] == "Old" and profile["tax_old"] < profile["tax_new"]) or
            (profile["current_regime"] == "New" and profile["tax_new"] <= profile["tax_old"])
    )
    planning_score = 100 if is_optimal_regime else 50

    # Calculate documentation score (30% weight) - assume 70% if deductions exist
    has_deductions = profile["total_deductions"] > 0
    documentation_score = 70 if has_deductions else 30

    # Weighted average
    total_score = (
            utilization_score * 0.40 +
            planning_score * 0.30 +
            documentation_score * 0.30
    )

    # Determine grade
    if total_score >= 80:
        grade = "Excellent"
        message = "You're maximizing your tax savings effectively!"
    elif total_score >= 60:
        grade = "Good"
        message = "You're on the right track, but there's room for optimization."
    elif total_score >= 40:
        grade = "Fair"
        message = "Significant tax-saving opportunities are being missed."
    else:
        grade = "Needs Improvement"
        message = "You could be saving much more with proper tax planning."

    return {
        "score": round(total_score, 1),
        "grade": grade,
        "message": message,
        "breakdown": {
            "deduction_utilization": round(utilization_score, 1),
            "tax_planning": round(planning_score, 1),
            "documentation": round(documentation_score, 1)
        }
    }