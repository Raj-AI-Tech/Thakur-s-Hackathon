"""
MonetIQ Savings Goals Module - Savings Intelligence Engine
============================================================

This module provides comprehensive savings goal management, tracking, and analysis.
It acts as a personal financial planner that:
- Manages multiple savings goals
- Tracks progress intelligently
- Evaluates goal feasibility in real-time
- Detects goal slippage and conflicts
- Integrates with stress and overspending signals
- Provides predictive analytics and actionable insights

Author: MonetIQ Development Team
Version: 1.0.0
"""

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json
from dataclasses import dataclass, asdict
from collections import defaultdict


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class GoalPriority(Enum):
    """Priority levels for savings goals"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class GoalHealth(Enum):
    """Health status indicators for savings goals"""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OFF_TRACK = "off_track"
    UNREALISTIC = "unrealistic"
    COMPLETED = "completed"


class GoalType(Enum):
    """Standard goal categories"""
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    GADGET = "gadget"
    HOME_DOWN_PAYMENT = "home_down_payment"
    RETIREMENT = "retirement"
    CUSTOM = "custom"


@dataclass
class SavingsGoal:
    """Data class representing a savings goal"""
    goal_id: str
    name: str
    goal_type: str
    target_amount: float
    current_amount: float
    target_date: Optional[str]  # ISO format date
    priority: str
    monthly_contribution: float
    created_date: str
    last_updated: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def get(self, param, param1):
        pass


@dataclass
class GoalProgress:
    """Data class for goal progress metrics"""
    goal_id: str
    completion_percentage: float
    time_elapsed_percentage: float
    expected_progress: float
    actual_progress: float
    variance: float
    on_track: bool
    months_elapsed: int
    months_remaining: Optional[int]


# ============================================================================
# CORE SAVINGS GOALS ENGINE
# ============================================================================

class SavingsGoalsEngine:
    """
    Main engine for savings goal intelligence and analysis.
    Provides comprehensive goal management, tracking, and predictive analytics.
    """

    def __init__(self):
        """Initialize the savings goals engine"""
        self.goals: Dict[str, SavingsGoal] = {}
        self.income_data: Dict[str, Any] = {}
        self.expense_data: Dict[str, Any] = {}
        self.overspending_data: Dict[str, Any] = {}
        self.stress_data: Dict[str, Any] = {}
        self.state: Dict[str, Any] = {}

    # ========================================================================
    # DATA ACCESS LAYER
    # ========================================================================

    def load_state(self) -> Dict[str, Any]:
        """
        Load application state from storage.
        In production, this would call utils/storage.py

        Returns:
            Dict containing application state
        """
        try:
            # Production: from utils.storage import load_state
            # self.state = load_state()

            # For now, return structure for integration
            self.state = {
                "income": {},
                "expenses": {},
                "savings_goals": {},
                "overspending": {},
                "stress_index": {},
                "financial_health": {}
            }
            return self.state
        except Exception as e:
            print(f"Error loading state: {e}")
            return {}

    def get_income(self) -> Dict[str, Any]:
        """
        Retrieve income data from expense tracker.

        Returns:
            Dict containing income information
        """
        try:
            # Production: from core.expense_tracker import get_income_data
            # self.income_data = get_income_data()

            income = self.state.get("income", {})
            self.income_data = {
                "monthly_income": income.get("monthly_income", 0),
                "income_sources": income.get("sources", []),
                "income_stability": income.get("stability", "stable"),
                "last_3_months": income.get("last_3_months", [])
            }
            return self.income_data
        except Exception as e:
            print(f"Error retrieving income: {e}")
            return {"monthly_income": 0}

    def get_expenses(self) -> Dict[str, Any]:
        """
        Retrieve expense data from expense tracker.

        Returns:
            Dict containing expense breakdown
        """
        try:
            # Production: from core.expense_tracker import get_expenses_data
            # self.expense_data = get_expenses_data()

            expenses = self.state.get("expenses", {})
            self.expense_data = {
                "monthly_total": expenses.get("monthly_total", 0),
                "categories": expenses.get("categories", {}),
                "essential_expenses": expenses.get("essential", 0),
                "discretionary_expenses": expenses.get("discretionary", 0),
                "last_3_months": expenses.get("last_3_months", [])
            }
            return self.expense_data
        except Exception as e:
            print(f"Error retrieving expenses: {e}")
            return {"monthly_total": 0}

    def get_savings_goals(self) -> Dict[str, SavingsGoal]:
        """
        Retrieve all savings goals from state.

        Returns:
            Dict mapping goal_id to SavingsGoal objects
        """
        try:
            goals_data = self.state.get("savings_goals", {})
            self.goals = {}

            for goal_id, goal_info in goals_data.items():
                self.goals[goal_id] = SavingsGoal(
                    goal_id=goal_id,
                    name=goal_info.get("name", "Unnamed Goal"),
                    goal_type=goal_info.get("type", "custom"),
                    target_amount=float(goal_info.get("target_amount", 0)),
                    current_amount=float(goal_info.get("current_amount", 0)),
                    target_date=goal_info.get("target_date"),
                    priority=goal_info.get("priority", "medium"),
                    monthly_contribution=float(goal_info.get("monthly_contribution", 0)),
                    created_date=goal_info.get("created_date", datetime.now().isoformat()),
                    last_updated=goal_info.get("last_updated", datetime.now().isoformat()),
                    description=goal_info.get("description")
                )

            return self.goals
        except Exception as e:
            print(f"Error retrieving savings goals: {e}")
            return {}

    def get_overspending_data(self) -> Dict[str, Any]:
        """
        Retrieve overspending analysis from analytics module.

        Returns:
            Dict containing overspending alerts and patterns
        """
        try:
            # Production: from analytics.overspending import get_overspending_analysis
            # self.overspending_data = get_overspending_analysis()

            self.overspending_data = self.state.get("overspending", {
                "is_overspending": False,
                "overspending_amount": 0,
                "affected_categories": [],
                "severity": "low",
                "trend": "stable"
            })
            return self.overspending_data
        except Exception as e:
            print(f"Error retrieving overspending data: {e}")
            return {"is_overspending": False}

    def get_stress_index(self) -> Dict[str, Any]:
        """
        Retrieve financial stress index from core module.

        Returns:
            Dict containing stress metrics and thresholds
        """
        try:
            # Production: from core.stress_index import get_stress_metrics
            # self.stress_data = get_stress_metrics()

            self.stress_data = self.state.get("stress_index", {
                "stress_score": 0,
                "stress_level": "low",
                "is_stressed": False,
                "stress_factors": []
            })
            return self.stress_data
        except Exception as e:
            print(f"Error retrieving stress index: {e}")
            return {"stress_score": 0, "is_stressed": False}

    # ========================================================================
    # CORE GOAL LOGIC
    # ========================================================================

    def calculate_goal_progress(self, goal: SavingsGoal) -> GoalProgress:
        """
        Calculate detailed progress metrics for a savings goal.

        Args:
            goal: SavingsGoal object

        Returns:
            GoalProgress object with detailed metrics
        """
        # Completion percentage
        completion_percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        completion_percentage = min(completion_percentage, 100)

        # Time calculations
        created_date = datetime.fromisoformat(goal.created_date)
        current_date = datetime.now()
        months_elapsed = max(1, (current_date.year - created_date.year) * 12 +
                             (current_date.month - created_date.month))

        months_remaining = None
        time_elapsed_percentage = 0

        if goal.target_date:
            target_date = datetime.fromisoformat(goal.target_date)
            total_months = max(1, (target_date.year - created_date.year) * 12 +
                               (target_date.month - created_date.month))
            months_remaining = max(0, (target_date.year - current_date.year) * 12 +
                                   (target_date.month - current_date.month))
            time_elapsed_percentage = (months_elapsed / total_months * 100) if total_months > 0 else 0

        # Expected vs actual progress
        expected_progress = time_elapsed_percentage if goal.target_date else 0
        actual_progress = completion_percentage
        variance = actual_progress - expected_progress

        # On track determination
        on_track = True
        if goal.target_date:
            # On track if within 10% variance or ahead of schedule
            on_track = variance >= -10
        else:
            # For goals without dates, check if monthly contribution is being met
            expected_amount = goal.monthly_contribution * months_elapsed
            on_track = goal.current_amount >= (expected_amount * 0.9)  # 90% threshold

        return GoalProgress(
            goal_id=goal.goal_id,
            completion_percentage=round(completion_percentage, 2),
            time_elapsed_percentage=round(time_elapsed_percentage, 2),
            expected_progress=round(expected_progress, 2),
            actual_progress=round(actual_progress, 2),
            variance=round(variance, 2),
            on_track=on_track,
            months_elapsed=months_elapsed,
            months_remaining=months_remaining
        )

    def estimate_monthly_savings_capacity(self) -> Dict[str, float]:
        """
        Calculate dynamic monthly savings capacity based on income, expenses, and stress.

        Returns:
            Dict with conservative, moderate, and aggressive savings estimates
        """
        income = self.get_income()
        expenses = self.get_expenses()
        stress = self.get_stress_index()
        overspending = self.get_overspending_data()

        monthly_income = income.get("monthly_income", 0)
        monthly_expenses = expenses.get("monthly_total", 0)

        # Base savings capacity
        base_capacity = monthly_income - monthly_expenses

        # Adjust for overspending
        if overspending.get("is_overspending", False):
            overspending_amount = overspending.get("overspending_amount", 0)
            base_capacity -= overspending_amount * 0.5  # Assume 50% continues

        # Stress-aware adjustments
        stress_multiplier = 1.0
        if stress.get("is_stressed", False):
            stress_score = stress.get("stress_score", 0)
            # Higher stress = more conservative savings recommendation
            stress_multiplier = max(0.6, 1.0 - (stress_score / 100) * 0.4)

        # Calculate ranges
        conservative = max(0, base_capacity * 0.2 * stress_multiplier)  # 20% of capacity
        moderate = max(0, base_capacity * 0.4 * stress_multiplier)  # 40% of capacity
        aggressive = max(0, base_capacity * 0.7 * stress_multiplier)  # 70% of capacity
        maximum = max(0, base_capacity * stress_multiplier)  # 100% of capacity

        return {
            "base_capacity": round(base_capacity, 2),
            "conservative": round(conservative, 2),
            "moderate": round(moderate, 2),
            "aggressive": round(aggressive, 2),
            "maximum": round(maximum, 2),
            "stress_adjusted": stress_multiplier < 1.0,
            "overspending_impact": overspending.get("is_overspending", False)
        }

    def evaluate_goal_feasibility(self, goal: SavingsGoal) -> Dict[str, Any]:
        """
        Evaluate whether a goal is realistically achievable.

        Args:
            goal: SavingsGoal object

        Returns:
            Dict with feasibility analysis and human-readable explanation
        """
        capacity = self.estimate_monthly_savings_capacity()
        progress = self.calculate_goal_progress(goal)

        remaining_amount = goal.target_amount - goal.current_amount

        # Calculate required monthly savings
        if goal.target_date and progress.months_remaining:
            if progress.months_remaining > 0:
                required_monthly = remaining_amount / progress.months_remaining
            else:
                required_monthly = remaining_amount  # Due now
        else:
            # No target date - use expected contribution
            required_monthly = goal.monthly_contribution

        # Feasibility checks
        is_feasible = True
        feasibility_score = 100
        reasons = []
        recommendations = []

        # Check 1: Required vs Available Capacity
        if required_monthly > capacity["maximum"]:
            is_feasible = False
            feasibility_score -= 50
            reasons.append(
                f"Required monthly savings (₹{required_monthly:,.0f}) exceeds maximum capacity (₹{capacity['maximum']:,.0f})")
            recommendations.append(
                f"Consider extending target date or reducing goal amount by ₹{(required_monthly - capacity['maximum']) * (progress.months_remaining or 12):,.0f}")
        elif required_monthly > capacity["aggressive"]:
            feasibility_score -= 20
            reasons.append(f"Goal requires aggressive savings (₹{required_monthly:,.0f}/month)")
            recommendations.append("This goal is achievable but requires significant financial discipline")
        elif required_monthly > capacity["moderate"]:
            feasibility_score -= 10
            reasons.append("Goal requires above-moderate savings commitment")

        # Check 2: Stress Impact
        if self.stress_data.get("is_stressed", False):
            feasibility_score -= 15
            reasons.append("Current financial stress may impact savings ability")
            recommendations.append("Focus on stress reduction and expense optimization first")

        # Check 3: Overspending Impact
        if self.overspending_data.get("is_overspending", False):
            feasibility_score -= 15
            severity = self.overspending_data.get("severity", "low")
            reasons.append(f"Active overspending ({severity} severity) threatens goal progress")
            recommendations.append(
                "Address overspending in discretionary categories before increasing goal contributions")

        # Check 4: Historical Performance
        if progress.variance < -20:
            feasibility_score -= 20
            reasons.append(f"Goal is {abs(progress.variance):.0f}% behind schedule")
            recommendations.append("Review and adjust monthly contribution or extend timeline")

        # Check 5: Timeline Realism
        if goal.target_date and progress.months_remaining is not None:
            if progress.months_remaining < 3 and remaining_amount > capacity["maximum"] * 3:
                is_feasible = False
                feasibility_score -= 30
                reasons.append("Insufficient time remaining to reach goal")
                recommendations.append(
                    f"Extend deadline by at least {int(remaining_amount / capacity['moderate']) - progress.months_remaining} months")

        feasibility_score = max(0, feasibility_score)

        # Generate summary
        if feasibility_score >= 80:
            summary = "Highly feasible - goal is well within reach"
        elif feasibility_score >= 60:
            summary = "Feasible with discipline - stay focused on contributions"
        elif feasibility_score >= 40:
            summary = "Challenging but possible - requires optimization"
        else:
            summary = "Unrealistic under current conditions - adjustment needed"

        return {
            "is_feasible": is_feasible,
            "feasibility_score": feasibility_score,
            "required_monthly": round(required_monthly, 2),
            "available_capacity": capacity["moderate"],
            "capacity_utilization": round(
                (required_monthly / capacity["maximum"] * 100) if capacity["maximum"] > 0 else 0, 2),
            "summary": summary,
            "reasons": reasons,
            "recommendations": recommendations
        }

    def detect_goal_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect conflicts between multiple goals competing for limited savings capacity.

        Returns:
            List of conflict descriptions with affected goals
        """
        if not self.goals:
            return []

        capacity = self.estimate_monthly_savings_capacity()
        conflicts = []

        # Calculate total required monthly savings
        total_required = sum(goal.monthly_contribution for goal in self.goals.values())

        # Conflict 1: Total requirements exceed capacity
        if total_required > capacity["maximum"]:
            excess = total_required - capacity["maximum"]
            conflicts.append({
                "type": "capacity_overload",
                "severity": "high",
                "description": f"All goals require ₹{total_required:,.0f}/month but maximum capacity is ₹{capacity['maximum']:,.0f}",
                "impact": f"₹{excess:,.0f} shortfall per month",
                "affected_goals": list(self.goals.keys()),
                "recommendation": "Prioritize goals or extend timelines"
            })

        # Conflict 2: High priority goals competing
        high_priority_goals = [g for g in self.goals.values() if g.priority == "high"]
        if len(high_priority_goals) > 1:
            total_high_priority = sum(g.monthly_contribution for g in high_priority_goals)
            if total_high_priority > capacity["aggressive"]:
                conflicts.append({
                    "type": "priority_conflict",
                    "severity": "medium",
                    "description": f"Multiple high-priority goals competing for ₹{total_high_priority:,.0f}/month",
                    "affected_goals": [g.goal_id for g in high_priority_goals],
                    "recommendation": "Re-evaluate goal priorities or adjust contribution amounts"
                })

        # Conflict 3: Short-term goals hurting long-term stability
        short_term_goals = []
        long_term_goals = []

        for goal in self.goals.values():
            if goal.target_date:
                target_date = datetime.fromisoformat(goal.target_date)
                months_away = (target_date.year - datetime.now().year) * 12 + \
                              (target_date.month - datetime.now().month)

                if months_away <= 12:
                    short_term_goals.append(goal)
                else:
                    long_term_goals.append(goal)

        if short_term_goals and long_term_goals:
            short_term_required = sum(g.monthly_contribution for g in short_term_goals)
            if short_term_required > capacity["moderate"]:
                conflicts.append({
                    "type": "temporal_conflict",
                    "severity": "medium",
                    "description": "Short-term goal focus may compromise long-term financial stability",
                    "affected_goals": {
                        "short_term": [g.goal_id for g in short_term_goals],
                        "long_term": [g.goal_id for g in long_term_goals]
                    },
                    "recommendation": "Ensure emergency fund and retirement goals maintain minimum contributions"
                })

        # Conflict 4: Goals impossible under current lifestyle
        for goal in self.goals.values():
            feasibility = self.evaluate_goal_feasibility(goal)
            if not feasibility["is_feasible"]:
                conflicts.append({
                    "type": "lifestyle_conflict",
                    "severity": "high",
                    "description": f"Goal '{goal.name}' is unachievable under current spending patterns",
                    "affected_goals": [goal.goal_id],
                    "feasibility_score": feasibility["feasibility_score"],
                    "recommendation": feasibility["recommendations"][0] if feasibility[
                        "recommendations"] else "Review goal parameters"
                })

        return conflicts

    # ========================================================================
    # RISK & HEALTH ANALYSIS
    # ========================================================================

    def assign_goal_health_status(self, goal: SavingsGoal) -> Tuple[GoalHealth, str]:
        """
        Assign health status to a goal based on progress, feasibility, and external factors.

        Args:
            goal: SavingsGoal object

        Returns:
            Tuple of (GoalHealth enum, explanation string)
        """
        progress = self.calculate_goal_progress(goal)
        feasibility = self.evaluate_goal_feasibility(goal)

        # Check if completed
        if progress.completion_percentage >= 100:
            return GoalHealth.COMPLETED, "Goal successfully completed! 🎉"

        # Check if unrealistic
        if not feasibility["is_feasible"] or feasibility["feasibility_score"] < 30:
            return GoalHealth.UNREALISTIC, feasibility["summary"]

        # Analyze based on progress and variance
        if progress.on_track and progress.variance >= -5:
            if feasibility["feasibility_score"] >= 70:
                return GoalHealth.ON_TRACK, "Goal is progressing as planned"
            else:
                return GoalHealth.AT_RISK, "On track but capacity concerns exist"

        elif progress.variance >= -20:
            return GoalHealth.AT_RISK, f"Goal is {abs(progress.variance):.0f}% behind schedule"

        else:
            return GoalHealth.OFF_TRACK, f"Goal is significantly behind (variance: {progress.variance:.0f}%)"

    def adjust_goals_using_stress(self) -> Dict[str, Any]:
        """
        Adjust goal recommendations based on financial stress levels.

        Returns:
            Dict with stress-adjusted recommendations
        """
        stress = self.get_stress_index()
        adjustments = {
            "stress_detected": stress.get("is_stressed", False),
            "stress_level": stress.get("stress_level", "low"),
            "recommendations": [],
            "frozen_goals": [],
            "reduced_contributions": []
        }

        if not stress.get("is_stressed", False):
            adjustments["recommendations"].append("No stress detected - maintain current goal strategy")
            return adjustments

        stress_score = stress.get("stress_score", 0)

        # High stress (>70): Recommend freezing low-priority goals
        if stress_score > 70:
            for goal in self.goals.values():
                if goal.priority == "low":
                    adjustments["frozen_goals"].append({
                        "goal_id": goal.goal_id,
                        "goal_name": goal.name,
                        "reason": "Low priority goal frozen due to high financial stress"
                    })

            adjustments["recommendations"].append("Focus only on essential goals (emergency fund, critical deadlines)")
            adjustments["recommendations"].append("Temporarily pause low-priority goals until stress reduces")

        # Moderate stress (40-70): Recommend reducing contributions
        elif stress_score > 40:
            for goal in self.goals.values():
                if goal.priority in ["low", "medium"]:
                    reduced_amount = goal.monthly_contribution * 0.5
                    adjustments["reduced_contributions"].append({
                        "goal_id": goal.goal_id,
                        "goal_name": goal.name,
                        "current_contribution": goal.monthly_contribution,
                        "recommended_contribution": round(reduced_amount, 2),
                        "reason": "Reduced contribution due to moderate financial stress"
                    })

            adjustments["recommendations"].append("Consider reducing non-essential goal contributions by 30-50%")
            adjustments["recommendations"].append("Prioritize financial stability and stress reduction")

        # Low stress: General caution
        else:
            adjustments["recommendations"].append("Monitor stress levels and adjust goals if stress increases")

        return adjustments

    def integrate_overspending_impact(self) -> Dict[str, Any]:
        """
        Analyze how overspending patterns impact savings goals.

        Returns:
            Dict with overspending impact analysis
        """
        overspending = self.get_overspending_data()

        impact = {
            "overspending_detected": overspending.get("is_overspending", False),
            "severity": overspending.get("severity", "low"),
            "affected_goals": [],
            "estimated_delay": {},
            "recovery_actions": []
        }

        if not overspending.get("is_overspending", False):
            return impact

        overspending_amount = overspending.get("overspending_amount", 0)
        affected_categories = overspending.get("affected_categories", [])

        # Calculate impact on each goal
        for goal in self.goals.values():
            progress = self.calculate_goal_progress(goal)
            remaining = goal.target_amount - goal.current_amount

            # Estimate delay if overspending continues
            if goal.monthly_contribution > 0:
                reduced_contribution = max(0, goal.monthly_contribution - (overspending_amount * 0.3))

                if reduced_contribution > 0:
                    original_months = remaining / goal.monthly_contribution
                    new_months = remaining / reduced_contribution
                    delay_months = int(new_months - original_months)
                else:
                    delay_months = 999  # Indefinite delay

                impact["affected_goals"].append(goal.goal_id)
                impact["estimated_delay"][goal.goal_id] = {
                    "goal_name": goal.name,
                    "delay_months": delay_months,
                    "impact_severity": "high" if delay_months > 6 else "medium" if delay_months > 3 else "low"
                }

        # Generate recovery actions
        if affected_categories:
            impact["recovery_actions"].append(
                f"Reduce spending in: {', '.join(affected_categories[:3])}"
            )

        impact["recovery_actions"].append(
            f"Reclaim ₹{overspending_amount:,.0f}/month to restore goal timelines"
        )

        if overspending.get("severity") == "high":
            impact["recovery_actions"].append(
                "Critical: Review and freeze non-essential subscriptions and expenses"
            )

        return impact

    # ========================================================================
    # PREDICTIVE ANALYTICS
    # ========================================================================

    def predict_goal_completion(self, goal: SavingsGoal) -> Dict[str, Any]:
        """
        Predict when a goal will be completed based on historical trends.

        Args:
            goal: SavingsGoal object

        Returns:
            Dict with completion prediction and probability
        """
        progress = self.calculate_goal_progress(goal)
        remaining = goal.target_amount - goal.current_amount

        # Analyze historical contribution rate
        # In production, this would analyze last 3-6 months of actual contributions
        months_elapsed = progress.months_elapsed
        if months_elapsed > 0:
            actual_monthly_rate = goal.current_amount / months_elapsed
        else:
            actual_monthly_rate = goal.monthly_contribution

        # Adjust for overspending and stress
        overspending = self.get_overspending_data()
        stress = self.get_stress_index()

        adjustment_factor = 1.0
        if overspending.get("is_overspending", False):
            adjustment_factor *= 0.85  # 15% reduction
        if stress.get("is_stressed", False):
            adjustment_factor *= 0.90  # 10% reduction

        predicted_monthly_rate = actual_monthly_rate * adjustment_factor

        # Calculate predicted completion
        if predicted_monthly_rate > 0:
            months_to_completion = remaining / predicted_monthly_rate
            predicted_date = datetime.now() + timedelta(days=months_to_completion * 30)

            # Calculate success probability
            if goal.target_date:
                target_date = datetime.fromisoformat(goal.target_date)
                if predicted_date <= target_date:
                    probability = min(0.95, 0.7 + (progress.variance / 100) * 0.25)
                else:
                    delay_days = (predicted_date - target_date).days
                    probability = max(0.1, 0.7 - (delay_days / 365) * 0.3)
            else:
                # No deadline - base on historical consistency
                probability = 0.8 if progress.variance >= -10 else 0.6
        else:
            months_to_completion = 999
            predicted_date = None
            probability = 0.1

        return {
            "goal_id": goal.goal_id,
            "goal_name": goal.name,
            "predicted_completion_date": predicted_date.isoformat() if predicted_date else None,
            "months_to_completion": round(months_to_completion, 1),
            "success_probability": round(probability, 2),
            "predicted_monthly_rate": round(predicted_monthly_rate, 2),
            "target_monthly_rate": goal.monthly_contribution,
            "confidence": "high" if months_elapsed >= 3 else "medium" if months_elapsed >= 1 else "low"
        }

    def estimate_goal_delay(self, goal: SavingsGoal) -> Dict[str, Any]:
        """
        Estimate potential delays in goal completion.

        Args:
            goal: SavingsGoal object

        Returns:
            Dict with delay estimation and risk factors
        """
        prediction = self.predict_goal_completion(goal)

        delay_info = {
            "goal_id": goal.goal_id,
            "has_delay": False,
            "delay_months": 0,
            "delay_reasons": [],
            "risk_level": "low"
        }

        if not goal.target_date:
            return delay_info

        target_date = datetime.fromisoformat(goal.target_date)
        predicted_date_str = prediction.get("predicted_completion_date")

        if not predicted_date_str:
            delay_info["has_delay"] = True
            delay_info["delay_months"] = 999
            delay_info["risk_level"] = "critical"
            delay_info["delay_reasons"].append("Goal appears unachievable at current rate")
            return delay_info

        predicted_date = datetime.fromisoformat(predicted_date_str)

        if predicted_date > target_date:
            delay_days = (predicted_date - target_date).days
            delay_months = delay_days / 30

            delay_info["has_delay"] = True
            delay_info["delay_months"] = round(delay_months, 1)

            # Determine risk level
            if delay_months > 6:
                delay_info["risk_level"] = "high"
            elif delay_months > 3:
                delay_info["risk_level"] = "medium"
            else:
                delay_info["risk_level"] = "low"

            # Identify reasons
            progress = self.calculate_goal_progress(goal)
            if progress.variance < -15:
                delay_info["delay_reasons"].append("Significantly behind schedule")

            if self.overspending_data.get("is_overspending"):
                delay_info["delay_reasons"].append("Overspending reducing available savings")

            if self.stress_data.get("is_stressed"):
                delay_info["delay_reasons"].append("Financial stress impacting contributions")

            feasibility = self.evaluate_goal_feasibility(goal)
            if feasibility["capacity_utilization"] > 80:
                delay_info["delay_reasons"].append("Limited savings capacity")

        return delay_info

    # ========================================================================
    # SMART INSIGHTS GENERATION
    # ========================================================================

    def generate_savings_insights(self) -> List[Dict[str, Any]]:
        """
        Generate actionable insights about savings goals.

        Returns:
            List of insight dictionaries with recommendations
        """
        insights = []

        if not self.goals:
            return [{
                "type": "no_goals",
                "priority": "high",
                "title": "No Savings Goals Set",
                "message": "Start building your financial future by creating your first savings goal",
                "action": "Create a goal"
            }]

        capacity = self.estimate_monthly_savings_capacity()

        # Insight 1: Capacity utilization
        total_contributions = sum(g.monthly_contribution for g in self.goals.values())
        utilization = (total_contributions / capacity["maximum"] * 100) if capacity["maximum"] > 0 else 0

        if utilization < 50:
            insights.append({
                "type": "underutilized_capacity",
                "priority": "medium",
                "title": "Opportunity to Save More",
                "message": f"You're using only {utilization:.0f}% of your savings capacity (₹{capacity['maximum'] - total_contributions:,.0f}/month available)",
                "action": "Consider increasing goal contributions or adding new goals"
            })
        elif utilization > 90:
            insights.append({
                "type": "overutilized_capacity",
                "priority": "high",
                "title": "Savings Capacity Strained",
                "message": f"Your goals require {utilization:.0f}% of available savings capacity",
                "action": "Review goal priorities or extend timelines"
            })

        # Insight 2: Goal-specific insights
        for goal in self.goals.values():
            progress = self.calculate_goal_progress(goal)
            feasibility = self.evaluate_goal_feasibility(goal)
            prediction = self.predict_goal_completion(goal)

            # Behind schedule warning
            if progress.variance < -20:
                additional_needed = (goal.target_amount * abs(progress.variance) / 100) / max(1,
                                                                                              progress.months_remaining or 12)
                insights.append({
                    "type": "behind_schedule",
                    "priority": "high",
                    "goal_id": goal.goal_id,
                    "title": f"{goal.name}: Behind Schedule",
                    "message": f"You need ₹{additional_needed:,.0f} more per month to meet your target date",
                    "action": f"Increase monthly contribution or extend deadline by {abs(progress.variance) / 10:.0f} months"
                })

            # Near completion encouragement
            elif progress.completion_percentage > 80 and progress.completion_percentage < 100:
                remaining = goal.target_amount - goal.current_amount
                insights.append({
                    "type": "near_completion",
                    "priority": "low",
                    "goal_id": goal.goal_id,
                    "title": f"{goal.name}: Almost There!",
                    "message": f"Only ₹{remaining:,.0f} remaining to reach your goal",
                    "action": "Stay focused - you're in the home stretch"
                })

            # Unrealistic goal warning
            if not feasibility["is_feasible"]:
                insights.append({
                    "type": "unrealistic_goal",
                    "priority": "critical",
                    "goal_id": goal.goal_id,
                    "title": f"{goal.name}: Needs Adjustment",
                    "message": feasibility["summary"],
                    "action": feasibility["recommendations"][0] if feasibility[
                        "recommendations"] else "Review goal parameters"
                })

        # Insight 3: Overspending impact
        overspending_impact = self.integrate_overspending_impact()
        if overspending_impact["overspending_detected"]:
            total_delay = sum(
                d.get("delay_months", 0)
                for d in overspending_impact["estimated_delay"].values()
            )
            if total_delay > 0:
                insights.append({
                    "type": "overspending_impact",
                    "priority": "high",
                    "title": "Overspending Delaying Goals",
                    "message": f"Current overspending could delay goals by {total_delay:.0f} months total",
                    "action": overspending_impact["recovery_actions"][0] if overspending_impact[
                        "recovery_actions"] else "Reduce discretionary spending"
                })

        # Insight 4: Stress-based recommendations
        stress_adjustments = self.adjust_goals_using_stress()
        if stress_adjustments["stress_detected"] and stress_adjustments["recommendations"]:
            insights.append({
                "type": "stress_warning",
                "priority": "high",
                "title": "Financial Stress Detected",
                "message": stress_adjustments["recommendations"][0],
                "action": "Consider pausing or reducing low-priority goals temporarily"
            })

        # Insight 5: Goal conflicts
        conflicts = self.detect_goal_conflicts()
        if conflicts:
            high_severity_conflicts = [c for c in conflicts if c["severity"] == "high"]
            if high_severity_conflicts:
                insights.append({
                    "type": "goal_conflict",
                    "priority": "critical",
                    "title": "Goal Conflicts Detected",
                    "message": high_severity_conflicts[0]["description"],
                    "action": high_severity_conflicts[0]["recommendation"]
                })

        return insights

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_savings_goals_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive savings goals report for consumption by app.py

        This is the main public interface for the module.

        Returns:
            Complete report dictionary with all goal analytics
        """
        # Load all data
        self.load_state()
        self.get_income()
        self.get_expenses()
        self.get_savings_goals()
        self.get_overspending_data()
        self.get_stress_index()

        # Generate summary statistics
        total_goals = len(self.goals)
        total_target = sum(g.target_amount for g in self.goals.values())
        total_saved = sum(g.current_amount for g in self.goals.values())
        total_remaining = total_target - total_saved
        overall_progress = (total_saved / total_target * 100) if total_target > 0 else 0

        # Analyze each goal
        goals_analysis = {}
        goal_health_summary = {
            "on_track": 0,
            "at_risk": 0,
            "off_track": 0,
            "unrealistic": 0,
            "completed": 0
        }

        predictions = {}

        for goal_id, goal in self.goals.items():
            progress = self.calculate_goal_progress(goal)
            feasibility = self.evaluate_goal_feasibility(goal)
            health_status, health_explanation = self.assign_goal_health_status(goal)
            prediction = self.predict_goal_completion(goal)
            delay = self.estimate_goal_delay(goal)

            goals_analysis[goal_id] = {
                "goal_info": goal.to_dict(),
                "progress": asdict(progress),
                "feasibility": feasibility,
                "health_status": health_status.value,
                "health_explanation": health_explanation,
                "prediction": prediction,
                "delay_estimate": delay
            }

            # Update health summary
            goal_health_summary[health_status.value] += 1
            predictions[goal_id] = prediction

        # Generate insights and conflicts
        insights = self.generate_savings_insights()
        conflicts = self.detect_goal_conflicts()
        capacity = self.estimate_monthly_savings_capacity()
        stress_adjustments = self.adjust_goals_using_stress()
        overspending_impact = self.integrate_overspending_impact()

        # Compile final report
        report = {
            "summary": {
                "total_goals": total_goals,
                "total_target_amount": round(total_target, 2),
                "total_saved": round(total_saved, 2),
                "total_remaining": round(total_remaining, 2),
                "overall_progress_percentage": round(overall_progress, 2),
                "health_distribution": goal_health_summary,
                "goals_on_track": goal_health_summary["on_track"] + goal_health_summary["completed"],
                "goals_needing_attention": goal_health_summary["at_risk"] + goal_health_summary["off_track"] +
                                           goal_health_summary["unrealistic"]
            },
            "goals": goals_analysis,
            "goal_health": goal_health_summary,
            "conflicts": conflicts,
            "predictions": predictions,
            "insights": insights,
            "savings_capacity": capacity,
            "stress_adjustments": stress_adjustments,
            "overspending_impact": overspending_impact,
            "report_generated": datetime.now().isoformat(),
            "engine_version": "1.0.0"
        }

        return report


# ============================================================================
# CONVENIENCE FUNCTIONS FOR app.py
# ============================================================================

def create_savings_goal(
        name: str,
        target_amount: float,
        goal_type: str = "custom",
        target_date: Optional[str] = None,
        priority: str = "medium",
        monthly_contribution: float = 0,
        description: Optional[str] = None
) -> SavingsGoal:
    """
    Create a new savings goal object.

    Args:
        name: Goal name
        target_amount: Target amount to save
        goal_type: Type of goal (emergency_fund, vacation, etc.)
        target_date: Optional target date (ISO format)
        priority: Priority level (low, medium, high)
        monthly_contribution: Expected monthly contribution
        description: Optional description

    Returns:
        SavingsGoal object
    """
    import uuid

    goal = SavingsGoal(
        goal_id=str(uuid.uuid4()),
        name=name,
        goal_type=goal_type,
        target_amount=target_amount,
        current_amount=0,
        target_date=target_date,
        priority=priority,
        monthly_contribution=monthly_contribution,
        created_date=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        description=description
    )

    return goal


def get_savings_goals_report() -> Dict[str, Any]:
    """
    Main entry point for app.py to get complete savings goals analysis.

    Returns:
        Complete savings goals report dictionary
    """
    engine = SavingsGoalsEngine()
    return engine.get_savings_goals_report()


def quick_goal_health_check(goal_id: str) -> Dict[str, Any]:
    """
    Quick health check for a specific goal.

    Args:
        goal_id: ID of the goal to check

    Returns:
        Dict with health status and key metrics
    """
    engine = SavingsGoalsEngine()
    engine.load_state()
    engine.get_savings_goals()

    if goal_id not in engine.goals:
        return {"error": "Goal not found"}

    goal = engine.goals[goal_id]
    progress = engine.calculate_goal_progress(goal)
    health_status, explanation = engine.assign_goal_health_status(goal)

    return {
        "goal_id": goal_id,
        "goal_name": goal.name,
        "health_status": health_status.value,
        "explanation": explanation,
        "completion_percentage": progress.completion_percentage,
        "on_track": progress.on_track
    }


# ============================================================================
# USAGE EXAMPLE (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("MonetIQ Savings Goals Engine - Test Run")
    print("=" * 60)

    # Initialize engine
    engine = SavingsGoalsEngine()

    # Get complete report
    report = engine.get_savings_goals_report()

    # Display summary
    print(f"\nTotal Goals: {report['summary']['total_goals']}")
    print(f"Overall Progress: {report['summary']['overall_progress_percentage']:.1f}%")
    print(f"Goals On Track: {report['summary']['goals_on_track']}")
    print(f"Goals Needing Attention: {report['summary']['goals_needing_attention']}")

    print(f"\nSavings Capacity:")
    capacity = report['savings_capacity']
    print(f"  Conservative: ₹{capacity['conservative']:,.2f}/month")
    print(f"  Moderate: ₹{capacity['moderate']:,.2f}/month")
    print(f"  Aggressive: ₹{capacity['aggressive']:,.2f}/month")

    print(f"\nInsights: {len(report['insights'])} generated")
    for insight in report['insights'][:3]:  # Show first 3
        print(f"  - [{insight['priority']}] {insight['title']}")

    print("\n" + "=" * 60)
    print("Engine initialized successfully!")
