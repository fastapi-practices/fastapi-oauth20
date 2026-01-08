from fastapi_oauth20.clients.feishu import FeiShuOAuth20
from fastapi_oauth20.clients.gitee import GiteeOAuth20
from fastapi_oauth20.clients.github import GitHubOAuth20
from fastapi_oauth20.clients.google import GoogleOAuth20
from fastapi_oauth20.clients.linuxdo import LinuxDoOAuth20
from fastapi_oauth20.clients.oschina import OSChinaOAuth20
from fastapi_oauth20.errors import (
    AccessTokenError,
    GetUserInfoError,
    HTTPXOAuth20Error,
    OAuth20RequestError,
    RefreshTokenError,
    RevokeTokenError,
)


def test_feishu_client_creation():
    """Test FeiShu client can be created."""
    client = FeiShuOAuth20('test_id', 'test_secret')
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint is not None
    assert client.access_token_endpoint is not None
    assert client.default_scopes is not None


def test_github_client_creation():
    """Test GitHub client can be created."""
    client = GitHubOAuth20('test_id', 'test_secret')
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint is not None
    assert client.access_token_endpoint is not None
    assert client.default_scopes is not None


def test_google_client_creation():
    """Test Google client can be created."""
    client = GoogleOAuth20('test_id', 'test_secret')
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint is not None
    assert client.access_token_endpoint is not None
    assert client.refresh_token_endpoint is not None
    assert client.revoke_token_endpoint is not None
    assert client.default_scopes is not None


def test_gitee_client_creation():
    """Test Gitee client can be created."""
    client = GiteeOAuth20('test_id', 'test_secret')
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint is not None
    assert client.access_token_endpoint is not None
    assert client.refresh_token_endpoint is not None
    assert client.default_scopes is not None


def test_oschina_client_creation():
    """Test OSChina client can be created."""
    client = OSChinaOAuth20('test_id', 'test_secret')
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint is not None
    assert client.access_token_endpoint is not None
    assert client.refresh_token_endpoint is not None


def test_linuxdo_client_creation():
    """Test Linux.do client can be created."""
    client = LinuxDoOAuth20('test_id', 'test_secret')
    assert client.client_id == 'test_id'
    assert client.client_secret == 'test_secret'
    assert client.authorize_endpoint is not None
    assert client.access_token_endpoint is not None
    assert client.refresh_token_endpoint is not None
    assert client.token_endpoint_basic_auth is True


def test_all_clients_inherit_from_base():
    """Test all clients inherit from OAuth20Base."""
    from fastapi_oauth20.oauth20 import OAuth20Base

    clients = [
        FeiShuOAuth20('id', 'secret'),
        GitHubOAuth20('id', 'secret'),
        GoogleOAuth20('id', 'secret'),
        GiteeOAuth20('id', 'secret'),
        OSChinaOAuth20('id', 'secret'),
        LinuxDoOAuth20('id', 'secret'),
    ]

    for client in clients:
        assert isinstance(client, OAuth20Base)


def test_error_classes_creation():
    """Test all error classes can be created."""
    # Test basic error creation
    base_error = OAuth20RequestError('Base error')
    assert str(base_error) == 'Base error'

    # Test specialized errors
    access_error = AccessTokenError('Access error')
    assert str(access_error) == 'Access error'

    refresh_error = RefreshTokenError('Refresh error')
    assert str(refresh_error) == 'Refresh error'

    revoke_error = RevokeTokenError('Revoke error')
    assert str(revoke_error) == 'Revoke error'

    user_error = GetUserInfoError('User info error')
    assert str(user_error) == 'User info error'

    httpx_error = HTTPXOAuth20Error('HTTPX error')
    assert str(httpx_error) == 'HTTPX error'


def test_error_inheritance():
    """Test error class inheritance hierarchy."""
    assert issubclass(AccessTokenError, OAuth20RequestError)
    assert issubclass(RefreshTokenError, OAuth20RequestError)
    assert issubclass(RevokeTokenError, OAuth20RequestError)
    assert issubclass(GetUserInfoError, OAuth20RequestError)
    assert issubclass(HTTPXOAuth20Error, OAuth20RequestError)


def test_client_endpoint_urls():
    """Test clients have proper endpoint URLs."""

    # FeiShu
    feishu = FeiShuOAuth20('id', 'secret')
    assert 'feishu.cn' in feishu.authorize_endpoint
    assert 'feishu.cn' in feishu.access_token_endpoint

    # GitHub
    github = GitHubOAuth20('id', 'secret')
    assert 'github.com' in github.authorize_endpoint
    assert 'github.com' in github.access_token_endpoint

    # Google
    google = GoogleOAuth20('id', 'secret')
    assert 'google.com' in google.authorize_endpoint
    assert 'googleapis.com' in google.access_token_endpoint

    # Gitee
    gitee = GiteeOAuth20('id', 'secret')
    assert 'gitee.com' in gitee.authorize_endpoint
    assert 'gitee.com' in gitee.access_token_endpoint

    # OSChina
    oschina = OSChinaOAuth20('id', 'secret')
    assert 'oschina.net' in oschina.authorize_endpoint
    assert 'oschina.net' in oschina.access_token_endpoint

    # Linux.do
    linuxdo = LinuxDoOAuth20('id', 'secret')
    assert 'linux.do' in linuxdo.authorize_endpoint
    assert 'linux.do' in linuxdo.access_token_endpoint


def test_client_scopes():
    """Test clients have appropriate default scopes."""

    feishu = FeiShuOAuth20('id', 'secret')
    assert isinstance(feishu.default_scopes, list)
    assert len(feishu.default_scopes) > 0

    github = GitHubOAuth20('id', 'secret')
    assert isinstance(github.default_scopes, list)
    assert len(github.default_scopes) > 0

    google = GoogleOAuth20('id', 'secret')
    assert isinstance(google.default_scopes, list)
    assert len(google.default_scopes) > 0

    gitee = GiteeOAuth20('id', 'secret')
    assert isinstance(gitee.default_scopes, list)
    assert len(gitee.default_scopes) > 0

    oschina = OSChinaOAuth20('id', 'secret')
    # OSChina has no default scopes
    assert oschina.default_scopes is None

    linuxdo = LinuxDoOAuth20('id', 'secret')
    # Linux.do has no default scopes
    assert linuxdo.default_scopes is None


def test_multiple_clients_independence():
    """Test multiple client instances work independently."""
    feishu1 = FeiShuOAuth20('id1', 'secret1')
    feishu2 = FeiShuOAuth20('id2', 'secret2')

    assert feishu1.client_id != feishu2.client_id
    assert feishu1.client_secret != feishu2.client_secret
    assert feishu1.authorize_endpoint == feishu2.authorize_endpoint


def test_google_special_features():
    """Test Google client special features."""
    google = GoogleOAuth20('id', 'secret')

    # Google has both refresh and revoke endpoints
    assert google.refresh_token_endpoint is not None
    assert google.revoke_token_endpoint is not None

    # Google uses same endpoint for refresh and access
    assert google.refresh_token_endpoint == google.access_token_endpoint


def test_linuxdo_special_features():
    """Test Linux.do client special features."""
    linuxdo = LinuxDoOAuth20('id', 'secret')

    # Linux.do uses basic auth for token endpoint
    assert linuxdo.token_endpoint_basic_auth is True
