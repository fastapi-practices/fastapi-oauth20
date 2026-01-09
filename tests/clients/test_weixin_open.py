import httpx
import pytest
import respx

from fastapi_oauth20 import WeChatOpenOAuth20
from fastapi_oauth20.errors import GetUserInfoError, HTTPXOAuth20Error
from fastapi_oauth20.oauth20 import OAuth20Base
from tests.conftest import (
    INVALID_TOKEN,
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    create_mock_user_data,
)

WECHAT_OPEN_USER_INFO_URL = 'https://api.weixin.qq.com/sns/userinfo'


@pytest.fixture
def wechat_open_client():
    """Create WeChat Open OAuth2 client instance for testing."""
    return WeChatOpenOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestWeChatOpenOAuth20:
    """Test WeChat Open OAuth2 client functionality."""

    def test_wechat_open_client_initialization(self, wechat_open_client):
        """Test WeChat Open client initialization with correct parameters."""
        assert wechat_open_client.client_id == TEST_CLIENT_ID
        assert wechat_open_client.client_secret == TEST_CLIENT_SECRET
        assert wechat_open_client.authorize_endpoint == 'https://open.weixin.qq.com/connect/qrconnect'
        assert wechat_open_client.access_token_endpoint == 'https://api.weixin.qq.com/sns/oauth2/access_token'
        assert wechat_open_client.refresh_token_endpoint == 'https://api.weixin.qq.com/sns/oauth2/refresh_token'
        assert wechat_open_client.userinfo_endpoint == 'https://api.weixin.qq.com/sns/userinfo'
        assert wechat_open_client.default_scopes == ['snsapi_login']

    def test_wechat_open_client_initialization_with_custom_credentials(self):
        """Test WeChat Open client initialization with custom credentials."""
        client = WeChatOpenOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        assert client.client_id == TEST_CLIENT_ID
        assert client.client_secret == TEST_CLIENT_SECRET

    def test_wechat_open_client_inheritance(self, wechat_open_client):
        """Test that WeChat Open client properly inherits from OAuth20Base."""
        assert isinstance(wechat_open_client, OAuth20Base)

    def test_wechat_open_client_scopes_are_lists(self, wechat_open_client):
        """Test that default scopes are properly configured as lists."""
        assert isinstance(wechat_open_client.default_scopes, list)
        assert len(wechat_open_client.default_scopes) == 1
        assert all(isinstance(scope, str) for scope in wechat_open_client.default_scopes)

    def test_wechat_open_client_endpoint_urls(self):
        """Test that WeChat Open client uses correct endpoint URLs."""
        client = WeChatOpenOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set
        assert client.authorize_endpoint.endswith('/connect/qrconnect')
        assert client.access_token_endpoint.endswith('/sns/oauth2/access_token')
        assert client.refresh_token_endpoint.endswith('/sns/oauth2/refresh_token')
        assert client.userinfo_endpoint.endswith('/sns/userinfo')

        # Test that all endpoints use the correct domain
        assert 'open.weixin.qq.com' in client.authorize_endpoint
        assert 'api.weixin.qq.com' in client.access_token_endpoint
        assert 'api.weixin.qq.com' in client.refresh_token_endpoint
        assert 'api.weixin.qq.com' in client.userinfo_endpoint

    def test_wechat_open_client_multiple_instances(self):
        """Test that multiple WeChat Open client instances work independently."""
        client1 = WeChatOpenOAuth20('client1', 'secret1')
        client2 = WeChatOpenOAuth20('client2', 'secret2')

        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint
        assert client1.access_token_endpoint == client2.access_token_endpoint

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, wechat_open_client):
        """Test WeChat Open authorization URL generation."""
        redirect_uri = 'https://example.com/callback'
        state = 'test_state'

        url = await wechat_open_client.get_authorization_url(redirect_uri=redirect_uri, state=state)

        assert 'open.weixin.qq.com/connect/qrconnect' in url
        assert f'appid={TEST_CLIENT_ID}' in url
        assert 'redirect_uri=https%3A%2F%2Fexample.com%2Fcallback' in url
        assert f'state={state}' in url
        assert 'response_type=code' in url
        assert 'scope=snsapi_login' in url
        assert url.endswith('#wechat_redirect')

    @pytest.mark.asyncio
    async def test_get_authorization_url_with_custom_scope(self, wechat_open_client):
        """Test WeChat Open authorization URL with custom scope."""
        redirect_uri = 'https://example.com/callback'
        scope = ['snsapi_login']

        url = await wechat_open_client.get_authorization_url(redirect_uri=redirect_uri, scope=scope)

        assert 'scope=snsapi_login' in url

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, wechat_open_client):
        """Test successful user info retrieval from WeChat Open API."""
        mock_user_data = create_mock_user_data('wechat_open')
        openid = 'test_openid'

        # Mock the userinfo endpoint with query parameters
        respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(200, json=mock_user_data))

        result = await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN, openid=openid)
        assert result == mock_user_data

    @pytest.mark.asyncio
    async def test_get_userinfo_without_openid(self, wechat_open_client):
        """Test that get_userinfo raises error when openid is not provided."""
        with pytest.raises(GetUserInfoError, match='openid is required'):
            await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_401(self, wechat_open_client):
        """Test handling of 401 HTTP error when getting user info."""
        openid = 'test_openid'
        respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))

        with pytest.raises(HTTPXOAuth20Error):
            await wechat_open_client.get_userinfo(INVALID_TOKEN, openid=openid)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_403(self, wechat_open_client):
        """Test handling of 403 HTTP error when getting user info."""
        openid = 'test_openid'
        respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(403, text='Forbidden'))

        with pytest.raises(HTTPXOAuth20Error):
            await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN, openid=openid)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_500(self, wechat_open_client):
        """Test handling of 500 HTTP error when getting user info."""
        openid = 'test_openid'
        respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(500, text='Internal Server Error'))

        with pytest.raises(HTTPXOAuth20Error):
            await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN, openid=openid)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, wechat_open_client):
        """Test handling of invalid JSON response."""
        openid = 'test_openid'
        respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))

        with pytest.raises(GetUserInfoError):
            await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN, openid=openid)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token_success(self, wechat_open_client):
        """Test successful access token retrieval."""
        mock_token_data = {
            'access_token': TEST_ACCESS_TOKEN,
            'expires_in': 7200,
            'refresh_token': 'test_refresh_token',
            'openid': 'test_openid',
            'scope': 'snsapi_login',
            'unionid': 'test_unionid',
        }

        respx.get('https://api.weixin.qq.com/sns/oauth2/access_token').mock(
            return_value=httpx.Response(200, json=mock_token_data)
        )

        result = await wechat_open_client.get_access_token(code='test_code')
        assert result == mock_token_data
        assert result['access_token'] == TEST_ACCESS_TOKEN
        assert result['openid'] == 'test_openid'
        assert result['unionid'] == 'test_unionid'

    @pytest.mark.asyncio
    @respx.mock
    async def test_refresh_token_success(self, wechat_open_client):
        """Test successful token refresh."""
        mock_token_data = {
            'access_token': 'new_access_token',
            'expires_in': 7200,
            'refresh_token': 'new_refresh_token',
            'openid': 'test_openid',
            'scope': 'snsapi_login',
        }

        respx.get('https://api.weixin.qq.com/sns/oauth2/refresh_token').mock(
            return_value=httpx.Response(200, json=mock_token_data)
        )

        result = await wechat_open_client.refresh_token(refresh_token='test_refresh_token')
        assert result == mock_token_data
        assert result['access_token'] == 'new_access_token'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_wechat_error_response(self, wechat_open_client):
        """Test handling of WeChat API error response with errcode."""
        openid = 'test_openid'
        error_response = {'errcode': 40001, 'errmsg': 'invalid credential'}

        respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(200, json=error_response))

        # WeChat returns 200 with error in body, should still work as valid JSON
        result = await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN, openid=openid)
        assert result == error_response
        assert result['errcode'] == 40001

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_access_token_wechat_error_response(self, wechat_open_client):
        """Test handling of WeChat API error response when getting access token."""
        error_response = {'errcode': 40029, 'errmsg': 'invalid code'}

        respx.get('https://api.weixin.qq.com/sns/oauth2/access_token').mock(
            return_value=httpx.Response(200, json=error_response)
        )

        # WeChat returns 200 with error in body
        result = await wechat_open_client.get_access_token(code='invalid_code')
        assert result == error_response
        assert result['errcode'] == 40029

    @pytest.mark.asyncio
    async def test_get_authorization_url_with_lang_parameter(self, wechat_open_client):
        """Test that authorization URL contains lang parameter."""
        redirect_uri = 'https://example.com/callback'
        state = 'test_state'

        url = await wechat_open_client.get_authorization_url(redirect_uri=redirect_uri, state=state)

        # Verify lang parameter is present (WeChat Open includes lang=cn by default)
        assert 'lang=cn' in url

    @pytest.mark.asyncio
    async def test_get_authorization_url_query_parameters(self, wechat_open_client):
        """Test that authorization URL contains correct query parameters."""
        redirect_uri = 'https://example.com/callback'
        state = 'test_state'

        url = await wechat_open_client.get_authorization_url(redirect_uri=redirect_uri, state=state)

        # Verify all required parameters are present
        assert 'appid=' in url
        assert 'redirect_uri=' in url
        assert 'response_type=code' in url
        assert 'scope=' in url
        assert 'state=' in url
        assert 'lang=' in url

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_with_lang_parameter(self, wechat_open_client):
        """Test that get_userinfo sends lang parameter."""
        mock_user_data = create_mock_user_data('wechat_open')
        openid = 'test_openid'

        route = respx.get(WECHAT_OPEN_USER_INFO_URL).mock(return_value=httpx.Response(200, json=mock_user_data))

        await wechat_open_client.get_userinfo(TEST_ACCESS_TOKEN, openid=openid)

        # Verify the request was made with lang parameter
        assert route.called
        request = route.calls[0].request
        assert 'lang=zh_CN' in str(request.url)
