from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime

class BankAuthBase(ABC):
    """Base class for bank API authentication"""
    
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        self.api_key = api_key
        self.api_url = api_url
        self._access_token = None
        self._token_expiry = None

    @abstractmethod
    async def authenticate(self) -> str:
        """Authenticate with the bank API and return access token"""
        pass

    @abstractmethod
    async def refresh_token(self) -> str:
        """Refresh the access token if expired"""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate the provided credentials"""
        pass

    @property
    def is_token_valid(self) -> bool:
        """Check if the current token is valid"""
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.now() < self._token_expiry

    @abstractmethod
    async def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        pass

    @abstractmethod
    async def revoke_token(self) -> bool:
        """Revoke the current access token"""
        pass

    async def ensure_valid_token(self) -> str:
        """Ensure we have a valid token, refresh if necessary"""
        if not self.is_token_valid:
            if self._access_token:
                return await self.refresh_token()
            return await self.authenticate()
        return self._access_token 