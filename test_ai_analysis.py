from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import List, Dict
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain.tools import Tool
import pandas as pd

print("Debug: Starting environment setup...")

# Get the current working directory
current_dir = Path.cwd()
env_path = current_dir / '.env'
print(f"Debug: Looking for .env file at: {env_path}")
print(f"Debug: .env file exists: {env_path.exists()}")

if env_path.exists():
    print("\nDebug: Reading .env file contents:")
    with open(env_path, 'r') as f:
        env_contents = f.read().strip()
        print("First few characters of each line:")
        for line in env_contents.split('\n'):
            if line.strip():  # Only process non-empty lines
                if 'API_KEY' in line:
                    key_part = line.split('=')[0]
                    print(f"{key_part}=****")
                else:
                    print(line[:20] + "..." if len(line) > 20 else line)

# Try different methods to load the environment variables
print("\nDebug: Attempting to load environment variables...")
load_dotenv(dotenv_path=env_path, override=True)

# Also try direct environment variable setting
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Debug: Print all environment variables (excluding the actual API key value)
print("\nDebug: Environment Variables after loading:")
for key in os.environ:
    if 'API_KEY' in key:
        print(f"{key}: {'*' * 10}")
    else:
        print(f"{key}: {os.environ[key][:50]}..." if len(os.environ[key]) > 50 else f"{key}: {os.environ[key]}")

# Verify OpenAI API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("\nError: OPENAI_API_KEY not found!")
    print("Please ensure your .env file contains a line like:")
    print("OPENAI_API_KEY=sk-...")
    print("\nTry one of these solutions:")
    print("1. Create a new .env file:")
    print("   echo 'OPENAI_API_KEY=your-key-here' > .env")
    print("2. Set the environment variable directly:")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("3. Check file permissions:")
    print("   chmod 600 .env")
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
else:
    print(f"\nDebug: OPENAI_API_KEY found with length: {len(api_key)}")
    if not api_key.startswith('sk-'):
        print("Warning: API key format might be incorrect (should start with 'sk-')")

# Mock transaction data covering different scenarios
MOCK_TRANSACTIONS = [
    {
        "id": "tx_001",
        "date": (datetime.now() - timedelta(days=5)).isoformat(),
        "amount": 14.99,
        "currency": "USD",
        "description": "Netflix Monthly Subscription",
        "category": "Subscriptions",
        "merchant": "Netflix"
    },
    {
        "id": "tx_002",
        "date": (datetime.now() - timedelta(days=5)).isoformat(),
        "amount": 9.99,
        "currency": "USD",
        "description": "Spotify Premium",
        "category": "Subscriptions",
        "merchant": "Spotify"
    },
    {
        "id": "tx_003",
        "date": (datetime.now() - timedelta(days=3)).isoformat(),
        "amount": 45.50,
        "currency": "USD",
        "description": "Grocery Store Purchase",
        "category": "Food & Dining",
        "merchant": "Whole Foods"
    },
    {
        "id": "tx_004",
        "date": (datetime.now() - timedelta(days=2)).isoformat(),
        "amount": 120.00,
        "currency": "USD",
        "description": "Electricity Bill",
        "category": "Utilities",
        "merchant": "Power Company"
    },
    {
        "id": "tx_005",
        "date": datetime.now().isoformat(),
        "amount": 25.00,
        "currency": "USD",
        "description": "Food Delivery",
        "category": "Food & Dining",
        "merchant": "DoorDash"
    }
]

class FinancialAnalysisTools:
    @staticmethod
    def analyze_spending_patterns(transactions) -> Dict:
        """Analyze spending patterns in the transactions"""
        # Handle different input formats
        if isinstance(transactions, str):
            # Handle various string inputs that agents might use
            if transactions.lower() in ["transaction data", "provided transaction data", "transactions"]:
                transactions = MOCK_TRANSACTIONS
        
        # Ensure we have a list of transactions
        if not isinstance(transactions, list):
            print(f"Debug: Received transaction type: {type(transactions)}")
            print(f"Debug: Transaction content: {transactions}")
            transactions = MOCK_TRANSACTIONS  # Fallback to mock data
            
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        analysis = {
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
        return analysis

    @staticmethod
    def identify_savings_opportunities(transactions) -> List[Dict]:
        """Identify potential savings opportunities"""
        # Handle different input formats
        if isinstance(transactions, str):
            # Handle various string inputs that agents might use
            if transactions.lower() in ["transaction data", "provided transaction data", "transactions"]:
                transactions = MOCK_TRANSACTIONS
        
        # Ensure we have a list of transactions
        if not isinstance(transactions, list):
            print(f"Debug: Received transaction type: {type(transactions)}")
            print(f"Debug: Transaction content: {transactions}")
            transactions = MOCK_TRANSACTIONS  # Fallback to mock data
            
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
            potential_savings = float(food_delivery['amount'].sum() * 0.7)  # Assume 70% could be saved by cooking
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

def create_financial_crew() -> Crew:
    # Create tools with more detailed descriptions
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

    # Create agents with more specific goals
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

    # Create more specific tasks
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

    # Create crew
    crew = Crew(
        agents=[analyst, advisor],
        tasks=[analysis_task, advice_task],
        verbose=True
    )

    return crew

def main():
    print("Starting Financial Analysis Test")
    print("-" * 50)
    
    # Create output directory
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Save mock transactions
        with open(output_dir / "mock_transactions.json", "w") as f:
            json.dump(MOCK_TRANSACTIONS, f, indent=2)
        print("\nMock transactions saved to test_results/mock_transactions.json")
        
        # Create and run the crew
        crew = create_financial_crew()
        result = crew.kickoff()
        
        # Save results
        with open(output_dir / "analysis_results.txt", "w") as f:
            f.write(result)
        print("\nAnalysis results saved to test_results/analysis_results.txt")
        
        # Print summary
        print("\nAnalysis Summary:")
        print("-" * 30)
        
        # Run direct analysis for verification
        tools = FinancialAnalysisTools()
        patterns = tools.analyze_spending_patterns(MOCK_TRANSACTIONS)
        opportunities = tools.identify_savings_opportunities(MOCK_TRANSACTIONS)
        
        print(f"\nTotal Spend: ${patterns['total_spend']:.2f}")
        print(f"Average Transaction: ${patterns['average_transaction']:.2f}")
        print("\nSpending by Category:")
        for category, amount in patterns['by_category'].items():
            print(f"  {category}: ${amount:.2f}")
        
        print("\nSavings Opportunities:")
        for opp in opportunities:
            print(f"  {opp['description']}")
            print(f"  Potential Savings: ${opp['potential_savings']:.2f}")
            
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")

if __name__ == "__main__":
    main() 