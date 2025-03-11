"""
Wise API client for fetching account data.
"""
import requests
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WiseClient:
    """Client for interacting with the Wise API."""
    
    PRODUCTION_URL = "https://api.wise.com"
    SANDBOX_URL = "https://api.sandbox.transferwise.tech"
    API_VERSION = "v1"
    
    def __init__(self, api_key: str, environment: str = "production"):
        """
        Initialize the Wise API client.
        
        Args:
            api_key: The Wise API key
            environment: The API environment ('production' or 'sandbox')
        """
        self.api_key = api_key
        self.environment = environment.lower()
        self.base_url = self.SANDBOX_URL if self.environment == "sandbox" else self.PRODUCTION_URL
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initialized Wise client with {self.environment} environment")
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Wise API.
        
        Args:
            endpoint: API endpoint to call
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            
        Returns:
            API response as a dictionary
        """
        url = f"{self.base_url}/{self.API_VERSION}/{endpoint}"
        
        logger.info(f"Making {method} request to {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Wise API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_profiles(self) -> List[Dict]:
        """
        Get all profiles associated with the account.
        
        Returns:
            List of profile objects
        """
        return self._make_request("profiles")
    
    def get_profile_id(self, profile_type: str = "personal") -> str:
        """
        Get the profile ID for the specified profile type.
        
        Args:
            profile_type: Type of profile ('personal' or 'business')
            
        Returns:
            Profile ID
        """
        profiles = self.get_profiles()
        for profile in profiles:
            if profile["type"].lower() == profile_type.lower():
                return profile["id"]
        raise ValueError(f"No {profile_type} profile found")
    
    def get_accounts(self, profile_id: Optional[str] = None) -> List[Dict]:
        """
        Get all accounts for a profile.
        
        Args:
            profile_id: Profile ID (if None, will use the personal profile)
            
        Returns:
            List of account objects
        """
        if profile_id is None:
            profile_id = self.get_profile_id()
        
        # Different endpoints for sandbox and production
        if self.environment == "sandbox":
            # In sandbox, we need to use the /borderless-accounts endpoint
            endpoint = f"borderless-accounts?profileId={profile_id}"
            response = self._make_request(endpoint)
            
            # Transform the response to match the format expected by the data processor
            accounts = []
            if isinstance(response, list):
                for account in response:
                    # Extract balances from each account
                    if "balances" in account:
                        for balance in account["balances"]:
                            accounts.append({
                                "id": account.get("id"),
                                "currency": balance.get("currency"),
                                "amount": {
                                    "value": balance.get("amount", {}).get("value", 0),
                                    "currency": balance.get("currency")
                                },
                                "type": "STANDARD",
                                "name": f"{balance.get('currency')} Account",
                                "creationTime": account.get("creationTime")
                            })
            return accounts
        else:
            # Production uses the /profiles/{id}/balances endpoint
            return self._make_request(f"profiles/{profile_id}/balances")
    
    def get_account_details(self, account_id: str) -> Dict:
        """
        Get details for a specific account.
        
        Args:
            account_id: Account ID
            
        Returns:
            Account details
        """
        if self.environment == "sandbox":
            return self._make_request(f"borderless-accounts/{account_id}")
        else:
            return self._make_request(f"accounts/{account_id}")
    
    def get_transactions(
        self, 
        profile_id: Optional[str] = None, 
        currency: Optional[str] = None,
        interval_start: Optional[str] = None,
        interval_end: Optional[str] = None,
        limit: int = 100,
        use_real_data: bool = True  # Default to always use real data
    ) -> List[Dict]:
        """
        Get transactions for a profile.
        
        Args:
            profile_id: Profile ID (if None, will use the personal profile)
            currency: Filter by currency code
            interval_start: Start date in ISO format (YYYY-MM-DD)
            interval_end: End date in ISO format (YYYY-MM-DD)
            limit: Maximum number of transactions to return
            use_real_data: If True, will attempt to fetch real transaction data (default is True)
            
        Returns:
            List of transaction objects
        """
        if profile_id is None:
            profile_id = self.get_profile_id()
        
        # Default to last 3 months if no dates provided
        if interval_start is None:
            interval_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if interval_end is None:
            interval_end = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "intervalStart": interval_start,
            "intervalEnd": interval_end,
            "limit": limit
        }
        
        if currency:
            params["currency"] = currency
        
        # Always try to fetch real transaction data
        logger.info("Fetching real transaction data")
        
        # Use the appropriate endpoint based on environment
        if self.environment == "sandbox":
            endpoint = f"profiles/{profile_id}/statements/transactions"
        else:
            endpoint = f"profiles/{profile_id}/statements/transactions"
        
        try:
            return self._make_request(endpoint, params=params)
        except Exception as e:
            logger.error(f"Error fetching real transaction data: {e}")
            # If we're in sandbox mode and real data fails, return an empty list
            # rather than mock data
            if self.environment == "sandbox":
                logger.warning("Unable to fetch real transaction data in sandbox mode. Returning empty list.")
                return []
            else:
                raise
    
    def get_statement(
        self,
        profile_id: Optional[str] = None,
        currency: str = "USD",
        interval_start: Optional[str] = None,
        interval_end: Optional[str] = None
    ) -> Dict:
        """
        Get a statement for a profile.
        
        Args:
            profile_id: Profile ID (if None, will use the personal profile)
            currency: Currency code
            interval_start: Start date in ISO format (YYYY-MM-DD)
            interval_end: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            Statement object
        """
        if profile_id is None:
            profile_id = self.get_profile_id()
        
        # Default to last month if no dates provided
        if interval_start is None:
            interval_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if interval_end is None:
            interval_end = datetime.now().strftime("%Y-%m-%d")
        
        params = {
            "currency": currency,
            "intervalStart": interval_start,
            "intervalEnd": interval_end
        }
        
        # Different handling for sandbox and production
        if self.environment == "sandbox":
            # For sandbox, we'll generate a mock statement
            return {
                "accountHolder": {
                    "type": "PERSONAL",
                    "address": {
                        "country": "US",
                        "city": "New York",
                        "postCode": "10001"
                    }
                },
                "issuer": {
                    "name": "Wise Sandbox",
                    "address": {
                        "country": "UK",
                        "city": "London",
                        "postCode": "EC2N 1HQ"
                    }
                },
                "transactions": self._generate_mock_transactions(profile_id, params),
                "balance": {
                    "value": 1234.56,
                    "currency": currency
                }
            }
        else:
            return self._make_request(f"profiles/{profile_id}/statements", params=params)
    
    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a simple request.
        
        Returns:
            True if the API key is valid, False otherwise
        """
        try:
            self.get_profiles()
            return True
        except requests.exceptions.RequestException:
            return False 