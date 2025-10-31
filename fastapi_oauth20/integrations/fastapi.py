#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any

import httpx

from fastapi import HTTPException, Request

from fastapi_oauth20.errors import AccessTokenError, HTTPXOAuth20Error, OAuth20BaseError
from fastapi_oauth20.oauth20 import OAuth20Base


class OAuth20AuthorizeCallbackError(HTTPException, OAuth20BaseError):
    """The OAuth2 authorization callback error."""

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        self.response = response
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class FastAPIOAuth20:
    def __init__(
        self,
        client: OAuth20Base,
        *,
        redirect_uri: str | None = None,
    ):
        """
        OAuth2 authorization callback dependency injection

        :param client: A client base on OAuth20Base.
        :param redirect_uri: OAuth2 callback full URL.
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
