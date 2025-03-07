from typing import Dict, List
import pandas as pd
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CostInsight:
    type: str
    description: str
    impact: float
    recommendation: str
    priority: str  # high, medium, low

class CostAnalyzer:
    """Analyzes transactions for cost-saving opportunities"""
    
    def analyze_transactions(self, transactions: List[Dict]) -> Dict:
        """Analyze transactions and generate insights"""
        df = pd.DataFrame(transactions)
        df["date"] = pd.to_datetime(df["date"])
        
        insights = []
        
        # Analyze category distribution
        category_summary = self._analyze_categories(df)
        
        # Find recurring costs
        recurring_costs = self._analyze_recurring_costs(df)
        
        # Analyze spending patterns
        spending_patterns = self._analyze_spending_patterns(df)
        
        # Find potential savings
        savings_opportunities = self._find_savings_opportunities(df)
        
        return {
            "summary": category_summary,
            "recurring_costs": recurring_costs,
            "spending_patterns": spending_patterns,
            "savings_opportunities": savings_opportunities,
            "insights": insights
        }

    def _analyze_categories(self, df: pd.DataFrame) -> Dict:
        """Analyze spending by category"""
        category_stats = df.groupby("category").agg({
            "amount": ["sum", "count", "mean"]
        }).round(2)
        
        # Calculate percentage of total spending
        total_spend = df["amount"].sum()
        category_stats["amount", "percentage"] = (
            category_stats["amount", "sum"] / total_spend * 100
        ).round(2)
        
        return category_stats.to_dict()

    def _analyze_recurring_costs(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze recurring transactions"""
        # Group by description and amount
        recurring = df.groupby(["description", "amount"]).agg({
            "date": ["count", "min", "max"]
        }).reset_index()
        
        # Filter for likely recurring transactions
        recurring = recurring[recurring["date", "count"] > 1]
        
        # Calculate monthly cost
        recurring["monthly_cost"] = recurring["amount"]
        
        return recurring.to_dict("records")

    def _analyze_spending_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze spending patterns over time"""
        # Monthly spending
        monthly_spend = df.groupby([df["date"].dt.to_period("M")]).agg({
            "amount": ["sum", "count"]
        }).round(2)
        
        # Day of week analysis
        daily_spend = df.groupby(df["date"].dt.day_name()).agg({
            "amount": ["sum", "mean", "count"]
        }).round(2)
        
        # Hour of day analysis
        hourly_spend = df.groupby(df["date"].dt.hour).agg({
            "amount": ["sum", "mean", "count"]
        }).round(2)
        
        return {
            "monthly": monthly_spend.to_dict(),
            "daily": daily_spend.to_dict(),
            "hourly": hourly_spend.to_dict()
        }

    def _find_savings_opportunities(self, df: pd.DataFrame) -> List[CostInsight]:
        """Identify potential cost-saving opportunities"""
        insights = []
        
        # Check for duplicate subscriptions
        subscriptions = df[df["category"] == "Subscriptions"]
        if not subscriptions.empty:
            duplicate_subs = self._find_duplicate_subscriptions(subscriptions)
            if duplicate_subs:
                insights.append(CostInsight(
                    type="duplicate_subscriptions",
                    description="Found potential duplicate subscriptions",
                    impact=sum(d["amount"] for d in duplicate_subs),
                    recommendation="Review and consolidate duplicate subscriptions",
                    priority="high"
                ))
        
        # Check for high-fee transactions
        high_fees = df[df["amount"] < 0].nsmallest(10, "amount")
        if not high_fees.empty:
            insights.append(CostInsight(
                type="high_fees",
                description="Identified transactions with high fees",
                impact=abs(high_fees["amount"].sum()),
                recommendation="Consider alternative payment methods or providers",
                priority="medium"
            ))
        
        # Analyze spending trends
        monthly_increase = self._analyze_spending_trend(df)
        if monthly_increase > 0.1:  # 10% increase
            insights.append(CostInsight(
                type="spending_increase",
                description=f"Monthly spending increased by {monthly_increase:.1%}",
                impact=monthly_increase,
                recommendation="Review recent spending patterns for unnecessary increases",
                priority="medium"
            ))
        
        return insights

    def _find_duplicate_subscriptions(self, subscriptions: pd.DataFrame) -> List[Dict]:
        """Find potential duplicate subscriptions"""
        # Group similar descriptions
        similar_subs = subscriptions.groupby(["description", "amount"]).agg({
            "date": "count"
        }).reset_index()
        
        return similar_subs[similar_subs["date"] > 1].to_dict("records")

    def _analyze_spending_trend(self, df: pd.DataFrame) -> float:
        """Calculate the trend in monthly spending"""
        monthly_spend = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
        if len(monthly_spend) < 2:
            return 0
            
        first_month = monthly_spend.iloc[0]
        last_month = monthly_spend.iloc[-1]
        
        return (last_month - first_month) / first_month if first_month != 0 else 0 