#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx
import pytest
import respx

from fastapi_oauth20 import GoogleOAuth20
from fastapi_oauth20.errors import GetUserInfoError, HTTPXOAuth20Error
from fastapi_oauth20.oauth20 import OAuth20Base
from tests.conftest import (
    INVALID_TOKEN,
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    create_mock_user_data,
    mock_user_info_response,
)

GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v1/userinfo'


@pytest.fixture
def google_client():
    """Create Google OAuth2 client instance for testing."""
    return GoogleOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestGoogleOAuth20:
    """Test Google OAuth2 client functionality."""

    def test_google_client_initialization(self, google_client):
        """Test Google client initialization with correct parameters."""
        assert google_client.client_id == TEST_CLIENT_ID
        assert google_client.client_secret == TEST_CLIENT_SECRET
        assert google_client.authorize_endpoint == 'https://accounts.google.com/o/oauth2/v2/auth'
        assert google_client.access_token_endpoint == 'https://oauth2.googleapis.com/token'
        assert google_client.refresh_token_endpoint == 'https://oauth2.googleapis.com/token'
        assert google_client.revoke_token_endpoint == 'https://accounts.google.com/o/oauth2/revoke'
        assert google_client.default_scopes == ['email', 'openid', 'profile']

    def test_google_client_initialization_with_custom_credentials(self):
        """Test Google client initialization with custom credentials."""
        client = GoogleOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        assert client.client_id == TEST_CLIENT_ID
        assert client.client_secret == TEST_CLIENT_SECRET

    def test_google_client_inheritance(self, google_client):
        """Test that Google client properly inherits from OAuth20Base."""
        assert isinstance(google_client, OAuth20Base)

    def test_google_client_scopes_are_lists(self, google_client):
        """Test that default scopes are properly configured as lists."""
        assert isinstance(google_client.default_scopes, list)
        assert len(google_client.default_scopes) == 3
        assert all(isinstance(scope, str) for scope in google_client.default_scopes)

    def test_google_client_endpoint_urls(self):
        """Test that Google client uses correct endpoint URLs."""
        client = GoogleOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set without hardcoding them in tests
        assert client.authorize_endpoint.endswith('/o/oauth2/v2/auth')
        assert client.access_token_endpoint.endswith('/token')
        assert client.refresh_token_endpoint.endswith('/token')
        assert client.revoke_token_endpoint.endswith('/o/oauth2/revoke')

        # Test that all endpoints use the correct domains
        assert 'accounts.google.com' in client.authorize_endpoint
        assert 'accounts.google.com' in client.revoke_token_endpoint
        assert 'oauth2.googleapis.com' in client.access_token_endpoint
        assert 'oauth2.googleapis.com' in client.refresh_token_endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, google_client):
        """Test successful user info retrieval from Google OAuth2 API."""
        mock_user_data = create_mock_user_data('google')
        mock_user_info_response(respx, GOOGLE_USER_INFO_URL, mock_user_data)

        result = await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, google_client):
        """Test that authorization header is correctly formatted."""
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(respx, GOOGLE_USER_INFO_URL, mock_user_data)

        await google_client.get_userinfo(TEST_ACCESS_TOKEN)

        # Verify the request was made with correct authorization header
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, google_client):
        """Test handling of HTTP errors when getting user info."""
        respx.get(GOOGLE_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))

        with pytest.raises(HTTPXOAuth20Error):
            await google_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, google_client):
        """Test handling of empty user info response."""
        mock_user_info_response(respx, GOOGLE_USER_INFO_URL, {})

        result = await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, google_client):
        """Test handling of partial user info response."""
        partial_data = {'id': '123456789', 'email': 'test@example.com'}
        mock_user_info_response(respx, GOOGLE_USER_INFO_URL, partial_data)

        result = await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, google_client):
        """Test handling of invalid JSON response."""
        respx.get(GOOGLE_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))

        with pytest.raises(GetUserInfoError):
            await google_client.get_userinfo(TEST_ACCESS_TOKEN)

    def test_google_client_multiple_instances(self):
        """Test that multiple Google client instances work independently."""
        client1 = GoogleOAuth20('client1', 'secret1')
        client2 = GoogleOAuth20('client2', 'secret2')

        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint
        assert client1.access_token_endpoint == client2.access_token_endpoint
