#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.oauth20 import OAuth20Base

AUTHORIZE_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
ACCESS_TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
REFRESH_TOKEN_ENDPOINT = ACCESS_TOKEN_ENDPOINT
REVOKE_TOKEN_ENDPOINT = 'https://accounts.google.com/o/oauth2/revoke'
DEFAULT_SCOPES = ['email', 'openid', 'profile']
PROFILE_ENDPOINT = 'https://www.googleapis.com/oauth2/v1/userinfo'


class GoogleOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint=AUTHORIZE_ENDPOINT,
            access_token_endpoint=ACCESS_TOKEN_ENDPOINT,
            refresh_token_endpoint=REFRESH_TOKEN_ENDPOINT,
            revoke_token_endpoint=REVOKE_TOKEN_ENDPOINT,
            oauth_callback_route_name='google',
            default_scopes=DEFAULT_SCOPES,
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """Gets user info from Google"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get(PROFILE_ENDPOINT, headers=headers)
            await self.raise_httpx_oauth20_errors(response)

            res = response.json()

            return res
