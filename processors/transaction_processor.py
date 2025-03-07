from typing import Dict, List
import pandas as pd
from datetime import datetime
import re
from dataclasses import dataclass

@dataclass
class CategoryRule:
    name: str
    keywords: List[str]
    min_amount: float = None
    max_amount: float = None
    merchant_patterns: List[str] = None

class TransactionProcessor:
    """Handles transaction processing, categorization, and enrichment"""
    
    def __init__(self):
        self.category_rules = [
            CategoryRule(
                name="Subscriptions",
                keywords=["netflix", "spotify", "amazon prime", "subscription", "monthly", "yearly"],
                merchant_patterns=[r".*\bsubscription\b.*", r".*\bstreaming\b.*"]
            ),
            CategoryRule(
                name="Utilities",
                keywords=["electricity", "water", "gas", "internet", "phone", "utility", "broadband"],
                merchant_patterns=[r".*\benergy\b.*", r".*\butilities\b.*"]
            ),
            CategoryRule(
                name="Travel",
                keywords=["airline", "hotel", "train", "taxi", "uber", "flight", "booking"],
                merchant_patterns=[r".*\bairlines\b.*", r".*\bhotels\b.*"]
            ),
            CategoryRule(
                name="Food & Dining",
                keywords=["restaurant", "cafe", "grocery", "food", "takeaway", "delivery"],
                merchant_patterns=[r".*\brestaurant\b.*", r".*\bcafe\b.*"]
            ),
            CategoryRule(
                name="Entertainment",
                keywords=["cinema", "theater", "concert", "movie", "game", "entertainment"],
                merchant_patterns=[r".*\bcinema\b.*", r".*\btheater\b.*"]
            ),
            CategoryRule(
                name="Business",
                keywords=["office", "software", "consulting", "business", "professional"],
                merchant_patterns=[r".*\bconsulting\b.*", r".*\bservices\b.*"]
            ),
            CategoryRule(
                name="Shopping",
                keywords=["amazon", "shop", "store", "retail", "purchase"],
                merchant_patterns=[r".*\bstore\b.*", r".*\bshop\b.*"]
            )
        ]

    def process_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Process and enrich transactions"""
        df = pd.DataFrame(transactions)
        
        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])
        
        # Add categorization
        df["category"] = df.apply(self._categorize_transaction, axis=1)
        
        # Add month and year columns
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year
        
        # Add day of week
        df["day_of_week"] = df["date"].dt.day_name()
        
        # Add transaction tags
        df["tags"] = df.apply(self._generate_tags, axis=1)
        
        # Add spending patterns
        df["is_recurring"] = df.apply(self._detect_recurring_pattern, axis=1)
        
        return df.to_dict("records")

    def _categorize_transaction(self, row) -> str:
        """Categorize a single transaction"""
        description = str(row["description"]).lower()
        merchant = str(row["merchant"]).lower() if row["merchant"] else ""
        amount = float(row["amount"]) if row["amount"] else 0
        
        for rule in self.category_rules:
            # Check keywords in description
            if any(keyword in description for keyword in rule.keywords):
                return rule.name
                
            # Check merchant patterns
            if rule.merchant_patterns and merchant:
                if any(re.match(pattern, merchant) for pattern in rule.merchant_patterns):
                    return rule.name
                    
            # Check amount ranges if specified
            if rule.min_amount is not None and rule.max_amount is not None:
                if rule.min_amount <= amount <= rule.max_amount:
                    return rule.name
                    
        return "Other"

    def _generate_tags(self, row) -> List[str]:
        """Generate tags for a transaction"""
        tags = []
        amount = float(row["amount"]) if row["amount"] else 0
        
        # Add amount-based tags
        if amount > 1000:
            tags.append("high_value")
        elif amount < 10:
            tags.append("low_value")
            
        # Add frequency-based tags
        if row.get("is_recurring"):
            tags.append("recurring")
            
        # Add category-based tags
        if row["category"] != "Other":
            tags.append(row["category"].lower())
            
        return tags

    def _detect_recurring_pattern(self, row) -> bool:
        """Detect if a transaction appears to be recurring"""
        description = str(row["description"]).lower()
        recurring_indicators = [
            "subscription",
            "monthly",
            "recurring",
            "payment",
            "bill",
            "auto-pay"
        ]
        
        return any(indicator in description for indicator in recurring_indicators) 