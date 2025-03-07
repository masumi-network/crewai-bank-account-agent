import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import Mock, patch
from banking_tools import BankingTools
from crew_definition import BankingAnalysisCrew

# Mock transaction data
MOCK_WISE_TRANSACTIONS = [
    {
        "referenceNumber": "TX123",
        "date": "2024-02-01T10:00:00Z",
        "amount": {"value": 100.00, "currency": "USD"},
        "details": {
            "description": "Netflix Subscription",
            "merchant": {"name": "Netflix"},
            "type": "subscription"
        }
    },
    {
        "referenceNumber": "TX124",
        "date": "2024-02-02T15:30:00Z",
        "amount": {"value": 50.00, "currency": "USD"},
        "details": {
            "description": "Grocery Store Purchase",
            "merchant": {"name": "Whole Foods"},
            "type": "purchase"
        }
    }
]

MOCK_REVOLUT_TRANSACTIONS = [
    {
        "id": "REV123",
        "created_at": "2024-02-01T12:00:00Z",
        "amount": 75.00,
        "currency": "USD",
        "description": "Amazon Prime",
        "merchant": {"name": "Amazon"},
        "type": "subscription"
    },
    {
        "id": "REV124",
        "created_at": "2024-02-02T09:15:00Z",
        "amount": 25.00,
        "currency": "USD",
        "description": "Coffee Shop",
        "merchant": {"name": "Starbucks"},
        "type": "purchase"
    }
]

@pytest.fixture
def mock_config():
    return {
        'wise': {
            'api_key': 'test_wise_key',
            'api_url': 'https://api.wise.com/v1'
        },
        'revolut': {
            'api_key': 'test_revolut_key',
            'api_url': 'https://api.revolut.com/v1'
        }
    }

@pytest.fixture
def mock_date_range():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return {
        'start_date': start_date,
        'end_date': end_date
    }

class MockResponse:
    def __init__(self, json_data, status=200):
        self.json_data = json_data
        self.status = status

    async def json(self):
        return self.json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_banking_analysis(mock_config, mock_date_range):
    """Test the complete banking analysis workflow"""
    
    # Mock aiohttp ClientSession
    async def mock_get(*args, **kwargs):
        if 'wise' in args[0]:
            if 'profiles' in args[0]:
                return MockResponse([{"id": "PROFILE123"}])
            elif 'borderless-accounts' in args[0]:
                return MockResponse([{"id": "ACC123"}])
            elif 'statement.json' in args[0]:
                return MockResponse({"transactions": MOCK_WISE_TRANSACTIONS})
        elif 'revolut' in args[0]:
            if 'accounts' in args[0]:
                return MockResponse([{"id": "RACC123"}])
            elif 'transactions' in args[0]:
                return MockResponse(MOCK_REVOLUT_TRANSACTIONS)
        return MockResponse([])

    # Create patches
    with patch('aiohttp.ClientSession.get', side_effect=mock_get), \
         patch('aiohttp.ClientSession.post', side_effect=mock_get):
        
        # Initialize crew
        crew = BankingAnalysisCrew(config=mock_config)
        
        # Run analysis
        results = await crew.run(date_range=mock_date_range)
        
        # Verify results
        assert results is not None
        assert 'analysis' in results
        assert 'reports' in results
        assert 'transaction_count' in results
        
        # Verify transaction count
        assert results['transaction_count'] == len(MOCK_WISE_TRANSACTIONS) + len(MOCK_REVOLUT_TRANSACTIONS)
        
        # Verify analysis results
        analysis = results['analysis']
        assert 'summary' in analysis
        assert 'recurring_costs' in analysis
        assert 'spending_patterns' in analysis
        assert 'savings_opportunities' in analysis

@pytest.mark.asyncio
async def test_transaction_processing(mock_config):
    """Test transaction processing functionality"""
    
    banking_tools = BankingTools(mock_config)
    
    # Process mock transactions
    processed_transactions = await banking_tools.process_transactions(
        MOCK_WISE_TRANSACTIONS + MOCK_REVOLUT_TRANSACTIONS,
        'wise'  # Use 'wise' format for testing
    )
    
    # Verify processing results
    assert len(processed_transactions) == len(MOCK_WISE_TRANSACTIONS) + len(MOCK_REVOLUT_TRANSACTIONS)
    
    # Verify transaction enrichment
    for transaction in processed_transactions:
        assert 'category' in transaction
        assert 'tags' in transaction
        assert 'is_recurring' in transaction
        assert 'month' in transaction
        assert 'year' in transaction
        assert 'day_of_week' in transaction

@pytest.mark.asyncio
async def test_cost_analysis(mock_config):
    """Test cost analysis functionality"""
    
    banking_tools = BankingTools(mock_config)
    
    # Process and analyze transactions
    processed_transactions = await banking_tools.process_transactions(
        MOCK_WISE_TRANSACTIONS + MOCK_REVOLUT_TRANSACTIONS,
        'wise'
    )
    analysis_results = await banking_tools.analyze_costs(processed_transactions)
    
    # Verify analysis results
    assert 'summary' in analysis_results
    assert 'recurring_costs' in analysis_results
    assert 'spending_patterns' in analysis_results
    assert 'savings_opportunities' in analysis_results
    
    # Verify specific analysis components
    summary = analysis_results['summary']
    assert isinstance(summary, dict)
    assert len(summary) > 0

@pytest.mark.asyncio
async def test_report_generation(mock_config):
    """Test report generation functionality"""
    
    banking_tools = BankingTools(mock_config)
    
    # Generate sample analysis data
    processed_transactions = await banking_tools.process_transactions(
        MOCK_WISE_TRANSACTIONS + MOCK_REVOLUT_TRANSACTIONS,
        'wise'
    )
    analysis_results = await banking_tools.analyze_costs(processed_transactions)
    
    # Generate reports
    reports = await banking_tools.generate_report(
        analysis_results,
        output_formats=['json', 'pdf']
    )
    
    # Verify report generation
    assert 'json' in reports
    assert 'pdf' in reports
    assert all(isinstance(path, str) for path in reports.values())

if __name__ == '__main__':
    pytest.main(['-v', 'test_banking_agent.py']) 