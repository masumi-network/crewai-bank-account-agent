from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
from auth.wise_auth import WiseAuth

class WiseAPI:
    def __init__(self, auth: WiseAuth):
        self.auth = auth
        self._profile_id = None

    async def get_profile_id(self) -> str:
        """Get the Wise profile ID"""
        if not self._profile_id:
            async with aiohttp.ClientSession() as session:
                headers = await self.auth.get_headers()
                async with session.get(
                    f"{self.auth.api_url}/profiles",
                    headers=headers
                ) as response:
                    profiles = await response.json()
                    self._profile_id = profiles[0]["id"]  # Get first profile
        return self._profile_id

    async def get_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch transactions from Wise"""
        profile_id = await self.get_profile_id()
        headers = await self.auth.get_headers()
        
        async with aiohttp.ClientSession() as session:
            # First get all accounts
            async with session.get(
                f"{self.auth.api_url}/profiles/{profile_id}/borderless-accounts",
                headers=headers
            ) as response:
                accounts = await response.json()

            all_transactions = []
            for account in accounts:
                # Get transactions for each account
                params = {
                    "intervalStart": start_date.isoformat(),
                    "intervalEnd": end_date.isoformat()
                }
                
                async with session.get(
                    f"{self.auth.api_url}/profiles/{profile_id}/borderless-accounts/{account['id']}/statement.json",
                    headers=headers,
                    params=params
                ) as response:
                    transactions = await response.json()
                    all_transactions.extend(transactions.get("transactions", []))

            return [self._format_transaction(t) for t in all_transactions]

    def _format_transaction(self, transaction: Dict) -> Dict:
        """Format Wise transaction to standard format"""
        return {
            "id": transaction.get("referenceNumber"),
            "date": transaction.get("date"),
            "amount": transaction.get("amount", {}).get("value"),
            "currency": transaction.get("amount", {}).get("currency"),
            "description": transaction.get("details", {}).get("description"),
            "type": transaction.get("details", {}).get("type"),
            "category": None,  # Will be filled by categorization agent
            "merchant": transaction.get("details", {}).get("merchant", {}).get("name"),
            "source": "wise"
        } 