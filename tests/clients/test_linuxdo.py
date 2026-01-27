import httpx
import pytest
import respx

from fastapi_oauth20 import LinuxDoOAuth20
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
    return LinuxDoOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestLinuxDoOAuth20:
    def test_client_initialization(self, linuxdo_client):
        assert linuxdo_client.client_id == TEST_CLIENT_ID
        assert linuxdo_client.client_secret == TEST_CLIENT_SECRET
        assert linuxdo_client.authorize_endpoint == 'https://connect.linux.do/oauth2/authorize'
        assert linuxdo_client.access_token_endpoint == 'https://connect.linux.do/oauth2/token'
        assert linuxdo_client.refresh_token_endpoint == 'https://connect.linux.do/oauth2/token'
        assert linuxdo_client.default_scopes is None
        assert linuxdo_client.token_endpoint_basic_auth is True

    def test_client_inheritance(self, linuxdo_client):
        assert isinstance(linuxdo_client, OAuth20Base)

    def test_client_basic_auth_enabled(self, linuxdo_client):
        assert linuxdo_client.token_endpoint_basic_auth is True

    def test_client_endpoint_urls(self, linuxdo_client):
        assert linuxdo_client.authorize_endpoint.endswith('/oauth2/authorize')
        assert linuxdo_client.access_token_endpoint.endswith('/oauth2/token')
        assert linuxdo_client.refresh_token_endpoint.endswith('/oauth2/token')
        for endpoint in [
            linuxdo_client.authorize_endpoint,
            linuxdo_client.access_token_endpoint,
            linuxdo_client.refresh_token_endpoint,
        ]:
            assert 'connect.linux.do' in endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, linuxdo_client):
        mock_user_data = create_mock_user_data('linuxdo')
        mock_user_info_response(respx, LINUXDO_USER_INFO_URL, mock_user_data)
        result = await linuxdo_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, linuxdo_client):
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(respx, LINUXDO_USER_INFO_URL, mock_user_data)
        await linuxdo_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, linuxdo_client):
        respx.get(LINUXDO_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))
        with pytest.raises(HTTPXOAuth20Error):
            await linuxdo_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token_uses_basic_auth(self, linuxdo_client):
        mock_token_data = {'access_token': 'new_access_token'}
        route = respx.post('https://connect.linux.do/oauth2/token').mock(
            return_value=httpx.Response(200, json=mock_token_data)
        )
        await linuxdo_client.get_access_token(code='auth_code_123', redirect_uri='https://example.com/callback')
        assert route.called
        request = route.calls[0].request
        assert 'authorization' in request.headers
        assert request.headers['authorization'].startswith('Basic ')
