"""
MonetIQ Financial Intelligence System
Overspending Analytics Module

Production-safe, Streamlit-compatible overspending detection engine.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import pandas as pd
import numpy as np
from scipy import stats


# =============================================================================
# LOGGER CONFIG
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SpendingThreshold(Enum):
    NORMAL = "normal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


class AnalysisMethod(Enum):
    STANDARD_DEVIATION = "std_dev"
    INTERQUARTILE_RANGE = "iqr"
    MOVING_AVERAGE = "moving_avg"
    PERCENTILE = "percentile"
    ZSCORE = "zscore"


# Explicit severity ordering (DO NOT rely on Enum order)
SEVERITY_ORDER = {
    SpendingThreshold.NORMAL: 0,
    SpendingThreshold.MODERATE: 1,
    SpendingThreshold.SIGNIFICANT: 2,
    SpendingThreshold.CRITICAL: 3,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class OverspendingAlert:
    category: str
    current_amount: float
    expected_amount: float
    deviation_amount: float
    deviation_percentage: float
    severity: SpendingThreshold
    period: str
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Streamlit-safe serialization."""
        return {
            "category": self.category,
            "current_amount": float(round(self.current_amount, 2)),
            "expected_amount": float(round(self.expected_amount, 2)),
            "deviation_amount": float(round(self.deviation_amount, 2)),
            "deviation_percentage": float(round(self.deviation_percentage, 2)),
            "severity": self.severity.value,
            "period": str(self.period),
            "timestamp": self.timestamp.isoformat(),
            "recommendations": list(self.recommendations),
        }


@dataclass
class CategoryBudget:
    category: str
    monthly_limit: float
    warning_threshold: float = 0.8
    critical_threshold: float = 1.0


# =============================================================================
# OVESPENDING ANALYZER
# =============================================================================

class OverspendingAnalyzer:

    def __init__(
        self,
        sensitivity: float = 2.0,
        lookback_months: int = 6,
        min_transactions: int = 3,
    ):
        self.sensitivity = sensitivity
        self.lookback_months = lookback_months
        self.min_transactions = min_transactions
        self.budgets: Dict[str, CategoryBudget] = {}

        logger.info(
            "OverspendingAnalyzer initialized "
            f"(sensitivity={sensitivity}, lookback={lookback_months})"
        )

    # -------------------------------------------------------------------------

    def set_category_budget(
        self,
        category: str,
        monthly_limit: float,
        warning_threshold: float = 0.8,
        critical_threshold: float = 1.0,
    ) -> None:
        if monthly_limit <= 0:
            raise ValueError("Monthly limit must be positive")

        self.budgets[category] = CategoryBudget(
            category=category,
            monthly_limit=float(monthly_limit),
            warning_threshold=float(warning_threshold),
            critical_threshold=float(critical_threshold),
        )

    # -------------------------------------------------------------------------

    def analyze_transactions(
        self,
        transactions_df: pd.DataFrame,
        method: AnalysisMethod = AnalysisMethod.ZSCORE,
    ) -> List[OverspendingAlert]:

        if transactions_df is None or transactions_df.empty:
            return []

        required = {"date", "category", "amount"}
        if not required.issubset(transactions_df.columns):
            raise ValueError(f"Missing required columns: {required}")

        df = self._prepare_data(transactions_df)
        alerts: List[OverspendingAlert] = []

        for category in df["category"].unique():
            alerts.extend(self._analyze_category(df, category, method))

        alerts.sort(
            key=lambda a: (
                SEVERITY_ORDER[a.severity],
                -a.deviation_percentage,
            ),
            reverse=True,
        )

        return alerts

    # -------------------------------------------------------------------------

    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").abs()
        df = df.dropna(subset=["amount"])

        df["year_month"] = df["date"].dt.strftime("%Y-%m")

        cutoff = datetime.now() - timedelta(days=self.lookback_months * 30)
        df = df[df["date"] >= cutoff]

        return df

    # -------------------------------------------------------------------------

    def _analyze_category(
        self,
        df: pd.DataFrame,
        category: str,
        method: AnalysisMethod,
    ) -> List[OverspendingAlert]:

        cat_df = df[df["category"] == category]
        if len(cat_df) < self.min_transactions:
            return []

        monthly = cat_df.groupby("year_month")["amount"].sum()

        if len(monthly) < 2:
            return []

        current_period = monthly.index[-1]
        current_value = float(monthly.iloc[-1])
        historical = monthly.iloc[:-1].astype(float)

        is_over, expected, severity = self._detect_overspending(
            current_value, historical, method
        )

        budget_severity = self._check_budget(category, current_value)
        if budget_severity:
            if not severity or SEVERITY_ORDER[budget_severity] > SEVERITY_ORDER[severity]:
                severity = budget_severity
                is_over = True

        if not is_over or not severity:
            return []

        expected = float(expected)
        deviation = current_value - expected
        deviation_pct = (deviation / expected * 100) if expected > 0 else 0.0

        return [
            OverspendingAlert(
                category=category,
                current_amount=current_value,
                expected_amount=expected,
                deviation_amount=deviation,
                deviation_percentage=deviation_pct,
                severity=severity,
                period=str(current_period),
                recommendations=self._generate_recommendations(
                    category, deviation_pct, severity
                ),
            )
        ]

    # -------------------------------------------------------------------------
    # STATISTICAL METHODS
    # -------------------------------------------------------------------------

    def _detect_overspending(
        self,
        current: float,
        historical: pd.Series,
        method: AnalysisMethod,
    ) -> Tuple[bool, float, Optional[SpendingThreshold]]:

        if historical.isnull().all():
            return False, current, None

        if method == AnalysisMethod.ZSCORE:
            return self._zscore_method(current, historical)
        if method == AnalysisMethod.STANDARD_DEVIATION:
            return self._std_dev_method(current, historical)
        if method == AnalysisMethod.INTERQUARTILE_RANGE:
            return self._iqr_method(current, historical)
        if method == AnalysisMethod.MOVING_AVERAGE:
            return self._moving_avg_method(current, historical)
        if method == AnalysisMethod.PERCENTILE:
            return self._percentile_method(current, historical)

        return False, current, None

    def _zscore_method(self, current: float, historical: pd.Series):
        mean = float(historical.mean())
        std = float(historical.std() or 0)

        if std == 0:
            return False, mean, None

        z = (current - mean) / std

        if z > self.sensitivity * 1.5:
            return True, mean, SpendingThreshold.CRITICAL
        if z > self.sensitivity:
            return True, mean, SpendingThreshold.SIGNIFICANT
        if z > self.sensitivity * 0.5:
            return True, mean, SpendingThreshold.MODERATE

        return False, mean, None

    def _std_dev_method(self, current, historical):
        mean = float(historical.mean())
        std = float(historical.std() or 0)

        if std == 0:
            return False, mean, None

        diff = current - mean

        if diff > std * 2:
            return True, mean, SpendingThreshold.CRITICAL
        if diff > std * 1.5:
            return True, mean, SpendingThreshold.SIGNIFICANT
        if diff > std:
            return True, mean, SpendingThreshold.MODERATE

        return False, mean, None

    def _iqr_method(self, current, historical):
        q1 = historical.quantile(0.25)
        q3 = historical.quantile(0.75)
        iqr = q3 - q1
        median = float(historical.median())

        if iqr == 0:
            return False, median, None

        if current > q3 + 3 * iqr:
            return True, median, SpendingThreshold.CRITICAL
        if current > q3 + 1.5 * iqr:
            return True, median, SpendingThreshold.SIGNIFICANT
        if current > q3:
            return True, median, SpendingThreshold.MODERATE

        return False, median, None

    def _moving_avg_method(self, current, historical):
        window = min(3, len(historical))
        avg = float(historical.tail(window).mean())

        if avg == 0:
            return False, avg, None

        pct = (current - avg) / avg * 100

        if pct > 50:
            return True, avg, SpendingThreshold.CRITICAL
        if pct > 30:
            return True, avg, SpendingThreshold.SIGNIFICANT
        if pct > 15:
            return True, avg, SpendingThreshold.MODERATE

        return False, avg, None

    def _percentile_method(self, current, historical):
        if historical.nunique() < 2:
            return False, float(historical.median()), None

        percentile = stats.percentileofscore(historical, current)
        median = float(historical.median())

        if percentile > 95:
            return True, median, SpendingThreshold.CRITICAL
        if percentile > 90:
            return True, median, SpendingThreshold.SIGNIFICANT
        if percentile > 75:
            return True, median, SpendingThreshold.MODERATE

        return False, median, None

    # -------------------------------------------------------------------------

    def _check_budget(self, category: str, current_spending: float):
        if category not in self.budgets:
            return None

        budget = self.budgets[category]
        usage = current_spending / budget.monthly_limit

        if usage >= budget.critical_threshold:
            return SpendingThreshold.CRITICAL
        if usage >= budget.warning_threshold:
            return SpendingThreshold.SIGNIFICANT

        return None

    # -------------------------------------------------------------------------

    def _generate_recommendations(
        self,
        category: str,
        deviation_pct: float,
        severity: SpendingThreshold,
    ) -> List[str]:

        recs: List[str] = []

        if severity == SpendingThreshold.CRITICAL:
            recs.append("⚠️ Immediate spending reduction required")
        elif severity == SpendingThreshold.SIGNIFICANT:
            recs.append("Review recent purchases and reduce discretionary spend")

        if category.lower() in ("dining", "food"):
            recs.append("Plan meals and reduce eating out")
        elif "entertainment" in category.lower():
            recs.append("Cancel unused subscriptions")

        return recs[:5]

    # -------------------------------------------------------------------------

    def get_spending_summary(self, transactions_df: pd.DataFrame) -> Dict[str, Any]:

        if transactions_df.empty:
            return {}

        df = self._prepare_data(transactions_df)

        summary = {
            "total_spending": float(df["amount"].sum()),
            "transaction_count": int(len(df)),
            "period": f"{df['date'].min().date()} → {df['date'].max().date()}",
            "categories": {},
        }

        grouped = df.groupby("category")["amount"]

        for cat, series in grouped:
            summary["categories"][cat] = {
                "total": float(series.sum()),
                "average": float(series.mean()),
                "count": int(series.count()),
            }

        return summary


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_analyze(
    transactions_df: pd.DataFrame,
    sensitivity: float = 2.0,
    method: AnalysisMethod = AnalysisMethod.ZSCORE,
) -> List[Dict[str, Any]]:
    analyzer = OverspendingAnalyzer(sensitivity=sensitivity)
    alerts = analyzer.analyze_transactions(transactions_df, method)
    return [a.to_dict() for a in alerts]
