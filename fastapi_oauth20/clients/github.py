#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

from fastapi_oauth20.errors import GetUserInfoError
from fastapi_oauth20.oauth20 import OAuth20Base


class GitHubOAuth20(OAuth20Base):
    def __init__(self, client_id: str, client_secret: str):
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://github.com/login/oauth/authorize',
            access_token_endpoint='https://github.com/login/oauth/access_token',
            default_scopes=['user', 'user:email'],
        )

    async def get_userinfo(self, access_token: str) -> dict:
        """Get user info from GitHub"""
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get('https://api.github.com/user')
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)

            email = result.get('email')
            if email is None:
                response = await client.get('https://api.github.com/user/emails')
                self.raise_httpx_oauth20_errors(response)
                emails = self.get_json_result(response, err_class=GetUserInfoError)
                email = next((email['email'] for email in emails if email.get('primary')), emails[0]['email'])
                result['email'] = email

            return result
