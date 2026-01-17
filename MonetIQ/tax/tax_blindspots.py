""""
tax/tax_blindspots.py

Intelligent tax inefficiency detection and opportunity identification system.
Identifies missed deductions, regime mismatches, compliance risks, and timing issues.

Standalone version - No external dependencies required.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import json


# ============================================================================
# TAX CONSTANTS & LIMITS (FY 2024-25)
# ============================================================================

# Tax deduction limits
DEDUCTION_LIMITS = {
    "80C": 150000,
    "80D_self": 25000,
    "80D_senior": 50000,
    "80D_parents": 25000,
    "80D_parents_senior": 50000,
    "80G": None,  # No limit, but capped at income
    "80E": None,  # No limit on education loan interest
    "80CCD1B": 50000,  # NPS additional
    "HRA_METRO": 0.50,  # 50% of salary
    "HRA_NON_METRO": 0.40,  # 40% of salary
    "24B": 200000,  # Home loan interest
}

# Tax slabs for Old Regime (FY 2024-25)
TAX_SLABS_OLD = [
    (250000, 0),
    (500000, 0.05),
    (1000000, 0.20),
    (float('inf'), 0.30)
]

# Tax slabs for New Regime (FY 2024-25)
TAX_SLABS_NEW = [
    (300000, 0),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float('inf'), 0.30)
]

# Standard deduction
STANDARD_DEDUCTION_OLD = 50000
STANDARD_DEDUCTION_NEW = 75000


# ============================================================================
# STANDALONE TAX CALCULATION FUNCTIONS
# ============================================================================

def calculate_tax_from_slabs(taxable_income: Decimal, slabs: List[Tuple[float, float]]) -> Decimal:
    """Calculate tax based on income tax slabs."""
    tax = Decimal(0)
    previous_limit = Decimal(0)

    for limit, rate in slabs:
        if taxable_income <= previous_limit:
            break

        taxable_in_slab = min(taxable_income, Decimal(str(limit))) - previous_limit
        tax += taxable_in_slab * Decimal(str(rate))
        previous_limit = Decimal(str(limit))

        if taxable_income <= Decimal(str(limit)):
            break

    return tax


def calculate_tax_old_regime(gross_income: Decimal, deductions: Decimal = Decimal(0)) -> Decimal:
    """Calculate tax under old regime with deductions."""
    # Apply standard deduction
    income_after_std = gross_income - Decimal(str(STANDARD_DEDUCTION_OLD))

    # Apply 80C, 80D, etc. deductions
    taxable_income = income_after_std - deductions
    taxable_income = max(Decimal(0), taxable_income)

    # Calculate tax
    tax = calculate_tax_from_slabs(taxable_income, TAX_SLABS_OLD)

    # Add cess (4%)
    tax_with_cess = tax * Decimal("1.04")

    return tax_with_cess


def calculate_tax_new_regime(gross_income: Decimal) -> Decimal:
    """Calculate tax under new regime (no deductions except standard)."""
    # Apply standard deduction
    taxable_income = gross_income - Decimal(str(STANDARD_DEDUCTION_NEW))
    taxable_income = max(Decimal(0), taxable_income)

    # Calculate tax
    tax = calculate_tax_from_slabs(taxable_income, TAX_SLABS_NEW)

    # Add cess (4%)
    tax_with_cess = tax * Decimal("1.04")

    return tax_with_cess


def get_days_remaining_in_fy() -> int:
    """Calculate days remaining in current financial year."""
    today = date.today()

    # Financial year ends on March 31
    if today.month >= 4:  # April to March (next year)
        fy_end = date(today.year + 1, 3, 31)
    else:  # January to March (current year)
        fy_end = date(today.year, 3, 31)

    days_remaining = (fy_end - today).days
    return max(0, days_remaining)


def get_current_financial_year() -> str:
    """Get current financial year string (e.g., '2024-25')."""
    today = date.today()

    if today.month >= 4:
        return f"{today.year}-{str(today.year + 1)[-2:]}"
    else:
        return f"{today.year - 1}-{str(today.year)[-2:]}"


# ============================================================================
# DATA LOADING & EXTRACTION (STANDALONE)
# ============================================================================

def load_financial_data() -> Dict[str, Any]:
    """
    Load complete financial state from storage.
    In standalone mode, returns empty state structure.
    Override this function to integrate with your storage system.
    """
    # Default empty state structure
    return {
        "income": {},
        "expenses": [],
        "tax": {
            "regime": "new",
            "deductions": {},
            "investments": {},
            "city_type": "non_metro",
            "age": 30,
            "parents_age": 60
        }
    }


def get_income_details(state: Dict[str, Any]) -> Dict[str, Decimal]:
    """Extract income details from state."""
    income = state.get("income", {})
    return {
        "gross_salary": Decimal(str(income.get("gross_salary", 0))),
        "basic_salary": Decimal(str(income.get("basic_salary", 0))),
        "hra_received": Decimal(str(income.get("hra_received", 0))),
        "freelance_income": Decimal(str(income.get("freelance_income", 0))),
        "business_income": Decimal(str(income.get("business_income", 0))),
        "rental_income": Decimal(str(income.get("rental_income", 0))),
        "other_income": Decimal(str(income.get("other_income", 0))),
    }


def get_expense_details(state: Dict[str, Any]) -> Dict[str, Decimal]:
    """Extract tax-relevant expenses from state."""
    expenses = state.get("expenses", [])

    expense_map = {
        "rent": Decimal(0),
        "medical_insurance": Decimal(0),
        "life_insurance": Decimal(0),
        "education": Decimal(0),
        "tuition": Decimal(0),
        "donations": Decimal(0),
        "home_loan_interest": Decimal(0),
        "education_loan_interest": Decimal(0),
    }

    for expense in expenses:
        category = expense.get("category", "").lower()
        amount = Decimal(str(expense.get("amount", 0)))

        if "rent" in category or "housing" in category:
            expense_map["rent"] += amount
        elif "insurance" in category:
            if "health" in category or "medical" in category:
                expense_map["medical_insurance"] += amount
            elif "life" in category:
                expense_map["life_insurance"] += amount
        elif "education" in category or "tuition" in category:
            expense_map["education"] += amount
        elif "donation" in category or "charity" in category:
            expense_map["donations"] += amount
        elif "loan" in category:
            if "home" in category or "housing" in category:
                expense_map["home_loan_interest"] += amount
            elif "education" in category:
                expense_map["education_loan_interest"] += amount

    return expense_map


def get_tax_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract tax profile and declared deductions."""
    tax_data = state.get("tax", {})
    return {
        "regime": tax_data.get("regime", "new"),
        "deductions": tax_data.get("deductions", {}),
        "investments": tax_data.get("investments", {}),
        "city_type": tax_data.get("city_type", "non_metro"),
        "age": tax_data.get("age", 30),
        "parents_age": tax_data.get("parents_age", 60),
    }


# ============================================================================
# CORE DETECTION LOGIC
# ============================================================================

def detect_missed_deductions(
    income: Dict[str, Decimal],
    expenses: Dict[str, Decimal],
    tax_profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Detect missing or underutilized deductions."""
    missed = []
    current_deductions = tax_profile.get("deductions", {})
    regime = tax_profile.get("regime", "new")

    # Only check deductions for old regime
    if regime != "old":
        return missed

    # 1. HRA Deduction
    hra_received = income.get("hra_received", Decimal(0))
    rent_paid = expenses.get("rent", Decimal(0)) * 12  # Annualize
    basic_salary = income.get("basic_salary", Decimal(0))

    if hra_received > 0 and rent_paid > 0:
        city_type = tax_profile.get("city_type", "non_metro")
        metro_rate = DEDUCTION_LIMITS["HRA_METRO"] if city_type == "metro" else DEDUCTION_LIMITS["HRA_NON_METRO"]

        hra_exempt = min(
            hra_received,
            rent_paid - (Decimal("0.10") * basic_salary),
            Decimal(str(metro_rate)) * basic_salary
        )

        claimed_hra = Decimal(str(current_deductions.get("HRA", 0)))
        if hra_exempt > claimed_hra:
            missed.append({
                "type": "HRA",
                "section": "10(13A)",
                "potential_saving": float(hra_exempt - claimed_hra),
                "current_claimed": float(claimed_hra),
                "max_possible": float(hra_exempt),
                "priority": "high",
                "description": f"You're paying ₹{float(rent_paid):,.0f} in rent annually but claiming only ₹{float(claimed_hra):,.0f} HRA exemption. You could claim ₹{float(hra_exempt):,.0f}."
            })

    # 2. Section 80C (Investments)
    claimed_80c = Decimal(str(current_deductions.get("80C", 0)))
    if claimed_80c < DEDUCTION_LIMITS["80C"]:
        shortfall = DEDUCTION_LIMITS["80C"] - claimed_80c
        life_insurance = expenses.get("life_insurance", Decimal(0)) * 12

        if life_insurance > 0 and claimed_80c + life_insurance <= DEDUCTION_LIMITS["80C"]:
            missed.append({
                "type": "80C",
                "section": "80C",
                "potential_saving": float(life_insurance),
                "current_claimed": float(claimed_80c),
                "max_possible": DEDUCTION_LIMITS["80C"],
                "priority": "high",
                "description": f"You're paying ₹{float(life_insurance):,.0f} in life insurance but not utilizing it under 80C. Still ₹{float(shortfall):,.0f} available."
            })
        elif shortfall > 50000:
            missed.append({
                "type": "80C",
                "section": "80C",
                "potential_saving": float(shortfall),
                "current_claimed": float(claimed_80c),
                "max_possible": DEDUCTION_LIMITS["80C"],
                "priority": "medium",
                "description": f"You have ₹{float(shortfall):,.0f} unutilized in Section 80C. Consider ELSS, PPF, or NPS."
            })

    # 3. Section 80D (Medical Insurance)
    medical_insurance = expenses.get("medical_insurance", Decimal(0)) * 12
    claimed_80d = Decimal(str(current_deductions.get("80D", 0)))
    age = tax_profile.get("age", 30)
    parents_age = tax_profile.get("parents_age", 60)

    max_80d_self = DEDUCTION_LIMITS["80D_senior"] if age >= 60 else DEDUCTION_LIMITS["80D_self"]
    max_80d_parents = DEDUCTION_LIMITS["80D_parents_senior"] if parents_age >= 60 else DEDUCTION_LIMITS["80D_parents"]
    max_80d = max_80d_self + max_80d_parents

    if medical_insurance > claimed_80d:
        potential = min(medical_insurance, max_80d_self)
        missed.append({
            "type": "80D",
            "section": "80D",
            "potential_saving": float(potential - claimed_80d),
            "current_claimed": float(claimed_80d),
            "max_possible": float(max_80d),
            "priority": "high",
            "description": f"Medical insurance of ₹{float(medical_insurance):,.0f} can save up to ₹{float(potential):,.0f} under 80D."
        })

    # 4. Section 80E (Education Loan Interest)
    edu_loan_interest = expenses.get("education_loan_interest", Decimal(0)) * 12
    claimed_80e = Decimal(str(current_deductions.get("80E", 0)))

    if edu_loan_interest > claimed_80e and edu_loan_interest > 0:
        missed.append({
            "type": "80E",
            "section": "80E",
            "potential_saving": float(edu_loan_interest - claimed_80e),
            "current_claimed": float(claimed_80e),
            "max_possible": float(edu_loan_interest),
            "priority": "high",
            "description": f"Education loan interest of ₹{float(edu_loan_interest):,.0f} has NO LIMIT under 80E. Full deduction available."
        })

    # 5. Section 24(b) (Home Loan Interest)
    home_loan_interest = expenses.get("home_loan_interest", Decimal(0)) * 12
    claimed_24b = Decimal(str(current_deductions.get("24B", 0)))

    if home_loan_interest > claimed_24b and home_loan_interest > 0:
        potential = min(home_loan_interest, DEDUCTION_LIMITS["24B"])
        missed.append({
            "type": "24B",
            "section": "24(b)",
            "potential_saving": float(potential - claimed_24b),
            "current_claimed": float(claimed_24b),
            "max_possible": float(potential),
            "priority": "medium",
            "description": f"Home loan interest of ₹{float(home_loan_interest):,.0f} can save up to ₹{float(potential):,.0f}."
        })

    # 6. Section 80G (Donations)
    donations = expenses.get("donations", Decimal(0)) * 12
    claimed_80g = Decimal(str(current_deductions.get("80G", 0)))

    if donations > claimed_80g and donations > 0:
        missed.append({
            "type": "80G",
            "section": "80G",
            "potential_saving": float(donations - claimed_80g),
            "current_claimed": float(claimed_80g),
            "max_possible": float(donations),
            "priority": "low",
            "description": f"Donations of ₹{float(donations):,.0f} qualify for 50-100% deduction under 80G."
        })

    return missed


def detect_regime_mismatch(
    income: Dict[str, Decimal],
    tax_profile: Dict[str, Any],
    missed_deductions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze if user is in the wrong tax regime."""
    current_regime = tax_profile.get("regime", "new")
    gross_income = income.get("gross_salary", Decimal(0))

    # Calculate tax under both regimes
    current_deductions = tax_profile.get("deductions", {})
    total_current_deductions = sum(Decimal(str(v)) for v in current_deductions.values())

    # Potential deductions if all missed ones are claimed
    potential_deductions = total_current_deductions + sum(
        Decimal(str(d["potential_saving"])) for d in missed_deductions
    )

    tax_old = calculate_tax_old_regime(gross_income, potential_deductions)
    tax_new = calculate_tax_new_regime(gross_income)

    optimal_regime = "old" if tax_old < tax_new else "new"
    is_mismatch = optimal_regime != current_regime

    potential_savings = abs(tax_old - tax_new)

    return {
        "is_mismatch": is_mismatch,
        "current_regime": current_regime,
        "optimal_regime": optimal_regime,
        "tax_old_regime": float(tax_old),
        "tax_new_regime": float(tax_new),
        "potential_savings": float(potential_savings) if is_mismatch else 0,
        "recommendation": (
            f"Switch to {optimal_regime} regime to save ₹{float(potential_savings):,.0f} annually."
            if is_mismatch
            else f"You're in the optimal regime ({current_regime})."
        ),
        "deductions_utilized": float(total_current_deductions),
        "deductions_potential": float(potential_deductions),
    }


def map_expenses_to_deductions(
    expenses: Dict[str, Decimal],
    tax_profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Map eligible expenses to tax deduction opportunities."""
    regime = tax_profile.get("regime", "new")

    if regime != "old":
        return []

    mappings = []

    expense_section_map = {
        "rent": {"section": "10(13A)", "name": "HRA", "limit": "Varies"},
        "medical_insurance": {"section": "80D", "name": "Health Insurance", "limit": "₹25k-₹100k"},
        "life_insurance": {"section": "80C", "name": "Life Insurance", "limit": "₹1.5L"},
        "education": {"section": "80C", "name": "Tuition Fees", "limit": "₹1.5L"},
        "education_loan_interest": {"section": "80E", "name": "Education Loan", "limit": "No Limit"},
        "home_loan_interest": {"section": "24(b)", "name": "Home Loan", "limit": "₹2L"},
        "donations": {"section": "80G", "name": "Donations", "limit": "50-100%"},
    }

    for expense_type, meta in expense_section_map.items():
        amount = expenses.get(expense_type, Decimal(0)) * 12
        if amount > 0:
            mappings.append({
                "expense_type": expense_type,
                "annual_amount": float(amount),
                "section": meta["section"],
                "deduction_name": meta["name"],
                "limit": meta["limit"],
                "status": "eligible"
            })

    return mappings


def detect_timing_blindspots(
    income: Dict[str, Decimal],
    tax_profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Detect timing-related tax planning issues."""
    blindspots = []

    current_deductions = tax_profile.get("deductions", {})
    total_deductions = sum(Decimal(str(v)) for v in current_deductions.values())

    # Get days remaining in FY
    days_left = get_days_remaining_in_fy()

    # Q4 rush warning
    if days_left < 90 and total_deductions < 100000:
        blindspots.append({
            "type": "late_planning",
            "severity": "high",
            "days_remaining": days_left,
            "description": f"Only {days_left} days left in FY! Current deductions: ₹{float(total_deductions):,.0f}. Plan tax-saving investments now.",
            "action": "Invest in ELSS, PPF, or NPS before March 31"
        })

    # Advance tax warning
    gross_income = income.get("gross_salary", Decimal(0))
    if gross_income > 500000:
        advance_tax_paid = Decimal(str(tax_profile.get("deductions", {}).get("advance_tax", 0)))
        if advance_tax_paid == 0:
            blindspots.append({
                "type": "advance_tax",
                "severity": "medium",
                "description": "No advance tax payments detected. You may face interest charges if tax liability > ₹10,000.",
                "action": "Pay advance tax before quarterly deadlines"
            })

    # Early year opportunity
    if days_left > 300:
        blindspots.append({
            "type": "early_planning",
            "severity": "low",
            "days_remaining": days_left,
            "description": f"Great! {days_left} days to plan. Start SIPs in ELSS for rupee-cost averaging.",
            "action": "Set up systematic tax-saving investments"
        })

    return blindspots


def detect_compliance_risks(
    income: Dict[str, Decimal],
    tax_profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Identify tax compliance and penalty risks."""
    risks = []

    gross_income = income.get("gross_salary", Decimal(0))
    total_income = sum(income.values())

    # High income without tax provision
    if total_income > 1000000:
        current_deductions = sum(Decimal(str(v)) for v in tax_profile.get("deductions", {}).values())
        estimated_tax = calculate_tax_new_regime(total_income)

        if estimated_tax > 100000 and current_deductions < 50000:
            risks.append({
                "type": "high_tax_liability",
                "severity": "high",
                "estimated_tax": float(estimated_tax),
                "description": f"Estimated tax liability: ₹{float(estimated_tax):,.0f}. Very low deductions claimed.",
                "consequence": "Potential large tax payout at year-end",
                "action": "Increase tax-saving investments immediately"
            })

    # Multiple income sources without ITR planning
    income_sources = sum(1 for v in income.values() if v > 0)
    if income_sources > 2:
        risks.append({
            "type": "multiple_income_sources",
            "severity": "medium",
            "sources": income_sources,
            "description": f"You have {income_sources} income sources. Ensure proper ITR filing (ITR-2 or ITR-3).",
            "consequence": "Incorrect ITR form = scrutiny",
            "action": "Consult CA for correct ITR selection"
        })

    # Freelance/business income without tax planning
    freelance_income = income.get("freelance_income", Decimal(0)) + income.get("business_income", Decimal(0))
    if freelance_income > 250000:
        risks.append({
            "type": "freelance_tax",
            "severity": "high",
            "amount": float(freelance_income),
            "description": f"Freelance/business income: ₹{float(freelance_income):,.0f}. Remember presumptive taxation (44ADA) or maintain books.",
            "consequence": "30% tax + no expense claims without books",
            "action": "Opt for 44ADA (50% deemed profit) or maintain accounts"
        })

    return risks


def calculate_tax_inefficiency_score(
    missed_deductions: List[Dict[str, Any]],
    regime_analysis: Dict[str, Any],
    timing_blindspots: List[Dict[str, Any]],
    risks: List[Dict[str, Any]]
) -> int:
    """Calculate tax optimization score (0-100). Higher = Better optimized."""
    score = 100

    # Deduct for missed deductions (max -40 points)
    missed_value = sum(d.get("potential_saving", 0) for d in missed_deductions)
    if missed_value > 150000:
        score -= 40
    elif missed_value > 75000:
        score -= 30
    elif missed_value > 25000:
        score -= 20
    elif missed_value > 0:
        score -= 10

    # Deduct for regime mismatch (max -25 points)
    if regime_analysis.get("is_mismatch"):
        potential_savings = regime_analysis.get("potential_savings", 0)
        if potential_savings > 50000:
            score -= 25
        elif potential_savings > 25000:
            score -= 15
        else:
            score -= 10

    # Deduct for timing issues (max -15 points)
    high_timing = sum(1 for t in timing_blindspots if t.get("severity") == "high")
    score -= high_timing * 10
    score -= (len(timing_blindspots) - high_timing) * 5

    # Deduct for compliance risks (max -20 points)
    high_risks = sum(1 for r in risks if r.get("severity") == "high")
    score -= high_risks * 15
    score -= (len(risks) - high_risks) * 5

    return max(0, min(100, score))


def prioritize_blindspots(
    missed_deductions: List[Dict[str, Any]],
    timing_blindspots: List[Dict[str, Any]],
    risks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Prioritize and rank all blindspots by impact."""
    all_blindspots = []

    # Add missed deductions
    for d in missed_deductions:
        impact_score = d.get("potential_saving", 0)
        if d.get("priority") == "high":
            impact_score *= 1.5

        all_blindspots.append({
            "category": "missed_deduction",
            "title": f"Unclaimed {d['section']}",
            "description": d["description"],
            "impact": float(impact_score),
            "priority": d.get("priority", "medium"),
            "action": f"Claim {d['type']} deduction"
        })

    # Add timing issues
    for t in timing_blindspots:
        all_blindspots.append({
            "category": "timing",
            "title": t["type"].replace("_", " ").title(),
            "description": t["description"],
            "impact": 10000 if t.get("severity") == "high" else 5000,
            "priority": t.get("severity", "medium"),
            "action": t.get("action", "Review timing")
        })

    # Add risks
    for r in risks:
        all_blindspots.append({
            "category": "risk",
            "title": r["type"].replace("_", " ").title(),
            "description": r["description"],
            "impact": r.get("estimated_tax", 15000) if "tax" in r.get("type", "") else 10000,
            "priority": r.get("severity", "medium"),
            "action": r.get("action", "Address risk")
        })

    # Sort by impact (descending)
    all_blindspots.sort(key=lambda x: x["impact"], reverse=True)

    return all_blindspots


def get_actionable_recommendations(
    missed_deductions: List[Dict[str, Any]],
    regime_analysis: Dict[str, Any],
    prioritized_blindspots: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate concrete, actionable recommendations."""
    recommendations = []

    # Top 3 blindspots
    for blindspot in prioritized_blindspots[:3]:
        recommendations.append({
            "priority": blindspot["priority"],
            "action": blindspot["action"],
            "expected_benefit": f"₹{blindspot['impact']:,.0f}",
            "effort": "low" if blindspot["category"] == "missed_deduction" else "medium"
        })

    # Regime switch recommendation
    if regime_analysis.get("is_mismatch"):
        recommendations.insert(0, {
            "priority": "critical",
            "action": regime_analysis["recommendation"],
            "expected_benefit": f"₹{regime_analysis['potential_savings']:,.0f}",
            "effort": "low"
        })

    return recommendations[:5]  # Top 5 recommendations


# ============================================================================
# PUBLIC API
# ============================================================================

def get_tax_blindspot_report(financial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main public API: Generate complete tax blindspot analysis report.

    Args:
        financial_state: Optional dict with income, expenses, tax data.
                        If None, loads from default storage.

    Returns:
        Comprehensive tax inefficiency and opportunity report
    """
    # Load data
    if financial_state is None:
        state = load_financial_data()
    else:
        state = financial_state

    income = get_income_details(state)
    expenses = get_expense_details(state)
    tax_profile = get_tax_profile(state)

    # Run detection logic
    missed_deductions = detect_missed_deductions(income, expenses, tax_profile)
    regime_analysis = detect_regime_mismatch(income, tax_profile, missed_deductions)
    expense_mappings = map_expenses_to_deductions(expenses, tax_profile)
    timing_blindspots = detect_timing_blindspots(income, tax_profile)
    compliance_risks = detect_compliance_risks(income, tax_profile)

    # Calculate score
    optimization_score = calculate_tax_inefficiency_score(
        missed_deductions,
        regime_analysis,
        timing_blindspots,
        compliance_risks
    )

    # Prioritize
    prioritized = prioritize_blindspots(
        missed_deductions,
        timing_blindspots,
        compliance_risks
    )

    # Generate recommendations
    recommendations = get_actionable_recommendations(
        missed_deductions,
        regime_analysis,
        prioritized
    )

    # Calculate summary metrics
    total_missed_value = sum(d.get("potential_saving", 0) for d in missed_deductions)
    high_priority_count = sum(1 for d in missed_deductions if d.get("priority") == "high")

    return {
        "summary": {
            "tax_optimization_score": optimization_score,
            "total_missed_savings": float(total_missed_value),
            "high_priority_issues": high_priority_count,
            "total_blindspots": len(prioritized),
            "current_regime": tax_profile.get("regime"),
            "optimal_regime": regime_analysis.get("optimal_regime"),
        },
        "blindspots": prioritized,
        "missed_deductions": missed_deductions,
        "regime_analysis": regime_analysis,
        "expense_to_deduction_mapping": expense_mappings,
        "timing_issues": timing_blindspots,
        "risk_flags": compliance_risks,
        "tax_optimization_score": optimization_score,
        "actionable_recommendations": recommendations,
        "generated_at": datetime.now().isoformat(),
    }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_tax_situation(
    gross_salary: float,
    regime: str = "new",
    deductions: Optional[Dict[str, float]] = None,
    rent_paid_monthly: float = 0,
    medical_insurance_monthly: float = 0,
    city_type: str = "non_metro"
) -> Dict[str, Any]:
    """
    Quick analysis function for simple scenarios.

    Args:
        gross_salary: Annual gross salary
        regime: 'old' or 'new'
        deductions: Dict of current deductions claimed
        rent_paid_monthly: Monthly rent payment
        medical_insurance_monthly: Monthly medical insurance premium
        city_type: 'metro' or 'non_metro'

    Returns:
        Simplified tax blindspot report
    """
    # Build financial state
    state = {
        "income": {
            "gross_salary": gross_salary,
            "basic_salary": gross_salary * 0.4,  # Typical 40%
            "hra_received": gross_salary * 0.5 * 0.4 if city_type == "metro" else gross_salary * 0.4 * 0.4,
        },
        "expenses": [
            {"category": "rent", "amount": rent_paid_monthly},
            {"category": "medical_insurance", "amount": medical_insurance_monthly},
        ],
        "tax": {
            "regime": regime,
            "deductions": deductions or {},
            "city_type": city_type,
            "age": 30,
            "parents_age": 60
        }
    }

    return get_tax_blindspot_report(state)


def compare_regimes(gross_salary: float, deductions: float = 0) -> Dict[str, Any]:
    """
    Compare tax liability under both regimes.

    Args:
        gross_salary: Annual gross salary
        deductions: Total deductions (for old regime)

    Returns:
        Comparison report
    """
    tax_old = calculate_tax_old_regime(Decimal(str(gross_salary)), Decimal(str(deductions)))
    tax_new = calculate_tax_new_regime(Decimal(str(gross_salary)))

    savings = abs(tax_old - tax_new)
    better_regime = "old" if tax_old < tax_new else "new"

    return {
        "gross_salary": gross_salary,
        "deductions": deductions,
        "tax_old_regime": float(tax_old),
        "tax_new_regime": float(tax_new),
        "better_regime": better_regime,
        "savings": float(savings),
        "recommendation": f"Choose {better_regime} regime to save ₹{float(savings):,.0f}"
    }


# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TAX BLINDSPOT DETECTION SYSTEM - STANDALONE VERSION")
    print("=" * 80)

    # Example 1: Simple regime comparison
    print("\n1. REGIME COMPARISON")
    print("-" * 80)
    comparison = compare_regimes(gross_salary=1200000, deductions=150000)
    print(f"Gross Salary: ₹{comparison['gross_salary']:,.0f}")
    print(f"Deductions: ₹{comparison['deductions']:,.0f}")
    print(f"Tax (Old Regime): ₹{comparison['tax_old_regime']:,.0f}")
    print(f"Tax (New Regime): ₹{comparison['tax_new_regime']:,.0f}")
    print(f"Better Regime: {comparison['better_regime'].upper()}")
    print(f"Savings: ₹{comparison['savings']:,.0f}")

    # Example 2: Quick analysis
    print("\n2. QUICK TAX BLINDSPOT ANALYSIS")
    print("-" * 80)
    analysis = analyze_tax_situation(
        gross_salary=1200000,
        regime="old",
        deductions={"80C": 100000, "80D": 15000},
        rent_paid_monthly=25000,
        medical_insurance_monthly=3000,
        city_type="metro"
    )

    print(f"Tax Optimization Score: {analysis['summary']['tax_optimization_score']}/100")
    print(f"Total Missed Savings: ₹{analysis['summary']['total_missed_savings']:,.0f}")
    print(f"High Priority Issues: {analysis['summary']['high_priority_issues']}")
    print(f"Current Regime: {analysis['summary']['current_regime']}")
    print(f"Optimal Regime: {analysis['summary']['optimal_regime']}")

    print("\nTop Recommendations:")
    for i, rec in enumerate(analysis['actionable_recommendations'][:3], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['action']}")
        print(f"     Expected Benefit: {rec['expected_benefit']} | Effort: {rec['effort']}")

    # Example 3: Full report with custom data
    print("\n3. FULL BLINDSPOT REPORT")
    print("-" * 80)

    custom_state = {
        "income": {
            "gross_salary": 1500000,
            "basic_salary": 600000,
            "hra_received": 300000,
            "freelance_income": 200000
        },
        "expenses": [
            {"category": "rent", "amount": 30000},
            {"category": "medical_insurance", "amount": 2500},
            {"category": "life_insurance", "amount": 5000},
            {"category": "home_loan_interest", "amount": 15000},
        ],
        "tax": {
            "regime": "new",  # User in new regime
            "deductions": {},  # No deductions claimed
            "city_type": "metro",
            "age": 35,
            "parents_age": 65
        }
    }

    report = get_tax_blindspot_report(custom_state)

    print(f"Tax Optimization Score: {report['tax_optimization_score']}/100")
    print(f"\nRegime Analysis:")
    print(f"  Current: {report['regime_analysis']['current_regime']}")
    print(f"  Optimal: {report['regime_analysis']['optimal_regime']}")
    print(f"  Is Mismatch: {report['regime_analysis']['is_mismatch']}")
    if report['regime_analysis']['is_mismatch']:
        print(f"  Potential Savings: ₹{report['regime_analysis']['potential_savings']:,.0f}")

    print(f"\nBlindspots Detected: {len(report['blindspots'])}")
    for blindspot in report['blindspots'][:5]:
        print(f"\n  • {blindspot['title']} [{blindspot['priority'].upper()}]")
        print(f"    {blindspot['description'][:100]}...")
        print(f"    Impact: ₹{blindspot['impact']:,.0f}")
        print(f"    Action: {blindspot['action']}")

    print("\n" + "=" * 80)
    print("Analysis complete! Module is working standalone.")
    print("=" * 80)
