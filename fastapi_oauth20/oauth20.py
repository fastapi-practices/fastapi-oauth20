#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import abc
import json

from typing import Literal, cast
from urllib.parse import urlencode

import httpx

from fastapi_oauth20.errors import (
    AccessTokenError,
    HTTPXOAuth20Error,
    OAuth20RequestError,
    RefreshTokenError,
    RevokeTokenError,
)


class OAuth20Base:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        authorize_endpoint: str,
        access_token_endpoint: str,
        refresh_token_endpoint: str | None = None,
        revoke_token_endpoint: str | None = None,
        default_scopes: list[str] | None = None,
        token_endpoint_basic_auth: bool = False,
        revoke_token_endpoint_basic_auth: bool = False,
    ):
        """
        Base OAuth2 client.

        :param client_id: The client ID provided by the OAuth2 provider.
        :param client_secret: The client secret provided by the OAuth2 provider.
        :param authorize_endpoint: The authorization endpoint URL.
        :param access_token_endpoint: The access token endpoint URL.
        :param refresh_token_endpoint: The refresh token endpoint URL.
        :param revoke_token_endpoint: The revoke token endpoint URL.
        :param default_scopes:
        :param token_endpoint_basic_auth:
        :param revoke_token_endpoint_basic_auth:
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.refresh_token_endpoint = refresh_token_endpoint
        self.revoke_token_endpoint = revoke_token_endpoint
        self.default_scopes = default_scopes
        self.token_endpoint_basic_auth = token_endpoint_basic_auth
        self.revoke_token_endpoint_basic_auth = revoke_token_endpoint_basic_auth

        self.request_headers = {
            'Accept': 'application/json',
        }

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        scope: list[str] | None = None,
        code_challenge: str | None = None,
        code_challenge_method: Literal['plain', 'S256'] | None = None,
        **kwargs,
    ) -> str:
        """
        Get authorization url for given.

        :param redirect_uri: redirected after authorization.
        :param state: An opaque value used by the client to maintain state between the request and the callback.
        :param scope: The scopes to be requested.
        :param code_challenge: [PKCE](https://datatracker.ietf.org/doc/html/rfc7636) code challenge.
        :param code_challenge_method: [PKCE](https://datatracker.ietf.org/doc/html/rfc7636) code challenge method.
        :param kwargs: Additional arguments passed to the OAuth2 client.
        :return:
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
        }

        if state is not None:
            params['state'] = state

        _scope = scope or self.default_scopes
        if _scope is not None:
            params['scope'] = ' '.join(_scope)

        if code_challenge is not None:
            params['code_challenge'] = code_challenge

        if code_challenge_method is not None:
            params['code_challenge_method'] = code_challenge_method

        if kwargs:
            params.update(kwargs)

        return f'{self.authorize_endpoint}?{urlencode(params)}'

    async def get_access_token(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> dict:
        """
        Get access token for given.

        :param code: The authorization code.
        :param redirect_uri: redirect uri after authorization.
        :param code_verifier: the code verifier for the [PKCE](https://datatracker.ietf.org/doc/html/rfc7636).
        :return:
        """
        data = {
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }

        auth = None
        if not self.token_endpoint_basic_auth:
            data.update({'client_id': self.client_id, 'client_secret': self.client_secret})
        else:
            auth = httpx.BasicAuth(self.client_id, self.client_secret)

        if code_verifier:
            data.update({'code_verifier': code_verifier})

        async with httpx.AsyncClient(auth=auth) as client:
            response = await client.post(
                self.access_token_endpoint,
                data=data,
                headers=self.request_headers,
            )
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=AccessTokenError)
            return result

    async def refresh_token(self, refresh_token: str) -> dict:
        """
        Get new access token by refresh token.

        :param refresh_token: The refresh token.
        :return:
        """
        if self.refresh_token_endpoint is None:
            raise RefreshTokenError('The refresh token address is missing')

        data = {
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }

        auth = None
        if not self.token_endpoint_basic_auth:
            data.update({'client_id': self.client_id, 'client_secret': self.client_secret})
        else:
            auth = httpx.BasicAuth(self.client_id, self.client_secret)

        async with httpx.AsyncClient(auth=auth) as client:
            response = await client.post(
                self.refresh_token_endpoint,
                data=data,
                headers=self.request_headers,
            )
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=RefreshTokenError)
            return result

    async def revoke_token(self, token: str, token_type_hint: str | None = None) -> None:
        """
        Revoke a token.

        :param token: A token or refresh token to revoke.
        :param token_type_hint: Usually either `token` or `refresh_token`.
        :return:
        """
        if self.revoke_token_endpoint is None:
            raise RevokeTokenError('The revoke token address is missing')

        data = {'token': token}

        if token_type_hint is not None:
            data.update({'token_type_hint': token_type_hint})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.revoke_token_endpoint,
                data=data,
                headers=self.request_headers,
            )
            self.raise_httpx_oauth20_errors(response)

    @staticmethod
    def raise_httpx_oauth20_errors(response: httpx.Response) -> None:
        """Raise HTTPXOAuth20Error if the response is invalid"""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPXOAuth20Error(str(e), e.response) from e
        except httpx.HTTPError as e:
            raise HTTPXOAuth20Error(str(e)) from e

    @staticmethod
    def get_json_result(response: httpx.Response, *, err_class: type[OAuth20RequestError]) -> dict:
        """Get response json"""
        try:
            return cast(dict, response.json())
        except json.decoder.JSONDecodeError as e:
            raise err_class('Result serialization failed.', response) from e

    @abc.abstractmethod
    async def get_userinfo(self, access_token: str) -> dict:
        """
        Get user info from the API provider

        :param access_token: The access token.
        :return:
        """
        raise NotImplementedError()
