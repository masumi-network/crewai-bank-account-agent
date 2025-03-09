from datetime import datetime
import json
from pathlib import Path
from typing import List, Dict
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain.tools import Tool
import pandas as pd
from fpdf import FPDF

# Initialize paths
current_dir = Path.cwd()
env_path = current_dir / '.env'
mock_data_path = current_dir / 'mock_data' / 'transactions.json'

def load_mock_transactions() -> List[Dict]:
    """Load mock transactions from JSON file"""
    try:
        with open(mock_data_path, 'r') as f:
            data = json.load(f)
            return data['transactions']
    except FileNotFoundError:
        print(f"Warning: Mock data file not found at {mock_data_path}")
        return []
    except (json.JSONDecodeError, KeyError):
        print("Warning: Error loading mock transactions data")
        return []

# Load environment variables
load_dotenv(dotenv_path=env_path, override=True)

# Load mock transactions
MOCK_TRANSACTIONS = load_mock_transactions()

class FinancialAnalysisTools:
    @staticmethod
    def analyze_spending_patterns(transactions) -> Dict:
        """Analyze spending patterns in the transactions"""
        if isinstance(transactions, str):
            transactions = MOCK_TRANSACTIONS
        
        if not isinstance(transactions, list):
            transactions = MOCK_TRANSACTIONS
            
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        return {
            "total_spend": float(df['amount'].sum()),
            "average_transaction": float(df['amount'].mean()),
            "by_category": df.groupby('category')['amount'].sum().to_dict(),
            "by_merchant": df.groupby('merchant')['amount'].sum().to_dict(),
            "subscription_costs": float(df[df['category'] == 'Subscriptions']['amount'].sum()),
            "transaction_count": len(df),
            "date_range": {
                "start": df['date'].min().isoformat(),
                "end": df['date'].max().isoformat()
            }
        }

    @staticmethod
    def identify_savings_opportunities(transactions) -> List[Dict]:
        """Identify potential savings opportunities"""
        if isinstance(transactions, str) or not isinstance(transactions, list):
            transactions = MOCK_TRANSACTIONS
            
        df = pd.DataFrame(transactions)
        opportunities = []

        # Check for subscription costs
        subscriptions = df[df['category'] == 'Subscriptions']
        if not subscriptions.empty and subscriptions['amount'].sum() > 20:
            opportunities.append({
                "type": "subscription_optimization",
                "description": "Consider reviewing your subscription services",
                "potential_savings": float(subscriptions['amount'].sum()),
                "details": {
                    "current_subscriptions": subscriptions[['merchant', 'amount']].to_dict('records')
                }
            })

        # Check for high food delivery costs
        food_delivery = df[df['description'].str.contains('Delivery', case=False, na=False)]
        if not food_delivery.empty:
            potential_savings = float(food_delivery['amount'].sum() * 0.7)
            opportunities.append({
                "type": "food_costs",
                "description": "Consider reducing food delivery services",
                "potential_savings": potential_savings,
                "details": {
                    "current_monthly_delivery_spend": float(food_delivery['amount'].sum()),
                    "delivery_transactions": len(food_delivery)
                }
            })

        return opportunities

class ReportGenerator:
    def __init__(self, google_creds_path=None, user_email=None):
        self.output_dir = Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        self.google_creds_path = google_creds_path
        self.user_email = user_email
        self.sheets_client = None
        if google_creds_path:
            self._init_google_client()

    def _init_google_client(self):
        """Initialize Google Sheets client"""
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            if not Path(self.google_creds_path).exists():
                print(f"Error: Credentials file not found at {self.google_creds_path}")
                return

            credentials = Credentials.from_service_account_file(
                self.google_creds_path, 
                scopes=scopes
            )
            self.sheets_client = gspread.authorize(credentials)
            print("Successfully initialized Google Sheets client")
        except Exception as e:
            print(f"Error initializing Google Sheets client: {str(e)}")
            self.sheets_client = None

    def _generate_sheets_report(self, analysis_data: Dict, savings_opportunities: List[Dict], timestamp: str) -> str:
        """Generate a Google Sheets report"""
        if not self.sheets_client:
            print("Google Sheets client not initialized")
            return None

        try:
            # Create new spreadsheet
            spreadsheet_title = f"Financial Analysis Report {timestamp}"
            spreadsheet = self.sheets_client.create(spreadsheet_title)

            # Get the first sheet
            summary_sheet = spreadsheet.sheet1
            summary_sheet.update_title("Summary")

            # Prepare summary data
            summary_data = [
                ["Financial Analysis Report", ""],
                ["Generated at", datetime.now().isoformat()],
                ["", ""],
                ["Summary", ""],
                ["Total Spend", f"${analysis_data['total_spend']:.2f}"],
                ["Average Transaction", f"${analysis_data['average_transaction']:.2f}"],
                ["Number of Transactions", analysis_data['transaction_count']],
                ["", ""],
                ["Spending by Category", "Amount"]
            ]

            # Add category breakdown
            for category, amount in analysis_data['by_category'].items():
                summary_data.append([category, f"${amount:.2f}"])

            # Update summary sheet
            summary_sheet.update("A1", summary_data)

            # Create Savings Opportunities sheet
            savings_sheet = spreadsheet.add_worksheet("Savings Opportunities", 100, 20)
            
            # Enhanced savings data with detailed breakdown
            savings_data = [
                ["Savings Opportunities Analysis", "", "", ""],
                ["", "", "", ""],
                ["Category", "Description", "Current Spend", "Potential Savings"]
            ]

            # Add subscription details
            subscription_opp = next((opp for opp in savings_opportunities if opp['type'] == 'subscription_optimization'), None)
            if subscription_opp:
                savings_data.append([
                    "Subscriptions",
                    "Current Subscription Services:",
                    "",
                    f"${subscription_opp['potential_savings']:.2f}"
                ])
                for sub in subscription_opp['details']['current_subscriptions']:
                    savings_data.append([
                        "",
                        sub['merchant'],
                        f"${sub['amount']:.2f}",
                        ""
                    ])
                savings_data.append(["", "", "", ""])

            # Add food delivery details
            food_opp = next((opp for opp in savings_opportunities if opp['type'] == 'food_costs'), None)
            if food_opp:
                savings_data.append([
                    "Food Delivery",
                    "Current Food Delivery Spending:",
                    f"${food_opp['details']['current_monthly_delivery_spend']:.2f}",
                    f"${food_opp['potential_savings']:.2f}"
                ])
                savings_data.append([
                    "",
                    f"Number of delivery transactions: {food_opp['details']['delivery_transactions']}",
                    "",
                    ""
                ])
                savings_data.append(["", "", "", ""])

            # Add total potential savings
            total_savings = sum(opp['potential_savings'] for opp in savings_opportunities)
            savings_data.append([
                "Total Potential Monthly Savings",
                "",
                "",
                f"${total_savings:.2f}"
            ])

            # Update savings sheet
            savings_sheet.update("A1", savings_data)

            # Format sheets
            summary_sheet.format("A1:B1", {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "textFormat": {"bold": True}
            })
            
            savings_sheet.format("A1:D1", {
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                "textFormat": {"bold": True}
            })
            savings_sheet.format("A3:D3", {
                "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95},
                "textFormat": {"bold": True}
            })
            
            savings_sheet.format("C:D", {
                "numberFormat": {"type": "CURRENCY"}
            })

            # Adjust column widths
            savings_sheet.columns_auto_resize(0, 4)
            summary_sheet.columns_auto_resize(0, 2)

            # Share with user if email is provided
            if self.user_email:
                spreadsheet.share(self.user_email, perm_type='user', role='writer')
                print(f"Shared spreadsheet with {self.user_email}")

            return spreadsheet.url

        except Exception as e:
            print(f"Error generating Google Sheets report: {str(e)}")
            return None

    def generate_report(self, analysis_data: Dict, savings_opportunities: List[Dict], 
                       formats=["json", "pdf", "sheets"]) -> Dict[str, str]:
        """Generate reports in specified formats"""
        report_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if "json" in formats:
            json_path = self._generate_json_report(analysis_data, savings_opportunities, timestamp)
            report_files["json"] = str(json_path)
            
        if "pdf" in formats:
            pdf_path = self._generate_pdf_report(analysis_data, savings_opportunities, timestamp)
            report_files["pdf"] = str(pdf_path)

        if "sheets" in formats and self.sheets_client:
            sheet_url = self._generate_sheets_report(analysis_data, savings_opportunities, timestamp)
            if sheet_url:
                report_files["sheets"] = sheet_url
                print(f"Google Sheets report created: {sheet_url}")
            
        return report_files

    def _generate_json_report(self, analysis_data: Dict, savings_opportunities: List[Dict], timestamp: str) -> Path:
        """Generate a JSON report"""
        report_data = {
            "analysis": analysis_data,
            "savings_opportunities": savings_opportunities,
            "generated_at": datetime.now().isoformat()
        }
        
        file_path = self.output_dir / f"financial_report_{timestamp}.json"
        with open(file_path, "w") as f:
            json.dump(report_data, f, indent=2)
            
        return file_path

    def _generate_pdf_report(self, analysis_data: Dict, savings_opportunities: List[Dict], timestamp: str) -> Path:
        """Generate a PDF report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Financial Analysis Report", ln=True, align="C")
        pdf.ln(10)
        
        # Summary Section
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Summary", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Total Spend: ${analysis_data['total_spend']:.2f}", ln=True)
        pdf.cell(0, 10, f"Average Transaction: ${analysis_data['average_transaction']:.2f}", ln=True)
        pdf.cell(0, 10, f"Number of Transactions: {analysis_data['transaction_count']}", ln=True)
        pdf.ln(5)
        
        # Category Breakdown
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Spending by Category", ln=True)
        pdf.set_font("Arial", "", 12)
        for category, amount in analysis_data['by_category'].items():
            pdf.cell(0, 10, f"{category}: ${amount:.2f}", ln=True)
        pdf.ln(5)
        
        # Savings Opportunities
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Savings Opportunities", ln=True)
        pdf.set_font("Arial", "", 12)
        for opportunity in savings_opportunities:
            pdf.cell(0, 10, f"{opportunity['description']}", ln=True)
            pdf.cell(0, 10, f"Potential Savings: ${opportunity['potential_savings']:.2f}", ln=True)
            pdf.ln(5)
        
        file_path = self.output_dir / f"financial_report_{timestamp}.pdf"
        pdf.output(str(file_path))
        
        return file_path

def create_financial_crew() -> Crew:
    tools = [
        Tool(
            name="analyze_spending_patterns",
            func=FinancialAnalysisTools.analyze_spending_patterns,
            description="Analyze spending patterns in transaction data. Returns detailed analysis including total spend, averages, and category breakdowns."
        ),
        Tool(
            name="identify_savings_opportunities",
            func=FinancialAnalysisTools.identify_savings_opportunities,
            description="Identify potential savings opportunities in spending. Analyzes subscriptions, food delivery, and other spending patterns."
        )
    ]

    analyst = Agent(
        role='Financial Analyst',
        goal='Analyze transaction data to identify spending patterns and trends',
        backstory='Expert financial analyst with experience in personal finance and spending optimization',
        tools=tools,
        verbose=True
    )

    advisor = Agent(
        role='Financial Advisor',
        goal='Provide actionable financial advice and savings recommendations',
        backstory='Experienced financial advisor specializing in personal budget optimization and cost reduction strategies',
        tools=tools,
        verbose=True
    )

    analysis_task = Task(
        description="""
        Analyze the provided transaction data to:
        1. Calculate total spending and averages
        2. Break down spending by category
        3. Identify major spending patterns
        4. Look for unusual transactions
        Use the analyze_spending_patterns tool for this analysis.
        """,
        agent=analyst
    )

    advice_task = Task(
        description="""
        Based on the analysis:
        1. Identify potential savings opportunities
        2. Review subscription costs
        3. Analyze food delivery spending
        4. Provide specific recommendations
        Use both tools to provide comprehensive advice.
        """,
        agent=advisor
    )

    return Crew(
        agents=[analyst, advisor],
        tasks=[analysis_task, advice_task],
        verbose=True
    )

def main():
    print("Starting Financial Analysis")
    
    # Create output directory
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Save mock transactions
        with open(output_dir / "mock_transactions.json", "w") as f:
            json.dump(MOCK_TRANSACTIONS, f, indent=2)
        
        # Run analysis
        crew = create_financial_crew()
        result = crew.kickoff()
        
        # Save crew analysis results
        with open(output_dir / "analysis_results.txt", "w") as f:
            f.write(result)
        
        # Generate reports
        tools = FinancialAnalysisTools()
        patterns = tools.analyze_spending_patterns(MOCK_TRANSACTIONS)
        opportunities = tools.identify_savings_opportunities(MOCK_TRANSACTIONS)
        
        # Initialize report generator
        google_creds_path = current_dir / 'mock_data' / 'crewai-bank-account-5b906d445427.json'
        user_email = os.getenv('GOOGLE_SHEETS_USER_EMAIL')
        
        report_gen = ReportGenerator(
            google_creds_path=google_creds_path,
            user_email=user_email
        )
        
        # Generate reports
        report_files = report_gen.generate_report(
            patterns, 
            opportunities, 
            formats=["json", "pdf", "sheets"]
        )
        
        # Print summary
        print("\nAnalysis Summary:")
        print(f"Total Spend: ${patterns['total_spend']:.2f}")
        print(f"Average Transaction: ${patterns['average_transaction']:.2f}")
        
        print("\nSpending by Category:")
        for category, amount in patterns['by_category'].items():
            print(f"  {category}: ${amount:.2f}")
        
        print("\nSavings Opportunities:")
        for opp in opportunities:
            print(f"  {opp['description']}")
            print(f"  Potential Savings: ${opp['potential_savings']:.2f}")
            
        print("\nGenerated Reports:")
        for format, path in report_files.items():
            print(f"  {format.upper()} Report: {path}")
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 