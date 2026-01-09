import inspect

from typing import Annotated, Any

import httpx

from fastapi import HTTPException, Query, Request

from fastapi_oauth20.errors import OAuth20BaseError, OAuth20RequestError
from fastapi_oauth20.oauth20 import OAuth20Base


class OAuth20AuthorizeCallbackError(HTTPException, OAuth20BaseError):
    """Exception raised during OAuth2 authorization callback processing in FastAPI."""

    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        """
        Initialize OAuth2 callback error.

        :param status_code: HTTP status code to return in the response.
        :param detail: Error detail message describing what went wrong.
        :param headers: Additional HTTP headers to include in the error response.
        :param response: The original HTTP response that caused the error (if any).
        :return:
        """
        self.response = response
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class FastAPIOAuth20:
    """FastAPI dependency for handling OAuth2 authorization callbacks."""

    def __init__(
        self,
        client: OAuth20Base,
        *,
        redirect_uri: str | None = None,
    ):
        """
        Initialize FastAPI OAuth2 callback handler.

        :param client: An OAuth2 client instance that inherits from OAuth20Base.
        :param redirect_uri: The full callback URL where the OAuth2 provider redirects after authorization. Must match the URL registered with the OAuth2 provider.
        :return:
        """
        self.client = client
        self.redirect_uri = redirect_uri

    async def __call__(
        self,
        request: Request,
        code: Annotated[str | None, Query(description='Authorization code from OAuth2 provider')] = None,
        state: Annotated[str | None, Query(description='State parameter for CSRF protection')] = None,
        code_verifier: Annotated[str | None, Query(description='PKCE code verifier for enhanced security')] = None,
        error: Annotated[str | None, Query(description='Error code if authorization failed')] = None,
    ) -> tuple[dict[str, Any], str | None]:
        """
        Process OAuth2 callback request and exchange authorization code for access token.

        :param request: The FastAPI Request object containing callback parameters.
        :param code: The authorization code received from the OAuth2 provider (extracted from query parameters).
        :param state: The state parameter for CSRF protection (extracted from query parameters).
        :param code_verifier: PKCE code verifier if PKCE was used in the authorization request.
        :param error: Error parameter from OAuth2 provider if authorization was denied or failed.
        :return:
        """
        if code is None or error is not None:
            raise OAuth20AuthorizeCallbackError(
                status_code=400,
                detail=error if error is not None else None,
            )

        kwargs = {'code': code}

        try:
            sig = inspect.signature(self.client.get_access_token)
            params = sig.parameters

            if 'redirect_uri' in params:
                kwargs['redirect_uri'] = self.redirect_uri

            if 'code_verifier' in params:
                kwargs['code_verifier'] = code_verifier

            access_token = await self.client.get_access_token(**kwargs)
        except OAuth20RequestError as e:
            raise OAuth20AuthorizeCallbackError(
                status_code=500,
                detail=e.msg,
                response=e.response,
            ) from e

        return access_token, state
