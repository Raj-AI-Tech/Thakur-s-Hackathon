"""
MonetIQ Analytics - Monthly Preview Module

A production-ready analytics system for generating intelligent monthly financial previews
with trend analysis, anomaly detection, and predictive insights.

Author: MonetIQ Engineering Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
import statistics
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionCategory(Enum):
    """Standard transaction categories"""
    INCOME = "income"
    HOUSING = "housing"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    SAVINGS = "savings"
    DEBT = "debt"
    OTHER = "other"


class AnomalyType(Enum):
    """Types of spending anomalies"""
    SPIKE = "spike"
    DROP = "drop"
    UNUSUAL_MERCHANT = "unusual_merchant"
    FREQUENCY_CHANGE = "frequency_change"


@dataclass
class Transaction:
    """Represents a financial transaction"""
    id: str
    date: datetime
    amount: Decimal
    category: TransactionCategory
    merchant: str
    description: str
    is_recurring: bool = False

    def __post_init__(self):
        """Validate transaction data"""
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))


@dataclass
class Anomaly:
    """Represents a detected spending anomaly"""
    type: AnomalyType
    category: TransactionCategory
    severity: float  # 0-1 scale
    current_amount: Decimal
    expected_amount: Decimal
    variance_pct: float
    description: str


@dataclass
class CategoryInsight:
    """Insights for a spending category"""
    category: TransactionCategory
    current_month_total: Decimal
    previous_month_total: Decimal
    avg_last_3_months: Decimal
    avg_last_6_months: Decimal
    trend: str  # "increasing", "decreasing", "stable"
    trend_pct: float
    transaction_count: int
    top_merchants: List[Tuple[str, Decimal]]


@dataclass
class MonthlyPreview:
    """Complete monthly financial preview"""
    month: datetime
    total_income: Decimal
    total_expenses: Decimal
    net_position: Decimal
    projected_end_balance: Decimal
    category_insights: Dict[TransactionCategory, CategoryInsight]
    anomalies: List[Anomaly]
    recurring_payments: List[Transaction]
    savings_rate: float
    burn_rate: Decimal  # Daily average spend
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)


class MonthlyPreviewAnalytics:
    """
    Core analytics engine for generating monthly financial previews.

    This class processes transaction history to generate insights, detect anomalies,
    and provide actionable recommendations for users.
    """

    def __init__(self, anomaly_threshold: float = 0.25, trend_window: int = 3):
        """
        Initialize the analytics engine.

        Args:
            anomaly_threshold: Variance threshold for anomaly detection (0.25 = 25%)
            trend_window: Number of months to use for trend analysis
        """
        self.anomaly_threshold = anomaly_threshold
        self.trend_window = trend_window
        logger.info(f"Initialized MonthlyPreviewAnalytics with threshold={anomaly_threshold}")

    def generate_preview(
            self,
            transactions: List[Transaction],
            current_balance: Decimal,
            target_month: Optional[datetime] = None
    ) -> MonthlyPreview:
        """
        Generate a comprehensive monthly preview.

        Args:
            transactions: Historical transaction data (minimum 6 months recommended)
            current_balance: User's current account balance
            target_month: Month to preview (defaults to current month)

        Returns:
            MonthlyPreview object with complete analytics
        """
        if target_month is None:
            target_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        logger.info(f"Generating preview for {target_month.strftime('%B %Y')}")

        # Organize transactions by month and category
        monthly_data = self._organize_by_month(transactions)

        # Calculate current month metrics
        current_month_txns = self._get_month_transactions(transactions, target_month)
        total_income, total_expenses = self._calculate_income_expenses(current_month_txns)

        # Generate category insights
        category_insights = self._analyze_categories(
            transactions,
            target_month,
            monthly_data
        )

        # Detect anomalies
        anomalies = self._detect_anomalies(category_insights, monthly_data, target_month)

        # Identify recurring payments
        recurring_payments = self._identify_recurring(transactions, target_month)

        # Calculate financial metrics
        net_position = total_income - total_expenses
        savings_rate = float(net_position / total_income * 100) if total_income > 0 else 0.0
        burn_rate = total_expenses / Decimal(30)  # Daily average
        projected_balance = current_balance + net_position

        # Generate recommendations
        recommendations = self._generate_recommendations(
            category_insights,
            anomalies,
            savings_rate,
            net_position
        )

        preview = MonthlyPreview(
            month=target_month,
            total_income=total_income,
            total_expenses=total_expenses,
            net_position=net_position,
            projected_end_balance=projected_balance,
            category_insights=category_insights,
            anomalies=anomalies,
            recurring_payments=recurring_payments,
            savings_rate=savings_rate,
            burn_rate=burn_rate,
            recommendations=recommendations
        )

        logger.info(f"Preview generated: Income=${total_income}, Expenses=${total_expenses}")
        return preview

    def _organize_by_month(
            self,
            transactions: List[Transaction]
    ) -> Dict[datetime, Dict[TransactionCategory, List[Transaction]]]:
        """Organize transactions by month and category"""
        monthly_data = defaultdict(lambda: defaultdict(list))

        for txn in transactions:
            month_key = txn.date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_data[month_key][txn.category].append(txn)

        return dict(monthly_data)

    def _get_month_transactions(
            self,
            transactions: List[Transaction],
            month: datetime
    ) -> List[Transaction]:
        """Get all transactions for a specific month"""
        next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
        return [
            txn for txn in transactions
            if month <= txn.date < next_month
        ]

    def _calculate_income_expenses(
            self,
            transactions: List[Transaction]
    ) -> Tuple[Decimal, Decimal]:
        """Calculate total income and expenses"""
        income = sum(
            txn.amount for txn in transactions
            if txn.category == TransactionCategory.INCOME
        )
        expenses = sum(
            txn.amount for txn in transactions
            if txn.category != TransactionCategory.INCOME
        )
        return Decimal(income), Decimal(expenses)

    def _analyze_categories(
            self,
            transactions: List[Transaction],
            target_month: datetime,
            monthly_data: Dict[datetime, Dict[TransactionCategory, List[Transaction]]]
    ) -> Dict[TransactionCategory, CategoryInsight]:
        """Analyze spending patterns by category"""
        insights = {}

        for category in TransactionCategory:
            if category == TransactionCategory.INCOME:
                continue

            # Current month data
            current_txns = monthly_data.get(target_month, {}).get(category, [])
            current_total = sum(txn.amount for txn in current_txns)

            # Previous month
            prev_month = (target_month - timedelta(days=1)).replace(day=1)
            prev_txns = monthly_data.get(prev_month, {}).get(category, [])
            prev_total = sum(txn.amount for txn in prev_txns)

            # 3-month average
            avg_3m = self._calculate_average(
                monthly_data, category, target_month, months=3
            )

            # 6-month average
            avg_6m = self._calculate_average(
                monthly_data, category, target_month, months=6
            )

            # Trend analysis
            trend, trend_pct = self._calculate_trend(
                monthly_data, category, target_month
            )

            # Top merchants
            top_merchants = self._get_top_merchants(current_txns, limit=3)

            insights[category] = CategoryInsight(
                category=category,
                current_month_total=current_total,
                previous_month_total=prev_total,
                avg_last_3_months=avg_3m,
                avg_last_6_months=avg_6m,
                trend=trend,
                trend_pct=trend_pct,
                transaction_count=len(current_txns),
                top_merchants=top_merchants
            )

        return insights

    def _calculate_average(
            self,
            monthly_data: Dict[datetime, Dict[TransactionCategory, List[Transaction]]],
            category: TransactionCategory,
            target_month: datetime,
            months: int
    ) -> Decimal:
        """Calculate average spending for a category over N months"""
        totals = []

        for i in range(1, months + 1):
            month = (target_month - timedelta(days=30 * i)).replace(day=1)
            txns = monthly_data.get(month, {}).get(category, [])
            total = sum(txn.amount for txn in txns)
            totals.append(total)

        return Decimal(sum(totals) / len(totals)) if totals else Decimal(0)

    def _calculate_trend(
            self,
            monthly_data: Dict[datetime, Dict[TransactionCategory, List[Transaction]]],
            category: TransactionCategory,
            target_month: datetime
    ) -> Tuple[str, float]:
        """Calculate spending trend and percentage change"""
        recent_totals = []

        for i in range(self.trend_window):
            month = (target_month - timedelta(days=30 * i)).replace(day=1)
            txns = monthly_data.get(month, {}).get(category, [])
            total = float(sum(txn.amount for txn in txns))
            recent_totals.append(total)

        if len(recent_totals) < 2 or all(t == 0 for t in recent_totals):
            return "stable", 0.0

        # Simple linear regression slope
        avg_change = (recent_totals[0] - recent_totals[-1]) / len(recent_totals)
        avg_value = statistics.mean(recent_totals) if recent_totals else 0

        if avg_value == 0:
            return "stable", 0.0

        change_pct = (avg_change / avg_value) * 100

        if abs(change_pct) < 5:
            return "stable", change_pct
        elif change_pct > 0:
            return "increasing", change_pct
        else:
            return "decreasing", change_pct

    def _get_top_merchants(
            self,
            transactions: List[Transaction],
            limit: int = 3
    ) -> List[Tuple[str, Decimal]]:
        """Get top merchants by spending"""
        merchant_totals = defaultdict(Decimal)

        for txn in transactions:
            merchant_totals[txn.merchant] += txn.amount

        sorted_merchants = sorted(
            merchant_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_merchants[:limit]

    def _detect_anomalies(
            self,
            category_insights: Dict[TransactionCategory, CategoryInsight],
            monthly_data: Dict[datetime, Dict[TransactionCategory, List[Transaction]]],
            target_month: datetime
    ) -> List[Anomaly]:
        """Detect spending anomalies"""
        anomalies = []

        for category, insight in category_insights.items():
            current = float(insight.current_month_total)
            expected = float(insight.avg_last_3_months)

            if expected == 0:
                continue

            variance = abs(current - expected) / expected

            # Check for significant variance
            if variance > self.anomaly_threshold:
                anomaly_type = AnomalyType.SPIKE if current > expected else AnomalyType.DROP

                anomalies.append(Anomaly(
                    type=anomaly_type,
                    category=category,
                    severity=min(variance, 1.0),
                    current_amount=insight.current_month_total,
                    expected_amount=insight.avg_last_3_months,
                    variance_pct=variance * 100,
                    description=self._generate_anomaly_description(
                        anomaly_type, category, variance * 100
                    )
                ))

        # Sort by severity
        anomalies.sort(key=lambda x: x.severity, reverse=True)

        return anomalies

    def _generate_anomaly_description(
            self,
            anomaly_type: AnomalyType,
            category: TransactionCategory,
            variance_pct: float
    ) -> str:
        """Generate human-readable anomaly description"""
        if anomaly_type == AnomalyType.SPIKE:
            return f"{category.value.title()} spending is {variance_pct:.1f}% higher than usual"
        else:
            return f"{category.value.title()} spending is {variance_pct:.1f}% lower than usual"

    def _identify_recurring(
            self,
            transactions: List[Transaction],
            target_month: datetime
    ) -> List[Transaction]:
        """Identify recurring payments expected this month"""
        # Group by merchant and amount
        merchant_patterns = defaultdict(list)

        for txn in transactions:
            if txn.date < target_month:  # Only historical data
                key = (txn.merchant, txn.category, txn.amount)
                merchant_patterns[key].append(txn)

        recurring = []
        for (merchant, category, amount), txns in merchant_patterns.items():
            # Check if appears monthly (at least 3 times in last 6 months)
            if len(txns) >= 3:
                # Check if already paid this month
                current_month_paid = any(
                    t.date >= target_month and
                    t.merchant == merchant and
                    t.amount == amount
                    for t in transactions
                )

                if not current_month_paid:
                    # Create expected transaction
                    recurring.append(Transaction(
                        id=f"expected_{merchant}_{amount}",
                        date=target_month,
                        amount=amount,
                        category=category,
                        merchant=merchant,
                        description=f"Expected recurring payment",
                        is_recurring=True
                    ))

        return recurring

    def _generate_recommendations(
            self,
            category_insights: Dict[TransactionCategory, CategoryInsight],
            anomalies: List[Anomaly],
            savings_rate: float,
            net_position: Decimal
    ) -> List[str]:
        """Generate actionable financial recommendations"""
        recommendations = []

        # Savings recommendations
        if savings_rate < 10:
            recommendations.append(
                f"Your savings rate is {savings_rate:.1f}%. Financial experts recommend "
                "saving at least 10-20% of income. Consider reviewing discretionary spending."
            )
        elif savings_rate > 20:
            recommendations.append(
                f"Excellent! Your {savings_rate:.1f}% savings rate exceeds recommended levels. "
                "Consider investing surplus funds for long-term growth."
            )

        # Anomaly-based recommendations
        for anomaly in anomalies[:2]:  # Top 2 anomalies
            if anomaly.type == AnomalyType.SPIKE and anomaly.severity > 0.5:
                recommendations.append(
                    f"Your {anomaly.category.value} spending increased significantly this month. "
                    f"Review your {anomaly.category.value} transactions to identify the cause."
                )

        # Category-specific insights
        for category, insight in category_insights.items():
            if insight.trend == "increasing" and insight.trend_pct > 15:
                recommendations.append(
                    f"{category.value.title()} spending has increased {insight.trend_pct:.1f}% "
                    f"over the last {self.trend_window} months. Consider setting a budget limit."
                )

        # Limit to top 5 recommendations
        return recommendations[:5]
def get_monthly_preview(
    transactions: List[Transaction],
    current_balance: Decimal,
    target_month: Optional[datetime] = None
) -> MonthlyPreview:
    """
    Public API wrapper for Monthly Preview analytics.

    This function is used by app.py and other UI layers.
    """
    engine = MonthlyPreviewAnalytics()
    return engine.generate_preview(
        transactions=transactions,
        current_balance=current_balance,
        target_month=target_month
    )


# Example usage and testing
if __name__ == "__main__":
    # Sample transaction data
    sample_transactions = [
        Transaction(
            id="1", date=datetime(2025, 1, 5), amount=Decimal("3500.00"),
            category=TransactionCategory.INCOME, merchant="Employer",
            description="Salary"
        ),
        Transaction(
            id="2", date=datetime(2025, 1, 1), amount=Decimal("1200.00"),
            category=TransactionCategory.HOUSING, merchant="Property Management",
            description="Rent"
        ),
        Transaction(
            id="3", date=datetime(2025, 1, 3), amount=Decimal("150.00"),
            category=TransactionCategory.UTILITIES, merchant="Electric Co",
            description="Electricity"
        ),
        Transaction(
            id="4", date=datetime(2025, 1, 10), amount=Decimal("75.50"),
            category=TransactionCategory.FOOD, merchant="Grocery Store",
            description="Groceries"
        ),
        Transaction(
            id="5", date=datetime(2025, 1, 15), amount=Decimal("450.00"),
            category=TransactionCategory.SHOPPING, merchant="Electronics Store",
            description="New laptop charger"
        ),
    ]

    # Initialize analytics engine
    analytics = MonthlyPreviewAnalytics(anomaly_threshold=0.25)

    # Generate preview
    preview = analytics.generate_preview(
        transactions=sample_transactions,
        current_balance=Decimal("5000.00"),
        target_month=datetime(2025, 1, 1)
    )

    # Display results
    print(f"\n{'=' * 60}")
    print(f"MonetIQ Monthly Preview - {preview.month.strftime('%B %Y')}")
    print(f"{'=' * 60}\n")
    print(f"Income:              ${preview.total_income:,.2f}")
    print(f"Expenses:            ${preview.total_expenses:,.2f}")
    print(f"Net Position:        ${preview.net_position:,.2f}")
    print(f"Projected Balance:   ${preview.projected_end_balance:,.2f}")
    print(f"Savings Rate:        {preview.savings_rate:.1f}%")
    print(f"Daily Burn Rate:     ${preview.burn_rate:.2f}")

    print(f"\n{'=' * 60}")
    print("Recommendations:")
    print(f"{'=' * 60}")
    for i, rec in enumerate(preview.recommendations, 1):
        print(f"{i}. {rec}")

    print(f"\n{'=' * 60}")
    print(f"Analysis complete - {preview.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")