"""
MonetIQ Analytics & Insights Engine
Production-ready financial intelligence module for Streamlit applications.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict
import statistics
from decimal import Decimal


# ============================================================================
# ENUMS
# ============================================================================

class InsightType(Enum):
    SPENDING_ANOMALY = "spending_anomaly"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    BUDGET_ALERT = "budget_alert"
    INCOME_PATTERN = "income_pattern"
    RECURRING_DETECTION = "recurring_detection"
    CASH_FLOW_WARNING = "cash_flow_warning"
    GOAL_PROGRESS = "goal_progress"
    CATEGORY_TREND = "category_trend"


class Severity(Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Transaction:
    id: str
    date: datetime
    amount: Decimal
    category: str
    description: str
    account: str
    is_income: bool = False
    merchant: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Budget:
    category: str
    limit: Decimal
    period: str
    start_date: datetime
    end_date: datetime


@dataclass
class Insight:
    type: InsightType
    severity: Severity
    title: str
    description: str
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # STREAMLIT SAFE SERIALIZATION
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "amount": float(self.amount) if self.amount is not None else None,
            "category": self.category,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SpendingPattern:
    category: str
    frequency: str
    avg_amount: Decimal
    transactions: List[Transaction]
    confidence: float


# ============================================================================
# SPENDING ANALYZER
# ============================================================================

class SpendingAnalyzer:

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.expense_txns = [t for t in transactions if not t.is_income]

    def detect_anomalies(self, std_threshold: float = 2.0) -> List[Insight]:
        insights = []
        category_amounts = defaultdict(list)

        for txn in self.expense_txns:
            category_amounts[txn.category].append(float(txn.amount))

        for category, amounts in category_amounts.items():
            if len(amounts) < 3 or len(set(amounts)) < 2:
                continue

            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts)

            recent = [
                t for t in self.expense_txns
                if t.category == category
                and (datetime.now() - t.date).days <= 7
            ]

            for txn in recent:
                if stdev == 0:
                    continue

                z_score = (float(txn.amount) - mean) / stdev

                if abs(z_score) > std_threshold:
                    severity = Severity.HIGH if abs(z_score) > 3 else Severity.MEDIUM

                    insights.append(Insight(
                        type=InsightType.SPENDING_ANOMALY,
                        severity=severity,
                        title=f"Unusual {category} Spending Detected",
                        description=(
                            f"${float(txn.amount):.2f} spent on {txn.description} "
                            f"is unusually high compared to your normal {category} spending."
                        ),
                        amount=txn.amount,
                        category=category,
                        recommendations=[
                            f"Average {category} spend: ${mean:.2f}",
                            "Review if this expense was necessary",
                            "Consider setting a category budget"
                        ],
                        metadata={
                            "z_score": z_score,
                            "mean": mean,
                            "stdev": stdev
                        }
                    ))

        return insights


    def analyze_category_trends(self, days: int = 30) -> List[Insight]:
        insights = []
        cutoff = datetime.now() - timedelta(days=days)

        current = defaultdict(Decimal)
        previous = defaultdict(Decimal)

        for txn in self.expense_txns:
            if txn.date >= cutoff:
                current[txn.category] += txn.amount
            elif cutoff - timedelta(days=days) <= txn.date < cutoff:
                previous[txn.category] += txn.amount

        for category in set(current) | set(previous):
            prev = previous.get(category, Decimal("0"))
            curr = current.get(category, Decimal("0"))

            if prev == 0:
                continue

            change_pct = ((curr - prev) / prev) * 100

            if abs(change_pct) >= 25:
                severity = Severity.HIGH if abs(change_pct) > 50 else Severity.MEDIUM
                trend = "increased" if change_pct > 0 else "decreased"

                insights.append(Insight(
                    type=InsightType.CATEGORY_TREND,
                    severity=severity,
                    title=f"{category} Spending {trend.capitalize()}",
                    description=(
                        f"Your {category} spending has {trend} by "
                        f"{abs(float(change_pct)):.1f}% compared to last period."
                    ),
                    amount=curr,
                    category=category,
                    recommendations=[
                        f"Current: ${float(curr):.2f}",
                        f"Previous: ${float(prev):.2f}",
                        "Review what caused this change"
                    ],
                    metadata={"change_percent": float(change_pct)}
                ))

        return insights


# ============================================================================
# RECURRING TRANSACTION DETECTOR
# ============================================================================

class RecurringTransactionDetector:

    def __init__(self, transactions: List[Transaction]):
        self.transactions = sorted(transactions, key=lambda t: t.date)

    def detect_recurring(self, min_occurrences: int = 3) -> List[SpendingPattern]:
        patterns = []
        merchants = defaultdict(list)

        for txn in self.transactions:
            if txn.merchant and not txn.is_income:
                merchants[txn.merchant].append(txn)

        for merchant, txns in merchants.items():
            if len(txns) < min_occurrences:
                continue

            clusters = []

            for txn in txns:
                placed = False
                for cluster in clusters:
                    avg = statistics.mean([float(t.amount) for t in cluster])
                    if avg == 0:
                        continue
                    if abs(float(txn.amount) - avg) / avg < 0.05:
                        cluster.append(txn)
                        placed = True
                        break
                if not placed:
                    clusters.append([txn])

            for cluster in clusters:
                if len(cluster) >= min_occurrences:
                    frequency, confidence = self._detect_frequency(cluster)
                    if confidence >= 0.6:
                        avg_amt = Decimal(str(statistics.mean(
                            [float(t.amount) for t in cluster]
                        )))

                        patterns.append(SpendingPattern(
                            category=cluster[0].category,
                            frequency=frequency,
                            avg_amount=avg_amt,
                            transactions=cluster,
                            confidence=confidence
                        ))

        return patterns


    def _detect_frequency(self, txns: List[Transaction]) -> Tuple[str, float]:
        gaps = [
            (txns[i].date - txns[i - 1].date).days
            for i in range(1, len(txns))
        ]

        if not gaps:
            return "irregular", 0.0

        avg = statistics.mean(gaps)
        std = statistics.stdev(gaps) if len(gaps) > 1 else 0
        variance = std / avg if avg else 1.0

        if 25 <= avg <= 35:
            return "monthly", max(0.0, 1.0 - variance)
        if 6 <= avg <= 8:
            return "weekly", max(0.0, 1.0 - variance)
        if 85 <= avg <= 95:
            return "quarterly", max(0.0, 1.0 - variance)

        return "irregular", 0.3


# ============================================================================
# BUDGET MONITOR
# ============================================================================

class BudgetMonitor:

    def __init__(self, transactions: List[Transaction], budgets: List[Budget]):
        self.transactions = transactions
        self.budgets = budgets

    def check_budget_status(self) -> List[Insight]:
        insights = []

        for budget in self.budgets:
            spent = self._calculate_spending(budget)

            if budget.limit <= 0:
                continue

            utilization = (spent / budget.limit) * 100

            if utilization >= 100:
                severity = Severity.CRITICAL
            elif utilization >= 80:
                severity = Severity.HIGH
            else:
                continue

            insights.append(Insight(
                type=InsightType.BUDGET_ALERT,
                severity=severity,
                title=f"{budget.category} Budget Alert",
                description=(
                    f"Budget utilization at {float(utilization):.1f}% "
                    f"(${float(spent):.2f} of ${float(budget.limit):.2f})"
                ),
                amount=spent,
                category=budget.category,
                recommendations=[
                    "Review recent transactions",
                    "Reduce discretionary spending",
                    "Adjust budget if consistently exceeded"
                ],
                metadata={"utilization": float(utilization)}
            ))

        return insights


    def _calculate_spending(self, budget: Budget) -> Decimal:
        return sum(
            (t.amount for t in self.transactions
             if t.category == budget.category
             and budget.start_date <= t.date <= budget.end_date
             and not t.is_income),
            Decimal("0")
        )


# ============================================================================
# CASH FLOW ANALYZER
# ============================================================================

class CashFlowAnalyzer:

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions

    def analyze_cash_flow(self, days: int = 30) -> List[Insight]:
        insights = []
        cutoff = datetime.now() - timedelta(days=days)

        recent = [t for t in self.transactions if t.date >= cutoff]
        income = sum((t.amount for t in recent if t.is_income), Decimal("0"))
        expenses = sum((t.amount for t in recent if not t.is_income), Decimal("0"))

        net = income - expenses

        if net < 0:
            insights.append(Insight(
                type=InsightType.CASH_FLOW_WARNING,
                severity=Severity.CRITICAL,
                title="Negative Cash Flow",
                description="Your expenses exceed income.",
                amount=abs(net),
                recommendations=[
                    "Cut discretionary spending",
                    "Review subscriptions",
                    "Increase income if possible"
                ]
            ))

        return insights


# ============================================================================
# INSIGHT ENGINE
# ============================================================================

class InsightEngine:

    def __init__(self, transactions: List[Transaction], budgets: List[Budget] = None):
        self.transactions = transactions
        self.budgets = budgets or []

        self.spending = SpendingAnalyzer(transactions)
        self.recurring = RecurringTransactionDetector(transactions)
        self.budget = BudgetMonitor(transactions, self.budgets)
        self.cashflow = CashFlowAnalyzer(transactions)

    def generate_insights(self) -> List[Dict[str, Any]]:
        insights = []

        patterns = self.recurring.detect_recurring()
        insights.extend(self.spending.detect_anomalies())
        insights.extend(self.spending.analyze_category_trends())
        insights.extend(self.budget.check_budget_status())
        insights.extend(self.cashflow.analyze_cash_flow())

        for p in patterns:
            if p.confidence >= 0.7:
                insights.append(Insight(
                    type=InsightType.RECURRING_DETECTION,
                    severity=Severity.INFO,
                    title="Recurring Expense Detected",
                    description=f"{p.frequency.capitalize()} charge detected.",
                    amount=p.avg_amount,
                    category=p.category
                ))

        return [i.to_dict() for i in insights]

    def get_dashboard_summary(self) -> Dict[str, Any]:
        insights = self.generate_insights()
        recent = [t for t in self.transactions if (datetime.now() - t.date).days <= 30]

        income = sum((t.amount for t in recent if t.is_income), Decimal("0"))
        expenses = sum((t.amount for t in recent if not t.is_income), Decimal("0"))

        return {
            "total_insights": len(insights),
            "critical_alerts": len([i for i in insights if i["severity"] == "critical"]),
            "monthly_income": float(income),
            "monthly_expenses": float(expenses),
            "net_cashflow": float(income - expenses),
            "savings_rate": float(((income - expenses) / income) * 100) if income else 0.0,
            "top_insights": insights[:5]
        }
