import httpx
import pytest
import respx

from fastapi_oauth20 import GitHubOAuth20
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

GITHUB_USER_INFO_URL = 'https://api.github.com/user'
GITHUB_EMAILS_URL = 'https://api.github.com/user/emails'


@pytest.fixture
def github_client():
    return GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


class TestGitHubOAuth20:
    def test_client_initialization(self, github_client):
        assert github_client.client_id == TEST_CLIENT_ID
        assert github_client.client_secret == TEST_CLIENT_SECRET
        assert github_client.authorize_endpoint == 'https://github.com/login/oauth/authorize'
        assert github_client.access_token_endpoint == 'https://github.com/login/oauth/access_token'
        assert github_client.default_scopes == ['user', 'user:email']

    def test_client_inheritance(self, github_client):
        assert isinstance(github_client, OAuth20Base)

    def test_client_scopes_are_lists(self, github_client):
        assert isinstance(github_client.default_scopes, list)
        assert len(github_client.default_scopes) == 2
        assert all(isinstance(scope, str) for scope in github_client.default_scopes)

    def test_client_endpoint_urls(self, github_client):
        assert github_client.authorize_endpoint.endswith('/login/oauth/authorize')
        assert github_client.access_token_endpoint.endswith('/login/oauth/access_token')
        for endpoint in [github_client.authorize_endpoint, github_client.access_token_endpoint]:
            assert 'github.com' in endpoint

    def test_client_multiple_instances(self):
        client1 = GitHubOAuth20('client1', 'secret1')
        client2 = GitHubOAuth20('client2', 'secret2')
        assert client1.client_id != client2.client_id
        assert client1.client_secret != client2.client_secret
        assert client1.authorize_endpoint == client2.authorize_endpoint

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success_with_email(self, github_client):
        mock_user_data = create_mock_user_data('github')
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)
        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_success_without_email(self, github_client):
        mock_user_data = create_mock_user_data('github', email=None)
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)
        emails_data = [{'email': 'test@example.com', 'primary': True}]
        respx.get(GITHUB_EMAILS_URL).mock(return_value=httpx.Response(200, json=emails_data))
        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result['login'] == mock_user_data['login']
        assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_with_different_access_token(self, github_client):
        mock_user_data = create_mock_user_data('github', id=789, login='different_user')
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)
        result = await github_client.get_userinfo('different_token')
        assert result == mock_user_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_authorization_header(self, github_client):
        mock_user_data = {'id': 'test_user', 'email': 'test@example.com'}
        route = mock_user_info_response(respx, GITHUB_USER_INFO_URL, mock_user_data)
        await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert route.called
        request = route.calls[0].request
        assert request.headers['authorization'] == f'Bearer {TEST_ACCESS_TOKEN}'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_empty_response(self, github_client):
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, {})
        emails_data = [{'email': 'test@example.com', 'primary': True}]
        respx.get(GITHUB_EMAILS_URL).mock(return_value=httpx.Response(200, json=emails_data))
        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result['email'] == 'test@example.com'

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_partial_data(self, github_client):
        partial_data = {'id': 123456, 'login': 'testuser', 'email': 'test@example.com'}
        mock_user_info_response(respx, GITHUB_USER_INFO_URL, partial_data)
        result = await github_client.get_userinfo(TEST_ACCESS_TOKEN)
        assert result == partial_data

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_401(self, github_client):
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(401, text='Unauthorized'))
        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(INVALID_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_403(self, github_client):
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(403, text='Forbidden'))
        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_http_error_500(self, github_client):
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(500, text='Internal Server Error'))
        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_invalid_json(self, github_client):
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(200, text='invalid json'))
        with pytest.raises(GetUserInfoError):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_userinfo_rate_limit(self, github_client):
        rate_limit_response = {
            'message': 'API rate limit exceeded for xxx.xxx.xxx.xxx.',
            'documentation_url': 'https://docs.github.com/rest/overview/rate-limits-for-the-rest-api',
        }
        respx.get(GITHUB_USER_INFO_URL).mock(return_value=httpx.Response(403, json=rate_limit_response))
        with pytest.raises(HTTPXOAuth20Error):
            await github_client.get_userinfo(TEST_ACCESS_TOKEN)
