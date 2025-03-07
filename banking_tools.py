from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from dataclasses import dataclass
import aiohttp
import asyncio
from langchain.tools import Tool
from auth.bank_auth_factory import BankAuthFactory
from bank_apis.wise_api import WiseAPI
from bank_apis.revolut_api import RevolutAPI
from processors.transaction_processor import TransactionProcessor
from processors.cost_analyzer import CostAnalyzer
from processors.report_generator import ReportGenerator

@dataclass
class BankConfig:
    api_key: str
    api_url: str
    bank_type: str

class BankingTools:
    """Unified banking tools for transaction analysis and reporting"""
    
    def __init__(self, config: Dict[str, Dict[str, str]]):
        """
        Initialize with bank configurations
        config = {
            'wise': {'api_key': 'key', 'api_url': 'url'},
            'revolut': {'api_key': 'key', 'api_url': 'url'}
        }
        """
        self.banks = {}
        for bank_type, settings in config.items():
            self.banks[bank_type] = BankConfig(
                api_key=settings['api_key'],
                api_url=settings['api_url'],
                bank_type=bank_type
            )
        
        self.session = None
        self.transaction_processor = TransactionProcessor()
        self.cost_analyzer = CostAnalyzer()
        self.report_generator = ReportGenerator(
            google_creds_path=config.get('google_sheets_credentials')
        )

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def _get_headers(self, bank_type: str) -> Dict[str, str]:
        """Get headers for bank API requests"""
        bank = self.banks.get(bank_type)
        if not bank:
            raise ValueError(f"Unsupported bank type: {bank_type}")
            
        return {
            "Authorization": f"Bearer {bank.api_key}",
            "Content-Type": "application/json"
        }

    async def get_transactions(self, 
                             bank_type: str, 
                             start_date: datetime, 
                             end_date: datetime) -> List[Dict]:
        """Fetch transactions from specified bank"""
        await self._ensure_session()
        headers = await self._get_headers(bank_type)
        bank = self.banks[bank_type]
        
        try:
            if bank_type == 'wise':
                transactions = await self._get_wise_transactions(headers, start_date, end_date)
            elif bank_type == 'revolut':
                transactions = await self._get_revolut_transactions(headers, start_date, end_date)
            else:
                raise ValueError(f"Unsupported bank type: {bank_type}")
                
            return await self.process_transactions(transactions, bank_type)
        except Exception as e:
            raise Exception(f"Failed to fetch transactions from {bank_type}: {str(e)}")

    async def _get_wise_transactions(self, headers: Dict, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch transactions from Wise"""
        bank = self.banks['wise']
        
        # First get profile ID
        async with self.session.get(f"{bank.api_url}/profiles", headers=headers) as response:
            profiles = await response.json()
            profile_id = profiles[0]["id"]
        
        # Get transactions
        params = {
            "intervalStart": start_date.isoformat(),
            "intervalEnd": end_date.isoformat()
        }
        
        async with self.session.get(
            f"{bank.api_url}/profiles/{profile_id}/borderless-accounts",
            headers=headers
        ) as response:
            accounts = await response.json()
            
        all_transactions = []
        for account in accounts:
            async with self.session.get(
                f"{bank.api_url}/profiles/{profile_id}/borderless-accounts/{account['id']}/statement.json",
                headers=headers,
                params=params
            ) as response:
                data = await response.json()
                all_transactions.extend(data.get("transactions", []))
                
        return all_transactions

    async def _get_revolut_transactions(self, headers: Dict, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch transactions from Revolut"""
        bank = self.banks['revolut']
        
        # Get accounts
        async with self.session.get(f"{bank.api_url}/accounts", headers=headers) as response:
            accounts = await response.json()
        
        all_transactions = []
        for account in accounts:
            params = {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
                "count": 1000
            }
            
            async with self.session.get(
                f"{bank.api_url}/transactions",
                headers=headers,
                params=params
            ) as response:
                transactions = await response.json()
                all_transactions.extend(transactions)
                
        return all_transactions

    async def process_transactions(self, transactions: List[Dict], bank_type: str) -> List[Dict]:
        """Process and enrich transactions"""
        # Standardize transaction format
        formatted_transactions = []
        for tx in transactions:
            if bank_type == 'wise':
                formatted_tx = {
                    "id": tx.get("referenceNumber"),
                    "date": tx.get("date"),
                    "amount": tx.get("amount", {}).get("value"),
                    "currency": tx.get("amount", {}).get("currency"),
                    "description": tx.get("details", {}).get("description"),
                    "merchant": tx.get("details", {}).get("merchant", {}).get("name"),
                    "source": "wise"
                }
            else:  # revolut
                formatted_tx = {
                    "id": tx.get("id"),
                    "date": tx.get("created_at"),
                    "amount": tx.get("amount"),
                    "currency": tx.get("currency"),
                    "description": tx.get("description"),
                    "merchant": tx.get("merchant", {}).get("name"),
                    "source": "revolut"
                }
            formatted_transactions.append(formatted_tx)
        
        # Process transactions
        return self.transaction_processor.process_transactions(formatted_transactions)

    async def analyze_costs(self, transactions: List[Dict]) -> Dict:
        """Analyze transactions for insights"""
        return self.cost_analyzer.analyze_transactions(transactions)

    async def generate_report(self, analysis_data: Dict, output_formats: List[str] = None) -> Dict[str, str]:
        """Generate reports in specified formats"""
        if output_formats is None:
            output_formats = ["json", "pdf"]
            
        return self.report_generator.generate_report(
            analysis_data,
            output_formats=output_formats
        )

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    def get_wise_transactions(self, date_range: Dict) -> Tool:
        """Tool for fetching transactions from Wise API"""
        async def _fetch_wise_data(date_range: Dict) -> List[Dict]:
            await self._ensure_wise_api()
            transactions = await self._wise_api.get_transactions(
                start_date=date_range["start_date"],
                end_date=date_range["end_date"]
            )
            return self.transaction_processor.process_transactions(transactions)
            
        return Tool(
            name="WiseTransactionFetcher",
            func=_fetch_wise_data,
            description="Fetches and processes transaction data from Wise API"
        )
    
    def get_revolut_transactions(self, date_range: Dict) -> Tool:
        """Tool for fetching transactions from Revolut API"""
        async def _fetch_revolut_data(date_range: Dict) -> List[Dict]:
            await self._ensure_revolut_api()
            transactions = await self._revolut_api.get_transactions(
                start_date=date_range["start_date"],
                end_date=date_range["end_date"]
            )
            return self.transaction_processor.process_transactions(transactions)
            
        return Tool(
            name="RevolutTransactionFetcher",
            func=_fetch_revolut_data,
            description="Fetches and processes transaction data from Revolut API"
        )
    
    def analyze_costs(self) -> Tool:
        """Tool for analyzing costs and finding optimization opportunities"""
        def _analyze(transactions: List[Dict]) -> Dict:
            return self.cost_analyzer.analyze_transactions(transactions)
            
        return Tool(
            name="CostAnalyzer",
            func=_analyze,
            description="Analyzes transactions to find cost-saving opportunities"
        )
    
    def generate_report(self) -> Tool:
        """Tool for generating financial reports"""
        def _generate(analysis_data: Dict) -> Dict:
            return self.report_generator.generate_report(
                analysis_data,
                output_formats=["json", "pdf", "sheets"]
            )
            
        return Tool(
            name="ReportGenerator",
            func=_generate,
            description="Generates comprehensive financial reports"
        ) 