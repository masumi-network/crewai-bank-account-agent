class AuthenticationError(Exception):
    """Raised when authentication with a bank API fails"""
    pass

class TokenRefreshError(Exception):
    """Raised when token refresh fails"""
    pass

class InvalidCredentialsError(Exception):
    """Raised when provided credentials are invalid"""
    pass

class BankNotSupportedError(Exception):
    """Raised when trying to use an unsupported bank"""
    pass 