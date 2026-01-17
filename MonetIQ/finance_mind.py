"""
core/expense_tracker.py

Expense Intelligence Engine for MonetIQ
Tracks, categorizes, and analyzes user transactions with behavioral intelligence.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import re

# ============================================================================
# CATEGORIZATION RULES ENGINE
# ============================================================================

CATEGORY_RULES = {
    "Food": {
        "keywords": [
            "swiggy", "zomato", "restaurant", "cafe", "food", "pizza", "burger",
            "mcdonald", "kfc", "domino", "subway", "starbucks", "cafe", "bakery",
            "meals", "dining", "breakfast", "lunch", "dinner", "grocery", "supermarket",
            "dmart", "bigbasket", "blinkit", "zepto", "instamart", "dunzo"
        ],
        "amount_range": None
    },
    "Transport": {
        "keywords": [
            "uber", "ola", "rapido", "metro", "bus", "taxi", "fuel", "petrol",
            "diesel", "parking", "toll", "fastag", "transport", "travel", "ride",
            "auto", "rickshaw", "cab", "railway", "irctc"
        ],
        "amount_range": None
    },
    "Shopping": {
        "keywords": [
            "amazon", "flipkart", "myntra", "ajio", "shopping", "mall", "store",
            "purchase", "buy", "meesho", "shoppers", "lifestyle", "reliance", "trends",
            "clothing", "fashion", "shoes", "accessories"
        ],
        "amount_range": None
    },
    "Rent": {
        "keywords": [
            "rent", "lease", "landlord", "housing", "accommodation", "flat",
            "apartment", "society", "maintenance"
        ],
        "amount_range": (5000, 100000)
    },
    "Utilities": {
        "keywords": [
            "electricity", "water", "gas", "broadband", "internet", "wifi",
            "mobile", "recharge", "bill", "paytm", "phonepe", "gpay", "airtel",
            "jio", "vodafone", "bsnl", "utility"
        ],
        "amount_range": None
    },
    "Entertainment": {
        "keywords": [
            "movie", "cinema", "netflix", "prime", "hotstar", "spotify", "youtube",
            "gaming", "game", "entertainment", "pvr", "inox", "theatre", "concert",
            "event", "ticket", "bookmyshow"
        ],
        "amount_range": None
    },
    "Healthcare": {
        "keywords": [
            "hospital", "clinic", "doctor", "medical", "pharmacy", "medicine",
            "health", "apollo", "practo", "1mg", "pharmeasy", "netmeds", "lab",
            "diagnostic", "insurance", "healthcare"
        ],
        "amount_range": None
    },
    "Education": {
        "keywords": [
            "school", "college", "university", "course", "tuition", "coaching",
            "education", "learning", "udemy", "coursera", "books", "study",
            "training", "workshop", "seminar", "fees"
        ],
        "amount_range": None
    },
    "Subscriptions": {
        "keywords": [
            "subscription", "membership", "prime", "netflix", "spotify", "gym",
            "club", "magazine", "newspaper", "recurring", "monthly", "annual"
        ],
        "amount_range": (99, 5000)
    },
    "Savings": {
        "keywords": [
            "savings", "investment", "fd", "mutual fund", "sip", "stocks",
            "deposit", "zerodha", "groww", "upstox", "gold", "ppf", "nps"
        ],
        "amount_range": None
    }
}


def auto_categorize_transaction(transaction: Dict) -> str:
    """
    Intelligently categorize a transaction based on description, amount, and patterns.

    Args:
        transaction: Transaction dictionary with 'description' and 'amount' keys

    Returns:
        Category name as string
    """
    description = transaction.get("description", "").lower().strip()
    amount = transaction.get("amount", 0)

    if not description:
        return "Other"

    # Score each category
    category_scores = {}

    for category, rules in CATEGORY_RULES.items():
        score = 0

        # Keyword matching
        for keyword in rules["keywords"]:
            if keyword in description:
                score += 10
                # Bonus for exact match
                if description == keyword:
                    score += 20

        # Amount range matching
        if rules["amount_range"]:
            min_amt, max_amt = rules["amount_range"]
            if min_amt <= amount <= max_amt:
                score += 5

        category_scores[category] = score

    # Get best match
    best_category = max(category_scores, key=category_scores.get)
    best_score = category_scores[best_category]

    # Only return if confidence is reasonable
    if best_score >= 10:
        return best_category

    return "Other"


# ============================================================================
# TRANSACTION MANAGEMENT
# ============================================================================

def add_transaction(state: Dict, transaction: Dict) -> Dict:
    """
    Add a new transaction to state with auto-categorization and validation.

    Args:
        state: Application state dictionary
        transaction: Transaction data

    Returns:
        Updated state dictionary
    """
    # Initialize transactions if not exists
    if "transactions" not in state:
        state["transactions"] = []

    # Assign unique ID if not provided
    if "id" not in transaction or not transaction["id"]:
        transaction["id"] = str(uuid.uuid4())

    # Validate and set date
    if "date" not in transaction or not transaction["date"]:
        transaction["date"] = datetime.now().strftime("%Y-%m-%d")

    # Ensure amount is float
    try:
        transaction["amount"] = float(transaction.get("amount", 0))
    except (ValueError, TypeError):
        transaction["amount"] = 0.0

    # Set description
    if "description" not in transaction:
        transaction["description"] = "Unknown"

    # Auto-categorize if missing
    if "category" not in transaction or not transaction["category"]:
        transaction["category"] = auto_categorize_transaction(transaction)

    # Set default source
    if "source" not in transaction:
        transaction["source"] = "Other"

    # Initialize recurring flag
    if "is_recurring" not in transaction:
        transaction["is_recurring"] = False

    # Add to state
    state["transactions"].append(transaction)

    return state


def get_all_expenses(state: Dict) -> List[Dict]:
    """
    Get all valid expense transactions.

    Args:
        state: Application state dictionary

    Returns:
        List of expense transactions
    """
    if "transactions" not in state:
        return []

    expenses = []
    for txn in state["transactions"]:
        # Validate transaction structure
        if not isinstance(txn, dict):
            continue

        # Ensure required fields exist
        if "amount" not in txn or "date" not in txn:
            continue

        # Filter positive expenses only (negative could be refunds)
        try:
            amount = float(txn["amount"])
            if amount > 0:
                expenses.append(txn)
        except (ValueError, TypeError):
            continue

    return expenses


def get_expenses_by_category(state: Dict) -> Dict[str, float]:
    """
    Calculate total expenses grouped by category.

    Args:
        state: Application state dictionary

    Returns:
        Dictionary mapping category to total amount
    """
    expenses = get_all_expenses(state)

    category_totals = defaultdict(float)

    for expense in expenses:
        category = expense.get("category", "Other")
        amount = float(expense.get("amount", 0))
        category_totals[category] += amount

    return dict(category_totals)


# ============================================================================
# TEMPORAL ANALYSIS
# ============================================================================

def monthly_expense_summary(state: Dict, year: int, month: int) -> Dict:
    """
    Generate comprehensive monthly expense summary.

    Args:
        state: Application state dictionary
        year: Target year
        month: Target month (1-12)

    Returns:
        Dictionary with monthly insights
    """
    expenses = get_all_expenses(state)

    # Filter for target month
    monthly_expenses = []
    for expense in expenses:
        try:
            txn_date = datetime.strptime(expense["date"], "%Y-%m-%d")
            if txn_date.year == year and txn_date.month == month:
                monthly_expenses.append(expense)
        except (ValueError, KeyError):
            continue

    if not monthly_expenses:
        return {
            "total_expenses": 0.0,
            "category_breakdown": {},
            "average_daily_spend": 0.0,
            "highest_spending_category": None,
            "expense_vs_income_ratio": 0.0,
            "transaction_count": 0
        }

    # Calculate totals
    total_expenses = sum(float(e.get("amount", 0)) for e in monthly_expenses)

    # Category breakdown
    category_breakdown = defaultdict(float)
    for expense in monthly_expenses:
        category = expense.get("category", "Other")
        amount = float(expense.get("amount", 0))
        category_breakdown[category] += amount

    # Days in month
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    average_daily_spend = total_expenses / days_in_month

    # Highest spending category
    highest_category = max(category_breakdown, key=category_breakdown.get) if category_breakdown else None

    # Income calculation
    total_income = state.get("monthly_income", 0) or state.get("income", 0) or 0
    expense_vs_income_ratio = (total_expenses / total_income * 100) if total_income > 0 else 0.0

    return {
        "total_expenses": round(total_expenses, 2),
        "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
        "average_daily_spend": round(average_daily_spend, 2),
        "highest_spending_category": highest_category,
        "expense_vs_income_ratio": round(expense_vs_income_ratio, 2),
        "transaction_count": len(monthly_expenses)
    }


# ============================================================================
# BEHAVIORAL INTELLIGENCE
# ============================================================================

def detect_recurring_expenses(state: Dict, similarity_threshold: float = 0.8) -> List[Dict]:
    """
    Detect recurring expenses using pattern recognition.

    Args:
        state: Application state dictionary
        similarity_threshold: Minimum similarity score (0-1)

    Returns:
        List of detected recurring expenses
    """
    expenses = get_all_expenses(state)

    # Group by similar description and amount
    groups = defaultdict(list)

    for expense in expenses:
        # Normalize description
        desc = expense.get("description", "").lower().strip()
        desc_normalized = re.sub(r'[^a-z0-9]', '', desc)

        # Amount bucket (±10% tolerance)
        amount = float(expense.get("amount", 0))
        amount_bucket = round(amount / 100) * 100

        key = f"{desc_normalized[:10]}_{amount_bucket}"
        groups[key].append(expense)

    recurring = []

    for group_key, transactions in groups.items():
        if len(transactions) < 2:
            continue

        # Sort by date
        sorted_txns = sorted(transactions, key=lambda x: x.get("date", ""))

        # Check time gaps
        dates = []
        for txn in sorted_txns:
            try:
                dates.append(datetime.strptime(txn["date"], "%Y-%m-%d"))
            except (ValueError, KeyError):
                continue

        if len(dates) < 2:
            continue

        # Calculate gaps
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

        # Check for regularity (weekly, monthly, etc.)
        avg_gap = sum(gaps) / len(gaps) if gaps else 0

        # Recurring if: 20-40 days (monthly) or 5-9 days (weekly)
        is_regular = (20 <= avg_gap <= 40) or (5 <= avg_gap <= 9)

        if is_regular:
            for txn in sorted_txns:
                txn["is_recurring"] = True
                recurring.append(txn)

    return recurring


def expense_velocity(state: Dict) -> float:
    """
    Calculate current spending velocity (amount per day).

    Args:
        state: Application state dictionary

    Returns:
        Daily spending rate as float
    """
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    expenses = get_all_expenses(state)

    # Filter current month
    current_month_expenses = []
    for expense in expenses:
        try:
            txn_date = datetime.strptime(expense["date"], "%Y-%m-%d")
            if txn_date.year == current_year and txn_date.month == current_month:
                current_month_expenses.append(expense)
        except (ValueError, KeyError):
            continue

    if not current_month_expenses:
        return 0.0

    total_spent = sum(float(e.get("amount", 0)) for e in current_month_expenses)
    days_elapsed = now.day

    velocity = total_spent / days_elapsed if days_elapsed > 0 else 0.0

    return round(velocity, 2)


def top_merchants(state: Dict, n: int = 5) -> List[Tuple[str, float]]:
    """
    Get top spending merchants/descriptions.

    Args:
        state: Application state dictionary
        n: Number of top merchants to return

    Returns:
        List of (merchant, total_amount) tuples
    """
    expenses = get_all_expenses(state)

    merchant_totals = defaultdict(float)

    for expense in expenses:
        merchant = expense.get("description", "Unknown")
        amount = float(expense.get("amount", 0))
        merchant_totals[merchant] += amount

    # Sort by amount
    sorted_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)

    return [(m, round(a, 2)) for m, a in sorted_merchants[:n]]


def expense_trends(state: Dict) -> Dict:
    """
    Analyze spending trends comparing current vs previous month.

    Args:
        state: Application state dictionary

    Returns:
        Dictionary with trend analysis
    """
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Previous month calculation
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    # Get summaries
    current_summary = monthly_expense_summary(state, current_year, current_month)
    previous_summary = monthly_expense_summary(state, prev_year, prev_month)

    current_total = current_summary["total_expenses"]
    previous_total = previous_summary["total_expenses"]

    # Calculate change
    if previous_total > 0:
        percentage_change = ((current_total - previous_total) / previous_total) * 100
    else:
        percentage_change = 100.0 if current_total > 0 else 0.0

    # Determine trend
    if abs(percentage_change) < 5:
        trend = "stable"
    elif percentage_change > 0:
        trend = "increasing"
    else:
        trend = "decreasing"

    return {
        "trend": trend,
        "percentage_change": round(percentage_change, 2),
        "current_month_total": current_total,
        "previous_month_total": previous_total
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_expense_by_id(state: Dict, transaction_id: str) -> Optional[Dict]:
    """
    Retrieve a specific transaction by ID.

    Args:
        state: Application state dictionary
        transaction_id: Transaction ID to find

    Returns:
        Transaction dictionary or None
    """
    expenses = get_all_expenses(state)

    for expense in expenses:
        if expense.get("id") == transaction_id:
            return expense

    return None


def delete_transaction(state: Dict, transaction_id: str) -> Dict:
    """
    Remove a transaction from state.

    Args:
        state: Application state dictionary
        transaction_id: Transaction ID to delete

    Returns:
        Updated state dictionary
    """
    if "transactions" not in state:
        return state

    state["transactions"] = [
        txn for txn in state["transactions"]
        if txn.get("id") != transaction_id
    ]

    return state


def update_transaction(state: Dict, transaction_id: str, updates: Dict) -> Dict:
    """
    Update a transaction with new data.

    Args:
        state: Application state dictionary
        transaction_id: Transaction ID to update
        updates: Dictionary of fields to update

    Returns:
        Updated state dictionary
    """
    if "transactions" not in state:
        return state

    for txn in state["transactions"]:
        if txn.get("id") == transaction_id:
            txn.update(updates)

            # Re-categorize if description changed
            if "description" in updates and "category" not in updates:
                txn["category"] = auto_categorize_transaction(txn)

            break

    return state


def get_category_list() -> List[str]:
    """
    Get list of available categories.

    Returns:
        List of category names
    """
    return list(CATEGORY_RULES.keys()) + ["Other"]


def validate_transaction(transaction: Dict) -> Tuple[bool, str]:
    """
    Validate transaction data structure.

    Args:
        transaction: Transaction dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["amount", "description", "date"]

    for field in required_fields:
        if field not in transaction:
            return False, f"Missing required field: {field}"

    # Validate amount
    try:
        amount = float(transaction["amount"])
        if amount < 0:
            return False, "Amount cannot be negative"
    except (ValueError, TypeError):
        return False, "Invalid amount format"

    # Validate date
    try:
        datetime.strptime(transaction["date"], "%Y-%m-%d")
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD"

    return True, ""

# ============================================================================
# SCORING WEIGHTS CONFIGURATION
# ============================================================================

COMPONENT_WEIGHTS = {
    "savings_rate": 0.25,  # 25% - Income vs Expenses
    "budget_discipline": 0.20,  # 20% - Adherence to budgets
    "expense_stability": 0.15,  # 15% - Volatility control
    "emergency_readiness": 0.20,  # 20% - Emergency fund coverage
    "debt_burden": 0.12,  # 12% - EMI/debt pressure
    "tax_pressure": 0.08  # 8% - Tax planning efficiency
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
    """
    Calculate savings rate score based on income vs expenses.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (score, details_dict)
    """
    try:
        # Import expense tracker functions
        from core.expense_tracker import get_all_expenses, monthly_expense_summary

        # Get current month data
        now = datetime.now()
        summary = monthly_expense_summary(state, now.year, now.month)

        # FIXED: Safely get income (handle dict or number)
        income_data = state.get("monthly_income", 0) or state.get("income", 0) or 0

        # Extract number from dict if needed
        if isinstance(income_data, dict):
            income = income_data.get('monthly', income_data.get('amount', 0))
        else:
            income = income_data

        # Convert to float
        income = float(income) if income else 0.0

        if income <= 0:
            return 0.0, {
                "savings_rate": 0.0,
                "monthly_savings": 0.0,
                "status": "No income data"
            }

        # FIXED: Safely get expenses
        expenses_data = summary.get("total_expenses", 0)
        if isinstance(expenses_data, dict):
            expenses = expenses_data.get('total', expenses_data.get('amount', 0))
        else:
            expenses = expenses_data

        expenses = float(expenses) if expenses else 0.0

        # Calculate savings
        savings = income - expenses
        savings_rate = (savings / income) * 100

        # Score calculation
        # Ideal: 20%+ savings = 100 points
        # 15-20% = 80-100
        # 10-15% = 60-80
        # 5-10% = 40-60
        # 0-5% = 20-40
        # Negative = 0-20

        if savings_rate >= 20:
            score = 100.0
        elif savings_rate >= 15:
            score = 80 + (savings_rate - 15) * 4
        elif savings_rate >= 10:
            score = 60 + (savings_rate - 10) * 4
        elif savings_rate >= 5:
            score = 40 + (savings_rate - 5) * 4
        elif savings_rate >= 0:
            score = 20 + (savings_rate) * 4
        else:
            # Negative savings (overspending)
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
    """
    Calculate budget discipline score based on overspending patterns.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (score, details_dict)
    """
    try:
        # Import overspending detection
        from analytics.overspending import detect_overspending

        # Get overspending data
        overspending_data = detect_overspending(state)

        if not overspending_data:
            # No budget set or no data
            return 70.0, {
                "breach_count": 0,
                "status": "no_budget_set"
            }

        # Count breaches
        breached_categories = overspending_data.get("breached_categories", [])
        total_categories = len(breached_categories) + len(overspending_data.get("safe_categories", []))

        if total_categories == 0:
            return 70.0, {"breach_count": 0, "status": "insufficient_data"}

        breach_count = len(breached_categories)
        breach_percentage = (breach_count / total_categories) * 100

        # Score calculation
        # 0 breaches = 100
        # 1 breach = 85
        # 2 breaches = 70
        # 3+ breaches = declining

        if breach_count == 0:
            score = 100.0
        elif breach_count == 1:
            score = 85.0
        elif breach_count == 2:
            score = 70.0
        else:
            score = max(0, 70 - (breach_count - 2) * 15)

        return score, {
            "breach_count": breach_count,
            "total_categories": total_categories,
            "breach_percentage": round(breach_percentage, 2),
            "breached_categories": [cat["category"] for cat in breached_categories],
            "status": "disciplined" if breach_count <= 1 else "needs_attention"
        }

    except ImportError:
        # Overspending module not available, return neutral score
        return 70.0, {"status": "module_unavailable"}
    except Exception as e:
        return 70.0, {"error": str(e), "status": "calculation_failed"}


def calculate_expense_stability_score(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate expense stability score based on spending volatility.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (score, details_dict)
    """
    try:
        from core.expense_tracker import monthly_expense_summary

        # Get last 3 months of data
        now = datetime.now()
        monthly_totals = []

        for months_back in range(3):
            target_date = now - timedelta(days=months_back * 30)
            summary = monthly_expense_summary(state, target_date.year, target_date.month)

            # FIXED: Safely extract total
            total_data = summary.get("total_expenses", 0)
            if isinstance(total_data, dict):
                total = total_data.get('total', total_data.get('amount', 0))
            else:
                total = total_data

            total = float(total) if total else 0.0

            if total > 0:
                monthly_totals.append(total)

        if len(monthly_totals) < 2:
            return 60.0, {
                "volatility": 0.0,
                "status": "insufficient_data"
            }

        # Calculate coefficient of variation (CV)
        mean_expense = statistics.mean(monthly_totals)
        std_dev = statistics.stdev(monthly_totals) if len(monthly_totals) > 1 else 0

        if mean_expense == 0:
            return 60.0, {"volatility": 0.0, "status": "no_expenses"}

        cv = (std_dev / mean_expense) * 100  # Coefficient of variation as percentage

        # Score calculation
        # CV < 10% = Very stable = 100
        # CV 10-20% = Stable = 80-100
        # CV 20-30% = Moderate = 60-80
        # CV 30-50% = Volatile = 40-60
        # CV > 50% = Highly volatile = 0-40

        if cv < 10:
            score = 100.0
        elif cv < 20:
            score = 80 + (20 - cv)
        elif cv < 30:
            score = 60 + (30 - cv) * 2
        elif cv < 50:
            score = 40 + (50 - cv)
        else:
            score = max(0, 40 - (cv - 50) * 0.5)

        return min(100.0, max(0.0, score)), {
            "volatility_cv": round(cv, 2),
            "mean_expense": round(mean_expense, 2),
            "std_deviation": round(std_dev, 2),
            "months_analyzed": len(monthly_totals),
            "status": "stable" if cv < 20 else "volatile"
        }

    except Exception as e:
        return 60.0, {"error": str(e), "status": "calculation_failed"}


def calculate_emergency_readiness_score(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate emergency readiness based on emergency fund coverage.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (score, details_dict)
    """
    try:
        from core.expense_tracker import monthly_expense_summary

        # FIXED: Safely get emergency fund
        emergency_fund_data = state.get("emergency_fund", 0) or 0
        if isinstance(emergency_fund_data, dict):
            emergency_fund = emergency_fund_data.get('amount', emergency_fund_data.get('total', 0))
        else:
            emergency_fund = emergency_fund_data

        emergency_fund = float(emergency_fund) if emergency_fund else 0.0

        # Get average monthly expense
        now = datetime.now()
        summary = monthly_expense_summary(state, now.year, now.month)

        # FIXED: Safely get monthly expense
        monthly_expense_data = summary.get("total_expenses", 0)
        if isinstance(monthly_expense_data, dict):
            monthly_expense = monthly_expense_data.get('total', monthly_expense_data.get('amount', 0))
        else:
            monthly_expense = monthly_expense_data

        monthly_expense = float(monthly_expense) if monthly_expense else 0.0

        if monthly_expense <= 0:
            return 50.0, {
                "months_coverage": 0.0,
                "emergency_fund": emergency_fund,
                "status": "no_expense_data"
            }

        # Calculate months of coverage
        months_coverage = emergency_fund / monthly_expense

        # Score calculation
        # 6+ months = 100 (ideal)
        # 3-6 months = 70-100
        # 1-3 months = 40-70
        # 0-1 month = 0-40

        if months_coverage >= 6:
            score = 100.0
        elif months_coverage >= 3:
            score = 70 + (months_coverage - 3) * 10
        elif months_coverage >= 1:
            score = 40 + (months_coverage - 1) * 15
        else:
            score = months_coverage * 40

        return min(100.0, max(0.0, score)), {
            "months_coverage": round(months_coverage, 2),
            "emergency_fund": emergency_fund,
            "monthly_expense": monthly_expense,
            "recommended_fund": monthly_expense * 6,
            "status": "excellent" if months_coverage >= 6 else "needs_building"
        }

    except Exception as e:
        return 50.0, {"error": str(e), "status": "calculation_failed"}


def calculate_debt_burden_score(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate debt burden score based on EMI/income ratio.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (score, details_dict)
    """
    try:
        # FIXED: Safely get EMI
        total_emi_data = state.get("monthly_emi", 0) or state.get("emi", 0) or 0
        if isinstance(total_emi_data, dict):
            total_emi = total_emi_data.get('monthly', total_emi_data.get('amount', 0))
        else:
            total_emi = total_emi_data

        total_emi = float(total_emi) if total_emi else 0.0

        # FIXED: Safely get income
        income_data = state.get("monthly_income", 0) or state.get("income", 0) or 0
        if isinstance(income_data, dict):
            income = income_data.get('monthly', income_data.get('amount', 0))
        else:
            income = income_data

        income = float(income) if income else 0.0

        if income <= 0:
            return 50.0, {
                "emi_to_income_ratio": 0.0,
                "status": "no_income_data"
            }

        # Calculate EMI to income ratio
        emi_ratio = (total_emi / income) * 100

        # Score calculation
        # 0% EMI = 100 (no debt)
        # < 20% = 90-100 (healthy)
        # 20-30% = 70-90 (manageable)
        # 30-40% = 50-70 (concerning)
        # 40-50% = 30-50 (risky)
        # > 50% = 0-30 (critical)

        if emi_ratio == 0:
            score = 100.0
        elif emi_ratio < 20:
            score = 90 + (20 - emi_ratio) * 0.5
        elif emi_ratio < 30:
            score = 70 + (30 - emi_ratio) * 2
        elif emi_ratio < 40:
            score = 50 + (40 - emi_ratio) * 2
        elif emi_ratio < 50:
            score = 30 + (50 - emi_ratio) * 2
        else:
            score = max(0, 30 - (emi_ratio - 50))

        return min(100.0, max(0.0, score)), {
            "emi_to_income_ratio": round(emi_ratio, 2),
            "total_emi": total_emi,
            "income": income,
            "status": "healthy" if emi_ratio < 30 else "high_burden"
        }

    except Exception as e:
        return 50.0, {"error": str(e), "status": "calculation_failed"}


def calculate_tax_pressure_score(state: Dict) -> Tuple[float, Dict]:
    """
    Calculate tax pressure score based on tax liability vs income.

    Args:
        state: Application state dictionary

    Returns:
        Tuple of (score, details_dict)
    """
    try:
        # Import tax estimator
        from tax.tax_estimator import estimate_annual_tax

        # Get tax estimate
        tax_data = estimate_annual_tax(state)

        if not tax_data:
            return 70.0, {
                "tax_to_income_ratio": 0.0,
                "status": "no_tax_data"
            }

        # FIXED: Safely get annual tax
        annual_tax_data = tax_data.get("total_tax", 0)
        if isinstance(annual_tax_data, dict):
            annual_tax = annual_tax_data.get('total', annual_tax_data.get('amount', 0))
        else:
            annual_tax = annual_tax_data

        annual_tax = float(annual_tax) if annual_tax else 0.0

        # FIXED: Safely get income
        income_data = state.get("monthly_income", 0) or state.get("income", 0) or 0
        if isinstance(income_data, dict):
            income = income_data.get('monthly', income_data.get('amount', 0))
        else:
            income = income_data

        income = float(income) if income else 0.0

        annual_income = income * 12

        if annual_income <= 0:
            return 70.0, {"status": "no_income_data"}

        # Calculate tax to income ratio
        tax_ratio = (annual_tax / annual_income) * 100

        # Score calculation
        # Lower tax burden (through planning) = better score
        # < 10% = 100 (excellent planning)
        # 10-15% = 85-100
        # 15-20% = 70-85
        # 20-25% = 55-70
        # 25-30% = 40-55
        # > 30% = 0-40

        if tax_ratio < 10:
            score = 100.0
        elif tax_ratio < 15:
            score = 85 + (15 - tax_ratio) * 3
        elif tax_ratio < 20:
            score = 70 + (20 - tax_ratio) * 3
        elif tax_ratio < 25:
            score = 55 + (25 - tax_ratio) * 3
        elif tax_ratio < 30:
            score = 40 + (30 - tax_ratio) * 3
        else:
            score = max(0, 40 - (tax_ratio - 30) * 2)

        return min(100.0, max(0.0, score)), {
            "tax_to_income_ratio": round(tax_ratio, 2),
            "annual_tax": annual_tax,
            "annual_income": annual_income,
            "status": "optimized" if tax_ratio < 20 else "high_pressure"
        }

    except ImportError:
        # Tax module not available
        return 70.0, {"status": "module_unavailable"}
    except Exception as e:
        return 70.0, {"error": str(e), "status": "calculation_failed"}
# ============================================================================
# AGGREGATION & GRADING
# ============================================================================

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