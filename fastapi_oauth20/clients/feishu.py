#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class FeiShuOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://passport.feishu.cn/suite/passport/oauth/authorize',
            access_token_endpoint='https://passport.feishu.cn/suite/passport/oauth/token',
            refresh_token_endpoint='https://passport.feishu.cn/suite/passport/oauth/authorize',
            default_scopes=[
                'contact:user.employee_id:readonly',
                'contact:user.base:readonly',
                'contact:user.email:readonly',
            ],
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """Get user info from FeiShu"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get('https://passport.feishu.cn/suite/passport/oauth/userinfo', headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
