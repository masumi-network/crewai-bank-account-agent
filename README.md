# CrewAI Bank Account Agent for Wise

This application provides a Streamlit-based dashboard for analyzing your Wise account data using CrewAI agents. The agents analyze your transactions and balances to provide optimization recommendations.

## Features

- Connect to Wise API (read-only)
- Visualize account balances and transactions
- Get AI-powered financial insights and recommendations
- Export reports in PDF, JSON, or Google Sheets format
- Support for both Wise production and sandbox environments

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```
4. Select your environment (Sandbox or Production) and enter your Wise API key in the web interface

## Wise API Key

### Sandbox Environment (for testing)

1. Sign up for a Wise developer account at [https://sandbox.transferwise.tech/register](https://sandbox.transferwise.tech/register)
2. Create a new API token with read-only permissions
3. Copy the token and use it in the application

The sandbox environment allows you to test the application without using real account data.

### Production Environment (for real account data)

1. Log in to your Wise account
2. Go to Settings > API tokens
3. Create a new token with read-only permissions
4. Copy the token and use it in the application

## Security Note

Your API key is only stored temporarily in the Streamlit session state and is never persisted to disk. All data processing happens locally on your machine.

## Project Structure

- `app.py`: Main Streamlit application
- `wise/`: Wise API client
- `agents/`: CrewAI agents and tasks
- `utils/`: Utility functions for data processing and export 