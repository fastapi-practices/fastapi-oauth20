import httpx
import pytest
import respx

from fastapi_oauth20 import GiteeOAuth20
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

GITEE_USER_INFO_URL = 'https://gitee.com/api/v5/user'


@pytest.fixture
def gitee_client():
    return GiteeOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestGiteeOAuth20:
    def test_client_initialization(self, gitee_client):
        assert gitee_client.client_id == TEST_CLIENT_ID
        assert gitee_client.client_secret == TEST_CLIENT_SECRET
        assert gitee_client.authorize_endpoint == 'https://gitee.com/oauth/authorize'
        assert gitee_client.access_token_endpoint == 'https://gitee.com/oauth/token'
        assert gitee_client.refresh_token_endpoint == 'https://gitee.com/oauth/token'
        assert gitee_client.default_scopes == ['user_info']

    def test_client_inheritance(self, gitee_client):
        assert isinstance(gitee_client, OAuth20Base)

    def test_client_scopes_are_lists(self, gitee_client):
        assert isinstance(gitee_client.default_scopes, list)
        assert len(gitee_client.default_scopes) == 1
        assert all(isinstance(scope, str) for scope in gitee_client.default_scopes)

    def test_client_endpoint_urls(self, gitee_client):
        assert gitee_client.authorize_endpoint.endswith('/oauth/authorize')
        assert gitee_client.access_token_endpoint.endswith('/oauth/token')
        assert gitee_client.refresh_token_endpoint.endswith('/oauth/token')
        for endpoint in [
            gitee_client.authorize_endpoint,
            gitee_client.access_token_endpoint,
            gitee_client.refresh_token_endpoint,
        ]:
            assert 'gitee.com' in endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, gitee_client):
        mock_user_data = create_mock_user_data('gitee')
        mock_user_info_response(respx, GITEE_USER_INFO_URL, mock_user_data)
        result = await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, gitee_client):
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(respx, GITEE_USER_INFO_URL, mock_user_data)
        await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, gitee_client):
        mock_user_info_response(respx, GITEE_USER_INFO_URL, {})
        result = await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, gitee_client):
        partial_data = {'id': 123456, 'login': 'testuser'}
        mock_user_info_response(respx, GITEE_USER_INFO_URL, partial_data)
        result = await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, gitee_client):
        respx.get(GITEE_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))
        with pytest.raises(HTTPXOAuth20Error):
            await gitee_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, gitee_client):
        respx.get(GITEE_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))
        with pytest.raises(GetUserInfoError):
            await gitee_client.get_userinfo(TEST_ACCESS_TOKEN)
