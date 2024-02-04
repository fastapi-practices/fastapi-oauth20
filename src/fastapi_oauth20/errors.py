#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class FastAPIOAuth20BaseError(Exception):
    pass


class HTTPXOAuth20Error(FastAPIOAuth20BaseError):
    """OAuth2 error for httpx raise for status"""

    pass


class RefreshTokenError(FastAPIOAuth20BaseError):
    """Refresh token error if the refresh endpoint is missing"""

    pass


class RevokeTokenError(FastAPIOAuth20BaseError):
    """Revoke token error if the revoke endpoint is missing"""

    pass


class RedirectURIError(FastAPIOAuth20BaseError):
    """Redirect URI set error"""

    pass
