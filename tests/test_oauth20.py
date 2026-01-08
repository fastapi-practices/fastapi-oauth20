import json

from unittest.mock import Mock

import httpx
import pytest
import respx

from fastapi_oauth20.errors import (
    AccessTokenError,
    HTTPXOAuth20Error,
    RefreshTokenError,
    RevokeTokenError,
)
from fastapi_oauth20.oauth20 import OAuth20Base


class MockOAuth20Client(OAuth20Base):
    """Test implementation of OAuth20Base for testing purposes."""

    async def get_userinfo(self, access_token: str) -> dict[str, any]:
        """Mock implementation for testing."""
        return {'user_id': 'test_user', 'access_token': access_token}


@pytest.fixture
def oauth_client():
    """Create OAuth20Base client instance for testing."""
    return MockOAuth20Client(
        client_id='test_client_id',
        client_secret='test_client_secret',
        authorize_endpoint='https://example.com/oauth/authorize',
        access_token_endpoint='https://example.com/oauth/token',
        userinfo_endpoint='https://example.com/oauth/userinfo',
        refresh_token_endpoint='https://example.com/oauth/refresh',
        revoke_token_endpoint='https://example.com/oauth/revoke',
        default_scopes=['read', 'write'],
    )


def test_oauth_base_initialization(oauth_client):
    """Test OAuth20Base initialization with all parameters."""
    assert oauth_client.client_id == 'test_client_id'
    assert oauth_client.client_secret == 'test_client_secret'
    assert oauth_client.authorize_endpoint == 'https://example.com/oauth/authorize'
    assert oauth_client.access_token_endpoint == 'https://example.com/oauth/token'
    assert oauth_client.refresh_token_endpoint == 'https://example.com/oauth/refresh'
    assert oauth_client.revoke_token_endpoint == 'https://example.com/oauth/revoke'
    assert oauth_client.default_scopes == ['read', 'write']
    assert oauth_client.token_endpoint_basic_auth is False
    assert oauth_client.revoke_token_endpoint_basic_auth is False
    assert oauth_client.request_headers == {'Accept': 'application/json'}


def test_oauth_base_initialization_minimal():
    """Test OAuth20Base initialization with minimal required parameters."""
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )

    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint == 'https://example.com/auth'
    assert client.access_token_endpoint == 'https://example.com/token'
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.default_scopes is None


def test_oauth_base_initialization_with_basic_auth():
    """Test OAuth20Base initialization with basic authentication enabled."""
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
        token_endpoint_basic_auth=True,
        revoke_token_endpoint_basic_auth=True,
    )

    assert client.token_endpoint_basic_auth is True
    assert client.revoke_token_endpoint_basic_auth is True


@pytest.mark.asyncio
async def test_get_authorization_url_basic(oauth_client):
    """Test basic authorization URL generation."""
    url = await oauth_client.get_authorization_url(redirect_uri='https://example.com/callback')

    assert 'https://example.com/oauth/authorize' in url
    assert 'client_id=test_client_id' in url
    assert 'redirect_uri=https%3A%2F%2Fexample.com%2Fcallback' in url
    assert 'response_type=code' in url
    assert 'scope=read+write' in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_state(oauth_client):
    """Test authorization URL generation with state parameter."""
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', state='random_state_123'
    )

    assert 'state=random_state_123' in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_custom_scope(oauth_client):
    """Test authorization URL generation with custom scope."""
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', scope=['read', 'delete']
    )

    assert 'scope=read+delete' in url
    assert 'write' not in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_pkce(oauth_client):
    """Test authorization URL generation with PKCE parameters."""
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', code_challenge='challenge_123', code_challenge_method='S256'
    )

    assert 'code_challenge=challenge_123' in url
    assert 'code_challenge_method=S256' in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_extra_params(oauth_client):
    """Test authorization URL generation with additional parameters."""
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', access_type='offline', prompt='consent'
    )

    assert 'access_type=offline' in url
    assert 'prompt=consent' in url


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_success(oauth_client):
    """Test successful access token exchange."""
    mock_token_data = {
        'access_token': 'new_access_token',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'refresh_token': 'refresh_token_123',
    }

    # Mock the token endpoint
    respx.post('https://example.com/oauth/token').mock(return_value=httpx.Response(200, json=mock_token_data))

    result = await oauth_client.get_access_token(code='auth_code_123', redirect_uri='https://example.com/callback')
    assert result == mock_token_data


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_with_code_verifier(oauth_client):
    """Test access token exchange with PKCE code verifier."""
    mock_token_data = {'access_token': 'new_access_token'}

    # Mock the token endpoint and capture the request
    route = respx.post('https://example.com/oauth/token').mock(return_value=httpx.Response(200, json=mock_token_data))

    await oauth_client.get_access_token(
        code='auth_code_123', redirect_uri='https://example.com/callback', code_verifier='verifier_123'
    )

    # Verify the request was made with code_verifier
    assert route.called
    request_data = route.calls[0].request.content.decode()
    assert 'code_verifier=verifier_123' in request_data


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_with_basic_auth():
    """Test access token exchange with HTTP Basic Authentication."""
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
        token_endpoint_basic_auth=True,
    )

    mock_token_data = {'access_token': 'new_access_token'}

    # Mock the token endpoint
    route = respx.post('https://example.com/token').mock(return_value=httpx.Response(200, json=mock_token_data))

    await client.get_access_token(code='auth_code_123', redirect_uri='https://example.com/callback')

    # Verify BasicAuth was used
    assert route.called
    request = route.calls[0].request
    assert 'authorization' in request.headers
    # Basic auth should be present
    assert request.headers['authorization'].startswith('Basic ')


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_http_error(oauth_client):
    """Test handling of HTTP errors during access token exchange."""
    # Mock HTTP error response
    respx.post('https://example.com/oauth/token').mock(return_value=httpx.Response(400, text='Bad Request'))

    with pytest.raises(HTTPXOAuth20Error):
        await oauth_client.get_access_token(code='invalid_code', redirect_uri='https://example.com/callback')


@pytest.mark.asyncio
@respx.mock
async def test_refresh_token_success(oauth_client):
    """Test successful token refresh."""
    mock_token_data = {'access_token': 'refreshed_access_token', 'token_type': 'Bearer', 'expires_in': 3600}

    # Mock the refresh endpoint
    respx.post('https://example.com/oauth/refresh').mock(return_value=httpx.Response(200, json=mock_token_data))

    result = await oauth_client.refresh_token('refresh_token_123')
    assert result == mock_token_data


@pytest.mark.asyncio
async def test_refresh_token_missing_endpoint():
    """Test refresh token when refresh endpoint is not configured."""
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )

    with pytest.raises(RefreshTokenError, match='refresh token address is missing'):
        await client.refresh_token('refresh_token_123')


@pytest.mark.asyncio
@respx.mock
async def test_refresh_token_http_error(oauth_client):
    """Test handling of HTTP errors during token refresh."""
    # Mock HTTP error response
    respx.post('https://example.com/oauth/refresh').mock(return_value=httpx.Response(401, text='Unauthorized'))

    with pytest.raises(HTTPXOAuth20Error):
        await oauth_client.refresh_token('invalid_refresh_token')


@pytest.mark.asyncio
@respx.mock
async def test_revoke_token_success(oauth_client):
    """Test successful token revocation."""
    # Mock successful revocation response
    respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(200, text='OK'))

    # Should not raise any exception for successful revocation
    await oauth_client.revoke_token('access_token_123')


@pytest.mark.asyncio
@respx.mock
async def test_revoke_token_with_type_hint(oauth_client):
    """Test token revocation with token type hint."""
    # Mock the revoke endpoint and capture the request
    route = respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(200, text='OK'))

    await oauth_client.revoke_token(token='refresh_token_123', token_type_hint='refresh_token')

    # Verify token_type_hint was included in the request
    assert route.called
    request_data = route.calls[0].request.content.decode()
    assert 'token_type_hint=refresh_token' in request_data


@pytest.mark.asyncio
async def test_revoke_token_missing_endpoint():
    """Test token revocation when revoke endpoint is not configured."""
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )

    with pytest.raises(RevokeTokenError, match='revoke token address is missing'):
        await client.revoke_token('access_token_123')


@pytest.mark.asyncio
@respx.mock
async def test_revoke_token_http_error(oauth_client):
    """Test handling of HTTP errors during token revocation."""
    # Mock HTTP error response
    respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(400, text='Bad Request'))

    with pytest.raises(HTTPXOAuth20Error):
        await oauth_client.revoke_token('invalid_token')


def test_raise_httpx_oauth20_errors_success():
    """Test successful HTTP response validation."""
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None

    # Should not raise any exception
    OAuth20Base.raise_httpx_oauth20_errors(mock_response)


def test_raise_httpx_oauth20_errors_http_status_error():
    """Test handling of HTTP status errors."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        'Not Found', request=None, response=mock_response
    )

    with pytest.raises(HTTPXOAuth20Error):
        OAuth20Base.raise_httpx_oauth20_errors(mock_response)


def test_raise_httpx_oauth20_errors_network_error():
    """Test handling of network errors."""
    # Test with a mock response that will raise RequestError when raise_for_status is called
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.RequestError('Network error')

    with pytest.raises(HTTPXOAuth20Error):
        OAuth20Base.raise_httpx_oauth20_errors(mock_response)


def test_get_json_result_success():
    """Test successful JSON result parsing."""
    mock_response = Mock()
    mock_response.json.return_value = {'key': 'value'}

    result = OAuth20Base.get_json_result(mock_response, err_class=AccessTokenError)
    assert result == {'key': 'value'}


def test_get_json_result_invalid_json():
    """Test handling of invalid JSON response."""
    mock_response = Mock()
    mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)

    with pytest.raises(AccessTokenError, match='Result serialization failed'):
        OAuth20Base.get_json_result(mock_response, err_class=AccessTokenError)


def test_concrete_implementation():
    """Test that OAuth20Base can be instantiated directly."""
    client = OAuth20Base(
        client_id='test',
        client_secret='test',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )

    assert client.client_id == 'test'
    assert client.client_secret == 'test'
    assert client.userinfo_endpoint == 'https://example.com/userinfo'


@pytest.mark.asyncio
async def test_get_userinfo_implementation():
    """Test that concrete implementation of get_userinfo works."""
    client = MockOAuth20Client(
        client_id='test',
        client_secret='test',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )

    result = await client.get_userinfo('test_token')
    assert result == {'user_id': 'test_user', 'access_token': 'test_token'}
