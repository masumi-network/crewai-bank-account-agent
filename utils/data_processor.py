"""
Utility functions for processing Wise API data.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def process_accounts(accounts_data: List[Dict]) -> pd.DataFrame:
    """
    Process accounts data into a pandas DataFrame.
    
    Args:
        accounts_data: List of account objects from Wise API
        
    Returns:
        DataFrame with processed account data
    """
    if not accounts_data:
        return pd.DataFrame()
    
    accounts = []
    for account in accounts_data:
        account_info = {
            'id': account.get('id'),
            'currency': account.get('currency'),
            'balance': account.get('amount', {}).get('value', 0),
            'type': account.get('type', ''),
            'name': account.get('name', ''),
            'created_at': account.get('creationTime', '')
        }
        accounts.append(account_info)
    
    df = pd.DataFrame(accounts)
    
    # Convert date columns to datetime
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
    
    return df

def process_transactions(transactions_data: List[Dict]) -> pd.DataFrame:
    """
    Process transactions data into a pandas DataFrame.
    
    Args:
        transactions_data: List of transaction objects from Wise API
        
    Returns:
        DataFrame with processed transaction data
    """
    if not transactions_data:
        return pd.DataFrame()
    
    transactions = []
    for tx in transactions_data:
        tx_info = {
            'id': tx.get('id'),
            'date': tx.get('date'),
            'amount': tx.get('amount', {}).get('value', 0),
            'currency': tx.get('amount', {}).get('currency', ''),
            'description': tx.get('description', ''),
            'reference': tx.get('reference', ''),
            'type': tx.get('type', ''),
            'category': tx.get('category', ''),
            'merchant': tx.get('merchant', {}).get('name', '') if tx.get('merchant') else '',
            'merchant_category': tx.get('merchant', {}).get('category', '') if tx.get('merchant') else '',
            'fee': tx.get('fee', {}).get('value', 0) if tx.get('fee') else 0,
            'exchange_rate': tx.get('exchangeDetails', {}).get('rate', None) if tx.get('exchangeDetails') else None,
        }
        transactions.append(tx_info)
    
    df = pd.DataFrame(transactions)
    
    # Convert date columns to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def categorize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add additional categorization to transactions.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        DataFrame with additional categorization
    """
    if df.empty:
        return df
    
    # Make a copy to avoid SettingWithCopyWarning
    result = df.copy()
    
    # Add a custom category column based on description or existing category
    def get_custom_category(row):
        desc = str(row.get('description', '')).lower()
        
        # Define category mapping based on keywords
        categories = {
            'food': ['restaurant', 'cafe', 'coffee', 'food', 'grocery', 'supermarket'],
            'transport': ['uber', 'lyft', 'taxi', 'transport', 'train', 'bus', 'subway', 'metro'],
            'shopping': ['amazon', 'shop', 'store', 'retail', 'clothing'],
            'entertainment': ['movie', 'cinema', 'theater', 'netflix', 'spotify', 'subscription'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
            'housing': ['rent', 'mortgage', 'apartment', 'house'],
            'health': ['doctor', 'hospital', 'medical', 'pharmacy', 'health'],
            'education': ['school', 'university', 'college', 'course', 'education'],
            'income': ['salary', 'income', 'deposit'],
            'transfer': ['transfer', 'sent', 'received']
        }
        
        for category, keywords in categories.items():
            if any(keyword in desc for keyword in keywords):
                return category
        
        # Use existing category if available
        if row.get('category'):
            return row['category']
        
        return 'other'
    
    result['custom_category'] = result.apply(get_custom_category, axis=1)
    
    # Add transaction direction (income/expense)
    result['direction'] = result['amount'].apply(lambda x: 'income' if x >= 0 else 'expense')
    
    return result

def calculate_summary_stats(transactions_df: pd.DataFrame) -> Dict:
    """
    Calculate summary statistics from transaction data.
    
    Args:
        transactions_df: DataFrame with transaction data
        
    Returns:
        Dictionary with summary statistics
    """
    if transactions_df.empty:
        return {
            'total_income': 0,
            'total_expenses': 0,
            'net_cashflow': 0,
            'avg_daily_expense': 0,
            'top_expense_categories': [],
            'top_income_categories': [],
            'monthly_summary': []
        }
    
    # Make a copy to avoid SettingWithCopyWarning
    df = transactions_df.copy()
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # Calculate basic stats
    income_df = df[df['amount'] >= 0]
    expense_df = df[df['amount'] < 0]
    
    total_income = income_df['amount'].sum()
    total_expenses = abs(expense_df['amount'].sum())
    net_cashflow = total_income - total_expenses
    
    # Calculate average daily expense
    if 'date' in df.columns:
        date_range = (df['date'].max() - df['date'].min()).days
        avg_daily_expense = total_expenses / max(1, date_range)
    else:
        avg_daily_expense = 0
    
    # Top expense categories
    if 'custom_category' in expense_df.columns and not expense_df.empty:
        top_expense_categories = expense_df.groupby('custom_category')['amount'].sum().abs().sort_values(ascending=False).head(5).to_dict()
    else:
        top_expense_categories = {}
    
    # Top income categories
    if 'custom_category' in income_df.columns and not income_df.empty:
        top_income_categories = income_df.groupby('custom_category')['amount'].sum().sort_values(ascending=False).head(5).to_dict()
    else:
        top_income_categories = {}
    
    # Monthly summary
    monthly_summary = []
    if 'month' in df.columns:
        for month, month_df in df.groupby('month'):
            month_income = month_df[month_df['amount'] >= 0]['amount'].sum()
            month_expenses = abs(month_df[month_df['amount'] < 0]['amount'].sum())
            month_net = month_income - month_expenses
            
            monthly_summary.append({
                'month': month,
                'income': month_income,
                'expenses': month_expenses,
                'net': month_net
            })
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_cashflow': net_cashflow,
        'avg_daily_expense': avg_daily_expense,
        'top_expense_categories': top_expense_categories,
        'top_income_categories': top_income_categories,
        'monthly_summary': monthly_summary
    } 