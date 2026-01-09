import httpx


class OAuth20BaseError(Exception):
    """Base exception class for all OAuth2-related errors."""

    msg: str

    def __init__(self, msg: str) -> None:
        """
        Initialize base OAuth2 error.

        :param msg: Human-readable error message describing the OAuth2 error.
        :return:
        """
        self.msg = msg
        super().__init__(msg)


class OAuth20RequestError(OAuth20BaseError):
    """Base exception for OAuth2 HTTP request errors."""

    def __init__(self, msg: str, response: httpx.Response | None = None) -> None:
        """
        Initialize OAuth2 request error.

        :param msg: Human-readable error message describing the request error.
        :param response: The HTTP response object that caused the error (if available).
        :return:
        """
        self.response = response
        super().__init__(msg)


class HTTPXOAuth20Error(OAuth20RequestError):
    """Exception raised when httpx raises an HTTP status error."""

    pass


class AccessTokenError(OAuth20RequestError):
    """Exception raised when access token exchange fails."""

    pass


class RefreshTokenError(OAuth20RequestError):
    """Exception raised when refresh token operation fails."""

    pass


class RevokeTokenError(OAuth20RequestError):
    """Exception raised when token revocation fails."""

    pass


class GetUserInfoError(OAuth20RequestError):
    """Exception raised when user info retrieval fails."""

    pass


class RedirectURIError(OAuth20RequestError):
    """Exception raised for redirect URI configuration errors."""

    pass
