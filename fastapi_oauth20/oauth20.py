import json

from typing import Any, Literal, cast
from urllib.parse import urlencode

import httpx

from fastapi_oauth20.errors import (
    AccessTokenError,
    GetUserInfoError,
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
        userinfo_endpoint: str,
        refresh_token_endpoint: str | None = None,
        revoke_token_endpoint: str | None = None,
        default_scopes: list[str] | None = None,
        token_endpoint_basic_auth: bool = False,
        revoke_token_endpoint_basic_auth: bool = False,
    ):
        """
        Base OAuth2 client implementing the OAuth 2.0 authorization framework.

        :param client_id: The client ID provided by the OAuth2 provider.
        :param client_secret: The client secret provided by the OAuth2 provider.
        :param authorize_endpoint: The authorization endpoint URL where users are redirected to grant access.
        :param access_token_endpoint: The token endpoint URL for exchanging authorization codes for access tokens.
        :param userinfo_endpoint: The endpoint URL for retrieving user information using access token.
        :param refresh_token_endpoint: The token endpoint URL for refreshing expired access tokens using refresh tokens.
        :param revoke_token_endpoint: The endpoint URL for revoking access tokens or refresh tokens.
        :param default_scopes: Default list of OAuth scopes to request if none are specified.
        :param token_endpoint_basic_auth: Whether to use HTTP Basic Authentication for token endpoint requests.
        :param revoke_token_endpoint_basic_auth: Whether to use HTTP Basic Authentication for revoke endpoint requests.
        :return:
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.refresh_token_endpoint = refresh_token_endpoint
        self.revoke_token_endpoint = revoke_token_endpoint
        self.userinfo_endpoint = userinfo_endpoint
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
        Generate OAuth2 authorization URL for redirecting users to grant access.

        :param redirect_uri: The URL where the OAuth2 provider will redirect after authorization.
        :param state: An opaque value used by the client to maintain state between the request and callback, preventing CSRF attacks.
        :param scope: The list of OAuth scopes to request. If None, uses default_scopes from initialization.
        :param code_challenge: PKCE code challenge generated from code_verifier using the specified method.
        :param code_challenge_method: PKCE code challenge method, either 'plain' or 'S256' (recommended).
        :param kwargs: Additional query parameters to include in the authorization URL.
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

    async def get_access_token(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> dict[str, Any]:
        """
        Exchange authorization code for access token.

        :param code: The authorization code received from the OAuth2 provider callback.
        :param redirect_uri: The exact redirect URI used in the authorization request (must match).
        :param code_verifier: The PKCE code verifier used to generate the code challenge (required if PKCE was used).
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

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an access token using a refresh token.

        :param refresh_token: The refresh token received from the initial token exchange.
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
        Revoke an access token or refresh token.

        :param token: The access token or refresh token to revoke.
        :param token_type_hint: Optional hint to the server about the token type ('access_token' or 'refresh_token').
        :return:
        """
        if self.revoke_token_endpoint is None:
            raise RevokeTokenError('The revoke token address is missing')

        data = {'token': token}

        if token_type_hint is not None:
            data.update({'token_type_hint': token_type_hint})

        auth = None
        if not self.revoke_token_endpoint_basic_auth:
            data.update({'client_id': self.client_id, 'client_secret': self.client_secret})
        else:
            auth = httpx.BasicAuth(self.client_id, self.client_secret)

        async with httpx.AsyncClient(auth=auth) as client:
            response = await client.post(
                self.revoke_token_endpoint,
                data=data,
                headers=self.request_headers,
            )
            self.raise_httpx_oauth20_errors(response)

    @staticmethod
    def raise_httpx_oauth20_errors(response: httpx.Response) -> None:
        """
        Check HTTP response and raise appropriate OAuth2 errors for invalid responses.

        :param response: The HTTP response object to validate.
        :return:
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPXOAuth20Error(str(e), e.response) from e
        except httpx.HTTPError as e:
            raise HTTPXOAuth20Error(str(e)) from e

    @staticmethod
    def get_json_result(response: httpx.Response, *, err_class: type[OAuth20RequestError]) -> dict[str, Any]:
        """
        Parse JSON response and handle JSON decoding errors.

        :param response: The HTTP response object containing JSON data.
        :param err_class: The specific OAuth2RequestError subclass to raise on JSON parsing failure.
        :return:
        """
        try:
            return cast(dict[str, Any], response.json())
        except json.JSONDecodeError as e:
            raise err_class('Result serialization failed.', response) from e

    async def get_userinfo(self, access_token: str) -> dict[str, Any]:
        """
        Retrieve user information from the OAuth2 provider.

        :param access_token: Valid access token to authenticate the request to the provider's user info endpoint.
        :return:
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.get(self.userinfo_endpoint, headers=headers)
            self.raise_httpx_oauth20_errors(response)
            result = self.get_json_result(response, err_class=GetUserInfoError)
            return result
