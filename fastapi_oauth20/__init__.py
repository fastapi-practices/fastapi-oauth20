"""在 FastAPI 中异步授权 OAuth2 客户端"""

__version__ = '0.0.1a1'

__all__ = ['OSChinaOAuth20', 'GoogleOAuth20', 'FeiShuOAuth20', 'GiteeOAuth20', 'GitHubOAuth20', 'FastAPIOAuth20']

from .clients.feishu import FeiShuOAuth20
from .clients.gitee import GiteeOAuth20
from .clients.github import GitHubOAuth20
from .clients.google import GoogleOAuth20
from .clients.oschina import OSChinaOAuth20
from .integrations.fastapi import OAuth20 as FastAPIOAuth20
