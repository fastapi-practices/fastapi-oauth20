#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class OSChinaOAuth20(OAuth20Base):
    """OSChina OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize OSChina OAuth2 client.

        :param client_id: OSChina OAuth application client ID.
        :param client_secret: OSChina OAuth application client secret.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://www.oschina.net/action/oauth2/authorize',
            access_token_endpoint='https://www.oschina.net/action/openapi/token',
            refresh_token_endpoint='https://www.oschina.net/action/openapi/token',
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """
        Retrieve user information from OSChina API.

        :param access_token: Valid OSChina access token.
        :return:
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get('https://www.oschina.net/action/openapi/user', headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
