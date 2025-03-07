from typing import Dict, List
import pandas as pd
from datetime import datetime
import json
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

class ReportGenerator:
    """Generates financial reports in various formats"""
    
    def __init__(self, google_creds_path: str = None):
        self.google_creds_path = google_creds_path
        self._google_client = None

    def generate_report(self, 
                       analysis_data: Dict,
                       output_formats: List[str] = ["json", "pdf"],
                       output_dir: str = "reports") -> Dict[str, str]:
        """Generate reports in specified formats"""
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        outputs = {}
        
        for format in output_formats:
            if format == "json":
                filepath = self._generate_json_report(analysis_data, output_dir, timestamp)
                outputs["json"] = filepath
            elif format == "pdf":
                filepath = self._generate_pdf_report(analysis_data, output_dir, timestamp)
                outputs["pdf"] = filepath
            elif format == "sheets":
                url = self._generate_sheets_report(analysis_data, timestamp)
                outputs["sheets"] = url
                
        return outputs

    def _generate_json_report(self, data: Dict, output_dir: str, timestamp: str) -> str:
        """Generate JSON report"""
        filepath = f"{output_dir}/report_{timestamp}.json"
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            
        return filepath

    def _generate_pdf_report(self, data: Dict, output_dir: str, timestamp: str) -> str:
        """Generate PDF report"""
        filepath = f"{output_dir}/report_{timestamp}.pdf"
        
        pdf = FPDF()
        pdf.add_page()
        
        # Add title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Financial Analysis Report", ln=True, align="C")
        pdf.ln(10)
        
        # Add summary section
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Summary", ln=True)
        pdf.set_font("Arial", "", 12)
        
        summary = data["summary"]
        pdf.cell(0, 10, f"Total Spend: ${summary['total_spend']:,.2f}", ln=True)
        pdf.cell(0, 10, f"Total Transactions: {summary['transaction_count']}", ln=True)
        pdf.ln(5)
        
        # Add category breakdown
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Category Breakdown", ln=True)
        pdf.set_font("Arial", "", 12)
        
        for category, stats in summary["categories"].items():
            pdf.cell(0, 10, 
                    f"{category}: ${stats['sum']:,.2f} ({stats['percentage']}%)", 
                    ln=True)
        pdf.ln(5)
        
        # Add insights
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Key Insights", ln=True)
        pdf.set_font("Arial", "", 12)
        
        for insight in data.get("insights", []):
            pdf.multi_cell(0, 10, 
                         f"- {insight['description']}\n  Recommendation: {insight['recommendation']}")
        
        pdf.output(filepath)
        return filepath

    def _generate_sheets_report(self, data: Dict, timestamp: str) -> str:
        """Generate Google Sheets report"""
        if not self.google_creds_path:
            raise ValueError("Google credentials path not provided")
            
        if not self._google_client:
            self._init_google_client()
            
        # Create new spreadsheet
        spreadsheet = self._google_client.create(f"Financial Report {timestamp}")
        
        # Add summary sheet
        summary_sheet = spreadsheet.sheet1
        summary_sheet.update_title("Summary")
        
        # Update summary data
        summary_data = [
            ["Financial Analysis Report"],
            [],
            ["Total Spend", f"${data['summary']['total_spend']:,.2f}"],
            ["Total Transactions", data['summary']['transaction_count']],
            [],
            ["Category Breakdown"],
        ]
        
        for category, stats in data["summary"]["categories"].items():
            summary_data.append([
                category,
                f"${stats['sum']:,.2f}",
                f"{stats['percentage']}%"
            ])
            
        summary_sheet.update("A1", summary_data)
        
        # Add insights sheet
        if data.get("insights"):
            insights_sheet = spreadsheet.add_worksheet("Insights", 100, 20)
            insights_data = [["Type", "Description", "Impact", "Recommendation", "Priority"]]
            
            for insight in data["insights"]:
                insights_data.append([
                    insight["type"],
                    insight["description"],
                    f"${insight['impact']:,.2f}",
                    insight["recommendation"],
                    insight["priority"]
                ])
                
            insights_sheet.update("A1", insights_data)
        
        return spreadsheet.url

    def _init_google_client(self):
        """Initialize Google Sheets client"""
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_file(
            self.google_creds_path,
            scopes=scopes
        )
        
        self._google_client = gspread.authorize(creds) 