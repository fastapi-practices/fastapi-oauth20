#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Global constants and shared fixtures for fastapi-oauth20 tests.
"""

import httpx
import pytest

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastapi_oauth20.clients.feishu import FeiShuOAuth20
from fastapi_oauth20.clients.gitee import GiteeOAuth20
from fastapi_oauth20.clients.github import GitHubOAuth20
from fastapi_oauth20.clients.google import GoogleOAuth20
from fastapi_oauth20.clients.linuxdo import LinuxDoOAuth20
from fastapi_oauth20.clients.oschina import OSChinaOAuth20

TEST_CLIENT_ID = 'test_client_id'
TEST_CLIENT_SECRET = 'test_client_secret'
TEST_ACCESS_TOKEN = 'test_access_token'
INVALID_TOKEN = 'invalid_token'
TEST_STATE = 'test_state'
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


@pytest.fixture(params=OAUTH_PROVIDERS)
def oauth_provider_config(request):
    """Get OAuth provider configuration."""
    return request.param


@pytest.fixture
def oauth_client(oauth_provider_config):
    """Create OAuth2 client for testing based on provider config."""
    provider_config = oauth_provider_config
    client_class = provider_config['client_class']
    return client_class(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


@pytest.fixture
def fastapi_app():
    """Create FastAPI app for testing."""
    app = FastAPI()

    @app.get('/')
    async def root():
        return {'message': 'OAuth2 Test App'}

    return app


@pytest.fixture
def test_client(fastapi_app):
    """Create TestClient for FastAPI app."""
    return TestClient(fastapi_app)


# Individual OAuth client fixtures for non-parametrized tests
@pytest.fixture
def github_client():
    """Create GitHub OAuth2 client instance for testing."""
    return GitHubOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


@pytest.fixture
def google_client():
    """Create Google OAuth2 client instance for testing."""
    return GoogleOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


@pytest.fixture
def gitee_client():
    """Create Gitee OAuth2 client instance for testing."""
    return GiteeOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


@pytest.fixture
def feishu_client():
    """Create FeiShu OAuth2 client instance for testing."""
    return FeiShuOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


@pytest.fixture
def linuxdo_client():
    """Create LinuxDo OAuth2 client instance for testing."""
    return LinuxDoOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


@pytest.fixture
def oschina_client():
    """Create OSChina OAuth2 client instance for testing."""
    return OSChinaOAuth20(client_id=TEST_CLIENT_ID, client_secret=TEST_CLIENT_SECRET)


def create_mock_user_data(provider_name: str, **overrides):
    """Create mock user data for a specific provider with optional overrides."""
    MOCK_USER_DATA = {
        'github': {
            'id': 123456,
            'login': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'bio': 'Test bio',
            'location': 'Test Location',
        },
        'google': {
            'id': '123456789',
            'email': 'test@gmail.com',
            'name': 'Test User',
            'picture': 'https://lh3.googleusercontent.com/test.jpg',
        },
        'gitee': {
            'id': 123456,
            'login': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'avatar_url': 'https://avatar.example.com/testuser.png',
        },
        'feishu': {
            'user_id': 'test_user_123',
            'employee_id': 'emp_456',
            'name': 'Test User',
            'email': 'test@example.com',
            'mobile': '13800000000',
        },
        'linuxdo': {
            'id': 123456,
            'username': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'avatar_url': 'https://linux.do/avatar/testuser.png',
        },
        'oschina': {
            'id': 123456,
            'name': 'Test User',
            'email': 'test@example.com',
            'avatar': 'https://oschina.net/img/test.jpg',
        },
    }

    base_data = MOCK_USER_DATA.get(provider_name, {}).copy()
    base_data.update(overrides)
    return base_data


def mock_oauth_token_response(respx_mock, provider_config: dict, status_code: int = 200):
    """Mock OAuth token endpoint response for a provider."""
    return respx_mock.post(provider_config['token_url']).mock(
        return_value=httpx.Response(status_code, json=provider_config['token_response'])
    )


def mock_user_info_response(respx_mock, provider_config: dict, user_data: dict = None, status_code: int = 200):
    """Mock user info endpoint response for a provider."""
    if user_data is None:
        user_data = create_mock_user_data(provider_config['name'])
    return respx_mock.get(provider_config['user_info_url']).mock(
        return_value=httpx.Response(status_code, json=user_data)
    )


def setup_oauth_callback_route(app: FastAPI, provider_config: dict, oauth_dependency):
    """Setup OAuth callback route for testing."""
    callback_path = f'/auth/{provider_config["name"]}/callback'

    @app.get(callback_path)
    async def oauth_callback_handler(access_token_state=Depends(oauth_dependency)):
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
