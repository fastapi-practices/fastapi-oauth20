import httpx

from fastapi_oauth20.errors import (
    AccessTokenError,
    GetUserInfoError,
    HTTPXOAuth20Error,
    OAuth20RequestError,
    RefreshTokenError,
    RevokeTokenError,
)


def test_oauth20_request_error_basic():
    error = OAuth20RequestError('Test error')
    assert str(error) == 'Test error'
    assert error.msg == 'Test error'


def test_oauth20_request_error_with_response():
    mock_response = httpx.Response(400)
    error = OAuth20RequestError('Bad request', mock_response)
    assert str(error) == 'Bad request'
    assert error.msg == 'Bad request'
    assert error.response is mock_response


def test_httpx_oauth20_error_basic():
    error = HTTPXOAuth20Error('HTTP error')
    assert str(error) == 'HTTP error'
    assert error.msg == 'HTTP error'


def test_httpx_oauth20_error_with_response():
    mock_response = httpx.Response(404)
    error = HTTPXOAuth20Error('Not found', mock_response)
    assert str(error) == 'Not found'
    assert error.msg == 'Not found'
    assert error.response is mock_response


def test_access_token_error():
    mock_response = httpx.Response(401)
    error = AccessTokenError('Invalid token', mock_response)
    assert str(error) == 'Invalid token'
    assert isinstance(error, OAuth20RequestError)
    assert error.response is mock_response


def test_refresh_token_error():
    mock_response = httpx.Response(401)
    error = RefreshTokenError('Invalid refresh token', mock_response)
    assert str(error) == 'Invalid refresh token'
    assert isinstance(error, OAuth20RequestError)
    assert error.response is mock_response


def test_revoke_token_error():
    mock_response = httpx.Response(400)
    error = RevokeTokenError('Revocation failed', mock_response)
    assert str(error) == 'Revocation failed'
    assert isinstance(error, OAuth20RequestError)
    assert error.response is mock_response


def test_get_userinfo_error():
    mock_response = httpx.Response(403)
    error = GetUserInfoError('Access denied', mock_response)
    assert str(error) == 'Access denied'
    assert isinstance(error, OAuth20RequestError)
    assert error.response is mock_response


def test_error_inheritance_chain():
    assert issubclass(AccessTokenError, OAuth20RequestError)
    assert issubclass(RefreshTokenError, OAuth20RequestError)
    assert issubclass(RevokeTokenError, OAuth20RequestError)
    assert issubclass(GetUserInfoError, OAuth20RequestError)
    assert issubclass(HTTPXOAuth20Error, OAuth20RequestError)
    assert issubclass(OAuth20RequestError, Exception)


def test_error_without_response():
    error = AccessTokenError('Simple error')
    assert str(error) == 'Simple error'
    assert error.msg == 'Simple error'
    assert not hasattr(error, 'response') or error.response is None


def test_error_catch_hierarchy():
    mock_response = httpx.Response(400)

    try:
        raise AccessTokenError('Access token error', mock_response)
    except AccessTokenError as e:
        assert str(e) == 'Access token error'

    try:
        raise RefreshTokenError('Refresh token error', mock_response)
    except OAuth20RequestError as e:
        assert str(e) == 'Refresh token error'

    try:
        raise HTTPXOAuth20Error('HTTPX error', mock_response)
    except HTTPXOAuth20Error as e:
        assert str(e) == 'HTTPX error'


def test_error_properties():
    mock_response = httpx.Response(500)
    error = RevokeTokenError('Server error', mock_response)
    assert hasattr(error, 'msg')
    assert hasattr(error, 'response')
    assert error.msg == 'Server error'
    assert error.response == mock_response


def test_error_str_representation():
    error1 = AccessTokenError('Simple message')
    assert str(error1) == 'Simple message'

    mock_response = httpx.Response(404)
    error2 = GetUserInfoError('User not found', mock_response)
    assert str(error2) == 'User not found'


def test_error_with_complex_message():
    complex_message = "Error: Invalid request\nDetails: Missing required parameter 'code'"
    error = OAuth20RequestError(complex_message)
    assert str(error) == complex_message
