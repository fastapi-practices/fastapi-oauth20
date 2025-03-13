#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class GiteeOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://gitee.com/oauth/authorize',
            access_token_endpoint='https://gitee.com/oauth/token',
            refresh_token_endpoint='https://gitee.com/oauth/token',
            default_scopes=['user_info'],
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """Get user info from Gitee"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get('https://gitee.com/api/v5/user', headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
