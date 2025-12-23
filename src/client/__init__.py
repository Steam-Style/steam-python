import logging
from typing import Optional
from utils.cm_client import CMClient
from enums.common import EResult


class SteamClient(CMClient):
    """
    A client for interacting with the Steam network.
    """

    def __init__(self) -> None:
        super().__init__()
        self.logged_in: bool = False

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> EResult:
        """
        Logs in the client with the provided credentials or anonymously if none are
            provided

        Args:
            username: The username for login.
            password: The password for login.

        Returns:
            An EResult indicating the outcome of the login attempt.
        """
        if username is None and password is None:
            return self.anonymous_login()

        # TODO: Implement login logic
        if not self.connected:
            logging.error("Client not connected")
            return EResult.NoConnection

        self.logged_in = True
        return EResult.OK

    def anonymous_login(self) -> EResult:
        """
        Logs in the client without credentials.

        Returns:
            An EResult indicating the outcome of the login attempt.
        """
        # TODO: Implement anonymous login logic
        if not self.connected:
            logging.error("Client not connected")
            return EResult.NoConnection

        self.logged_in = True
        return EResult.OK

    def logout(self) -> EResult:
        """
        Logs out the client.

        Returns:
            An EResult indicating the outcome of the logout attempt.
        """
        # TODO: Implement logout logic
        self.logged_in = False
        return EResult.OK
