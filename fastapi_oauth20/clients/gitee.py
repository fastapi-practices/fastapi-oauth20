#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.oauth20 import OAuth20Base

AUTHORIZE_ENDPOINT = 'https://gitee.com/oauth/authorize'
ACCESS_TOKEN_ENDPOINT = 'https://gitee.com/oauth/token'
REFRESH_TOKEN_ENDPOINT = ACCESS_TOKEN_ENDPOINT
REVOKE_TOKEN_ENDPOINT = None
DEFAULT_SCOPES = ['user_info']
PROFILE_ENDPOINT = 'https://gitee.com/api/v5/user'


class GiteeOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint=AUTHORIZE_ENDPOINT,
            access_token_endpoint=ACCESS_TOKEN_ENDPOINT,
            refresh_token_endpoint=REFRESH_TOKEN_ENDPOINT,
            revoke_token_endpoint=REVOKE_TOKEN_ENDPOINT,
            oauth_callback_route_name='gitee',
            default_scopes=DEFAULT_SCOPES,
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """Get user info from Gitee"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get(PROFILE_ENDPOINT, headers=headers)
            await self.raise_httpx_oauth20_errors(response)

            res = response.json()

            return res
