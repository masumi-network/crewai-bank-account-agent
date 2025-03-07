import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from .bank_auth_base import BankAuthBase
from .exceptions import AuthenticationError

class WiseAuth(BankAuthBase):
    """Wise API Authentication Handler"""
    
    def __init__(self, api_key: str, api_url: Optional[str] = None):
        super().__init__(
            api_key=api_key,
            api_url=api_url or "https://api.wise.com/v1"
        )
        self._session = None

    async def _ensure_session(self):
        """Ensure we have an active aiohttp session"""
        if not self._session:
            self._session = aiohttp.ClientSession()

    async def authenticate(self) -> str:
        """Authenticate with Wise API"""
        try:
            await self._ensure_session()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._session.post(
                f"{self.api_url}/oauth/token",
                headers=headers
            ) as response:
                if response.status != 200:
                    raise AuthenticationError(
                        f"Failed to authenticate with Wise: {await response.text()}"
                    )
                
                data = await response.json()
                self._access_token = data["access_token"]
                # Set token expiry to 1 hour from now (adjust based on Wise's actual token lifetime)
                self._token_expiry = datetime.now() + timedelta(hours=1)
                
                return self._access_token
        except Exception as e:
            raise AuthenticationError(f"Wise authentication failed: {str(e)}")

    async def refresh_token(self) -> str:
        """Refresh Wise access token"""
        # Wise might use a different endpoint or mechanism for token refresh
        return await self.authenticate()

    async def validate_credentials(self) -> bool:
        """Validate Wise API credentials"""
        try:
            await self._ensure_session()
            headers = await self.get_headers()
            
            async with self._session.get(
                f"{self.api_url}/profiles",
                headers=headers
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def get_headers(self) -> Dict[str, str]:
        """Get headers for Wise API requests"""
        token = await self.ensure_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def revoke_token(self) -> bool:
        """Revoke Wise access token"""
        if not self._access_token:
            return True
            
        try:
            await self._ensure_session()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._session.post(
                f"{self.api_url}/oauth/token/revoke",
                headers=headers
            ) as response:
                return response.status == 200
        except Exception:
            return False
        finally:
            self._access_token = None
            self._token_expiry = None

    async def close(self):
        """Close the aiohttp session"""
        if self._session:
            await self._session.close()
            self._session = None 