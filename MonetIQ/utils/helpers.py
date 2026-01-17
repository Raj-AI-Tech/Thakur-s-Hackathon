"""
utils/helpers.py

Reusable utility and intelligence helper layer for MonetIQ.
Provides stateless, pure functions for calculations, formatting, and data processing.
"""

from typing import Any, List, Dict, Optional, Union
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re

def _to_number(value, default=0.0):
    """
    Safely convert dict / int / float / None to float
    """
    if isinstance(value, dict):
        return float(
            value.get("monthly",
            value.get("amount",
            value.get("total",
            default)))
        )
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

# ============================================================================
# DATE & TIME UTILITIES
# ============================================================================

def get_current_month() -> str:
    """
    Get current month in YYYY-MM format.

    Returns:
        Current month string (e.g., "2025-01")
    """
    return datetime.now().strftime("%Y-%m")


def get_previous_month(month: str) -> str:
    """
    Get previous month from given YYYY-MM string.

    Args:
        month: Month string in YYYY-MM format

    Returns:
        Previous month in YYYY-MM format

    Example:
        >>> get_previous_month("2025-01")
        "2024-12"
    """
    try:
        date = datetime.strptime(month, "%Y-%m")
        previous = date - relativedelta(months=1)
        return previous.strftime("%Y-%m")
    except (ValueError, TypeError):
        return get_current_month()


def get_next_month(month: str) -> str:
    """
    Get next month from given YYYY-MM string.

    Args:
        month: Month string in YYYY-MM format

    Returns:
        Next month in YYYY-MM format
    """
    try:
        date = datetime.strptime(month, "%Y-%m")
        next_month = date + relativedelta(months=1)
        return next_month.strftime("%Y-%m")
    except (ValueError, TypeError):
        return get_current_month()


def months_between(start: str, end: str) -> int:
    """
    Calculate number of months between two YYYY-MM dates.

    Args:
        start: Start month in YYYY-MM format
        end: End month in YYYY-MM format

    Returns:
        Number of months between dates (inclusive)

    Example:
        >>> months_between("2024-01", "2024-06")
        6
    """
    try:
        start_date = datetime.strptime(start, "%Y-%m")
        end_date = datetime.strptime(end, "%Y-%m")

        delta = relativedelta(end_date, start_date)
        return abs(delta.years * 12 + delta.months) + 1
    except (ValueError, TypeError):
        return 0


def is_valid_month(month: str) -> bool:
    """
    Validate if string is valid YYYY-MM format.

    Args:
        month: Month string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(month, "%Y-%m")
        return True
    except (ValueError, TypeError):
        return False


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string into datetime object.

    Args:
        date_str: Date string in various formats

    Returns:
        Datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue

    return None


def days_in_month(month: str) -> int:
    """
    Get number of days in a given month.

    Args:
        month: Month string in YYYY-MM format

    Returns:
        Number of days in month
    """
    try:
        date = datetime.strptime(month, "%Y-%m")
        next_month = date + relativedelta(months=1)
        last_day = next_month - timedelta(days=1)
        return last_day.day
    except (ValueError, TypeError):
        return 30


# ============================================================================
# FINANCIAL MATH HELPERS
# ============================================================================

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Perform division with zero-division protection.

    Args:
        a: Numerator
        b: Denominator
        default: Default value if division by zero

    Returns:
        Result of a/b or default if b is zero
    """
    try:
        a_val = float(a)
        b_val = float(b)

        if b_val == 0:
            return default

        return a_val / b_val
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def percentage(part: float, whole: float, decimals: int = 2) -> float:
    """
    Calculate percentage safely.

    Args:
        part: Part value
        whole: Whole value
        decimals: Number of decimal places

    Returns:
        Percentage value

    Example:
        >>> percentage(25, 100)
        25.0
    """
    result = safe_divide(part, whole, 0) * 100
    return round(result, decimals)


def percentage_change(old: float, new: float, decimals: int = 2) -> float:
    """
    Calculate percentage change between two values.

    Args:
        old: Old value
        new: New value
        decimals: Number of decimal places

    Returns:
        Percentage change
    """
    if old == 0:
        return 0.0

    change = ((new - old) / abs(old)) * 100
    return round(change, decimals)


def moving_average(values: List[float], window: int = 3) -> float:
    """
    Calculate moving average of values.

    Args:
        values: List of numeric values
        window: Window size for average

    Returns:
        Moving average value
    """
    if not values:
        return 0.0

    clean_values = [normalize_amount(v) for v in values]
    clean_values = [v for v in clean_values if v is not None]

    if not clean_values:
        return 0.0

    window_values = clean_values[-window:] if len(clean_values) >= window else clean_values
    return sum(window_values) / len(window_values)


def compound_interest(principal: float, rate: float, time: float, frequency: int = 12) -> float:
    """
    Calculate compound interest.

    Args:
        principal: Principal amount
        rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        time: Time in years
        frequency: Compounding frequency per year

    Returns:
        Final amount after compound interest
    """
    try:
        amount = principal * ((1 + rate / frequency) ** (frequency * time))
        return round(amount, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return principal


def simple_interest(principal: float, rate: float, time: float) -> float:
    """
    Calculate simple interest.

    Args:
        principal: Principal amount
        rate: Annual interest rate (as decimal)
        time: Time in years

    Returns:
        Interest amount
    """
    try:
        interest = principal * rate * time
        return round(interest, 2)
    except (ValueError, TypeError):
        return 0.0


def emi_calculator(principal: float, rate: float, tenure: int) -> float:
    """
    Calculate EMI (Equated Monthly Installment).

    Args:
        principal: Loan amount
        rate: Annual interest rate (as decimal)
        tenure: Tenure in months

    Returns:
        Monthly EMI amount
    """
    try:
        monthly_rate = rate / 12

        if monthly_rate == 0:
            return principal / tenure

        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / (((1 + monthly_rate) ** tenure) - 1)
        return round(emi, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


# ============================================================================
# NORMALIZATION & CLEANING
# ============================================================================

def normalize_amount(value: Any) -> float:
    """
    Convert any value to safe float amount.

    Args:
        value: Value to normalize (str, int, float, None, etc.)

    Returns:
        Normalized float value

    Examples:
        >>> normalize_amount("1,234.56")
        1234.56
        >>> normalize_amount(None)
        0.0
        >>> normalize_amount("invalid")
        0.0
    """
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


def normalize_category(category: str) -> str:
    """
    Standardize category name.

    Args:
        category: Category string

    Returns:
        Normalized category (lowercase, trimmed)

    Example:
        >>> normalize_category("  Food & Dining  ")
        "food & dining"
    """
    if not isinstance(category, str):
        return "uncategorized"

    return category.strip().lower()


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison and storage.

    Args:
        text: Text to normalize

    Returns:
        Normalized text
    """
    if not isinstance(text, str):
        return ""

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    return text


def clean_dict(data: Dict[str, Any], remove_empty: bool = False) -> Dict[str, Any]:
    """
    Clean dictionary by removing None values and optionally empty values.

    Args:
        data: Dictionary to clean
        remove_empty: Remove empty strings, lists, dicts

    Returns:
        Cleaned dictionary
    """
    if not isinstance(data, dict):
        return {}

    cleaned = {}

    for key, value in data.items():
        if value is None:
            continue

        if remove_empty:
            if value == "" or value == [] or value == {}:
                continue

        cleaned[key] = value

    return cleaned


# ============================================================================
# RISK & SCORING HELPERS
# ============================================================================

def score_to_label(score: float) -> str:
    """
    Map numeric score to descriptive label.

    Args:
        score: Numeric score (0-100)

    Returns:
        Label: EXCELLENT, GOOD, FAIR, POOR, CRITICAL
    """
    score = clamp(score, 0, 100)

    if score >= 85:
        return "EXCELLENT"
    elif score >= 70:
        return "GOOD"
    elif score >= 50:
        return "FAIR"
    elif score >= 30:
        return "POOR"
    else:
        return "CRITICAL"


def risk_flag(value: float, thresholds: Dict[str, float]) -> str:
    """
    Determine risk level based on thresholds.

    Args:
        value: Value to evaluate
        thresholds: Dict with 'safe' and 'warning' keys

    Returns:
        Risk level: SAFE, WARNING, CRITICAL

    Example:
        >>> risk_flag(50, {'safe': 30, 'warning': 70})
        "WARNING"
    """
    safe_threshold = thresholds.get('safe', 0)
    warning_threshold = thresholds.get('warning', 100)

    if value <= safe_threshold:
        return "SAFE"
    elif value <= warning_threshold:
        return "WARNING"
    else:
        return "CRITICAL"


def health_score_color(score: float) -> str:
    """
    Get color code for health score visualization.

    Args:
        score: Health score (0-100)

    Returns:
        Color string
    """
    if score >= 80:
        return "green"
    elif score >= 60:
        return "blue"
    elif score >= 40:
        return "orange"
    else:
        return "red"


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_currency(amount: float, currency: str = "INR", decimals: int = 2) -> str:
    """
    Format amount as currency string.

    Args:
        amount: Amount to format
        currency: Currency code
        decimals: Number of decimal places

    Returns:
        Formatted currency string

    Example:
        >>> format_currency(1234.56, "INR")
        "₹1,234.56"
    """
    amount = normalize_amount(amount)

    symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
    }

    symbol = symbols.get(currency.upper(), "₹")

    formatted = f"{amount:,.{decimals}f}"

    return f"{symbol}{formatted}"


def human_readable_delta(value: float, use_sign: bool = True) -> str:
    """
    Convert numeric delta to human-readable string.

    Args:
        value: Numeric value (e.g., 0.42 for 42%)
        use_sign: Include + for positive values

    Returns:
        Human-readable string

    Example:
        >>> human_readable_delta(0.42)
        "+42% increase"
        >>> human_readable_delta(-0.15)
        "-15% decrease"
    """
    percentage_val = value * 100

    if value > 0:
        sign = "+" if use_sign else ""
        return f"{sign}{abs(percentage_val):.1f}% increase"
    elif value < 0:
        return f"-{abs(percentage_val):.1f}% decrease"
    else:
        return "No change"


def format_large_number(num: float, decimals: int = 1) -> str:
    """
    Format large numbers with K, M, B suffixes.

    Args:
        num: Number to format
        decimals: Decimal places

    Returns:
        Formatted string

    Example:
        >>> format_large_number(1500)
        "1.5K"
        >>> format_large_number(1500000)
        "1.5M"
    """
    num = normalize_amount(num)

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.{decimals}f}K"
    else:
        return f"{num:.{decimals}f}"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not isinstance(text, str):
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def ensure_list(value: Any) -> List:
    """
    Ensure value is a list.

    Args:
        value: Value to convert

    Returns:
        List representation of value
    """
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    return [value]


def ensure_dict(value: Any) -> Dict:
    """
    Ensure value is a dictionary.

    Args:
        value: Value to convert

    Returns:
        Dictionary representation of value
    """
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    return {}


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email string to validate

    Returns:
        True if valid email format
    """
    if not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_positive(value: float) -> bool:
    """
    Check if value is positive.

    Args:
        value: Value to check

    Returns:
        True if positive
    """
    try:
        return float(value) > 0
    except (ValueError, TypeError):
        return False


def is_in_range(value: float, min_val: float, max_val: float) -> bool:
    """
    Check if value is within range.

    Args:
        value: Value to check
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        True if in range
    """
    try:
        val = float(value)
        return min_val <= val <= max_val
    except (ValueError, TypeError):
        return False


# ============================================================================
# STATISTICAL HELPERS
# ============================================================================

def mean(values: List[float]) -> float:
    """
    Calculate mean of values.

    Args:
        values: List of numeric values

    Returns:
        Mean value
    """
    if not values:
        return 0.0

    clean_values = [normalize_amount(v) for v in values]
    return sum(clean_values) / len(clean_values)


def median(values: List[float]) -> float:
    """
    Calculate median of values.

    Args:
        values: List of numeric values

    Returns:
        Median value
    """
    if not values:
        return 0.0

    clean_values = sorted([normalize_amount(v) for v in values])
    n = len(clean_values)

    if n % 2 == 0:
        return (clean_values[n // 2 - 1] + clean_values[n // 2]) / 2
    else:
        return clean_values[n // 2]


def std_deviation(values: List[float]) -> float:
    """
    Calculate standard deviation.

    Args:
        values: List of numeric values

    Returns:
        Standard deviation
    """
    if len(values) < 2:
        return 0.0

    clean_values = [normalize_amount(v) for v in values]
    avg = mean(clean_values)

    variance = sum((x - avg) ** 2 for x in clean_values) / len(clean_values)

    return variance ** 0.5


def sum_list(values: List[float]) -> float:
    """
    Safely sum a list of values.

    Args:
        values: List of numeric values

    Returns:
        Sum of values
    """
    return sum(normalize_amount(v) for v in values)


def max_value(values: List[float], default: float = 0.0) -> float:
    """
    Get maximum value from list.

    Args:
        values: List of numeric values
        default: Default if list is empty

    Returns:
        Maximum value
    """
    if not values:
        return default

    clean_values = [normalize_amount(v) for v in values]
    return max(clean_values)


def min_value(values: List[float], default: float = 0.0) -> float:
    """
    Get minimum value from list.

    Args:
        values: List of numeric values
        default: Default if list is empty

    Returns:
        Minimum value
    """
    if not values:
        return default

    clean_values = [normalize_amount(v) for v in values]
    return min(clean_values)