#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class FeiShuOAuth20(OAuth20Base):
    """FeiShu (Lark) OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize FeiShu OAuth2 client.

        :param client_id: FeiShu app client ID from the FeiShu developer console.
        :param client_secret: FeiShu app client secret from the FeiShu developer console.
        """
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
        """
        Retrieve user information from FeiShu API.

        :param access_token: Valid FeiShu access token with contact:user scopes.
        :return:
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get('https://passport.feishu.cn/suite/passport/oauth/userinfo', headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
