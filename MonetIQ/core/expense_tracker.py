"""
core/expense_tracker.py

Expense Intelligence Engine for MonetIQ
Tracks, categorizes, and analyzes user transactions with behavioral intelligence.

THIS VERSION:
- Preserves ALL features
- Is Streamlit-safe
- Handles dict vs numeric mismatches
- Works with MonetIQ JSON structure
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
import re
import calendar


# =============================================================================
# CATEGORY RULES ENGINE
# =============================================================================

CATEGORY_RULES = {
    "Food": {
        "keywords": [
            "swiggy", "zomato", "restaurant", "cafe", "food", "pizza", "burger",
            "mcdonald", "kfc", "domino", "subway", "starbucks", "bakery",
            "meals", "dining", "breakfast", "lunch", "dinner", "grocery",
            "supermarket", "dmart", "bigbasket", "blinkit", "zepto"
        ],
        "amount_range": None
    },
    "Transport": {
        "keywords": [
            "uber", "ola", "rapido", "metro", "bus", "taxi", "fuel",
            "petrol", "diesel", "parking", "toll", "fastag"
        ],
        "amount_range": None
    },
    "Shopping": {
        "keywords": [
            "amazon", "flipkart", "myntra", "ajio", "shopping",
            "purchase", "meesho", "lifestyle", "reliance"
        ],
        "amount_range": None
    },
    "Rent": {
        "keywords": [
            "rent", "lease", "landlord", "housing",
            "apartment", "society", "maintenance"
        ],
        "amount_range": (5000, 100000)
    },
    "Utilities": {
        "keywords": [
            "electricity", "water", "gas", "broadband",
            "internet", "wifi", "mobile", "recharge", "bill"
        ],
        "amount_range": None
    },
    "Entertainment": {
        "keywords": [
            "movie", "cinema", "netflix", "prime",
            "hotstar", "spotify", "gaming", "bookmyshow"
        ],
        "amount_range": None
    },
    "Healthcare": {
        "keywords": [
            "hospital", "clinic", "doctor", "medical",
            "pharmacy", "apollo", "practo", "1mg"
        ],
        "amount_range": None
    },
    "Education": {
        "keywords": [
            "school", "college", "university",
            "course", "tuition", "education"
        ],
        "amount_range": None
    },
    "Subscriptions": {
        "keywords": [
            "subscription", "membership", "recurring",
            "monthly", "annual"
        ],
        "amount_range": (99, 5000)
    },
    "Savings": {
        "keywords": [
            "investment", "fd", "mutual fund", "sip",
            "stocks", "ppf", "nps"
        ],
        "amount_range": None
    }
}


# =============================================================================
# INTERNAL STATE SAFETY HELPERS (NO FEATURE REMOVAL)
# =============================================================================

def ensure_state_initialized(state: Dict) -> None:
    """
    Ensures Streamlit state always contains required keys.
    This prevents partial-rerun crashes.
    """
    if "transactions" not in state or not isinstance(state["transactions"], list):
        state["transactions"] = []

    if "expenses" not in state:
        state["expenses"] = state["transactions"]

    if "income" not in state or not isinstance(state["income"], dict):
        state["income"] = {"monthly_income": 0}

    if "monthly_income" not in state["income"]:
        state["income"]["monthly_income"] = 0


def extract_monthly_income(state: Dict) -> float:
    """
    Safely extracts numeric monthly income from MonetIQ JSON.
    """
    try:
        return float(state.get("income", {}).get("monthly_income", 0))
    except (ValueError, TypeError):
        return 0.0


# =============================================================================
# AUTO CATEGORIZATION
# =============================================================================

def auto_categorize_transaction(transaction: Dict) -> str:
    description = str(transaction.get("description", "")).lower().strip()
    amount = float(transaction.get("amount", 0))

    if not description:
        return "Other"

    category_scores = {}

    for category, rules in CATEGORY_RULES.items():
        score = 0

        for keyword in rules["keywords"]:
            if keyword in description:
                score += 10

        if rules["amount_range"]:
            min_amt, max_amt = rules["amount_range"]
            if min_amt <= amount <= max_amt:
                score += 5

        category_scores[category] = score

    best_category = max(category_scores, key=category_scores.get)
    return best_category if category_scores[best_category] >= 10 else "Other"


# =============================================================================
# TRANSACTION MANAGEMENT
# =============================================================================

def add_transaction(state: Dict, transaction: Dict) -> Dict:
    ensure_state_initialized(state)

    txn = dict(transaction)

    if not txn.get("id"):
        txn["id"] = str(uuid.uuid4())

    if not txn.get("date"):
        txn["date"] = datetime.now().strftime("%Y-%m-%d")

    try:
        txn["amount"] = float(txn.get("amount", 0))
    except (ValueError, TypeError):
        txn["amount"] = 0.0

    if not txn.get("description"):
        txn["description"] = "Unknown"

    if not txn.get("category"):
        txn["category"] = auto_categorize_transaction(txn)

    if "source" not in txn:
        txn["source"] = "Other"

    if "is_recurring" not in txn:
        txn["is_recurring"] = False

    state["transactions"].append(txn)
    state["expenses"] = state["transactions"]

    return state


def get_all_expenses(state: Dict) -> List[Dict]:
    ensure_state_initialized(state)

    valid_expenses = []

    for txn in state["transactions"]:
        if not isinstance(txn, dict):
            continue

        try:
            amount = float(txn.get("amount", 0))
            if amount > 0:
                valid_expenses.append(txn)
        except (ValueError, TypeError):
            continue

    return valid_expenses


def get_expenses_by_category(state):
    """
    FINAL FIX — normalizes categories to Title Case
    so budgets, UI, and transactions ALWAYS match.
    """

    totals = {}

    sources = []
    if isinstance(state.get("transactions"), list):
        sources.append(state["transactions"])
    if isinstance(state.get("expenses"), list):
        sources.append(state["expenses"])

    for source in sources:
        for item in source:

            if not isinstance(item, dict):
                continue

            raw_category = (
                item.get("category")
                or item.get("expense_category")
                or item.get("type")
            )

            if not raw_category:
                continue

            # 🔥 THIS IS THE FIX
            category = str(raw_category).strip().title()

            raw_amount = (
                item.get("amount")
                or item.get("value")
                or item.get("expense")
                or 0
            )

            try:
                amount = float(raw_amount)
            except:
                continue

            if amount <= 0:
                continue

            totals[category] = totals.get(category, 0.0) + amount

    return totals




# =============================================================================
# TEMPORAL ANALYSIS
# =============================================================================

def monthly_expense_summary(state: Dict, year: int, month: int) -> Dict:
    ensure_state_initialized(state)

    monthly_expenses = []

    for expense in get_all_expenses(state):
        try:
            txn_date = datetime.strptime(expense["date"], "%Y-%m-%d")
            if txn_date.year == year and txn_date.month == month:
                monthly_expenses.append(expense)
        except Exception:
            continue

    total_expenses = sum(float(e["amount"]) for e in monthly_expenses)

    category_breakdown = defaultdict(float)
    for e in monthly_expenses:
        category_breakdown[e.get("category", "Other")] += float(e["amount"])

    days_in_month = calendar.monthrange(year, month)[1]
    average_daily_spend = total_expenses / days_in_month if days_in_month else 0

    monthly_income = extract_monthly_income(state)

    return {
        "total_expenses": round(total_expenses, 2),
        "category_breakdown": dict(category_breakdown),
        "average_daily_spend": round(average_daily_spend, 2),
        "highest_spending_category": (
            max(category_breakdown, key=category_breakdown.get)
            if category_breakdown else None
        ),
        "expense_vs_income_ratio": (
            round((total_expenses / monthly_income) * 100, 2)
            if monthly_income > 0 else 0
        ),
        "transaction_count": len(monthly_expenses)
    }


# =============================================================================
# BEHAVIORAL INTELLIGENCE
# =============================================================================

def detect_recurring_expenses(state: Dict) -> List[Dict]:
    ensure_state_initialized(state)

    grouped = defaultdict(list)

    for expense in get_all_expenses(state):
        normalized_desc = re.sub(r"[^a-z0-9]", "", expense["description"].lower())
        bucket = round(float(expense["amount"]) / 100) * 100
        key = f"{normalized_desc[:10]}_{bucket}"
        grouped[key].append(expense)

    recurring = []

    for group in grouped.values():
        if len(group) >= 2:
            for txn in group:
                txn["is_recurring"] = True
                recurring.append(txn)

    return recurring


def expense_velocity(state: Dict) -> float:
    ensure_state_initialized(state)

    now = datetime.now()
    summary = monthly_expense_summary(state, now.year, now.month)

    return summary["average_daily_spend"]


def top_merchants(state: Dict, n: int = 5) -> List[Tuple[str, float]]:
    ensure_state_initialized(state)

    merchant_totals = defaultdict(float)

    for expense in get_all_expenses(state):
        merchant_totals[expense["description"]] += float(expense["amount"])

    sorted_merchants = sorted(
        merchant_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [(m, round(a, 2)) for m, a in sorted_merchants[:n]]


def expense_trends(state: Dict) -> Dict:
    ensure_state_initialized(state)

    now = datetime.now()
    current = monthly_expense_summary(state, now.year, now.month)

    if now.month == 1:
        prev_month, prev_year = 12, now.year - 1
    else:
        prev_month, prev_year = now.month - 1, now.year

    previous = monthly_expense_summary(state, prev_year, prev_month)

    diff = current["total_expenses"] - previous["total_expenses"]

    pct_change = (
        (diff / previous["total_expenses"]) * 100
        if previous["total_expenses"] > 0 else 0
    )

    return {
        "trend": "stable" if abs(pct_change) < 5 else (
            "increasing" if pct_change > 0 else "decreasing"
        ),
        "percentage_change": round(pct_change, 2),
        "current_month_total": current["total_expenses"],
        "previous_month_total": previous["total_expenses"]
    }


# =============================================================================
# UTILITIES
# =============================================================================

def get_expense_by_id(state: Dict, transaction_id: str) -> Optional[Dict]:
    ensure_state_initialized(state)

    for txn in state["transactions"]:
        if txn.get("id") == transaction_id:
            return txn
    return None


def delete_transaction(state: Dict, transaction_id: str) -> Dict:
    ensure_state_initialized(state)

    state["transactions"] = [
        txn for txn in state["transactions"]
        if txn.get("id") != transaction_id
    ]
    state["expenses"] = state["transactions"]
    return state


def update_transaction(state: Dict, transaction_id: str, updates: Dict) -> Dict:
    ensure_state_initialized(state)

    for txn in state["transactions"]:
        if txn.get("id") == transaction_id:
            txn.update(updates)
            if "description" in updates and "category" not in updates:
                txn["category"] = auto_categorize_transaction(txn)
            break

    return state


def get_category_list() -> List[str]:
    return list(CATEGORY_RULES.keys()) + ["Other"]


def validate_transaction(transaction: Dict) -> Tuple[bool, str]:
    for field in ("amount", "description", "date"):
        if field not in transaction:
            return False, f"Missing required field: {field}"

    try:
        if float(transaction["amount"]) < 0:
            return False, "Amount cannot be negative"
    except Exception:
        return False, "Invalid amount format"

    try:
        datetime.strptime(transaction["date"], "%Y-%m-%d")
    except Exception:
        return False, "Invalid date format. Use YYYY-MM-DD"

    return True, ""
