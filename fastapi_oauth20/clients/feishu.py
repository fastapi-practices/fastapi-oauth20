from fastapi_oauth20.oauth20 import OAuth20Base


class FeiShuOAuth20(OAuth20Base):
    """FeiShu (Lark) OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize FeiShu OAuth2 client.

        :param client_id: FeiShu app client ID from the FeiShu developer console.
        :param client_secret: FeiShu app client secret from the FeiShu developer console.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://passport.feishu.cn/suite/passport/oauth/authorize',
            access_token_endpoint='https://passport.feishu.cn/suite/passport/oauth/token',
            refresh_token_endpoint='https://passport.feishu.cn/suite/passport/oauth/authorize',
            userinfo_endpoint='https://passport.feishu.cn/suite/passport/oauth/userinfo',
            default_scopes=[
                'contact:user.employee_id:readonly',
                'contact:user.base:readonly',
                'contact:user.email:readonly',
            ],
        )
