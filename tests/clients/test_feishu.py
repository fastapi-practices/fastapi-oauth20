import httpx
import pytest
import respx

from fastapi_oauth20 import FeiShuOAuth20
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

FEISHU_USER_INFO_URL = 'https://passport.feishu.cn/suite/passport/oauth/userinfo'


@pytest.fixture
def feishu_client():
    return FeiShuOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestFeiShuOAuth20:
    def test_client_initialization(self, feishu_client):
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

    def test_client_inheritance(self, feishu_client):
        assert isinstance(feishu_client, OAuth20Base)

    def test_client_scopes_are_lists(self, feishu_client):
        assert isinstance(feishu_client.default_scopes, list)
        assert len(feishu_client.default_scopes) == 3
        assert all(isinstance(scope, str) for scope in feishu_client.default_scopes)

    def test_client_endpoint_urls(self, feishu_client):
        assert feishu_client.authorize_endpoint.endswith('/suite/passport/oauth/authorize')
        assert feishu_client.access_token_endpoint.endswith('/suite/passport/oauth/token')
        assert feishu_client.refresh_token_endpoint.endswith('/suite/passport/oauth/authorize')
        for endpoint in [
            feishu_client.authorize_endpoint,
            feishu_client.access_token_endpoint,
            feishu_client.refresh_token_endpoint,
        ]:
            assert 'passport.feishu.cn' in endpoint

    def test_client_multiple_instances(self):
        client1 = FeiShuOAuth20('client1', 'secret1')
        client2 = FeiShuOAuth20('client2', 'secret2')
        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, feishu_client):
        mock_user_data = create_mock_user_data('feishu')
        mock_user_info_response(respx, FEISHU_USER_INFO_URL, mock_user_data)
        result = await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_with_different_access_token(self, feishu_client):
        mock_user_data = create_mock_user_data('feishu', user_id='user_789', name='Another User')
        mock_user_info_response(respx, FEISHU_USER_INFO_URL, mock_user_data)
        result = await feishu_client.get_userinfo('different_token')
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, feishu_client):
        mock_user_info_response(respx, FEISHU_USER_INFO_URL, {})
        result = await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == {}

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, feishu_client):
        partial_data = {'user_id': 'test_user', 'name': 'Test User'}
        mock_user_info_response(respx, FEISHU_USER_INFO_URL, partial_data)
        result = await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, feishu_client):
        mock_user_data = {'user_id': 'test_user'}
        route = mock_user_info_response(respx, FEISHU_USER_INFO_URL, mock_user_data)
        await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_401(self, feishu_client):
        respx.get(FEISHU_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))
        with pytest.raises(HTTPXOAuth20Error):
            await feishu_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_403(self, feishu_client):
        respx.get(FEISHU_USER_INFO_URL).mock(return_value=httpx.Response(403, text='Forbidden'))
        with pytest.raises(HTTPXOAuth20Error):
            await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_500(self, feishu_client):
        respx.get(FEISHU_USER_INFO_URL).mock(return_value=httpx.Response(500, text='Internal Server Error'))
        with pytest.raises(HTTPXOAuth20Error):
            await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, feishu_client):
        respx.get(FEISHU_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))
        with pytest.raises(GetUserInfoError):
            await feishu_client.get_userinfo(TEST_ACCESS_TOKEN)
