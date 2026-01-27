import json

from typing import Any
from unittest.mock import Mock

import httpx
import pytest
import respx

from fastapi_oauth20.errors import AccessTokenError, HTTPXOAuth20Error, RefreshTokenError, RevokeTokenError
from fastapi_oauth20.oauth20 import OAuth20Base


class MockOAuth20Client(OAuth20Base):
    async def get_userinfo(self, access_token: str) -> dict[str, Any]:
        return {'user_id': 'test_user', 'access_token': access_token}


@pytest.fixture
def oauth_client():
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
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.refresh_token_endpoint is None
    assert client.revoke_token_endpoint is None
    assert client.default_scopes is None


def test_oauth_base_initialization_with_basic_auth():
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


def test_concrete_implementation():
    client = OAuth20Base(
        client_id='test',
        client_secret='test',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )
    assert client.client_id == 'test'
    assert client.userinfo_endpoint == 'https://example.com/userinfo'


@pytest.mark.asyncio
async def test_get_userinfo_implementation():
    client = MockOAuth20Client(
        client_id='test',
        client_secret='test',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
    )
    result = await client.get_userinfo('test_token')
    assert result == {'user_id': 'test_user', 'access_token': 'test_token'}


@pytest.mark.asyncio
async def test_get_authorization_url_basic(oauth_client):
    url = await oauth_client.get_authorization_url(redirect_uri='https://example.com/callback')
    assert 'https://example.com/oauth/authorize' in url
    assert 'client_id=test_client_id' in url
    assert 'redirect_uri=https%3A%2F%2Fexample.com%2Fcallback' in url
    assert 'response_type=code' in url
    assert 'scope=read+write' in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_state(oauth_client):
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', state='random_state_123'
    )
    assert 'state=random_state_123' in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_custom_scope(oauth_client):
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', scope=['read', 'delete']
    )
    assert 'scope=read+delete' in url
    assert 'write' not in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_pkce(oauth_client):
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', code_challenge='challenge_123', code_challenge_method='S256'
    )
    assert 'code_challenge=challenge_123' in url
    assert 'code_challenge_method=S256' in url


@pytest.mark.asyncio
async def test_get_authorization_url_with_extra_params(oauth_client):
    url = await oauth_client.get_authorization_url(
        redirect_uri='https://example.com/callback', access_type='offline', prompt='consent'
    )
    assert 'access_type=offline' in url
    assert 'prompt=consent' in url


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_success(oauth_client):
    mock_token_data = {
        'access_token': 'new_access_token',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'refresh_token': 'refresh_token_123',
    }
    respx.post('https://example.com/oauth/token').mock(return_value=httpx.Response(200, json=mock_token_data))
    result = await oauth_client.get_access_token(code='auth_code_123', redirect_uri='https://example.com/callback')
    assert result == mock_token_data


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_with_code_verifier(oauth_client):
    mock_token_data = {'access_token': 'new_access_token'}
    route = respx.post('https://example.com/oauth/token').mock(return_value=httpx.Response(200, json=mock_token_data))
    await oauth_client.get_access_token(
        code='auth_code_123', redirect_uri='https://example.com/callback', code_verifier='verifier_123'
    )
    assert route.called
    request_data = route.calls[0].request.content.decode()
    assert 'code_verifier=verifier_123' in request_data


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_with_basic_auth():
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
        token_endpoint_basic_auth=True,
    )
    mock_token_data = {'access_token': 'new_access_token'}
    route = respx.post('https://example.com/token').mock(return_value=httpx.Response(200, json=mock_token_data))
    await client.get_access_token(code='auth_code_123', redirect_uri='https://example.com/callback')
    assert route.called
    request = route.calls[0].request
    assert 'authorization' in request.headers
    assert request.headers['authorization'].startswith('Basic ')


@pytest.mark.asyncio
@respx.mock
async def test_get_access_token_http_error(oauth_client):
    respx.post('https://example.com/oauth/token').mock(return_value=httpx.Response(400, text='Bad Request'))
    with pytest.raises(HTTPXOAuth20Error):
        await oauth_client.get_access_token(code='invalid_code', redirect_uri='https://example.com/callback')


@pytest.mark.asyncio
@respx.mock
async def test_refresh_token_success(oauth_client):
    mock_token_data = {'access_token': 'refreshed_access_token', 'token_type': 'Bearer', 'expires_in': 3600}
    respx.post('https://example.com/oauth/refresh').mock(return_value=httpx.Response(200, json=mock_token_data))
    result = await oauth_client.refresh_token('refresh_token_123')
    assert result == mock_token_data


@pytest.mark.asyncio
@respx.mock
async def test_refresh_token_with_basic_auth():
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
        refresh_token_endpoint='https://example.com/oauth/refresh',
        token_endpoint_basic_auth=True,
    )
    mock_token_data = {'access_token': 'refreshed_access_token', 'token_type': 'Bearer', 'expires_in': 3600}
    route = respx.post('https://example.com/oauth/refresh').mock(return_value=httpx.Response(200, json=mock_token_data))
    await client.refresh_token('refresh_token_123')
    assert route.called
    request = route.calls[0].request
    assert 'authorization' in request.headers
    assert request.headers['authorization'].startswith('Basic ')


@pytest.mark.asyncio
async def test_refresh_token_missing_endpoint():
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
    respx.post('https://example.com/oauth/refresh').mock(return_value=httpx.Response(401, text='Unauthorized'))
    with pytest.raises(HTTPXOAuth20Error):
        await oauth_client.refresh_token('invalid_refresh_token')


@pytest.mark.asyncio
@respx.mock
async def test_revoke_token_success(oauth_client):
    respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(200, text='OK'))
    await oauth_client.revoke_token('access_token_123')


@pytest.mark.asyncio
@respx.mock
async def test_revoke_token_with_type_hint(oauth_client):
    route = respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(200, text='OK'))
    await oauth_client.revoke_token(token='refresh_token_123', token_type_hint='refresh_token')
    assert route.called
    request_data = route.calls[0].request.content.decode()
    assert 'token_type_hint=refresh_token' in request_data


@pytest.mark.asyncio
@respx.mock
async def test_revoke_token_with_basic_auth():
    client = MockOAuth20Client(
        client_id='test_id',
        client_secret='test_secret',
        authorize_endpoint='https://example.com/auth',
        access_token_endpoint='https://example.com/token',
        userinfo_endpoint='https://example.com/userinfo',
        revoke_token_endpoint='https://example.com/oauth/revoke',
        revoke_token_endpoint_basic_auth=True,
    )
    route = respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(200, text='OK'))
    await client.revoke_token('access_token_123')
    assert route.called
    request = route.calls[0].request
    assert 'authorization' in request.headers
    assert request.headers['authorization'].startswith('Basic ')


@pytest.mark.asyncio
async def test_revoke_token_missing_endpoint():
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
    respx.post('https://example.com/oauth/revoke').mock(return_value=httpx.Response(400, text='Bad Request'))
    with pytest.raises(HTTPXOAuth20Error):
        await oauth_client.revoke_token('invalid_token')


def test_raise_httpx_oauth20_errors_success():
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    OAuth20Base.raise_httpx_oauth20_errors(mock_response)


def test_raise_httpx_oauth20_errors_http_status_error():
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        'Not Found', request=None, response=mock_response
    )
    with pytest.raises(HTTPXOAuth20Error):
        OAuth20Base.raise_httpx_oauth20_errors(mock_response)


def test_raise_httpx_oauth20_errors_network_error():
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.RequestError('Network error')
    with pytest.raises(HTTPXOAuth20Error):
        OAuth20Base.raise_httpx_oauth20_errors(mock_response)


def test_get_json_result_success():
    mock_response = Mock()
    mock_response.json.return_value = {'key': 'value'}
    result = OAuth20Base.get_json_result(mock_response, err_class=AccessTokenError)
    assert result == {'key': 'value'}


def test_get_json_result_invalid_json():
    mock_response = Mock()
    mock_response.json.side_effect = json.JSONDecodeError('Invalid JSON', '', 0)
    with pytest.raises(AccessTokenError, match='Result serialization failed'):
        OAuth20Base.get_json_result(mock_response, err_class=AccessTokenError)
