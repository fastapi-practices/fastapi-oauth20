from fastapi_oauth20.oauth20 import OAuth20Base


class GiteeOAuth20(OAuth20Base):
    """Gitee OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Gitee OAuth2 client.

        :param client_id: Gitee OAuth application client ID.
        :param client_secret: Gitee OAuth application client secret.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://gitee.com/oauth/authorize',
            access_token_endpoint='https://gitee.com/oauth/token',
            refresh_token_endpoint='https://gitee.com/oauth/token',
            userinfo_endpoint='https://gitee.com/api/v5/user',
            default_scopes=['user_info'],
        )
