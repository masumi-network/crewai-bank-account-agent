# Wise Account Analysis with CrewAI

## Overview

Wise Account Analysis with CrewAI is a powerful financial analysis tool that connects to your Wise account to analyze your balances and transactions. It uses CrewAI to create a team of specialized AI agents that provide personalized financial insights and recommendations based on your real financial data.

## Features

- **Real-time Wise Integration**: Connect directly to your Wise account to fetch real transaction data and account balances
- **Comprehensive Dashboard**: Visualize your financial data with interactive charts and metrics
- **AI-powered Analysis**: Get personalized financial insights from a team of AI agents
- **Export Functionality**: Export your financial data and analysis results in various formats

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/masumi-network/crewai-bank-account-agent/tree/main
   cd crewai-bank-account-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Open in your browser**:
   The application will be available at http://localhost:8501

## Requirements

- Python 3.8 or higher
- Wise API key (sandbox or production)
- OpenAI API key

## How It Works

1. **Connect to Wise**: Enter your Wise API key and select the environment (sandbox or production)
2. **View Your Data**: Explore your account balances and transaction history in the Dashboard and Transactions tabs
3. **Generate AI Analysis**: Get personalized financial insights and recommendations from the AI Analysis tab
4. **Export Results**: Export your financial data and analysis results in various formats

## AI Analysis

The application uses CrewAI to create a team of specialized AI agents:

1. **Financial Data Analyst**: Analyzes patterns and trends in your financial data
2. **Financial Advisor**: Provides personalized financial advice
3. **Budget Optimizer**: Identifies opportunities to optimize your spending

## Documentation

For detailed documentation, see [DOCUMENTATION.md](DOCUMENTATION.md).

## Security

- API keys are stored only in the Streamlit session state and are not persisted to disk
- The application uses HTTPS for all API requests
- The Wise API client uses bearer token authentication
- The application only requests read-only access to your Wise account

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Wise API](https://api-docs.wise.com/)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [Streamlit](https://streamlit.io/)
- [OpenAI](https://openai.com/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/) 