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
    return GoogleOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestGoogleOAuth20:
    def test_client_initialization(self, google_client):
        assert google_client.client_id == TEST_CLIENT_ID
        assert google_client.client_secret == TEST_CLIENT_SECRET
        assert google_client.authorize_endpoint == 'https://accounts.google.com/o/oauth2/v2/auth'
        assert google_client.access_token_endpoint == 'https://oauth2.googleapis.com/token'
        assert google_client.refresh_token_endpoint == 'https://oauth2.googleapis.com/token'
        assert google_client.revoke_token_endpoint == 'https://accounts.google.com/o/oauth2/revoke'
        assert google_client.default_scopes == ['email', 'openid', 'profile']

    def test_client_inheritance(self, google_client):
        assert isinstance(google_client, OAuth20Base)

    def test_client_scopes_are_lists(self, google_client):
        assert isinstance(google_client.default_scopes, list)
        assert len(google_client.default_scopes) == 3
        assert all(isinstance(scope, str) for scope in google_client.default_scopes)

    def test_client_endpoint_urls(self, google_client):
        assert google_client.authorize_endpoint.endswith('/o/oauth2/v2/auth')
        assert google_client.access_token_endpoint.endswith('/token')
        assert google_client.refresh_token_endpoint.endswith('/token')
        assert google_client.revoke_token_endpoint.endswith('/o/oauth2/revoke')
        assert 'accounts.google.com' in google_client.authorize_endpoint
        assert 'accounts.google.com' in google_client.revoke_token_endpoint
        assert 'oauth2.googleapis.com' in google_client.access_token_endpoint
        assert 'oauth2.googleapis.com' in google_client.refresh_token_endpoint

    def test_client_multiple_instances(self):
        client1 = GoogleOAuth20('client1', 'secret1')
        client2 = GoogleOAuth20('client2', 'secret2')
        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, google_client):
        mock_user_data = create_mock_user_data('google')
        mock_user_info_response(respx, GOOGLE_USER_INFO_URL, mock_user_data)
        result = await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, google_client):
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(respx, GOOGLE_USER_INFO_URL, mock_user_data)
        await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, google_client):
        mock_user_info_response(respx, GOOGLE_USER_INFO_URL, {})
        result = await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, google_client):
        partial_data = {'id': '123456789', 'email': 'test@example.com'}
        mock_user_info_response(respx, GOOGLE_USER_INFO_URL, partial_data)
        result = await google_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, google_client):
        respx.get(GOOGLE_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))
        with pytest.raises(HTTPXOAuth20Error):
            await google_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, google_client):
        respx.get(GOOGLE_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))
        with pytest.raises(GetUserInfoError):
            await google_client.get_userinfo(TEST_ACCESS_TOKEN)
