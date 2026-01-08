import httpx
import pytest
import respx

from fastapi_oauth20 import OSChinaOAuth20
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

OSCHINA_USER_INFO_URL = 'https://www.oschina.net/action/openapi/user'


@pytest.fixture
def oschina_client():
    """Create OSChina OAuth2 client instance for testing."""
    return OSChinaOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestOSChinaOAuth20:
    """Test OSChina OAuth2 client functionality."""

    def test_oschina_client_initialization(self, oschina_client):
        """Test OSChina client initialization with correct parameters."""
        assert oschina_client.client_id == TEST_CLIENT_ID
        assert oschina_client.client_secret == TEST_CLIENT_SECRET
        assert oschina_client.authorize_endpoint == 'https://www.oschina.net/action/oauth2/authorize'
        assert oschina_client.access_token_endpoint == 'https://www.oschina.net/action/openapi/token'
        assert oschina_client.refresh_token_endpoint == 'https://www.oschina.net/action/openapi/token'
        assert oschina_client.default_scopes is None

    def test_oschina_client_initialization_with_custom_credentials(self):
        """Test OSChina client initialization with custom credentials."""
        client = OSChinaOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        assert client.client_id == TEST_CLIENT_ID
        assert client.client_secret == TEST_CLIENT_SECRET

    def test_oschina_client_inheritance(self, oschina_client):
        """Test that OSChina client properly inherits from OAuth20Base."""
        assert isinstance(oschina_client, OAuth20Base)

    def test_oschina_client_no_default_scopes(self, oschina_client):
        """Test that OSChina client has no default scopes configured."""
        assert oschina_client.default_scopes is None

    def test_oschina_client_endpoint_urls(self):
        """Test that OSChina client uses correct endpoint URLs."""
        client = OSChinaOAuth20(TEST_CLIENT_ID, TEST_CLIENT_SECRET)

        # Test that endpoints are correctly set without hardcoding them in tests
        assert client.authorize_endpoint.endswith('/action/oauth2/authorize')
        assert client.access_token_endpoint.endswith('/action/openapi/token')
        assert client.refresh_token_endpoint.endswith('/action/openapi/token')

        # Test that all endpoints use the correct domain
        for endpoint in [client.authorize_endpoint, client.access_token_endpoint, client.refresh_token_endpoint]:
            assert 'oschina.net' in endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success(self, oschina_client):
        """Test successful user info retrieval from OSChina API."""
        mock_user_data = create_mock_user_data('oschina')
        mock_user_info_response(respx, OSCHINA_USER_INFO_URL, mock_user_data)

        result = await oschina_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, oschina_client):
        """Test that authorization header is correctly formatted."""
        mock_user_data = {'id': 'test_user'}
        route = mock_user_info_response(respx, OSCHINA_USER_INFO_URL, mock_user_data)

        await oschina_client.get_userinfo(TEST_ACCESS_TOKEN)

        # Verify the request was made with correct authorization header
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error(self, oschina_client):
        """Test handling of HTTP errors when getting user info."""
        respx.get(OSCHINA_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))

        with pytest.raises(HTTPXOAuth20Error):
            await oschina_client.get_userinfo(INVALID_TOKEN)
