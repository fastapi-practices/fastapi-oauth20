#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class GoogleOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
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
        """Get user info from Google"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
