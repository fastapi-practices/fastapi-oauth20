from typing import Annotated

import httpx
import pytest
import respx

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from fastapi_oauth20 import (
    FastAPIOAuth20,
    FeiShuOAuth20,
    GiteeOAuth20,
    GitHubOAuth20,
    GoogleOAuth20,
    LinuxDoOAuth20,
    OAuth20AuthorizeCallbackError,
    OSChinaOAuth20,
)
from tests.conftest import (
    TEST_ACCESS_TOKEN,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_STATE,
)

OAUTH_PROVIDERS = [
    {
        'name': 'github',
        'client_class': GitHubOAuth20,
        'token_url': 'https://github.com/login/oauth/access_token',
        'user_info_url': 'https://api.github.com/user',
        'token_response': {'access_token': TEST_ACCESS_TOKEN, 'token_type': 'bearer', 'scope': 'user'},
        'redirect_uri': 'http://localhost:8000/auth/github/callback',
    },
    {
        'name': 'google',
        'client_class': GoogleOAuth20,
        'token_url': 'https://oauth2.googleapis.com/token',
        'user_info_url': 'https://www.googleapis.com/oauth2/v1/userinfo',
        'token_response': {'access_token': TEST_ACCESS_TOKEN, 'token_type': 'Bearer', 'expires_in': 3600},
        'redirect_uri': 'http://localhost:8000/auth/google/callback',
    },
    {
        'name': 'gitee',
        'client_class': GiteeOAuth20,
        'token_url': 'https://gitee.com/oauth/token',
        'user_info_url': 'https://gitee.com/api/v5/user',
        'token_response': {'access_token': TEST_ACCESS_TOKEN, 'token_type': 'bearer', 'scope': 'user_info'},
        'redirect_uri': 'http://localhost:8000/auth/gitee/callback',
    },
    {
        'name': 'feishu',
        'client_class': FeiShuOAuth20,
        'token_url': 'https://passport.feishu.cn/suite/passport/oauth/token',
        'user_info_url': 'https://passport.feishu.cn/suite/passport/oauth/userinfo',
        'token_response': {'access_token': TEST_ACCESS_TOKEN, 'token_type': 'bearer', 'expires_in': 3600},
        'redirect_uri': 'http://localhost:8000/auth/feishu/callback',
    },
    {
        'name': 'linuxdo',
        'client_class': LinuxDoOAuth20,
        'token_url': 'https://connect.linux.do/oauth2/token',
        'user_info_url': 'https://connect.linux.do/api/user',
        'token_response': {'access_token': TEST_ACCESS_TOKEN, 'token_type': 'bearer', 'expires_in': 3600},
        'redirect_uri': 'http://localhost:8000/auth/linuxdo/callback',
    },
    {
        'name': 'oschina',
        'client_class': OSChinaOAuth20,
        'token_url': 'https://www.oschina.net/action/openapi/token',
        'user_info_url': 'https://www.oschina.net/action/openapi/user',
        'token_response': {'access_token': TEST_ACCESS_TOKEN, 'token_type': 'bearer', 'expires_in': 3600},
        'redirect_uri': 'http://localhost:8000/auth/oschina/callback',
    },
]

LOCALHOST_URL = 'http://localhost:8000'
DEV_URL = 'http://dev.example.com'
APP_URL = 'http://app.example.org'
IP_URL = 'http://192.168.1.100:8080'
SECURE_LOCALHOST_URL = 'https://localhost:8000'
SECURE_DEV_URL = 'https://secure.example.com'
SECURE_APP_URL = 'https://app.example.org'
SECURE_IP_URL = 'https://192.168.1.100:8443'

AUTH_PATH = '/auth'
CALLBACK_PATH = '/callback'
OAUTH_CALLBACK_PATH = '/oauth2/callback'

HTTP_URIS = [
    f'{LOCALHOST_URL}{CALLBACK_PATH}',
    f'{DEV_URL}{AUTH_PATH}/callback',
    f'{APP_URL}{OAUTH_CALLBACK_PATH}',
    f'{IP_URL}{AUTH_PATH}',
]

HTTPS_URIS = [
    f'{SECURE_LOCALHOST_URL}{CALLBACK_PATH}',
    f'{SECURE_DEV_URL}{AUTH_PATH}/callback',
    f'{SECURE_APP_URL}{OAUTH_CALLBACK_PATH}',
    f'{SECURE_IP_URL}{AUTH_PATH}',
]


@pytest.fixture
def fastapi_app():
    """Create FastAPI app for testing."""
    app = FastAPI()

    @app.get('/')
    async def root():
        return {'message': 'OAuth2 Test App'}

    return app


def mock_oauth_token_response(respx_mock, provider_config: dict, status_code: int = 200):
    """Mock OAuth token endpoint response for a provider."""
    return respx_mock.post(provider_config['token_url']).mock(
        return_value=httpx.Response(status_code, json=provider_config['token_response'])
    )


def setup_oauth_callback_route(app: FastAPI, provider_config: dict, oauth_dependency):
    """Setup OAuth callback route for testing."""
    callback_path = f'/auth/{provider_config["name"]}/callback'

    @app.get(callback_path)
    async def oauth_callback_handler(
        access_token_state: Annotated[
            FastAPIOAuth20,
            Depends(oauth_dependency),
        ],
    ):
        token, state = access_token_state
        return {'provider': provider_config['name'], 'access_token': token, 'state': state}

    return callback_path


def assert_oauth_error_response(response, expected_error: str, expected_status: int = 400):
    """Assert OAuth error response has correct format."""
    assert response.status_code == expected_status
    data = response.json()
    if 'detail' in data:
        assert data['detail'] == expected_error
    else:
        assert data.get('error') == expected_error


class TestFastAPIOAuth20Basic:
    """Basic tests for FastAPI OAuth2 integration using parametrized providers."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_successful_callback_parametrized(self, provider_config, fastapi_app):
        """Test successful OAuth2 callback with multiple providers."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        # Create OAuth client and dependency
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])

        # Setup callback route
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        # Test successful callback
        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}')

        assert response.status_code == 200
        data = response.json()
        assert data['provider'] == provider_config['name']
        assert data['access_token']['access_token'] == TEST_ACCESS_TOKEN

    @pytest.mark.asyncio
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_callback_missing_code_parametrized(self, provider_config, fastapi_app):
        """Test OAuth2 callback with missing authorization code."""
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?state={TEST_STATE}')

        assert_oauth_error_response(response, 'Bad Request')

    @pytest.mark.asyncio
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_callback_with_error_parametrized(self, provider_config, fastapi_app):
        """Test OAuth2 callback with error parameter."""
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?error=access_denied&state={TEST_STATE}')

        assert_oauth_error_response(response, 'access_denied')

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_callback_token_exchange_error_parametrized(self, provider_config, fastapi_app):
        """Test OAuth2 callback with token exchange error."""
        # Mock token exchange error
        respx.post(provider_config['token_url']).mock(return_value=httpx.Response(400, text='Bad Request'))

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=invalid_code&state={TEST_STATE}')

        assert response.status_code == 500
        assert 'detail' in response.json()

    def test_custom_exception_handler(self, fastapi_app):
        """Test custom exception handler for OAuth2 errors."""
        github_client = GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)

        @fastapi_app.get('/auth/github/callback')
        async def github_callback(
            access_token_state: Annotated[
                FastAPIOAuth20,
                Depends(FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/auth/github/callback')),
            ],
        ):
            token, state = access_token_state
            return {'access_token': token, 'state': state}

        @fastapi_app.exception_handler(OAuth20AuthorizeCallbackError)
        async def oauth2_error_handler(request: Request, exc: OAuth20AuthorizeCallbackError):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    'message': 'OAuth2 authentication failed',
                    'error': exc.detail,
                    'status_code': exc.status_code,
                },
            )

        client = TestClient(fastapi_app)
        response = client.get('/auth/github/callback?error=access_denied')

        assert response.status_code == 400
        data = response.json()
        assert data['message'] == 'OAuth2 authentication failed'
        assert data['error'] == 'access_denied'
        assert data['status_code'] == 400

    def test_multiple_oauth_providers(self, fastapi_app):
        """Test multiple OAuth providers in the same app."""
        # Setup GitHub OAuth
        github_client = GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)

        @fastapi_app.get('/auth/github/callback')
        async def github_callback(
            access_token_state: Annotated[
                FastAPIOAuth20,
                Depends(FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/auth/github/callback')),
            ],
        ):
            token, state = access_token_state
            return {'provider': 'github', 'access_token': token, 'state': state}

        # Setup Google OAuth
        google_client = GoogleOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)

        @fastapi_app.get('/auth/google/callback')
        async def google_callback(
            access_token_state: Annotated[
                FastAPIOAuth20,
                Depends(FastAPIOAuth20(google_client, redirect_uri=f'{LOCALHOST_URL}/auth/google/callback')),
            ],
        ):
            token, state = access_token_state
            return {'provider': 'google', 'access_token': token, 'state': state}

        client = TestClient(fastapi_app)

        # Test GitHub route
        response = client.get('/auth/github/callback?error=access_denied')
        assert response.status_code == 400

        # Test Google route
        response = client.get('/auth/google/callback?error=access_denied')
        assert response.status_code == 400


class TestFastAPIOAuth20PKCE:
    """Test PKCE functionality across providers."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    async def test_pkce_flow(self, provider_config, fastapi_app):
        """Test PKCE flow with code verifier and challenge."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}&code_verifier=test_verifier')

        assert response.status_code == 200
        data = response.json()
        assert data['provider'] == provider_config['name']


class TestFastAPIOAuth20URIs:
    """Test URI validation and functionality."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('redirect_uri', HTTP_URIS)
    async def test_http_redirect_uris(self, provider_config, redirect_uri, fastapi_app):
        """Test OAuth2 with HTTP redirect URIs."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=redirect_uri)
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}')

        assert response.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('redirect_uri', HTTPS_URIS)
    async def test_https_redirect_uris(self, provider_config, redirect_uri, fastapi_app):
        """Test OAuth2 with HTTPS redirect URIs."""
        # Mock token exchange
        mock_oauth_token_response(respx, provider_config)

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=redirect_uri)
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=test_code&state={TEST_STATE}')

        assert response.status_code == 200


class TestFastAPIOAuth20ErrorScenarios:
    """Test various error scenarios across providers."""

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('error_code', ['access_denied', 'temporarily_unavailable', 'invalid_request'])
    async def test_oauth_errors(self, provider_config, error_code, fastapi_app):
        """Test various OAuth error codes."""
        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?error={error_code}&state={TEST_STATE}')

        assert_oauth_error_response(response, error_code)

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize('provider_config', OAUTH_PROVIDERS)
    @pytest.mark.parametrize('http_status', [400, 401, 500, 502])
    async def test_token_exchange_errors(self, provider_config, http_status, fastapi_app):
        """Test token exchange with various HTTP error codes."""
        # Mock token exchange error
        respx.post(provider_config['token_url']).mock(
            return_value=httpx.Response(http_status, text=f'Error {http_status}')
        )

        client_class = provider_config['client_class']
        oauth_client = client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        oauth_callback = FastAPIOAuth20(oauth_client, redirect_uri=provider_config['redirect_uri'])
        callback_path = setup_oauth_callback_route(fastapi_app, provider_config, oauth_callback)

        client = TestClient(fastapi_app)
        response = client.get(f'{callback_path}?code=invalid_code&state={TEST_STATE}')

        # Should return server error for token exchange failures
        assert response.status_code >= 400
        assert 'detail' in response.json()


# Additional test classes for different scenarios
class TestFastAPIOAuth20Integration:
    """Integration tests for FastAPI OAuth2."""

    def test_oauth_dependency_creation(self):
        """Test OAuth dependency creation with different parameters."""
        github_client = GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        # Basic OAuth dependency
        oauth_dep = FastAPIOAuth20(github_client)
        assert oauth_dep.client == github_client

        # OAuth dependency with custom redirect URI
        custom_redirect = f'{LOCALHOST_URL}/custom/callback'
        oauth_dep_custom = FastAPIOAuth20(github_client, redirect_uri=custom_redirect)
        assert oauth_dep_custom.client == github_client

    def test_multiple_apps_same_provider(self):
        """Test the same OAuth provider in multiple FastAPI apps."""
        github_client = GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)
        app1 = FastAPI()
        app2 = FastAPI()

        # Setup first app
        @app1.get('/auth/github/callback')
        async def github_callback1(
            access_token_state: Annotated[
                FastAPIOAuth20,
                Depends(FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/app1/callback')),
            ],
        ):
            return {'app': 'app1', 'access_token': access_token_state}

        # Setup second app
        @app2.get('/auth/github/callback')
        async def github_callback2(
            access_token_state: Annotated[
                FastAPIOAuth20,
                Depends(FastAPIOAuth20(github_client, redirect_uri=f'{LOCALHOST_URL}/app2/callback')),
            ],
        ):
            return {'app': 'app2', 'access_token': access_token_state}

        client1 = TestClient(app1)
        client2 = TestClient(app2)

        # Both apps should work independently
        response1 = client1.get('/auth/github/callback?error=access_denied')
        response2 = client2.get('/auth/github/callback?error=access_denied')

        assert response1.status_code == 400
        assert response2.status_code == 400
