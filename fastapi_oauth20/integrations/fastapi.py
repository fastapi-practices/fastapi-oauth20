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
        redirect_route_name: str | None = None,
    ):
        """
        OAuth2 authorization callback dependency injection

        :param client: A client base on OAuth20Base.
        :param redirect_uri: OAuth2 callback full URL.
        :param redirect_route_name: OAuth2 callback route name, as defined by the route decorator 'name' parameter.
        """
        assert (redirect_uri is None and redirect_route_name is not None) or (
            redirect_uri is not None and redirect_route_name is None
        ), 'FastAPIOAuth20 redirect_uri and oauth2_callback_route_name cannot be defined at the same time.'
        self.client = client
        self.redirect_uri = redirect_uri
        self.redirect_route_name = redirect_route_name

    async def __call__(
        self,
        request: Request,
        code: str | None = None,
        state: str | None = None,
        code_verifier: str | None = None,
        error: str | None = None,
    ) -> tuple[dict, str]:
        if code is None or error is not None:
            raise OAuth20AuthorizeCallbackError(
                status_code=400,
                detail=error if error is not None else None,
            )

        if self.redirect_route_name:
            redirect_url = str(request.url_for(self.redirect_route_name))
        else:
            redirect_url = self.redirect_uri

        try:
            access_token = await self.client.get_access_token(
                code=code,
                redirect_uri=redirect_url,
                code_verifier=code_verifier,
            )
        except (HTTPXOAuth20Error, AccessTokenError) as e:
            raise OAuth20AuthorizeCallbackError(
                status_code=500,
                detail=e.msg,
                response=e.response,
            ) from e

        return access_token, state
