# Banking Analysis System

An AI-powered financial analysis system that integrates with Wise and Revolut APIs to provide automated transaction analysis, cost optimization insights, and comprehensive financial reporting.

## Key Features

- 🔄 Seamless integration with Wise and Revolut APIs
- 🤖 AI-powered transaction analysis using CrewAI
- 📊 Intelligent transaction categorization and pattern detection
- 💰 Cost optimization and savings recommendations
- 📑 Multi-format reporting (JSON, PDF, Google Sheets)
- 🔒 Secure API authentication and data handling
- ⚡ Asynchronous processing for better performance

## System Architecture

```
Banking Analysis System
├── API Layer (FastAPI)
├── Banking Tools
│   ├── Transaction Processing
│   ├── Cost Analysis
│   └── Report Generation
├── AI Layer (CrewAI)
    ├── Data Analysis Agent
    └── Report Generation Agent
```

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Wise API credentials
- Revolut API credentials
- Google Sheets API credentials (optional)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/banking-analysis-system.git
cd banking-analysis-system
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

3. Run with Docker:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Main Endpoints

- `POST /analyze`: Run transaction analysis
  ```json
  {
    "date_range": {
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-02-29T23:59:59Z"
    },
    "bank_configs": {
      "wise": {
        "api_key": "your-wise-api-key",
        "api_url": "https://api.wise.com/v1"
      },
      "revolut": {
        "api_key": "your-revolut-api-key",
        "api_url": "https://api.revolut.com/v1"
      }
    },
    "output_formats": ["json", "pdf", "sheets"]
  }
  ```

- `GET /health`: System health check

## Development Setup

1. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Run development server:
```bash
poetry run uvicorn main:app --reload
```

## Project Structure

```
banking-analysis/
├── processors/
│   ├── transaction_processor.py
│   ├── cost_analyzer.py
│   └── report_generator.py
├── banking_tools.py
├── crew_definition.py
├── main.py
├── pyproject.toml
├── docker-compose.yml
└── Dockerfile
```

## Configuration

### Environment Variables

```env
# API Keys
WISE_API_KEY=your_wise_api_key
REVOLUT_API_KEY=your_revolut_api_key

# API URLs
WISE_API_URL=https://api.wise.com/v1
REVOLUT_API_URL=https://api.revolut.com/v1

# Google Sheets (Optional)
GOOGLE_SHEETS_CREDENTIALS=path_to_credentials.json
```

## Features in Detail

### Transaction Processing
- Automatic categorization using rule-based system
- Pattern detection for recurring payments
- Multi-currency support
- Merchant data enrichment

### Cost Analysis
- Category-based spending analysis
- Recurring cost detection
- Duplicate subscription identification
- Spending pattern analysis
- Cost-saving recommendations

### Report Generation
- Multiple format support (JSON, PDF, Google Sheets)
- Customizable report templates
- Interactive data visualization
- Executive summaries
- Detailed transaction breakdowns

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 