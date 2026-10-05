"""
Budget monitoring and threshold alert guardrails.
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import Budget, SpendEvent


class BudgetService:

    @staticmethod
    def get_project_budget_status(db: Session, project_name: str) -> Dict[str, Any]:
        """Calculates current monthly spend vs budget for a given project."""
        budget = db.query(Budget).filter(Budget.project_name == project_name).first()
        monthly_limit = budget.monthly_limit_usd if budget else 1000.0
        alert_threshold = budget.alert_threshold_percent if budget else 80.0
        hard_cap = budget.hard_cap_enabled if budget else False

        # Current month start
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)

        spent = db.query(func.coalesce(func.sum(SpendEvent.total_cost_usd), 0.0))\
            .filter(SpendEvent.project_name == project_name, SpendEvent.timestamp >= start_of_month)\
            .scalar() or 0.0

        percent_used = (spent / monthly_limit * 100.0) if monthly_limit > 0 else 0.0
        status = "NORMAL"
        if percent_used >= 100.0:
            status = "EXCEEDED"
        elif percent_used >= alert_threshold:
            status = "WARNING"

        return {
            "project_name": project_name,
            "monthly_limit_usd": round(monthly_limit, 2),
            "current_spend_usd": round(spent, 2),
            "percent_used": round(percent_used, 1),
            "status": status,
            "alert_threshold_percent": alert_threshold,
            "hard_cap_enabled": hard_cap
        }

    @staticmethod
    def get_all_budgets(db: Session) -> List[Dict[str, Any]]:
        """Returns status for all known projects with budgets or spend."""
        projects = db.query(SpendEvent.project_name).distinct().all()
        project_names = {p[0] for p in projects}
        
        # Include budgeted projects that might not have spend yet
        budgeted = db.query(Budget.project_name).all()
        for b in budgeted:
            project_names.add(b[0])

        results = []
        for name in sorted(project_names):
            results.append(BudgetService.get_project_budget_status(db, name))
        return results
