#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx
import pytest
import respx

from fastapi_oauth20.clients.linuxdo import LinuxDoOAuth20
from fastapi_oauth20.errors import HTTPXOAuth20Error
from fastapi_oauth20.oauth20 import OAuth20Base
from tests.conftest import (
    INVALID_TOKEN,
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    create_mock_user_data,
    mock_user_info_response,
)

LINUXDO_USER_INFO_URL = 'https://connect.linux.do/api/user'


@pytest.fixture
def linuxdo_client():
    """Create LinuxDo OAuth2 client instance for testing."""
    return LinuxDoOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestLinuxDoOAuth20:
    """Test LinuxDo OAuth2 client functionality."""

    def test_linuxdo_client_initialization(self, linuxdo_client):
        """Test LinuxDo client initialization with correct parameters."""
        assert linuxdo_client.client_id == TEST_CLIENT_ID
        assert linuxdo_client.client_secret == TEST_CLIENT_SECRET
        assert linuxdo_client.authorize_endpoint == 'https://connect.linux.do/oauth2/authorize'
        assert linuxdo_client.access_token_endpoint == 'https://connect.linux.do/oauth2/token'
        assert linuxdo_client.refresh_token_endpoint == 'https://connect.linux.do/oauth2/token'
        assert linuxdo_client.default_scopes is None
        assert linuxdo_client.token_endpoint_basic_auth is True

    def test_linuxdo_client_initialization_with_custom_credentials(self):
        """Test LinuxDo client initialization with custom credentials."""
        client = LinuxDoOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        assert client.client_id == TEST_CLIENT_ID
        assert client.client_secret == TEST_CLIENT_SECRET

    def test_linuxdo_client_inheritance(self, linuxdo_client):
        """Test that LinuxDo client properly inherits from OAuth20Base."""
        assert isinstance(linuxdo_client, OAuth20Base)

    def test_linuxdo_client_basic_auth_enabled(self, linuxdo_client):
        """Test that LinuxDo client has basic authentication enabled for token endpoint."""
        assert linuxdo_client.token_endpoint_basic_auth is True

    def test_linuxdo_client_endpoint_urls(self):
        """Test that LinuxDo client uses correct endpoint URLs."""
        client = LinuxDoOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set without hardcoding them in tests
        assert client.authorize_endpoint.endswith('/oauth2/authorize')
        assert client.access_token_endpoint.endswith('/oauth2/token')
        assert client.refresh_token_endpoint.endswith('/oauth2/token')

        # Test that all endpoints use the correct domain
        for endpoint in [client.authorize_endpoint, client.access_token_endpoint, client.refresh_token_endpoint]:
            assert 'connect.linux.do' in endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, linuxdo_client):
        """Test successful user info retrieval from LinuxDo API."""
        mock_user_data = create_mock_user_data('linuxdo')
        mock_user_info_response(respx, LINUXDO_USER_INFO_URL, mock_user_data)

        result = await linuxdo_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, linuxdo_client):
        """Test that authorization header is correctly formatted."""
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(respx, LINUXDO_USER_INFO_URL, mock_user_data)

        await linuxdo_client.get_userinfo(TEST_ACCESS_TOKEN)

        # Verify the request was made with correct authorization header
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, linuxdo_client):
        """Test handling of HTTP errors when getting user info."""
        respx.get(LINUXDO_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))

        with pytest.raises(HTTPXOAuth20Error):
            await linuxdo_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token_uses_basic_auth(self, linuxdo_client):
        """Test that access token requests use HTTP Basic Authentication."""
        mock_token_data = {'access_token': 'new_access_token'}

        # Mock the token endpoint and capture the request
        route = respx.post('https://connect.linux.do/oauth2/token').mock(
            return_value=httpx.Response(200, json=mock_token_data)
        )

        await linuxdo_client.get_access_token(code='auth_code_123', redirect_uri='https://example.com/callback')

        # Verify BasicAuth was used
        assert route.called
        request = route.calls[0].request
        assert 'authorization' in request.headers
        # Basic auth should be present
        assert request.headers['authorization'].startswith('Basic ')
