from fastapi_oauth20.oauth20 import OAuth20Base


class OSChinaOAuth20(OAuth20Base):
    """OSChina OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize OSChina OAuth2 client.

        :param client_id: OSChina OAuth application client ID.
        :param client_secret: OSChina OAuth application client secret.
        :return:
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://www.oschina.net/action/oauth2/authorize',
            access_token_endpoint='https://www.oschina.net/action/openapi/token',
            refresh_token_endpoint='https://www.oschina.net/action/openapi/token',
            userinfo_endpoint='https://www.oschina.net/action/openapi/user',
        )
