from typing import Any
from urllib.parse import urlencode

import httpx

from fastapi_oauth20.errors import AccessTokenError, GetUserInfoError, RefreshTokenError
from fastapi_oauth20.oauth20 import OAuth20Base


class WeChatOpenOAuth20(OAuth20Base):
    """WeChat open platform OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize WeChat open platform OAuth2 client.

        :param client_id: AppID from the WeChat open platform developer console.
        :param client_secret: AppSecret from the WeChat open platform developer console.
        :return:
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://open.weixin.qq.com/connect/qrconnect',
            access_token_endpoint='https://api.weixin.qq.com/sns/oauth2/access_token',
            refresh_token_endpoint='https://api.weixin.qq.com/sns/oauth2/refresh_token',
            userinfo_endpoint='https://api.weixin.qq.com/sns/userinfo',
            default_scopes=['snsapi_login'],
        )

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        scope: list[str] | None = None,
        **kwargs,
    ) -> str:
        """
        Generate WeChat Open Platform OAuth2 authorization URL.

        :param redirect_uri: The URL where WeChat will redirect after authorization.
        :param state: An opaque value used to maintain state between request and callback.
        :param scope: The list of OAuth scopes to request. Default is ['snsapi_login'].
        :param kwargs: Additional query parameters.
        :return:
        """
        params = {'appid': self.client_id, 'redirect_uri': redirect_uri, 'response_type': 'code', 'lang': 'cn'}

        if state is not None:
            params['state'] = state

        _scope = scope or self.default_scopes
        if _scope is not None:
            params['scope'] = ','.join(_scope)

        if kwargs:
            params.update(kwargs)

        return f'{self.authorize_endpoint}?{urlencode(params)}#wechat_redirect'

    async def get_access_token(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for access token using WeChat's GET method.

        :param code: The authorization code received from WeChat callback.
        :return:
        """
        params = {
            'appid': self.client_id,
            'secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.access_token_endpoint,
                params=params,
                headers=self.request_headers,
            )
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=AccessTokenError)
            return result

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using WeChat's GET method.

        :param refresh_token: The refresh token received from initial token exchange.
        :return:
        """
        if self.refresh_token_endpoint is None:
            raise RefreshTokenError('The refresh token address is missing')

        params = {
            'appid': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.refresh_token_endpoint,
                params=params,
                headers=self.request_headers,
            )
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=RefreshTokenError)
            return result

    async def get_userinfo(self, access_token: str, openid: str | None = None) -> dict[str, Any]:
        """
        Retrieve user information from WeChat Open Platform API.

        :param access_token: Valid WeChat access token.
        :param openid: User's OpenID. If not provided, will attempt to extract from previous token response.
        :return:
        """
        if openid is None:
            raise GetUserInfoError('openid is required')

        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN',
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.userinfo_endpoint,
                params=params,
            )
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
