#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class HTTPXOAuth20Error(Exception):
    """OAuth2 error for httpx raise for status"""

    pass


class RefreshTokenError(Exception):
    """Refresh token error if the refresh endpoint is missing"""

    pass


class RevokeTokenError(Exception):
    """Revoke token error if the revoke endpoint is missing"""

    pass
