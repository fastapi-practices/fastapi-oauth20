#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx
import pytest
import respx

from fastapi_oauth20.clients.gitee import GiteeOAuth20
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

# Constants specific to this test file
CUSTOM_CLIENT_ID = 'custom_id'
CUSTOM_CLIENT_SECRET = 'custom_secret'


class TestGiteeOAuth20:
    """Test Gitee OAuth2 client functionality."""

    def test_gitee_client_initialization(self, gitee_client):
        """Test Gitee client initialization with correct parameters."""
        assert gitee_client.client_id == TEST_CLIENT_ID
        assert gitee_client.client_secret == TEST_CLIENT_SECRET
        assert gitee_client.authorize_endpoint == 'https://gitee.com/oauth/authorize'
        assert gitee_client.access_token_endpoint == 'https://gitee.com/oauth/token'
        assert gitee_client.refresh_token_endpoint == 'https://gitee.com/oauth/token'
        assert gitee_client.default_scopes == ['user_info']

    def test_gitee_client_initialization_with_custom_credentials(self):
        """Test Gitee client initialization with custom credentials."""
        client = GiteeOAuth20(client_id=CUSTOM_CLIENT_ID, client_secret=CUSTOM_CLIENT_SECRET)
        assert client.client_id == CUSTOM_CLIENT_ID
        assert client.client_secret == CUSTOM_CLIENT_SECRET

    def test_gitee_client_inheritance(self, gitee_client):
        """Test that Gitee client properly inherits from OAuth20Base."""
        assert isinstance(gitee_client, OAuth20Base)

    def test_gitee_client_scopes_are_lists(self, gitee_client):
        """Test that default scopes are properly configured as lists."""
        assert isinstance(gitee_client.default_scopes, list)
        assert len(gitee_client.default_scopes) == 1
        assert all(isinstance(scope, str) for scope in gitee_client.default_scopes)

    def test_gitee_client_endpoint_urls(self):
        """Test that Gitee client uses correct endpoint URLs."""
        client = GiteeOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set without hardcoding them in tests
        assert client.authorize_endpoint.endswith('/oauth/authorize')
        assert client.access_token_endpoint.endswith('/oauth/token')
        assert client.refresh_token_endpoint.endswith('/oauth/token')

        # Test that all endpoints use the correct domain
        for endpoint in [client.authorize_endpoint, client.access_token_endpoint, client.refresh_token_endpoint]:
            assert 'gitee.com' in endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, gitee_client):
        """Test successful user info retrieval from Gitee API."""
        mock_user_data = create_mock_user_data('gitee')
        mock_user_info_response(
            respx, {'name': 'gitee', 'user_info_url': 'https://gitee.com/api/v5/user'}, mock_user_data
        )

        result = await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, gitee_client):
        """Test that authorization header is correctly formatted."""
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(
            respx, {'name': 'gitee', 'user_info_url': 'https://gitee.com/api/v5/user'}, mock_user_data
        )

        await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)

        # Verify the request was made with correct authorization header
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, gitee_client):
        """Test handling of HTTP errors when getting user info."""
        respx.get('https://gitee.com/api/v5/user').mock(return_value=httpx.Response(401, text='Unauthorized'))

        with pytest.raises(HTTPXOAuth20Error):
            await gitee_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, gitee_client):
        """Test handling of empty user info response."""
        mock_user_info_response(respx, {'name': 'gitee', 'user_info_url': 'https://gitee.com/api/v5/user'}, {})

        result = await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, gitee_client):
        """Test handling of partial user info response."""
        partial_data = {'id': 123456, 'login': 'testuser'}
        mock_user_info_response(
            respx, {'name': 'gitee', 'user_info_url': 'https://gitee.com/api/v5/user'}, partial_data
        )

        result = await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, gitee_client):
        """Test handling of invalid JSON response."""
        respx.get('https://gitee.com/api/v5/user').mock(return_value=httpx.Response(200, text='invalid json'))

        with pytest.raises(GetUserInfoError):
            await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
