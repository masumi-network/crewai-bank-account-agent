# Wise Account Analysis with CrewAI - Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Setup and Installation](#setup-and-installation)
4. [Configuration](#configuration)
5. [Wise API Integration](#wise-api-integration)
6. [Data Processing](#data-processing)
7. [AI Analysis with CrewAI](#ai-analysis-with-crewai)
8. [User Interface](#user-interface)
9. [Export Functionality](#export-functionality)
10. [Troubleshooting](#troubleshooting)
11. [Security Considerations](#security-considerations)
12. [Future Enhancements](#future-enhancements)

## Introduction

The Wise Account Analysis application is a powerful tool that connects to your Wise account to analyze your balances and transactions. It uses CrewAI to create a team of specialized AI agents that provide personalized financial insights and recommendations based on your real financial data.

The application features:
- Real-time connection to your Wise account
- Comprehensive dashboard visualization of your financial data
- AI-powered financial analysis using CrewAI and OpenAI
- Export functionality for reports in various formats

## System Architecture

The application is built with the following components:

1. **Frontend**: Streamlit web application
2. **Backend Services**:
   - Wise API Client
   - Data Processor
   - Financial Analysis Agents (CrewAI)
   - Export Utilities

### Component Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Streamlit UI   │────▶│   Wise Client   │────▶│  Data Processor │
│                 │     │                 │     │                 │
└────────┬────────┘     └─────────────────┘     └────────┬────────┘
         │                                               │
         │                                               │
         │                                               ▼
┌────────▼────────┐                           ┌─────────────────┐
│                 │                           │                 │
│ Export Utilities│◀──────────────────────────│ Financial Agents│
│                 │                           │    (CrewAI)     │
└─────────────────┘                           └─────────────────┘
```

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Wise API key (sandbox or production)
- OpenAI API key

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crewai-bank-account-agent.git
   cd crewai-bank-account-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Configuration

The application uses the following configuration options:

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (set automatically when entered in the UI)

### Session State Variables

- `api_key`: Wise API key
- `openai_api_key`: OpenAI API key
- `environment`: Wise API environment (sandbox or production)
- `accounts_data`: Processed account data
- `transactions_data`: Processed transaction data
- `summary_stats`: Calculated summary statistics
- `analysis_results`: Results from the AI analysis
- `export_path`: Path to exported files
- `google_sheets_url`: URL to exported Google Sheets
- `analysis_error`: Flag for analysis errors

## Wise API Integration

The application integrates with the Wise API to fetch account and transaction data.

### WiseClient Class

The `WiseClient` class in `wise/client.py` handles all interactions with the Wise API. Key methods include:

#### `__init__(api_key, environment)`

Initializes the client with your API key and selected environment.

```python
def __init__(self, api_key: str, environment: str = "production"):
    self.api_key = api_key
    self.environment = environment.lower()
    self.base_url = self.SANDBOX_URL if self.environment == "sandbox" else self.PRODUCTION_URL
    
    self.headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
```

#### `get_profiles()`

Fetches all profiles associated with your Wise account.

#### `get_accounts(profile_id=None)`

Fetches all accounts for a profile. If no profile ID is provided, it uses the personal profile.

```python
def get_accounts(self, profile_id: Optional[str] = None) -> List[Dict]:
    if profile_id is None:
        profile_id = self.get_profile_id()
    
    # Different endpoints for sandbox and production
    if self.environment == "sandbox":
        endpoint = f"borderless-accounts?profileId={profile_id}"
        # Transform response to match expected format
        # ...
    else:
        return self._make_request(f"profiles/{profile_id}/balances")
```

#### `get_transactions(profile_id=None, currency=None, interval_start=None, interval_end=None, limit=100)`

Fetches transactions for a profile within a specified date range.

```python
def get_transactions(self, profile_id=None, currency=None, interval_start=None, interval_end=None, limit=100):
    # Set up parameters and fetch real transaction data
    # ...
    endpoint = f"profiles/{profile_id}/statements/transactions"
    return self._make_request(endpoint, params=params)
```

#### `validate_api_key()`

Validates the API key by making a test request to the Wise API.

## Data Processing

The application processes the raw data from the Wise API to make it more suitable for analysis and visualization.

### Data Processor Module

The `utils/data_processor.py` module contains functions for processing account and transaction data:

#### `process_accounts(accounts_data)`

Transforms raw account data into a pandas DataFrame with standardized columns.

#### `process_transactions(transactions_data)`

Transforms raw transaction data into a pandas DataFrame with standardized columns.

#### `categorize_transactions(transactions_df)`

Adds custom categories to transactions based on descriptions and merchant information.

#### `calculate_summary_stats(transactions_df)`

Calculates summary statistics from transaction data, including:
- Total income
- Total expenses
- Net cashflow
- Average daily expense
- Top expense categories
- Monthly summary

## AI Analysis with CrewAI

The application uses CrewAI to create a team of specialized AI agents that analyze your financial data and provide personalized recommendations.

### FinancialAgents Class

The `agents/financial_agents.py` module contains the `FinancialAgents` class, which manages the AI analysis:

#### `__init__(accounts_data, transactions_data, summary_stats, openai_api_key=None)`

Initializes the financial agents with your data and OpenAI API key.

```python
def __init__(self, accounts_data, transactions_data, summary_stats, openai_api_key=None):
    self.accounts_data = accounts_data
    self.transactions_data = transactions_data
    self.summary_stats = summary_stats
    
    # Set OpenAI API key
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
        # Validate the API key
        # ...
```

#### `create_agents()`

Creates three specialized AI agents:
1. **Data Analyst**: Analyzes patterns and trends in your financial data
2. **Financial Advisor**: Provides personalized financial advice
3. **Budget Optimizer**: Identifies opportunities to optimize your spending

```python
def create_agents(self):
    # Create a language model
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    
    # Create the data analyst agent
    data_analyst = Agent(
        role="Financial Data Analyst",
        goal="Analyze financial transaction data to identify patterns and trends",
        backstory="...",
        llm=llm
    )
    
    # Create the financial advisor agent
    # ...
    
    # Create the budget optimizer agent
    # ...
    
    return data_analyst, financial_advisor, budget_optimizer
```

#### `create_tasks(data_analyst, financial_advisor, budget_optimizer)`

Creates tasks for each agent with detailed instructions and access to your financial data.

```python
def create_tasks(self, data_analyst, financial_advisor, budget_optimizer):
    # Convert data to JSON for the agents
    accounts_json = self.accounts_data.to_json(orient='records')
    transactions_json = self.transactions_data.to_json(orient='records')
    summary_json = json.dumps(self.summary_stats)
    
    # Create the data analysis task
    analysis_task = Task(
        description=f"""
        Analyze the financial transaction data and identify key patterns and trends.
        
        Focus on:
        1. Income and expense patterns
        2. Spending categories analysis
        3. Cash flow trends
        4. Unusual transactions or anomalies
        5. Account balance analysis
        
        Here is the complete account data with balances:
        {accounts_json}
        
        Here is the complete transaction data:
        {transactions_json}
        
        Here are the summary statistics:
        {summary_json}
        
        Provide a comprehensive analysis with specific insights.
        Your output should start with "# Data Analysis" as a header.
        Make sure to include analysis of the account balances and how they've changed over time.
        """,
        agent=data_analyst
    )
    
    # Create the financial advice task
    # ...
    
    # Create the budget optimization task
    # ...
    
    return [analysis_task, advice_task, optimization_task]
```

#### `run_analysis()`

Runs the AI analysis by creating a crew with the agents and tasks, and processing the results.

```python
def run_analysis(self):
    try:
        # Create agents and tasks
        data_analyst, financial_advisor, budget_optimizer = self.create_agents()
        tasks = self.create_tasks(data_analyst, financial_advisor, budget_optimizer)
        
        # Create and run the crew
        crew = Crew(
            agents=[data_analyst, financial_advisor, budget_optimizer],
            tasks=tasks,
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        # Process the results
        # ...
        
        return {
            "analysis": analysis_results,
            "advice": advice_results,
            "optimization": optimization_results,
            "recommendations": recommendations
        }
    except Exception as e:
        # Handle errors
        # ...
```

#### `_extract_recommendations(advice, optimization)`

Extracts key recommendations from the advice and optimization results.

## User Interface

The application uses Streamlit to create a user-friendly web interface.

### Main App Structure

The `app.py` file defines the main structure of the application:

#### Sidebar

The sidebar contains:
- Environment selection (Sandbox or Production)
- API key inputs (Wise and OpenAI)
- Date range selection
- Connect button
- Export options

#### Dashboard Tab

The Dashboard tab displays:
- Account balances chart
- Financial summary metrics
- Monthly income vs. expenses chart
- Top expense categories pie chart

#### Transactions Tab

The Transactions tab displays:
- Filterable transaction list
- Transaction timeline chart

#### AI Analysis Tab

The AI Analysis tab displays:
- Data Analysis section
- Financial Advice section
- Budget Optimization section
- Key Recommendations list

## Export Functionality

The application allows you to export your financial data and analysis results in various formats.

### Export Module

The `utils/export.py` module contains functions for exporting data:

#### `export_to_json(data)`

Exports data to a JSON file.

#### `export_to_pdf(data)`

Exports data to a PDF report.

#### `export_to_google_sheets(data, credentials_file)`

Exports data to a Google Sheets spreadsheet.

## Troubleshooting

### Common Issues

#### "Unable to fetch real transaction data in sandbox mode"

This occurs when the Wise sandbox API doesn't support the same endpoints as the production API. To resolve this:
- Use the production environment with a real Wise API key
- Check that your sandbox account has test transactions

#### "Invalid OpenAI API key"

This occurs when the OpenAI API key is invalid or has expired. To resolve this:
- Check that your OpenAI API key is correct
- Ensure your OpenAI account has sufficient credits

#### "Error generating analysis"

This occurs when there's an issue with the AI analysis. To resolve this:
- Check the error details in the UI
- Ensure your OpenAI API key is valid
- Try regenerating the analysis

## Security Considerations

The application handles sensitive financial data and API keys, so security is a priority:

- API keys are stored only in the Streamlit session state and are not persisted to disk
- The application uses HTTPS for all API requests
- The Wise API client uses bearer token authentication
- The application only requests read-only access to your Wise account

## Future Enhancements

Potential future enhancements for the application include:

1. **Multi-account support**: Analyze multiple Wise accounts together
2. **Custom categories**: Allow users to define custom transaction categories
3. **Budget planning**: Create and track budgets based on historical data
4. **Recurring transaction detection**: Automatically identify recurring expenses
5. **Investment recommendations**: Provide investment advice based on savings potential
6. **Mobile app**: Create a mobile version of the application
7. **Data synchronization**: Automatically sync data with Wise on a schedule
8. **User accounts**: Allow users to create accounts to save their analysis history 