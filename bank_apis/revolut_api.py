from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
from auth.revolut_auth import RevolutAuth

class RevolutAPI:
    def __init__(self, auth: RevolutAuth):
        self.auth = auth

    async def get_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch transactions from Revolut"""
        headers = await self.auth.get_headers()
        
        async with aiohttp.ClientSession() as session:
            # First get all accounts
            async with session.get(
                f"{self.auth.api_url}/accounts",
                headers=headers
            ) as response:
                accounts = await response.json()

            all_transactions = []
            for account in accounts:
                # Get transactions for each account
                params = {
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat(),
                    "count": 1000  # Adjust based on needs
                }
                
                async with session.get(
                    f"{self.auth.api_url}/transactions",
                    headers=headers,
                    params=params
                ) as response:
                    transactions = await response.json()
                    all_transactions.extend(transactions)

            return [self._format_transaction(t) for t in all_transactions]

    def _format_transaction(self, transaction: Dict) -> Dict:
        """Format Revolut transaction to standard format"""
        return {
            "id": transaction.get("id"),
            "date": transaction.get("created_at"),
            "amount": transaction.get("amount"),
            "currency": transaction.get("currency"),
            "description": transaction.get("description"),
            "type": transaction.get("type"),
            "category": None,  # Will be filled by categorization agent
            "merchant": transaction.get("merchant", {}).get("name"),
            "source": "revolut"
        } 