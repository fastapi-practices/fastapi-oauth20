from fastapi_oauth20.oauth20 import OAuth20Base


class LinuxDoOAuth20(OAuth20Base):
    """Linux.do OAuth2 client implementation."""

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Linux.do OAuth2 client.

        :param client_id: Linux.do OAuth application client ID.
        :param client_secret: Linux.do OAuth application client secret.
        """
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            authorize_endpoint='https://connect.linux.do/oauth2/authorize',
            access_token_endpoint='https://connect.linux.do/oauth2/token',
            refresh_token_endpoint='https://connect.linux.do/oauth2/token',
            userinfo_endpoint='https://connect.linux.do/api/user',
            token_endpoint_basic_auth=True,
        )
