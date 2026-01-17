"""
tax/tax_estimator.py

Intelligent tax estimation and regime comparison engine for Indian tax compliance.
Provides comprehensive tax analysis, simulations, and readiness scoring.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TaxRegime(Enum):
    """Tax regime options."""
    OLD = "old"
    NEW = "new"


# Indian Income Tax Slabs (FY 2024-25)
TAX_SLABS_OLD_REGIME = [
    {"min": 0, "max": 250000, "rate": 0.00},
    {"min": 250000, "max": 500000, "rate": 0.05},
    {"min": 500000, "max": 1000000, "rate": 0.20},
    {"min": 1000000, "max": float('inf'), "rate": 0.30},
]

TAX_SLABS_NEW_REGIME = [
    {"min": 0, "max": 300000, "rate": 0.00},
    {"min": 300000, "max": 600000, "rate": 0.05},
    {"min": 600000, "max": 900000, "rate": 0.10},
    {"min": 900000, "max": 1200000, "rate": 0.15},
    {"min": 1200000, "max": 1500000, "rate": 0.20},
    {"min": 1500000, "max": float('inf'), "rate": 0.30},
]

# Standard deduction
STANDARD_DEDUCTION_OLD = 50000
STANDARD_DEDUCTION_NEW = 75000

# Cess
CESS_RATE = 0.04  # 4% health and education cess

# Surcharge thresholds
SURCHARGE_THRESHOLDS = [
    {"min": 5000000, "max": 10000000, "rate": 0.10},
    {"min": 10000000, "max": 20000000, "rate": 0.15},
    {"min": 20000000, "max": 50000000, "rate": 0.25},
    {"min": 50000000, "max": float('inf'), "rate": 0.37},
]


# Helper functions to replace utils imports
def safe_decimal(value: Any) -> Decimal:
    """Convert value to Decimal safely."""
    try:
        if isinstance(value, Decimal):
            return value
        if value is None:
            return Decimal(0)
        return Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return Decimal(0)


def get_current_financial_year() -> str:
    """Get current financial year (April to March)."""
    now = datetime.now()
    if now.month >= 4:
        return f"FY {now.year}-{now.year + 1}"
    else:
        return f"FY {now.year - 1}-{now.year}"


def load_financial_data() -> Dict[str, Any]:
    """
    Load complete financial state from storage.
    Returns empty dict if no data available.
    """
    # Placeholder - in real implementation, this would load from actual storage
    return {
        "income": {},
        "tax": {"deductions": {}},
        "expenses": [],
        "monthly_expenses": 0
    }


def get_income_data(state: Dict[str, Any]) -> Dict[str, Decimal]:
    """
    Extract and aggregate all income sources.

    Returns:
        Dictionary with income breakdown and totals
    """
    income_raw = state.get("income", {})

    income = {
        "gross_salary": safe_decimal(income_raw.get("gross_salary", 0)),
        "basic_salary": safe_decimal(income_raw.get("basic_salary", 0)),
        "hra_received": safe_decimal(income_raw.get("hra_received", 0)),
        "freelance_income": safe_decimal(income_raw.get("freelance_income", 0)),
        "business_income": safe_decimal(income_raw.get("business_income", 0)),
        "rental_income": safe_decimal(income_raw.get("rental_income", 0)),
        "capital_gains": safe_decimal(income_raw.get("capital_gains", 0)),
        "interest_income": safe_decimal(income_raw.get("interest_income", 0)),
        "other_income": safe_decimal(income_raw.get("other_income", 0)),
    }

    # Calculate total income
    income["total_income"] = sum(v for k, v in income.items() if k != "total_income")

    return income


def get_deductions(state: Dict[str, Any]) -> Dict[str, Decimal]:
    """
    Extract declared deductions from state.

    Returns:
        Dictionary of deduction sections and amounts
    """
    deductions_raw = state.get("tax", {}).get("deductions", {})

    return {
        "80C": safe_decimal(deductions_raw.get("80C", 0)),
        "80D": safe_decimal(deductions_raw.get("80D", 0)),
        "80E": safe_decimal(deductions_raw.get("80E", 0)),
        "80G": safe_decimal(deductions_raw.get("80G", 0)),
        "80CCD1B": safe_decimal(deductions_raw.get("80CCD1B", 0)),
        "HRA": safe_decimal(deductions_raw.get("HRA", 0)),
        "24B": safe_decimal(deductions_raw.get("24B", 0)),
        "other": safe_decimal(deductions_raw.get("other", 0)),
    }


def get_user_profile(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user tax profile information."""
    tax_data = state.get("tax", {})

    return {
        "age": tax_data.get("age", 30),
        "preferred_regime": tax_data.get("regime", "new"),
        "city_type": tax_data.get("city_type", "non_metro"),
        "has_home_loan": tax_data.get("has_home_loan", False),
        "has_health_insurance": tax_data.get("has_health_insurance", False),
    }


def get_tax_slabs(regime: TaxRegime) -> List[Dict[str, Any]]:
    """Get tax slabs for the specified regime."""
    if regime == TaxRegime.OLD:
        return TAX_SLABS_OLD_REGIME
    return TAX_SLABS_NEW_REGIME


def calculate_slab_wise_tax(
    taxable_income: Decimal,
    slabs: List[Dict[str, Any]]
) -> Tuple[Decimal, List[Dict[str, Any]]]:
    """
    Calculate tax using progressive slab system.

    Args:
        taxable_income: Income after deductions
        slabs: Tax slab structure

    Returns:
        Tuple of (total_tax, slab_breakdown)
    """
    total_tax = Decimal(0)
    breakdown = []
    remaining_income = taxable_income

    for slab in slabs:
        slab_min = Decimal(str(slab["min"]))
        slab_max = Decimal(str(slab["max"]))
        rate = Decimal(str(slab["rate"]))

        if remaining_income <= 0:
            break

        if taxable_income <= slab_min:
            continue

        # Calculate income in this slab
        income_in_slab = min(
            remaining_income,
            slab_max - slab_min if slab_max != float('inf') else remaining_income
        )

        tax_in_slab = income_in_slab * rate
        total_tax += tax_in_slab

        breakdown.append({
            "slab": f"₹{float(slab_min):,.0f} - {'₹' + f'{float(slab_max):,.0f}' if slab_max != float('inf') else 'Above'}",
            "rate": f"{float(rate * 100):.0f}%",
            "income_in_slab": float(income_in_slab),
            "tax": float(tax_in_slab),
        })

        remaining_income -= income_in_slab

    return total_tax, breakdown


def calculate_surcharge(base_tax: Decimal, total_income: Decimal) -> Decimal:
    """Calculate surcharge based on income level."""
    surcharge = Decimal(0)

    for threshold in SURCHARGE_THRESHOLDS:
        if total_income >= threshold["min"]:
            surcharge = base_tax * Decimal(str(threshold["rate"]))
            break

    return surcharge


def calculate_cess(base_tax: Decimal, surcharge: Decimal) -> Decimal:
    """Calculate health and education cess."""
    return (base_tax + surcharge) * Decimal(str(CESS_RATE))


def calculate_tax_old_regime(
    gross_income: Decimal,
    deductions: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate tax under old regime.

    Args:
        gross_income: Total gross income
        deductions: Total deductions (if None, uses 0)

    Returns:
        Total tax liability
    """
    if deductions is None:
        deductions = Decimal(0)

    # Apply standard deduction
    income_after_std = gross_income - Decimal(str(STANDARD_DEDUCTION_OLD))

    # Apply other deductions
    taxable_income = max(Decimal(0), income_after_std - deductions)

    # Calculate slab-wise tax
    base_tax, _ = calculate_slab_wise_tax(taxable_income, TAX_SLABS_OLD_REGIME)

    # Calculate surcharge
    surcharge = calculate_surcharge(base_tax, gross_income)

    # Calculate cess
    cess = calculate_cess(base_tax, surcharge)

    # Total tax
    total_tax = base_tax + surcharge + cess

    return total_tax


def calculate_tax_new_regime(gross_income: Decimal) -> Decimal:
    """
    Calculate tax under new regime (no deductions except standard).

    Args:
        gross_income: Total gross income

    Returns:
        Total tax liability
    """
    # Apply standard deduction (new regime)
    taxable_income = max(Decimal(0), gross_income - Decimal(str(STANDARD_DEDUCTION_NEW)))

    # Calculate slab-wise tax
    base_tax, _ = calculate_slab_wise_tax(taxable_income, TAX_SLABS_NEW_REGIME)

    # Calculate surcharge
    surcharge = calculate_surcharge(base_tax, gross_income)

    # Calculate cess
    cess = calculate_cess(base_tax, surcharge)

    # Total tax
    total_tax = base_tax + surcharge + cess

    return total_tax


def calculate_tax_detailed(
    gross_income: Decimal,
    deductions: Dict[str, Decimal],
    regime: TaxRegime
) -> Dict[str, Any]:
    """
    Calculate detailed tax breakdown for a regime.

    Returns:
        Comprehensive tax calculation with all components
    """
    if regime == TaxRegime.OLD:
        standard_deduction = Decimal(str(STANDARD_DEDUCTION_OLD))
        total_deductions = sum(deductions.values())
        slabs = TAX_SLABS_OLD_REGIME
    else:
        standard_deduction = Decimal(str(STANDARD_DEDUCTION_NEW))
        total_deductions = Decimal(0)  # New regime doesn't allow deductions
        slabs = TAX_SLABS_NEW_REGIME

    # Calculate taxable income
    income_after_std = gross_income - standard_deduction
    taxable_income = max(Decimal(0), income_after_std - total_deductions)

    # Slab-wise calculation
    base_tax, slab_breakdown = calculate_slab_wise_tax(taxable_income, slabs)

    # Surcharge
    surcharge = calculate_surcharge(base_tax, gross_income)

    # Cess
    cess = calculate_cess(base_tax, surcharge)

    # Total tax
    total_tax = base_tax + surcharge + cess

    # Effective tax rate
    effective_rate = (total_tax / gross_income * 100) if gross_income > 0 else Decimal(0)

    return {
        "regime": regime.value,
        "gross_income": float(gross_income),
        "standard_deduction": float(standard_deduction),
        "other_deductions": float(total_deductions),
        "deduction_breakdown": {k: float(v) for k, v in deductions.items() if v > 0} if regime == TaxRegime.OLD else {},
        "taxable_income": float(taxable_income),
        "base_tax": float(base_tax),
        "surcharge": float(surcharge),
        "cess": float(cess),
        "total_tax": float(total_tax),
        "effective_tax_rate": float(effective_rate),
        "slab_breakdown": slab_breakdown,
        "post_tax_income": float(gross_income - total_tax),
    }


def compare_tax_regimes(
    gross_income: Decimal,
    deductions: Dict[str, Decimal]
) -> Dict[str, Any]:
    """
    Compare old vs new tax regime and recommend the better option.

    Returns:
        Detailed comparison with recommendation
    """
    old_regime_calc = calculate_tax_detailed(gross_income, deductions, TaxRegime.OLD)
    new_regime_calc = calculate_tax_detailed(gross_income, deductions, TaxRegime.NEW)

    old_tax = Decimal(str(old_regime_calc["total_tax"]))
    new_tax = Decimal(str(new_regime_calc["total_tax"]))

    savings = abs(old_tax - new_tax)
    best_regime = TaxRegime.OLD if old_tax < new_tax else TaxRegime.NEW

    # Determine reasoning
    if best_regime == TaxRegime.OLD:
        reason = f"Your deductions of ₹{old_regime_calc['other_deductions']:,.0f} make the old regime more beneficial."
    else:
        reason = "Lower tax slabs in new regime outweigh your deductions."

    return {
        "old_regime": old_regime_calc,
        "new_regime": new_regime_calc,
        "recommended_regime": best_regime.value,
        "savings_amount": float(savings),
        "savings_percentage": float((savings / max(old_tax, new_tax) * 100)) if max(old_tax, new_tax) > 0 else 0,
        "reason": reason,
    }


def calculate_effective_tax_rate(
    gross_income: Decimal,
    total_tax: Decimal
) -> Decimal:
    """Calculate effective tax rate as percentage of gross income."""
    if gross_income <= 0:
        return Decimal(0)
    return (total_tax / gross_income) * 100


def simulate_tax_scenarios(
    current_income: Decimal,
    deductions: Dict[str, Decimal],
    regime: TaxRegime
) -> List[Dict[str, Any]]:
    """
    Simulate various tax scenarios.

    Returns:
        List of scenario simulations with outcomes
    """
    scenarios = []

    # Current baseline
    current_tax = calculate_tax_detailed(current_income, deductions, regime)

    # Scenario 1: Income increase by 10%
    increased_income = current_income * Decimal("1.10")
    increased_calc = calculate_tax_detailed(increased_income, deductions, regime)
    scenarios.append({
        "scenario": "Income +10%",
        "description": f"If your income increases to ₹{float(increased_income):,.0f}",
        "new_income": float(increased_income),
        "new_tax": float(increased_calc["total_tax"]),
        "tax_increase": float(increased_calc["total_tax"] - current_tax["total_tax"]),
        "effective_rate": increased_calc["effective_tax_rate"],
    })

    # Scenario 2: Income decrease by 10%
    decreased_income = current_income * Decimal("0.90")
    decreased_calc = calculate_tax_detailed(decreased_income, deductions, regime)
    scenarios.append({
        "scenario": "Income -10%",
        "description": f"If your income decreases to ₹{float(decreased_income):,.0f}",
        "new_income": float(decreased_income),
        "new_tax": float(decreased_calc["total_tax"]),
        "tax_decrease": float(current_tax["total_tax"] - decreased_calc["total_tax"]),
        "effective_rate": decreased_calc["effective_tax_rate"],
    })

    # Scenario 3: Additional ₹50k investment (old regime only)
    if regime == TaxRegime.OLD:
        additional_deduction = Decimal("50000")
        new_deductions = deductions.copy()
        new_deductions["80C"] = new_deductions.get("80C", Decimal(0)) + additional_deduction
        extra_inv_calc = calculate_tax_detailed(current_income, new_deductions, regime)
        scenarios.append({
            "scenario": "Additional ₹50k Investment",
            "description": "If you invest ₹50,000 more in 80C",
            "new_income": float(current_income),
            "new_tax": float(extra_inv_calc["total_tax"]),
            "tax_saved": float(current_tax["total_tax"] - extra_inv_calc["total_tax"]),
            "effective_rate": extra_inv_calc["effective_tax_rate"],
        })

    # Scenario 4: Switch regime
    other_regime = TaxRegime.NEW if regime == TaxRegime.OLD else TaxRegime.OLD
    switched_calc = calculate_tax_detailed(
        current_income,
        deductions if other_regime == TaxRegime.OLD else {},
        other_regime
    )
    scenarios.append({
        "scenario": f"Switch to {other_regime.value.title()} Regime",
        "description": f"If you switch from {regime.value} to {other_regime.value} regime",
        "new_income": float(current_income),
        "new_tax": float(switched_calc["total_tax"]),
        "tax_difference": float(switched_calc["total_tax"] - current_tax["total_tax"]),
        "effective_rate": switched_calc["effective_tax_rate"],
    })

    return scenarios


def calculate_tax_stress(
    gross_income: Decimal,
    total_tax: Decimal,
    monthly_expenses: Decimal
) -> Dict[str, Any]:
    """
    Analyze tax burden and financial stress.

    Returns:
        Tax stress metrics and severity flags
    """
    # Tax as % of income
    tax_percentage = (total_tax / gross_income * 100) if gross_income > 0 else Decimal(0)

    # Post-tax income
    post_tax_income = gross_income - total_tax

    # Annual expenses
    annual_expenses = monthly_expenses * 12

    # Post-tax savings
    post_tax_savings = post_tax_income - annual_expenses
    post_tax_savings_rate = (post_tax_savings / post_tax_income * 100) if post_tax_income > 0 else Decimal(0)

    # Monthly tax burden
    monthly_tax = total_tax / 12

    # Stress level determination
    if tax_percentage > 25:
        stress_level = "high"
        stress_message = "Tax burden is very high. Consider tax optimization strategies."
    elif tax_percentage > 15:
        stress_level = "medium"
        stress_message = "Moderate tax burden. Some optimization possible."
    else:
        stress_level = "low"
        stress_message = "Tax burden is manageable."

    return {
        "tax_as_percentage_of_income": float(tax_percentage),
        "post_tax_income": float(post_tax_income),
        "annual_expenses": float(annual_expenses),
        "post_tax_savings": float(post_tax_savings),
        "post_tax_savings_rate": float(post_tax_savings_rate),
        "monthly_tax_burden": float(monthly_tax),
        "stress_level": stress_level,
        "stress_message": stress_message,
    }


def compute_tax_readiness_score(
    income: Dict[str, Decimal],
    deductions: Dict[str, Decimal],
    regime: TaxRegime,
    user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate tax readiness score (0-100).

    Score based on:
    - Deduction utilization
    - Regime optimization
    - Documentation readiness
    - Income stability
    """
    score = 100
    factors = []

    # Factor 1: Deduction utilization (old regime only)
    if regime == TaxRegime.OLD:
        total_deductions = sum(deductions.values())
        max_possible_deductions = Decimal("250000")  # Typical max

        deduction_utilization = (total_deductions / max_possible_deductions * 100) if max_possible_deductions > 0 else Decimal(0)

        if deduction_utilization < 30:
            score -= 25
            factors.append("Low deduction utilization (-25)")
        elif deduction_utilization < 60:
            score -= 10
            factors.append("Moderate deduction utilization (-10)")
        else:
            factors.append("Good deduction utilization (+0)")

    # Factor 2: Regime optimization
    gross_income = income.get("total_income", Decimal(0))
    comparison = compare_tax_regimes(gross_income, deductions)

    if comparison["recommended_regime"] != regime.value:
        score -= 20
        factors.append(f"Not in optimal regime (-20)")
    else:
        factors.append("Optimal regime selected (+0)")

    # Factor 3: Multiple income sources (complexity)
    income_sources = sum(1 for v in income.values() if v > 0 and isinstance(v, Decimal))
    if income_sources > 3:
        score -= 10
        factors.append("Multiple income sources require careful filing (-10)")

    # Factor 4: Documentation (proxy via deductions)
    if regime == TaxRegime.OLD and len([d for d in deductions.values() if d > 0]) >= 3:
        factors.append("Good documentation likely (+0)")
    elif regime == TaxRegime.OLD and len([d for d in deductions.values() if d > 0]) < 2:
        score -= 15
        factors.append("Poor documentation (-15)")

    # Factor 5: High income readiness
    if gross_income > 1000000:
        if sum(deductions.values()) < 100000:
            score -= 15
            factors.append("High income but low planning (-15)")

    score = max(0, min(100, score))

    # Readiness level
    if score >= 80:
        readiness_level = "excellent"
        message = "You're well-prepared for tax filing."
    elif score >= 60:
        readiness_level = "good"
        message = "Mostly ready, some improvements possible."
    elif score >= 40:
        readiness_level = "fair"
        message = "Tax planning needs attention."
    else:
        readiness_level = "poor"
        message = "Significant tax planning required."

    return {
        "score": score,
        "level": readiness_level,
        "message": message,
        "factors": factors,
    }


def estimate_annual_tax(
    income: Optional[Decimal] = None,
    deductions: Optional[Decimal] = None
) -> Decimal:
    """
    Quick tax estimation (used by other modules).

    Args:
        income: Gross annual income (if None, loads from state)
        deductions: Total deductions (if None, loads from state)

    Returns:
        Estimated tax liability
    """
    if income is None or deductions is None:
        state = load_financial_data()
        income_data = get_income_data(state)
        deductions_data = get_deductions(state)

        income = income or income_data.get("total_income", Decimal(0))
        deductions = deductions or sum(deductions_data.values())

    # Estimate using both regimes, return lower
    tax_old = calculate_tax_old_regime(income, deductions)
    tax_new = calculate_tax_new_regime(income)

    return min(tax_old, tax_new)


def get_tax_estimation_report() -> Dict[str, Any]:
    """
    Main public API: Generate comprehensive tax estimation report.

    Returns:
        Complete tax analysis with all components
    """
    # Load data
    state = load_financial_data()
    income = get_income_data(state)
    deductions = get_deductions(state)
    user_profile = get_user_profile(state)

    gross_income = income.get("total_income", Decimal(0))
    preferred_regime = TaxRegime(user_profile.get("preferred_regime", "new"))

    # Get monthly expenses for stress calculation
    monthly_expenses = Decimal(str(state.get("monthly_expenses", 0)))
    if monthly_expenses == 0:
        # Calculate from expense tracker
        expenses = state.get("expenses", [])
        total_exp = sum(Decimal(str(e.get("amount", 0))) for e in expenses)
        monthly_expenses = total_exp

    # Calculate tax for both regimes
    regime_comparison = compare_tax_regimes(gross_income, deductions)

    # Current regime details
    current_regime_calc = calculate_tax_detailed(
        gross_income,
        deductions if preferred_regime == TaxRegime.OLD else {},
        preferred_regime
    )

    # Simulations
    scenarios = simulate_tax_scenarios(gross_income, deductions, preferred_regime)

    # Tax stress
    current_tax = Decimal(str(current_regime_calc["total_tax"]))
    tax_stress = calculate_tax_stress(gross_income, current_tax, monthly_expenses)

    # Readiness score
    readiness = compute_tax_readiness_score(income, deductions, preferred_regime, user_profile)

    # Summary
    summary = {
        "total_income": float(gross_income),
        "current_regime": preferred_regime.value,
        "recommended_regime": regime_comparison["recommended_regime"],
        "current_tax": float(current_tax),
        "potential_savings": regime_comparison["savings_amount"],
        "effective_tax_rate": current_regime_calc["effective_tax_rate"],
        "readiness_score": readiness["score"],
    }

    return {
        "summary": summary,
        "income_breakdown": {k: float(v) for k, v in income.items()},
        "old_regime": regime_comparison["old_regime"],
        "new_regime": regime_comparison["new_regime"],
        "regime_comparison": regime_comparison,
        "best_regime": {
            "regime": regime_comparison["recommended_regime"],
            "tax": regime_comparison["old_regime"]["total_tax"] if regime_comparison["recommended_regime"] == "old" else regime_comparison["new_regime"]["total_tax"],
            "savings": regime_comparison["savings_amount"],
            "reason": regime_comparison["reason"],
        },
        "what_if_scenarios": scenarios,
        "tax_stress": tax_stress,
        "readiness_score": readiness,
        "generated_at": datetime.now().isoformat(),
        "financial_year": get_current_financial_year(),
    }