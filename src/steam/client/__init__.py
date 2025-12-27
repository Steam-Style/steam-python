import logging
import os
from typing import Any
from steam.utils.cm_client import CMClient
from steam.client.mixins import LogonMixin, ProductInfoMixin


class SteamClient(CMClient, LogonMixin, ProductInfoMixin):
    """
    A client for interacting with the Steam network.
    """

    _log: logging.Logger = logging.getLogger(__name__)

    def __init__(self):
        """
        Initializes the SteamClient.
        """
        super().__init__()
        self.logged_in: bool = False
        self.machine_id: bytes = os.urandom(16)

    def send_protobuf_message(self, *args: Any, **kwargs: Any) -> Any:
        return CMClient.send_protobuf_message(self, *args, **kwargs)

    async def disconnect(self):
        """
        Disconnects from the current server.
        """
        self._stop_heartbeat()
        await super().disconnect()
