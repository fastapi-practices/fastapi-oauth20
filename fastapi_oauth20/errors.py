#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx


class OAuth20BaseError(Exception):
    """The oauth2 base error."""

    msg: str

    def __init__(self, msg: str) -> None:
        self.msg = msg
        super().__init__(msg)


class OAuth20RequestError(OAuth20BaseError):
    """OAuth2 httpx request error"""

    def __init__(self, msg: str, response: httpx.Response | None = None) -> None:
        self.response = response
        super().__init__(msg)


class HTTPXOAuth20Error(OAuth20RequestError):
    """OAuth2 error for httpx raise for status"""

    pass


class AccessTokenError(OAuth20RequestError):
    """Error raised when get access token fail."""

    pass


class RefreshTokenError(OAuth20RequestError):
    """Refresh token error when refresh token fail."""

    pass


class RevokeTokenError(OAuth20RequestError):
    """Revoke token error when revoke token fail."""

    pass


class GetUserInfoError(OAuth20RequestError):
    """Get user info error when get user info fail."""

    pass


class RedirectURIError(OAuth20RequestError):
    """Redirect URI set error"""

    pass
