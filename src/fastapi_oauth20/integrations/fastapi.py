#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request

from fastapi_oauth20.oauth20 import OAuth20Base


class OAuth20:
    def __init__(
        self,
        client: OAuth20Base,
        redirect_uri: str | None = None,
        oauth_callback_route_name: str | None = None,
    ):
        self.client = client
        self.oauth_callback_route_name = oauth_callback_route_name
        self.redirect_uri = redirect_uri

    async def __call__(
        self, request: Request, code: str, state: str | None, code_verifier: str | None = None
    ) -> tuple[dict, str]:
        if self.redirect_uri is None:
            self.redirect_uri = str(request.url_for(self.oauth_callback_route_name))

        access_token = await self.client.get_access_token(
            code=code, redirect_uri=self.redirect_uri, code_verifier=code_verifier
        )

        return access_token, state
