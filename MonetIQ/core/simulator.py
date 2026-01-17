"""
core/simulator.py

Financial future simulation and what-if intelligence engine.
Provides deterministic, explainable scenario-based financial projections.
"""

from typing import Dict, Any, List, Optional
from copy import deepcopy
import json


def _safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely retrieve value from dictionary.

    Args:
        dictionary: Source dictionary
        key: Key to retrieve
        default: Default value if key not found

    Returns:
        Value or default
    """
    return dictionary.get(key, default)


def _safe_divide(numerator: float, denominator: float) -> float:
    """
    Safely divide two numbers, returning 0 if denominator is 0.

    Args:
        numerator: Number to divide
        denominator: Number to divide by

    Returns:
        Result of division or 0
    """
    return numerator / denominator if denominator != 0 else 0


def _get_total_expenses(state: Dict[str, Any]) -> float:
    """
    Calculate total expenses from state.

    Args:
        state: Financial state

    Returns:
        Total expenses amount
    """
    expenses = _safe_get(state, 'expenses', {})
    total = 0

    for category, expense_list in expenses.items():
        if isinstance(expense_list, list):
            for expense in expense_list:
                total += _safe_get(expense, 'amount', 0)

    return total


def _get_category_total(state: Dict[str, Any], category: str) -> float:
    """
    Get total expenses for a specific category.

    Args:
        state: Financial state
        category: Expense category

    Returns:
        Total for category
    """
    expenses = _safe_get(state, 'expenses', {})
    category_expenses = _safe_get(expenses, category, [])

    total = 0
    if isinstance(category_expenses, list):
        for expense in category_expenses:
            total += _safe_get(expense, 'amount', 0)

    return total


def _calculate_health_score(state: Dict[str, Any]) -> int:
    """
    Calculate financial health score (0-100).

    Args:
        state: Financial state

    Returns:
        Health score between 0-100
    """
    score = 50  # Base score

    income = _safe_get(state, 'income', 0)
    expenses = _get_total_expenses(state)
    balance = _safe_get(state, 'balance', 0)
    debt = _safe_get(state, 'debt', 0)

    # Savings rate impact (+/- 20 points)
    if income > 0:
        savings_rate = _safe_divide(income - expenses, income)
        if savings_rate >= 0.3:
            score += 20
        elif savings_rate >= 0.2:
            score += 15
        elif savings_rate >= 0.1:
            score += 10
        elif savings_rate < 0:
            score -= 20

    # Emergency fund impact (+/- 15 points)
    monthly_expenses = expenses
    if balance >= monthly_expenses * 6:
        score += 15
    elif balance >= monthly_expenses * 3:
        score += 10
    elif balance >= monthly_expenses:
        score += 5
    elif balance < monthly_expenses * 0.5:
        score -= 10

    # Debt impact (+/- 15 points)
    if debt == 0:
        score += 15
    elif debt < income * 2:
        score += 5
    elif debt > income * 5:
        score -= 15
    elif debt > income * 3:
        score -= 10

    return max(0, min(100, score))


def _calculate_stress_index(state: Dict[str, Any]) -> int:
    """
    Calculate financial stress index (0-100, higher = more stress).

    Args:
        state: Financial state

    Returns:
        Stress index between 0-100
    """
    stress = 30  # Base stress

    income = _safe_get(state, 'income', 0)
    expenses = _get_total_expenses(state)
    balance = _safe_get(state, 'balance', 0)
    debt = _safe_get(state, 'debt', 0)

    # Negative savings (high stress)
    if income > 0:
        savings = income - expenses
        if savings < 0:
            stress += 30
        elif savings < income * 0.05:
            stress += 20

    # Low emergency fund
    if balance < expenses:
        stress += 20
    elif balance < expenses * 2:
        stress += 10

    # High debt burden
    if income > 0 and debt > 0:
        debt_to_income = _safe_divide(debt, income * 12)
        if debt_to_income > 0.5:
            stress += 20
        elif debt_to_income > 0.3:
            stress += 10

    # EMI obligations
    emi_total = _get_category_total(state, 'emi')
    if income > 0 and emi_total > 0:
        emi_ratio = _safe_divide(emi_total, income)
        if emi_ratio > 0.5:
            stress += 15
        elif emi_ratio > 0.4:
            stress += 10

    return max(0, min(100, stress))


def _get_goals(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get savings goals from state.

    Args:
        state: Financial state

    Returns:
        List of goals
    """
    return _safe_get(state, 'goals', [])


def _estimate_tax_liability(state: Dict[str, Any]) -> float:
    """
    Estimate annual tax liability based on income.
    Uses simplified Indian tax slabs (old regime as example).

    Args:
        state: Financial state

    Returns:
        Estimated annual tax
    """
    annual_income = _safe_get(state, 'income', 0) * 12

    # Simplified tax calculation (old regime)
    tax = 0

    if annual_income <= 250000:
        tax = 0
    elif annual_income <= 500000:
        tax = (annual_income - 250000) * 0.05
    elif annual_income <= 1000000:
        tax = 12500 + (annual_income - 500000) * 0.20
    else:
        tax = 12500 + 100000 + (annual_income - 1000000) * 0.30

    # Add 4% cess
    tax = tax * 1.04

    return tax


def _calculate_tax_savings(state: Dict[str, Any], investment: float) -> float:
    """
    Calculate tax savings from investment.

    Args:
        state: Financial state
        investment: Investment amount

    Returns:
        Tax saved
    """
    annual_income = _safe_get(state, 'income', 0) * 12

    # Determine tax rate based on income
    if annual_income <= 250000:
        tax_rate = 0
    elif annual_income <= 500000:
        tax_rate = 0.05
    elif annual_income <= 1000000:
        tax_rate = 0.20
    else:
        tax_rate = 0.30

    # Max 80C deduction
    max_deduction = min(investment, 150000)

    # Tax saved (with cess)
    tax_saved = max_deduction * tax_rate * 1.04

    return tax_saved


def _deep_clone_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a deep copy of state for simulation without affecting original.

    Args:
        state: Original financial state

    Returns:
        Deep copy of state
    """
    return deepcopy(state)


def _extract_baseline_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract current financial metrics as baseline.

    Args:
        state: Current financial state

    Returns:
        Dictionary of baseline metrics
    """
    income = _safe_get(state, 'income', 0)
    expenses = _get_total_expenses(state)
    savings = income - expenses
    health_score = _calculate_health_score(state)
    stress_index = _calculate_stress_index(state)

    return {
        'income': income,
        'total_expenses': expenses,
        'monthly_savings': savings,
        'savings_rate': _safe_divide(savings, income) * 100 if income > 0 else 0,
        'health_score': health_score,
        'stress_index': stress_index,
        'balance': _safe_get(state, 'balance', 0),
        'debt': _safe_get(state, 'debt', 0)
    }


def simulate_income_change(state: Dict[str, Any], delta: float) -> Dict[str, Any]:
    """
    Simulate income increase or decrease.

    Args:
        state: Current financial state
        delta: Income change (positive for increase, negative for decrease)

    Returns:
        Simulation results with before/after comparison
    """
    before = _extract_baseline_metrics(state)
    sim_state = _deep_clone_state(state)

    # Apply income change
    current_income = _safe_get(sim_state, 'income', 0)
    new_income = max(0, current_income + delta)
    sim_state['income'] = new_income

    after = _extract_baseline_metrics(sim_state)

    warnings = []
    recommendations = []

    # Analyze impact
    savings_change = after['monthly_savings'] - before['monthly_savings']
    health_change = after['health_score'] - before['health_score']
    stress_change = after['stress_index'] - before['stress_index']

    if new_income < before['total_expenses']:
        warnings.append("Warning: New income insufficient to cover current expenses")
        recommendations.append("Consider reducing discretionary spending immediately")

    if delta < 0 and after['monthly_savings'] < 0:
        warnings.append("Critical: Negative savings with reduced income")
        recommendations.append("Emergency budget cuts required")

    if delta > 0 and savings_change > 0:
        recommendations.append(f"Additional ₹{savings_change:.2f}/month available for goals or emergency fund")
        recommendations.append("Consider increasing retirement/goal contributions proportionally")

    return {
        'summary': {
            'scenario': 'Income Change',
            'delta': delta,
            'new_income': new_income,
            'change_percentage': _safe_divide(delta, current_income) * 100 if current_income > 0 else 0
        },
        'before_metrics': before,
        'after_metrics': after,
        'impact': {
            'savings_change': savings_change,
            'health_score_change': health_change,
            'stress_index_change': stress_change,
            'savings_rate_change': after['savings_rate'] - before['savings_rate']
        },
        'warnings': warnings,
        'recommendations': recommendations
    }


def simulate_expense_change(state: Dict[str, Any], category: str, delta: float) -> Dict[str, Any]:
    """
    Simulate expense increase or decrease in specific category.

    Args:
        state: Current financial state
        category: Expense category to modify
        delta: Expense change (positive for increase, negative for decrease)

    Returns:
        Simulation results with affordability analysis
    """
    before = _extract_baseline_metrics(state)
    sim_state = _deep_clone_state(state)

    # Get current category expenses
    expenses = _safe_get(sim_state, 'expenses', {})
    category_expenses = _safe_get(expenses, category, [])

    # Calculate current category total
    current_category_total = sum(_safe_get(exp, 'amount', 0) for exp in category_expenses)

    # Apply change by adding a simulated expense entry
    if delta != 0:
        sim_expense = {
            'amount': delta,
            'category': category,
            'description': f'Simulated change in {category}',
            'date': 'simulation'
        }
        if isinstance(category_expenses, list):
            category_expenses.append(sim_expense)
        else:
            category_expenses = [sim_expense]
        expenses[category] = category_expenses
        sim_state['expenses'] = expenses

    after = _extract_baseline_metrics(sim_state)

    warnings = []
    recommendations = []

    # Analyze impact
    savings_change = after['monthly_savings'] - before['monthly_savings']
    affordability_ratio = _safe_divide(after['total_expenses'], after['income']) if after['income'] > 0 else 1

    if delta > 0:
        if after['monthly_savings'] < 0:
            warnings.append(f"Critical: {category} increase causes negative monthly savings")
            recommendations.append(f"Cannot afford ₹{delta:.2f} increase in {category} with current income")
        elif after['monthly_savings'] < before['monthly_savings'] * 0.3:
            warnings.append(f"Warning: {category} increase significantly impacts savings capacity")
            recommendations.append(f"Consider reducing other discretionary expenses to offset {category} increase")

        if affordability_ratio > 0.8:
            warnings.append(f"High expense ratio: {affordability_ratio*100:.1f}% of income")

    if delta < 0:
        recommendations.append(f"Reducing {category} by ₹{abs(delta):.2f} frees up ₹{abs(savings_change):.2f} for savings/goals")
        if before['stress_index'] > 60:
            recommendations.append("Use savings to build emergency fund and reduce financial stress")

    return {
        'summary': {
            'scenario': 'Expense Change',
            'category': category,
            'delta': delta,
            'new_category_total': current_category_total + delta,
            'change_percentage': _safe_divide(delta, current_category_total) * 100 if current_category_total > 0 else 0
        },
        'before_metrics': before,
        'after_metrics': after,
        'impact': {
            'savings_change': savings_change,
            'health_score_change': after['health_score'] - before['health_score'],
            'stress_index_change': after['stress_index'] - before['stress_index'],
            'affordability_ratio': affordability_ratio
        },
        'warnings': warnings,
        'recommendations': recommendations
    }


def simulate_savings_adjustment(state: Dict[str, Any], delta: float) -> Dict[str, Any]:
    """
    Simulate adjustment to monthly savings target.

    Args:
        state: Current financial state
        delta: Savings change (positive for increase, negative for decrease)

    Returns:
        Simulation results with feasibility analysis
    """
    before = _extract_baseline_metrics(state)

    # Target savings calculation
    target_savings = before['monthly_savings'] + delta
    required_expense_reduction = -delta if delta > 0 else 0

    warnings = []
    recommendations = []

    # Feasibility check
    if delta > 0:
        if target_savings > before['income']:
            warnings.append("Impossible: Target savings exceeds total income")
            recommendations.append("Set realistic savings target based on income")
        elif required_expense_reduction > before['total_expenses'] * 0.5:
            warnings.append("Extremely difficult: Requires cutting expenses by >50%")
            recommendations.append("Consider increasing income or setting more gradual savings target")
        else:
            recommendations.append(f"To save additional ₹{delta:.2f}/month, reduce expenses by ₹{delta:.2f}")

            # Suggest categories to cut
            expenses = _safe_get(state, 'expenses', {})
            discretionary_categories = ['entertainment', 'shopping', 'dining', 'lifestyle']
            for cat in discretionary_categories:
                cat_total = _get_category_total(state, cat)
                if cat_total > 0:
                    recommendations.append(f"  • Consider reducing {cat}: currently ₹{cat_total:.2f}/month")

    if delta < 0:
        warnings.append("Reducing savings target decreases financial security")
        recommendations.append("Only reduce savings if absolutely necessary for essential expenses")

    # Calculate goal impact
    goals = _get_goals(state)
    goal_impacts = []

    for goal in goals:
        goal_target = _safe_get(goal, 'target_amount', 0)
        goal_saved = _safe_get(goal, 'current_amount', 0)
        remaining = goal_target - goal_saved

        if remaining > 0 and target_savings > 0:
            months_to_goal = _safe_divide(remaining, target_savings)
            goal_impacts.append({
                'goal_name': _safe_get(goal, 'name', 'Unknown'),
                'months_to_complete': months_to_goal,
                'impact': 'faster' if delta > 0 else 'slower'
            })

    return {
        'summary': {
            'scenario': 'Savings Adjustment',
            'delta': delta,
            'target_savings': target_savings,
            'required_expense_reduction': required_expense_reduction
        },
        'before_metrics': before,
        'after_metrics': {
            'monthly_savings': target_savings,
            'savings_rate': _safe_divide(target_savings, before['income']) * 100 if before['income'] > 0 else 0
        },
        'impact': {
            'feasible': target_savings <= before['income'] and required_expense_reduction <= before['total_expenses'],
            'goal_impacts': goal_impacts
        },
        'warnings': warnings,
        'recommendations': recommendations
    }


def simulate_new_emi(state: Dict[str, Any], emi_amount: float) -> Dict[str, Any]:
    """
    Simulate addition of new fixed monthly obligation (EMI/loan).

    Args:
        state: Current financial state
        emi_amount: Monthly EMI amount to add

    Returns:
        Simulation results with debt pressure analysis
    """
    before = _extract_baseline_metrics(state)
    sim_state = _deep_clone_state(state)

    # Add EMI as fixed expense
    expenses = _safe_get(sim_state, 'expenses', {})
    emi_category = _safe_get(expenses, 'emi', [])

    if not isinstance(emi_category, list):
        emi_category = []

    emi_category.append({
        'amount': emi_amount,
        'category': 'emi',
        'description': 'Simulated new EMI',
        'date': 'simulation'
    })
    expenses['emi'] = emi_category
    sim_state['expenses'] = expenses

    # Update debt (assume EMI represents debt obligation)
    current_debt = _safe_get(sim_state, 'debt', 0)
    sim_state['debt'] = current_debt + (emi_amount * 12)  # Rough annual debt estimate

    after = _extract_baseline_metrics(sim_state)

    warnings = []
    recommendations = []

    # Debt-to-income ratio
    total_emi = _get_category_total(sim_state, 'emi')
    debt_to_income = _safe_divide(total_emi, after['income']) * 100 if after['income'] > 0 else 0

    # Analyze affordability
    if after['monthly_savings'] < 0:
        warnings.append(f"Critical: Cannot afford EMI of ₹{emi_amount:.2f} - causes negative savings")
        recommendations.append("Reject this loan/EMI - not affordable with current income")
    elif debt_to_income > 50:
        warnings.append(f"Dangerous: EMI obligations consume {debt_to_income:.1f}% of income")
        recommendations.append("High debt burden - avoid taking additional loans")
    elif debt_to_income > 40:
        warnings.append(f"High debt pressure: {debt_to_income:.1f}% of income")
        recommendations.append("Consider smaller loan amount or longer tenure")
    elif after['monthly_savings'] < before['monthly_savings'] * 0.5:
        warnings.append("EMI significantly reduces savings capacity")
        recommendations.append("Ensure emergency fund is in place before taking this loan")
    else:
        recommendations.append(f"EMI is affordable but reduces monthly savings by ₹{emi_amount:.2f}")
        recommendations.append("Maintain emergency fund and avoid additional debt")

    return {
        'summary': {
            'scenario': 'New EMI Addition',
            'emi_amount': emi_amount,
            'total_emi_obligations': total_emi,
            'debt_to_income_ratio': debt_to_income
        },
        'before_metrics': before,
        'after_metrics': after,
        'impact': {
            'savings_reduction': before['monthly_savings'] - after['monthly_savings'],
            'health_score_change': after['health_score'] - before['health_score'],
            'stress_index_change': after['stress_index'] - before['stress_index'],
            'affordable': after['monthly_savings'] >= 0
        },
        'warnings': warnings,
        'recommendations': recommendations
    }


def simulate_goal_timeline(state: Dict[str, Any], goal_id: str) -> Dict[str, Any]:
    """
    Simulate early or delayed goal completion.

    Args:
        state: Current financial state
        goal_id: ID of goal to simulate

    Returns:
        Simulation results with timeline analysis
    """
    goals = _get_goals(state)
    target_goal = None

    for goal in goals:
        if _safe_get(goal, 'id', '') == goal_id:
            target_goal = goal
            break

    if not target_goal:
        return {
            'summary': {'error': f'Goal {goal_id} not found'},
            'before_metrics': {},
            'after_metrics': {},
            'impact': {},
            'warnings': [f'Goal {goal_id} does not exist'],
            'recommendations': ['Create the goal first before simulating timeline']
        }

    before = _extract_baseline_metrics(state)

    goal_name = _safe_get(target_goal, 'name', 'Unknown Goal')
    target_amount = _safe_get(target_goal, 'target_amount', 0)
    current_amount = _safe_get(target_goal, 'current_amount', 0)
    remaining = target_amount - current_amount

    warnings = []
    recommendations = []

    # Calculate timelines with different contribution rates
    current_savings = before['monthly_savings']

    scenarios = {}

    if current_savings > 0:
        # Conservative (30% of savings)
        conservative_contrib = current_savings * 0.3
        conservative_months = _safe_divide(remaining, conservative_contrib) if conservative_contrib > 0 else 999

        # Moderate (50% of savings)
        moderate_contrib = current_savings * 0.5
        moderate_months = _safe_divide(remaining, moderate_contrib) if moderate_contrib > 0 else 999

        # Aggressive (80% of savings)
        aggressive_contrib = current_savings * 0.8
        aggressive_months = _safe_divide(remaining, aggressive_contrib) if aggressive_contrib > 0 else 999

        scenarios = {
            'conservative': {
                'monthly_contribution': conservative_contrib,
                'months_to_complete': conservative_months,
                'years': conservative_months / 12
            },
            'moderate': {
                'monthly_contribution': moderate_contrib,
                'months_to_complete': moderate_months,
                'years': moderate_months / 12
            },
            'aggressive': {
                'monthly_contribution': aggressive_contrib,
                'months_to_complete': aggressive_months,
                'years': aggressive_months / 12
            }
        }

        recommendations.append(f"To achieve {goal_name} (₹{target_amount:.2f}):")
        recommendations.append(f"  • Conservative: ₹{conservative_contrib:.2f}/month → {conservative_months:.0f} months ({conservative_months/12:.1f} years)")
        recommendations.append(f"  • Moderate: ₹{moderate_contrib:.2f}/month → {moderate_months:.0f} months ({moderate_months/12:.1f} years)")
        recommendations.append(f"  • Aggressive: ₹{aggressive_contrib:.2f}/month → {aggressive_months:.0f} months ({aggressive_months/12:.1f} years)")
    else:
        warnings.append("No monthly savings available for goal contributions")
        recommendations.append("Increase income or reduce expenses to start saving toward goals")

    return {
        'summary': {
            'scenario': 'Goal Timeline Analysis',
            'goal_name': goal_name,
            'target_amount': target_amount,
            'current_amount': current_amount,
            'remaining_amount': remaining
        },
        'before_metrics': before,
        'after_metrics': scenarios,
        'impact': {
            'achievable': current_savings > 0,
            'scenarios': scenarios
        },
        'warnings': warnings,
        'recommendations': recommendations
    }


def simulate_tax_impact(state: Dict[str, Any], tax_saving_investment: float) -> Dict[str, Any]:
    """
    Simulate tax savings through investments.

    Args:
        state: Current financial state
        tax_saving_investment: Amount to invest in tax-saving instruments

    Returns:
        Simulation results with tax vs cash flow analysis
    """
    before = _extract_baseline_metrics(state)

    # Calculate current tax liability
    annual_income = before['income'] * 12
    current_tax = _estimate_tax_liability(state)

    # Calculate tax savings (assuming 80C deductions)
    max_80c_deduction = 150000  # Standard limit
    applicable_investment = min(tax_saving_investment, max_80c_deduction)
    tax_saved = _calculate_tax_savings(state, applicable_investment)

    # Monthly impact
    monthly_investment = tax_saving_investment / 12
    monthly_tax_benefit = tax_saved / 12
    net_monthly_cost = monthly_investment - monthly_tax_benefit

    warnings = []
    recommendations = []

    # Affordability check
    if net_monthly_cost > before['monthly_savings']:
        warnings.append(f"Tax-saving investment of ₹{monthly_investment:.2f}/month exceeds current savings")
        recommendations.append("Reduce investment amount or increase savings capacity")
    elif net_monthly_cost > before['monthly_savings'] * 0.7:
        warnings.append("Investment significantly impacts available savings")
        recommendations.append("Ensure emergency fund is in place before locking funds")
    else:
        recommendations.append(f"Tax-saving investment is affordable with net cost of ₹{net_monthly_cost:.2f}/month")
        recommendations.append(f"Annual tax benefit: ₹{tax_saved:.2f}")

    if tax_saving_investment > max_80c_deduction:
        recommendations.append(f"Only ₹{max_80c_deduction:.2f} eligible for 80C deduction")
        recommendations.append("Consider other tax-saving instruments for excess amount")

    return {
        'summary': {
            'scenario': 'Tax Saving Investment',
            'annual_investment': tax_saving_investment,
            'monthly_investment': monthly_investment,
            'tax_benefit': tax_saved,
            'monthly_tax_benefit': monthly_tax_benefit
        },
        'before_metrics': {
            'annual_income': annual_income,
            'estimated_tax': current_tax,
            'monthly_savings': before['monthly_savings']
        },
        'after_metrics': {
            'tax_after_savings': current_tax - tax_saved,
            'net_monthly_cost': net_monthly_cost,
            'savings_remaining': before['monthly_savings'] - net_monthly_cost
        },
        'impact': {
            'tax_savings': tax_saved,
            'net_benefit_ratio': _safe_divide(tax_saved, tax_saving_investment) * 100,
            'affordable': net_monthly_cost <= before['monthly_savings']
        },
        'warnings': warnings,
        'recommendations': recommendations
    }


def run_simulation(state: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main simulation interface - routes to appropriate simulation based on type.

    Args:
        state: Current financial state
        scenario: Simulation scenario specification
            {
                "type": "income | expense | emi | savings | tax | goal",
                "parameters": {...}
            }

    Returns:
        Comprehensive simulation results
    """
    scenario_type = _safe_get(scenario, 'type', '').lower()
    parameters = _safe_get(scenario, 'parameters', {})

    # Route to appropriate simulation
    if scenario_type == 'income':
        delta = _safe_get(parameters, 'delta', 0)
        return simulate_income_change(state, delta)

    elif scenario_type == 'expense':
        category = _safe_get(parameters, 'category', 'miscellaneous')
        delta = _safe_get(parameters, 'delta', 0)
        return simulate_expense_change(state, category, delta)

    elif scenario_type == 'emi':
        emi_amount = _safe_get(parameters, 'emi_amount', 0)
        return simulate_new_emi(state, emi_amount)

    elif scenario_type == 'savings':
        delta = _safe_get(parameters, 'delta', 0)
        return simulate_savings_adjustment(state, delta)

    elif scenario_type == 'tax':
        investment = _safe_get(parameters, 'tax_saving_investment', 0)
        return simulate_tax_impact(state, investment)

    elif scenario_type == 'goal':
        goal_id = _safe_get(parameters, 'goal_id', '')
        return simulate_goal_timeline(state, goal_id)

    else:
        return {
            'summary': {'error': f'Unknown scenario type: {scenario_type}'},
            'before_metrics': {},
            'after_metrics': {},
            'impact': {},
            'warnings': [f'Scenario type "{scenario_type}" not supported'],
            'recommendations': [
                'Supported types: income, expense, emi, savings, tax, goal'
            ]
        }


def compare_scenarios(state: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare multiple simulation scenarios side-by-side.

    Args:
        state: Current financial state
        scenarios: List of scenario specifications

    Returns:
        Comparative analysis of all scenarios
    """
    results = []

    for i, scenario in enumerate(scenarios):
        result = run_simulation(state, scenario)
        result['scenario_index'] = i
        result['scenario_name'] = _safe_get(scenario, 'name', f'Scenario {i+1}')
        results.append(result)

    # Find best scenario based on health score improvement
    best_scenario = None
    best_health_change = float('-inf')
    for result in results:
        health_change = _safe_get(result.get('impact', {}), 'health_score_change', 0)
    if health_change > best_health_change:
        best_health_change = health_change
    best_scenario = result.get('scenario_name')

    return {
        'scenarios': results,
        'comparison': {
            'best_scenario': best_scenario,
            'best_health_improvement': best_health_change
        },
        'recommendations': [
            f'Best option: {best_scenario}' if best_scenario else 'No clear winner',
            'Compare stress index and savings impact before deciding'
        ]
    }