#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class GoogleOAuth20(OAuth20Base):
    """Google OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Google OAuth2 client.

        :param client_id: Google OAuth 2.0 client ID from Google Cloud Console.
        :param client_secret: Google OAuth 2.0 client secret from Google Cloud Console.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://accounts.google.com/o/oauth2/v2/auth',
            access_token_endpoint='https://oauth2.googleapis.com/token',
            refresh_token_endpoint='https://oauth2.googleapis.com/token',
            revoke_token_endpoint='https://accounts.google.com/o/oauth2/revoke',
            default_scopes=['email', 'openid', 'profile'],
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """
        Retrieve user information from Google OAuth2 API.

        :param access_token: Valid Google access token with appropriate scopes.
        :return:
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
