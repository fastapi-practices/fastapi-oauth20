#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.oauth20 import OAuth20Base

AUTHORIZE_ENDPOINT = 'https://github.com/login/oauth/authorize'
ACCESS_TOKEN_ENDPOINT = 'https://github.com/login/oauth/access_token'
REFRESH_TOKEN_ENDPOINT = None
REVOKE_TOKEN_ENDPOINT = None
DEFAULT_SCOPES = ['user', 'user:email']
PROFILE_ENDPOINT = 'https://api.github.com/user'


class GitHubOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint=AUTHORIZE_ENDPOINT,
            access_token_endpoint=ACCESS_TOKEN_ENDPOINT,
            refresh_token_endpoint=REFRESH_TOKEN_ENDPOINT,
            revoke_token_endpoint=REVOKE_TOKEN_ENDPOINT,
            oauth_callback_route_name='github',
            default_scopes=DEFAULT_SCOPES,
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """Get user info from GitHub"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(PROFILE_ENDPOINT)
            await self.raise_httpx_oauth20_errors(response)

            res = response.json()

            email = res.get('email')
            if email is None:
                response = await client.get(f'{PROFILE_ENDPOINT}/emails')
                await self.raise_httpx_oauth20_errors(response)

                emails = response.json()

                email = next((email['email'] for email in emails if email.get('primary')), emails[0]['email'])
                res['email'] = email

            return res
