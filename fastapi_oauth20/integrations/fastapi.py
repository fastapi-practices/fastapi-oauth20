#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any

import httpx

from fastapi import HTTPException, Request

from fastapi_oauth20.errors import AccessTokenError, HTTPXOAuth20Error, OAuth20BaseError
from fastapi_oauth20.oauth20 import OAuth20Base


class OAuth20AuthorizeCallbackError(HTTPException, OAuth20BaseError):
    """Exception raised during OAuth2 authorization callback processing in FastAPI."""

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        """
        Initialize OAuth2 callback error.

        :param status_code: HTTP status code to return in the response.
        :param detail: Error detail message describing what went wrong.
        :param headers: Additional HTTP headers to include in the error response.
        :param response: The original HTTP response that caused the error (if any).
        """
        self.response = response
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class FastAPIOAuth20:
    """FastAPI dependency for handling OAuth2 authorization callbacks."""

    def __init__(
        self,
        client: OAuth20Base,
        *,
        redirect_uri: str | None = None,
    ):
        """
        Initialize FastAPI OAuth2 callback handler.

        :param client: An OAuth2 client instance that inherits from OAuth20Base.
        :param redirect_uri: The full callback URL where the OAuth2 provider redirects after authorization. Must match the URL registered with the OAuth2 provider.
        """
        self.client = client
        self.redirect_uri = redirect_uri

    async def __call__(
        self,
        request: Request,
        code: str | None = None,
        state: str | None = None,
        code_verifier: str | None = None,
        error: str | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        """
        Process OAuth2 callback request and exchange authorization code for access token.

        :param request: The FastAPI Request object containing callback parameters.
        :param code: The authorization code received from the OAuth2 provider (extracted from query parameters).
        :param state: The state parameter for CSRF protection (extracted from query parameters).
        :param code_verifier: PKCE code verifier if PKCE was used in the authorization request.
        :param error: Error parameter from OAuth2 provider if authorization was denied or failed.
        """
        if code is None or error is not None:
            raise OAuth20AuthorizeCallbackError(
                status_code=400,
                detail=error if error is not None else None,
            )

        try:
            access_token = await self.client.get_access_token(
                code=code,
                redirect_uri=self.redirect_uri,
                code_verifier=code_verifier,
            )
        except (HTTPXOAuth20Error, AccessTokenError) as e:
            raise OAuth20AuthorizeCallbackError(
                status_code=500,
                detail=e.msg,
                response=e.response,
            ) from e

        return access_token, state
