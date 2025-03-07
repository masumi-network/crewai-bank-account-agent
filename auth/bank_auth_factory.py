from typing import Dict, Type
from .bank_auth_base import BankAuthBase
from .wise_auth import WiseAuth
from .revolut_auth import RevolutAuth
from .exceptions import BankNotSupportedError

class BankAuthFactory:
    """Factory class for creating bank authentication instances"""
    
    _auth_classes: Dict[str, Type[BankAuthBase]] = {
        "wise": WiseAuth,
        "revolut": RevolutAuth
    }

    @classmethod
    def register_bank(cls, bank_name: str, auth_class: Type[BankAuthBase]):
        """Register a new bank authentication class"""
        cls._auth_classes[bank_name.lower()] = auth_class

    @classmethod
    def create(cls, bank_name: str, api_key: str, api_url: str = None) -> BankAuthBase:
        """Create a bank authentication instance"""
        auth_class = cls._auth_classes.get(bank_name.lower())
        if not auth_class:
            raise BankNotSupportedError(
                f"Bank '{bank_name}' is not supported. "
                f"Supported banks: {', '.join(cls._auth_classes.keys())}"
            )
        
        return auth_class(api_key=api_key, api_url=api_url)

    @classmethod
    def get_supported_banks(cls) -> list:
        """Get list of supported banks"""
        return list(cls._auth_classes.keys()) 