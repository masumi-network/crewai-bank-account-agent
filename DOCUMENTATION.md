# Banking Analysis System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Security](#security)
8. [Development Guide](#development-guide)

## System Overview

The Banking Analysis System is a modern, AI-powered financial analysis tool that integrates with banking APIs to provide automated transaction analysis, cost optimization insights, and comprehensive financial reporting. Built with Python 3.12+ and leveraging CrewAI for intelligent processing, the system offers a scalable and maintainable solution for financial data analysis.

### Key Features
- Asynchronous API integration with Wise and Revolut
- AI-powered transaction analysis and categorization
- Cost optimization and savings detection
- Multi-format reporting capabilities
- Secure data handling and authentication
- Docker-based deployment

## Architecture

### High-Level Architecture
```
Banking Analysis System
├── API Layer (FastAPI)
├── Banking Tools
│   ├── Transaction Processing
│   ├── Cost Analysis
│   └── Report Generation
└── AI Layer (CrewAI)
    ├── Data Analysis Agent
    └── Report Generation Agent
```

### Technology Stack
- **Backend**: FastAPI, Python 3.12+
- **AI Processing**: CrewAI
- **Data Processing**: Pandas
- **Authentication**: Bearer Token
- **Containerization**: Docker
- **Documentation**: OpenAPI/Swagger

## Core Components

### 1. Banking Tools (`banking_tools.py`)

The central component that integrates all functionality:

```python
class BankingTools:
    def __init__(self, config: Dict[str, Dict[str, str]]):
        self.banks = {}  # Bank configurations
        self.session = None  # Async HTTP session
        self.transaction_processor = TransactionProcessor()
        self.cost_analyzer = CostAnalyzer()
        self.report_generator = ReportGenerator()
```

Key responsibilities:
- Bank API integration management
- Transaction fetching and processing
- Cost analysis coordination
- Report generation

### 2. Transaction Processing (`processors/transaction_processor.py`)

Handles transaction categorization and enrichment:

```python
class TransactionProcessor:
    def process_transactions(self, transactions: List[Dict]) -> List[Dict]:
        # Transaction processing logic
```

Features:
- Rule-based categorization
- Pattern detection
- Transaction enrichment
- Tag generation

### 3. Cost Analysis (`processors/cost_analyzer.py`)

Analyzes transactions for insights and savings opportunities:

```python
class CostAnalyzer:
    def analyze_transactions(self, transactions: List[Dict]) -> Dict:
        # Cost analysis logic
```

Capabilities:
- Category analysis
- Recurring payment detection
- Spending pattern analysis
- Cost-saving identification

### 4. Report Generation (`processors/report_generator.py`)

Generates comprehensive financial reports:

```python
class ReportGenerator:
    def generate_report(self, 
                       analysis_data: Dict,
                       output_formats: List[str] = ["json", "pdf"]) -> Dict[str, str]:
        # Report generation logic
```

Supported formats:
- JSON (raw data)
- PDF (formatted reports)
- Google Sheets (interactive)

## API Reference

### Endpoints

#### POST /analyze
Analyze banking transactions and generate reports.

Request:
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

Response:
```json
{
  "status": "success",
  "data": {
    "analysis": {
      "summary": {},
      "insights": [],
      "recommendations": []
    },
    "reports": {
      "json": "path/to/report.json",
      "pdf": "path/to/report.pdf",
      "sheets": "https://sheets.google.com/..."
    },
    "transaction_count": 150
  },
  "timestamp": "2024-02-29T12:00:00Z"
}
```

## Configuration

### Environment Variables
```env
# Required
WISE_API_KEY=your_wise_api_key
REVOLUT_API_KEY=your_revolut_api_key

# Optional
WISE_API_URL=https://api.wise.com/v1
REVOLUT_API_URL=https://api.revolut.com/v1
GOOGLE_SHEETS_CREDENTIALS=path_to_credentials.json
```

### Docker Configuration
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - WISE_API_KEY=${WISE_API_KEY}
      - REVOLUT_API_KEY=${REVOLUT_API_KEY}
```

## Security

### API Security
- Bearer token authentication
- HTTPS encryption
- API key validation
- Rate limiting

### Data Security
- Secure credential storage
- Token management
- Session handling
- Error handling

## Development Guide

### Setting Up Development Environment

1. Install dependencies:
```bash
poetry install
```

2. Set up pre-commit hooks:
```bash
poetry run pre-commit install
```

3. Run tests:
```bash
poetry run pytest
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Maintain test coverage

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## Error Handling

### Common Errors

1. Authentication Errors
```python
{
    "status": "error",
    "code": "AUTH_ERROR",
    "message": "Invalid API credentials",
    "timestamp": "2024-02-29T12:00:00Z"
}
```

2. Processing Errors
```python
{
    "status": "error",
    "code": "PROCESSING_ERROR",
    "message": "Failed to process transactions",
    "timestamp": "2024-02-29T12:00:00Z"
}
```

## Monitoring and Logging

### Health Checks
- API endpoint health
- Bank API connectivity
- Processing system status

### Performance Monitoring
- Response times
- Error rates
- Resource usage

### Logging
- Request/response logging
- Error tracking
- Performance metrics

## Future Enhancements

1. Additional Features
   - More bank integrations
   - Advanced ML categorization
   - Real-time notifications
   - Mobile app support

2. Technical Improvements
   - Caching layer
   - Improved error handling
   - Enhanced monitoring
   - Performance optimizations