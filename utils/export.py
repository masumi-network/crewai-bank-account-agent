"""
Utility functions for exporting data to different formats.
"""
import json
import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from fpdf import FPDF
import os
import tempfile
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)

def export_to_json(data: Dict, filename: Optional[str] = None) -> str:
    """
    Export data to a JSON file.
    
    Args:
        data: Data to export
        filename: Output filename (optional)
        
    Returns:
        Path to the exported file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wise_report_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    return filename

def export_to_pdf(data: Dict, filename: Optional[str] = None) -> str:
    """
    Export data to a PDF file.
    
    Args:
        data: Data to export
        filename: Output filename (optional)
        
    Returns:
        Path to the exported file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wise_report_{timestamp}.pdf"
    
    pdf = FPDF()
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Wise Account Analysis Report", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(10)
    
    # Summary section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Financial Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    
    summary = data.get('summary', {})
    pdf.cell(0, 8, f"Total Income: {summary.get('total_income', 0):.2f}", ln=True)
    pdf.cell(0, 8, f"Total Expenses: {summary.get('total_expenses', 0):.2f}", ln=True)
    pdf.cell(0, 8, f"Net Cashflow: {summary.get('net_cashflow', 0):.2f}", ln=True)
    pdf.cell(0, 8, f"Average Daily Expense: {summary.get('avg_daily_expense', 0):.2f}", ln=True)
    pdf.ln(5)
    
    # Top expense categories
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Top Expense Categories", ln=True)
    pdf.set_font("Arial", "", 12)
    
    top_expenses = summary.get('top_expense_categories', {})
    for category, amount in top_expenses.items():
        pdf.cell(0, 8, f"{category}: {abs(amount):.2f}", ln=True)
    pdf.ln(5)
    
    # Monthly summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Monthly Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    
    monthly_data = summary.get('monthly_summary', [])
    for month_data in monthly_data:
        month = month_data.get('month', '')
        income = month_data.get('income', 0)
        expenses = month_data.get('expenses', 0)
        net = month_data.get('net', 0)
        
        pdf.cell(0, 8, f"Month: {month}", ln=True)
        pdf.cell(0, 8, f"  Income: {income:.2f}", ln=True)
        pdf.cell(0, 8, f"  Expenses: {expenses:.2f}", ln=True)
        pdf.cell(0, 8, f"  Net: {net:.2f}", ln=True)
        pdf.ln(5)
    
    # Recommendations section
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Financial Recommendations", ln=True)
    pdf.set_font("Arial", "", 12)
    
    recommendations = data.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        pdf.multi_cell(0, 8, f"{i}. {rec}")
        pdf.ln(5)
    
    pdf.output(filename)
    return filename

def export_to_google_sheets(data: Dict, credentials_json: str, sheet_name: Optional[str] = None) -> str:
    """
    Export data to Google Sheets.
    
    Args:
        data: Data to export
        credentials_json: Path to Google API credentials JSON file
        sheet_name: Name of the sheet (optional)
        
    Returns:
        URL of the Google Sheet
    """
    if sheet_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sheet_name = f"Wise Report {timestamp}"
    
    # Set up credentials
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
    client = gspread.authorize(credentials)
    
    # Create a new spreadsheet
    spreadsheet = client.create(sheet_name)
    
    # Summary sheet
    summary_sheet = spreadsheet.get_worksheet(0)
    summary_sheet.update_title("Summary")
    
    # Add summary data
    summary = data.get('summary', {})
    summary_data = [
        ["Wise Account Analysis Report"],
        [f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
        [],
        ["Financial Summary"],
        ["Total Income", summary.get('total_income', 0)],
        ["Total Expenses", summary.get('total_expenses', 0)],
        ["Net Cashflow", summary.get('net_cashflow', 0)],
        ["Average Daily Expense", summary.get('avg_daily_expense', 0)],
        [],
        ["Top Expense Categories"]
    ]
    
    # Add top expense categories
    top_expenses = summary.get('top_expense_categories', {})
    for category, amount in top_expenses.items():
        summary_data.append([category, abs(amount)])
    
    summary_data.append([])
    summary_data.append(["Monthly Summary"])
    summary_data.append(["Month", "Income", "Expenses", "Net"])
    
    # Add monthly data
    monthly_data = summary.get('monthly_summary', [])
    for month_data in monthly_data:
        month = month_data.get('month', '')
        income = month_data.get('income', 0)
        expenses = month_data.get('expenses', 0)
        net = month_data.get('net', 0)
        summary_data.append([month, income, expenses, net])
    
    summary_sheet.update("A1", summary_data)
    
    # Recommendations sheet
    recommendations_sheet = spreadsheet.add_worksheet(title="Recommendations", rows=100, cols=20)
    
    recommendations = data.get('recommendations', [])
    rec_data = [["Financial Recommendations"], []]
    for i, rec in enumerate(recommendations, 1):
        rec_data.append([f"{i}. {rec}"])
    
    recommendations_sheet.update("A1", rec_data)
    
    # Transactions sheet if available
    if 'transactions' in data:
        transactions = data.get('transactions', [])
        if transactions:
            transactions_sheet = spreadsheet.add_worksheet(title="Transactions", rows=len(transactions)+10, cols=20)
            
            # Get column names from first transaction
            columns = list(transactions[0].keys())
            tx_data = [columns]
            
            # Add transaction data
            for tx in transactions:
                row = [tx.get(col, '') for col in columns]
                tx_data.append(row)
            
            transactions_sheet.update("A1", tx_data)
    
    # Make the spreadsheet publicly accessible with the link
    spreadsheet.share(None, perm_type='anyone', role='reader')
    
    return spreadsheet.url 