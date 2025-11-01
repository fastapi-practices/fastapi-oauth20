#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx
import pytest
import respx

from fastapi_oauth20.clients.feishu import FeiShuOAuth20
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


class TestFeiShuOAuth20:
    """Test FeiShu OAuth2 client functionality."""

    def test_feishu_client_initialization(self, feishu_client):
        """Test FeiShu client initialization with correct parameters."""
        assert feishu_client.client_id == TEST_CLIENT_ID
        assert feishu_client.client_secret == TEST_CLIENT_SECRET
        assert feishu_client.authorize_endpoint == 'https://passport.feishu.cn/suite/passport/oauth/authorize'
        assert feishu_client.access_token_endpoint == 'https://passport.feishu.cn/suite/passport/oauth/token'
        assert feishu_client.refresh_token_endpoint == 'https://passport.feishu.cn/suite/passport/oauth/authorize'
        assert feishu_client.default_scopes == [
            'contact:user.employee_id:readonly',
            'contact:user.base:readonly',
            'contact:user.email:readonly',
        ]

    def test_feishu_client_initialization_with_custom_credentials(self):
        """Test FeiShu client initialization with custom credentials."""
        client = FeiShuOAuth20(client_id=CUSTOM_CLIENT_ID, client_secret=CUSTOM_CLIENT_SECRET)
        assert client.client_id == CUSTOM_CLIENT_ID
        assert client.client_secret == CUSTOM_CLIENT_SECRET

    def test_feishu_client_inheritance(self, feishu_client):
        """Test that FeiShu client properly inherits from OAuth20Base."""
        assert isinstance(feishu_client, OAuth20Base)

    def test_feishu_client_scopes_are_lists(self, feishu_client):
        """Test that default scopes are properly configured as lists."""
        assert isinstance(feishu_client.default_scopes, list)
        assert len(feishu_client.default_scopes) == 3
        assert all(isinstance(scope, str) for scope in feishu_client.default_scopes)

    def test_feishu_client_endpoint_urls(self):
        """Test that FeiShu client uses correct endpoint URLs."""
        client = FeiShuOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set without hardcoding them in tests
        assert client.authorize_endpoint.endswith('/suite/passport/oauth/authorize')
        assert client.access_token_endpoint.endswith('/suite/passport/oauth/token')
        assert client.refresh_token_endpoint.endswith('/suite/passport/oauth/authorize')

        # Test that all endpoints use the correct domain
        for endpoint in [client.authorize_endpoint, client.access_token_endpoint, client.refresh_token_endpoint]:
            assert 'passport.feishu.cn' in endpoint

    def test_feishu_client_multiple_instances(self):
        """Test that multiple FeiShu client instances work independently."""
        client1 = FeiShuOAuth20('client1', 'secret1')
        client2 = FeiShuOAuth20('client2', 'secret2')

        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint
        assert client1.access_token_endpoint == client2.access_token_endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, feishu_client):
        """Test successful user info retrieval from FeiShu API."""
        mock_user_data = create_mock_user_data('feishu')
        mock_user_info_response(
            respx,
            {'name': 'feishu', 'user_info_url': 'https://passport.feishu.cn/suite/passport/oauth/userinfo'},
            mock_user_data,
        )

        result = await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_with_different_access_token(self, feishu_client):
        """Test user info retrieval with different access tokens."""
        mock_user_data = create_mock_user_data('feishu', user_id='user_789', name='Another User')
        mock_user_info_response(
            respx,
            {'name': 'feishu', 'user_info_url': 'https://passport.feishu.cn/suite/passport/oauth/userinfo'},
            mock_user_data,
        )

        result = await feishu_client.get_userinfo('different_token')
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, feishu_client):
        """Test handling of empty user info response."""
        mock_user_info_response(
            respx, {'name': 'feishu', 'user_info_url': 'https://passport.feishu.cn/suite/passport/oauth/userinfo'}, {}
        )

        result = await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, feishu_client):
        """Test handling of partial user info response."""
        partial_data = {'user_id': 'test_user', 'name': 'Test User'}
        mock_user_info_response(
            respx,
            {'name': 'feishu', 'user_info_url': 'https://passport.feishu.cn/suite/passport/oauth/userinfo'},
            partial_data,
        )

        result = await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, feishu_client):
        """Test that authorization header is correctly formatted."""
        mock_user_data = {'user_id': 'test_user'}
        route = mock_user_info_response(
            respx,
            {'name': 'feishu', 'user_info_url': 'https://passport.feishu.cn/suite/passport/oauth/userinfo'},
            mock_user_data,
        )

        await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)

        # Verify the request was made with correct authorization header
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_401(self, feishu_client):
        """Test handling of 401 HTTP error when getting user info."""
        respx.get('https://passport.feishu.cn/suite/passport/oauth/userinfo').mock(
            return_value=httpx.Response(401, text='Unauthorized')
        )

        with pytest.raises(HTTPXOAuth20Error):
            await feishu_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_403(self, feishu_client):
        """Test handling of 403 HTTP error when getting user info."""
        respx.get('https://passport.feishu.cn/suite/passport/oauth/userinfo').mock(
            return_value=httpx.Response(403, text='Forbidden')
        )

        with pytest.raises(HTTPXOAuth20Error):
            await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_500(self, feishu_client):
        """Test handling of 500 HTTP error when getting user info."""
        respx.get('https://passport.feishu.cn/suite/passport/oauth/userinfo').mock(
            return_value=httpx.Response(500, text='Internal Server Error')
        )

        with pytest.raises(HTTPXOAuth20Error):
            await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, feishu_client):
        """Test handling of invalid JSON response."""
        respx.get('https://passport.feishu.cn/suite/passport/oauth/userinfo').mock(
            return_value=httpx.Response(200, text='invalid json')
        )

        with pytest.raises(GetUserInfoError):
            await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
