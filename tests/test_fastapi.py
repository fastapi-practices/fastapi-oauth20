#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx
import pytest
import respx

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from fastapi_oauth20 import FastAPIOAuth20, OAuth20AuthorizeCallbackError
from tests.conftest import (
    OAUTH_PROVIDERS,
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_STATE,
    assert_oauth_error_response,
    mock_oauth_token_response,
    setup_oauth_callback_route,
)

# Integration test specific constants
LOCALHOST_URL = 'http://localhost:8000'
DEV_URL = 'http://dev.example.com'
APP_URL = 'http://app.example.org'
IP_URL = 'http://192.168.1.100:8080'
SECURE_LOCALHOST_URL = 'https://localhost:8000'
SECURE_DEV_URL = 'https://secure.example.com'
SECURE_APP_URL = 'https://app.example.org'
SECURE_IP_URL = 'https://192.168.1.100:8443'

# Callback paths
AUTH_PATH = '/auth'
CALLBACK_PATH = '/callback'
OAUTH_CALLBACK_PATH = '/oauth2/callback'

# Test URIs
HTTP_URIS = [
    f'{LOCALHOST_URL}{CALLBACK_PATH}',
    f'{DEV_URL}{AUTH_PATH}/callback',
    f'{APP_URL}{OAUTH_CALLBACK_PATH}',
    f'{IP_URL}{AUTH_PATH}',
]

HTTPS_URIS = [
    f'{SECURE_LOCALHOST_URL}{CALLBACK_PATH}',
    f'{SECURE_DEV_URL}{AUTH_PATH}/callback',
    f'{SECURE_APP_URL}{OAUTH_CALLBACK_PATH}',
    f'{SECURE_IP_URL}{AUTH_PATH}',
]


class TestFastAPIOAuth20Basic:
    """Basic tests for FastAPI OAuth2 integration using parametrized providers."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_successful_callback_parametrized(self, provider_config, fastapi_app):
        """Test successful OAuth2 callback with multiple providers."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        # Create OAuth client and dependency
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])

        # Setup callback route
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        # Test successful callback
        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}')

        assert response.status_code == 200
        data = response.json()
        assert data['provider'] == provider_config['name']
        assert data['access_token']['access_token'] == TEST_ACCESS_TOKEN

    @pytest.mark.asyncio
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_callback_missing_code_parametrized(self, provider_config, fastapi_app):
        """Test OAuth2 callback with missing authorization code."""
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?state={TEST_STATE}')

        assert_oauth_error_response(response, 'Bad Request')

    @pytest.mark.asyncio
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_callback_with_error_parametrized(self, provider_config, fastapi_app):
        """Test OAuth2 callback with error parameter."""
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?error=access_denied&state={TEST_STATE}')

        assert_oauth_error_response(response, 'access_denied')

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_callback_token_exchange_error_parametrized(self, provider_config, fastapi_app):
        """Test OAuth2 callback with token exchange error."""
        # Mock token exchange error
        respx.post(provider_config['token_url']).mock(return_value=httpx.Response(400, text='Bad Request'))

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=invalid_code&state={TEST_STATE}')

        assert response.status_code == 500
        assert 'detail' in response.json()

    def test_custom_exception_handler(self, github_client, fastapi_app):
        """Test custom exception handler for OAuth2 errors."""
        github_oauth2_callback = FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/auth/github/callback')

        @fastapi_app.get('/auth/github/callback')
        async def github_callback(access_token_state=Depends(github_oauth2_callback)):
            token, state = access_token_state
            return {'access_token': token, 'state': state}

        @fastapi_app.exception_handler(OAuth20AuthorizeCallbackError)
        async def oauth2_error_handler(request: Request, exc: OAuth20AuthorizeCallbackError):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    'message': 'OAuth2 authentication failed',
                    'error': exc.detail,
                    'status_code': exc.status_code,
                },
            )

        client = TestClient(fastapi_app)
        response = client.get('/auth/github/callback?error=access_denied')

        assert response.status_code == 400
        data = response.json()
        assert data['message'] == 'OAuth2 authentication failed'
        assert data['error'] == 'access_denied'
        assert data['status_code'] == 400

    def test_multiple_oauth_providers(self, github_client, google_client, fastapi_app):
        """Test multiple OAuth providers in the same app."""
        # Setup GitHub OAuth
        github_oauth2_callback = FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/auth/github/callback')

        @fastapi_app.get('/auth/github/callback')
        async def github_callback(access_token_state=Depends(github_oauth2_callback)):
            token, state = access_token_state
            return {'provider': 'github', 'access_token': token, 'state': state}

        # Setup Google OAuth
        google_oauth2_callback = FastAPIOAuth20(google_client, redirect_uri=f'{LOCALHOST_URL}/auth/google/callback')

        @fastapi_app.get('/auth/google/callback')
        async def google_callback(access_token_state=Depends(google_oauth2_callback)):
            token, state = access_token_state
            return {'provider': 'google', 'access_token': token, 'state': state}

        client = TestClient(fastapi_app)

        # Test GitHub route
        response = client.get('/auth/github/callback?error=access_denied')
        assert response.status_code == 400

        # Test Google route
        response = client.get('/auth/google/callback?error=access_denied')
        assert response.status_code == 400


class TestFastAPIOAuth20PKCE:
    """Test PKCE functionality across providers."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_pkce_flow(self, provider_config, fastapi_app):
        """Test PKCE flow with code verifier and challenge."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}&code_verifier=test_verifier')

        assert response.status_code == 200
        data = response.json()
        assert data['provider'] == provider_config['name']


class TestFastAPIOAuth20URIs:
    """Test URI validation and functionality."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('redirect_uri', HTTP_URIS)
    async def test_http_redirect_uris(self, provider_config, redirect_uri, fastapi_app):
        """Test OAuth2 with HTTP redirect URIs."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=redirect_uri)
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}')

        assert response.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('redirect_uri', HTTPS_URIS)
    async def test_https_redirect_uris(self, provider_config, redirect_uri, fastapi_app):
        """Test OAuth2 with HTTPS redirect URIs."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=redirect_uri)
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}')

        assert response.status_code == 200


class TestFastAPIOAuth20ErrorScenarios:
    """Test various error scenarios across providers."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('error_code', ['access_denied', 'temporarily_unavailable', 'invalid_request'])
    async def test_oauth_errors(self, provider_config, error_code, fastapi_app):
        """Test various OAuth error codes."""
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?error={error_code}&state={TEST_STATE}')

        assert_oauth_error_response(response, error_code)

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('http_status', [400, 401, 500, 502])
    async def test_token_exchange_errors(self, provider_config, http_status, fastapi_app):
        """Test token exchange with various HTTP error codes."""
        # Mock token exchange error
        respx.post(provider_config['token_url']).mock(
            return_value=httpx.Response(http_status, text=f'Error {http_status}')
        )

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=invalid_code&state={TEST_STATE}')

        # Should return server error for token exchange failures
        assert response.status_code >= 400
        assert 'detail' in response.json()


# Additional test classes for different scenarios
class TestFastAPIOAuth20Integration:
    """Integration tests for FastAPI OAuth2."""

    def test_oauth_dependency_creation(self, github_client):
        """Test OAuth dependency creation with different parameters."""
        # Basic OAuth dependency
        oauth_dep = FastAPIOAuth20(github_client)
        assert oauth_dep.client == github_client

        # OAuth dependency with custom redirect URI
        custom_redirect = f'{LOCALHOST_URL}/custom/callback'
        oauth_dep_custom = FastAPIOAuth20(github_client, redirect_uri=custom_redirect)
        assert oauth_dep_custom.client == github_client

    def test_multiple_apps_same_provider(self, github_client):
        """Test the same OAuth provider in multiple FastAPI apps."""
        app1 = FastAPI()
        app2 = FastAPI()

        # Setup first app
        oauth_dep1 = FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/app1/callback')

        @app1.get('/auth/github/callback')
        async def github_callback1(access_token_state=Depends(oauth_dep1)):
            return {'app': 'app1', 'access_token': access_token_state}

        # Setup second app
        oauth_dep2 = FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/app2/callback')

        @app2.get('/auth/github/callback')
        async def github_callback2(access_token_state=Depends(oauth_dep2)):
            return {'app': 'app2', 'access_token': access_token_state}

        client1 = TestClient(app1)
        client2 = TestClient(app2)

        # Both apps should work independently
        response1 = client1.get('/auth/github/callback?error=access_denied')
        response2 = client2.get('/auth/github/callback?error=access_denied')

        assert response1.status_code == 400
        assert response2.status_code == 400
