#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from urllib.parse import urlencode, urljoin

import httpx

from fastapi_oauth20.errors import HTTPXOAuth20Error, RefreshTokenError, RevokeTokenError


class OAuth20Base:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_endpoint: str,
        access_token_endpoint: str,
        refresh_token_endpoint: str | None = None,
        revoke_token_endpoint: str | None = None,
        oauth_callback_route_name: str = 'oauth20',
        default_scopes: list[str] | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.refresh_token_endpoint = refresh_token_endpoint
        self.revoke_token_endpoint = revoke_token_endpoint
        self.oauth_callback_route_name = oauth_callback_route_name
        self.default_scopes = default_scopes

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        scope: list[str] | None = None,
        extras_params: dict = None,
    ) -> str:
        """
        Get authorization url for given.

        :param redirect_uri: redirect uri
        :param state: state to use
        :param scope: scopes to use
        :param extras_params: authorization url params
        :return:
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
        }

        if state is not None:
            params.update({'state': state})

        _scope = scope or self.default_scopes
        if _scope is not None:
            params.update({'scope': ' '.join(_scope)})

        if extras_params is not None:
            params = params.update(extras_params)

        authorization_url = urljoin(self.authorize_endpoint, '?' + urlencode(params))

        return authorization_url

    async def get_access_token(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> dict:
        """
        Get access token for given.

        :param code: authorization code
        :param redirect_uri: redirect uri
        :param code_verifier: the code verifier for the PKCE request
        :return:
        """
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

        if code_verifier:
            data.update({'code_verifier': code_verifier})
        async with httpx.AsyncClient() as client:
            response = await client.post(self.access_token_endpoint, data=data)
            await self.raise_httpx_oauth20_errors(response)

            res = response.json()

            return res

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh the access token"""
        if self.refresh_token_endpoint is None:
            raise RefreshTokenError('The refresh token address is missing')
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.refresh_token_endpoint, data=data)
            await self.raise_httpx_oauth20_errors(response)

            res = response.json()

            return res

    async def revoke_token(self, token: str, token_type_hint: str | None = None) -> None:
        """Revoke the access token"""
        if self.revoke_token_endpoint is None:
            raise RevokeTokenError('The revoke token address is missing')

        async with httpx.AsyncClient() as client:
            data = {'token': token}

            if token_type_hint is not None:
                data.update({'token_type_hint': token_type_hint})

            response = await client.post(self.revoke_token_endpoint, data=data)

            await self.raise_httpx_oauth20_errors(response)

    @staticmethod
    async def raise_httpx_oauth20_errors(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPXOAuth20Error(e) from e
