#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx
import pytest
import respx

from fastapi_oauth20.clients.github import GitHubOAuth20
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

GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_INFO_URL = 'https://api.github.com/user'
GITHUB_EMAILS_URL = 'https://api.github.com/user/emails'


@pytest.fixture
def github_client():
    """Create GitHub OAuth2 client instance for testing."""
    return GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestGitHubOAuth20:
    """Test GitHub OAuth2 client functionality."""

    def test_github_client_initialization(self, github_client):
        """Test GitHub client initialization with correct parameters."""
        assert github_client.client_id == TEST_CLIENT_ID
        assert github_client.client_secret == TEST_CLIENT_SECRET
        assert github_client.authorize_endpoint == 'https://github.com/login/oauth/authorize'
        assert github_client.access_token_endpoint == 'https://github.com/login/oauth/access_token'
        assert github_client.default_scopes == ['user', 'user:email']

    def test_github_client_initialization_with_custom_credentials(self):
        """Test GitHub client initialization with custom credentials."""
        client = GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        assert client.client_id == TEST_CLIENT_ID
        assert client.client_secret == TEST_CLIENT_SECRET

    def test_github_client_inheritance(self, github_client):
        """Test that GitHub client properly inherits from OAuth20Base."""
        assert isinstance(github_client, OAuth20Base)

    def test_github_client_scopes_are_lists(self, github_client):
        """Test that default scopes are properly configured as lists."""
        assert isinstance(github_client.default_scopes, list)
        assert len(github_client.default_scopes) == 2
        assert all(isinstance(scope, str) for scope in github_client.default_scopes)

    def test_github_client_endpoint_urls(self):
        """Test that GitHub client uses correct endpoint URLs."""
        client = GitHubOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set without hardcoding them in tests
        assert client.authorize_endpoint.endswith('/login/oauth/authorize')
        assert client.access_token_endpoint.endswith('/login/oauth/access_token')

        # Test that all endpoints use the correct domain
        for endpoint in [client.authorize_endpoint, client.access_token_endpoint]:
            assert 'github.com' in endpoint

    def test_github_client_multiple_instances(self):
        """Test that multiple GitHub client instances work independently."""
        client1 = GitHubOAuth20('client1', 'secret1')
        client2 = GitHubOAuth20('client2', 'secret2')

        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint
        assert client1.access_token_endpoint == client2.access_token_endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success_with_email(self, github_client):
        """Test successful user info retrieval from GitHub API with email included."""
        mock_user_data = create_mock_user_data('github')
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)

        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success_without_email(self, github_client):
        """Test successful user info retrieval from GitHub API without email."""
        mock_user_data = create_mock_user_data('github', email=None)
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)
        # Mock emails endpoint
        emails_data = [{'email': 'test@example.com', 'primary': True}]
        respx.get(GITHUB_EMAILS_URL).mock(return_value=httpx.Response(200, json=emails_data))

        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result['login'] == mock_user_data['login']
        assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_with_different_access_token(self, github_client):
        """Test user info retrieval with different access tokens."""
        mock_user_data = create_mock_user_data('github', id=789, login='different_user')
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)

        result = await github_client.get_userinfo('different_token')
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, github_client):
        """Test that authorization header is correctly formatted."""
        mock_user_data = {'id': 'test_user', 'email': 'test@example.com'}  # Include email to avoid emails endpoint call
        route = mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)

        await github_client.get_userinfo(TEST_ACCESS_TOKEN)

        # Verify the request was made with correct authorization header
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_401(self, github_client):
        """Test handling of 401 HTTP error when getting user info."""
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))

        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_403(self, github_client):
        """Test handling of 403 HTTP error when getting user info."""
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(403, text='Forbidden'))

        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_500(self, github_client):
        """Test handling of 500 HTTP error when getting user info."""
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(500, text='Internal Server Error'))

        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, github_client):
        """Test handling of invalid JSON response."""
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))

        with pytest.raises(GetUserInfoError):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, github_client):
        """Test handling of empty user info response."""
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, {})
        # Mock emails endpoint since empty response will trigger email lookup
        emails_data = [{'email': 'test@example.com', 'primary': True}]
        respx.get(GITHUB_EMAILS_URL).mock(return_value=httpx.Response(200, json=emails_data))

        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, github_client):
        """Test handling of partial user info response."""
        partial_data = {
            'id': 123456,
            'login': 'testuser',
            'email': 'test@example.com',
        }  # Add email to avoid emails endpoint call
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, partial_data)

        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_rate_limit(self, github_client):
        """Test handling of GitHub API rate limit."""
        # GitHub rate limit response
        rate_limit_response = {
            'message': 'API rate limit exceeded for xxx.xxx.xxx.xxx.',
            'documentation_url': 'https://docs.github.com/rest/overview/rate-limits-for-the-rest-api',
        }

        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(403, json=rate_limit_response))

        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)
