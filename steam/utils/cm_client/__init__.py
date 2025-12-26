import binascii
import aiohttp
import asyncio
import time
import logging
from typing import Optional
from steam.enums.emsgs import EMsg
from steam.utils.structs import MsgChannelEncryptRequest, MsgChannelEncryptResponse, MsgHdr
from steam.utils.packet import SteamPacket
from steam.enums.common import EResult
from .constants import (
    STEAM_CM_LIST_URL,
    MAGIC_HEADER,
    CONNECTION_TIMEOUT,
    MAX_CONNECTIONS
)
from steam.utils.crypto import generate_session_key


class CMClient:
    """
    Manages connections to Steam Connection Manager servers.
    """

    __LOG: logging.Logger = logging.getLogger(__name__)

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.server_list: list[tuple[str, int]] = []
        self.fastest_server: tuple[Optional[tuple[str, int]], float] = (
            None, float("inf"))
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected: bool = False

    async def __test_server_latency(self, host: str, port: int) -> float:
        try:
            start_time = time.time()
            future = asyncio.open_connection(host, port)
            _, writer = await asyncio.wait_for(future, timeout=CONNECTION_TIMEOUT)

            latency = time.time() - start_time
            writer.close()
            await writer.wait_closed()

            return latency

        except (asyncio.TimeoutError, OSError, ValueError):
            return float("inf")

    async def __find_fastest_server(self) -> tuple[Optional[tuple[str, int]], float]:
        semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

        async def bounded_test(host: str, port: int) -> float:
            async with semaphore:
                return await self.__test_server_latency(host, port)

        tasks = [bounded_test(host, port) for (host, port) in self.server_list]
        latencies = await asyncio.gather(*tasks)
        fastest_server = (None, float("inf"))

        for (server_ip), latency in zip(self.server_list, latencies):
            if latency < fastest_server[1]:
                fastest_server = (server_ip, latency)

        self.fastest_server = fastest_server
        return fastest_server

    async def get_server_list(self) -> list[tuple[str, int]]:
        """
        Fetches a list of available servers.

        Returns:
            A list of tuples containing server host and port.
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(STEAM_CM_LIST_URL) as response:
                response.raise_for_status()
                json_data = await response.json()
                raw_server_list = json_data.get(
                    "response", {}).get("serverlist", [])
                self.server_list = []

                for server_ip in raw_server_list:
                    host, port = server_ip.split(':')
                    port = int(port)
                    self.server_list.append((host, port))

                return self.server_list
        except aiohttp.ClientError as e:
            self.__LOG.error(f"Failed to fetch server list: {e}")
            return []

    async def connect(self, retry: bool = False, use_fastest: bool = False) -> EResult:
        """
        Connects to a server.

        Args:
            retry: If True, retries connecting if the initial connection attempt fails.
            use_fastest: If True, determines and connects to the server with the lowest latency.
                This adds initial overhead but may improve connection speed.

        Returns:
            True if connection is successful, False otherwise.
        """
        while True:
            server = await self._select_server(use_fastest)

            if not server:
                return EResult.ConnectFailed

            host, port = server

            try:
                self.reader, self.writer = await asyncio.open_connection(host, port)
            except (OSError, ValueError, TimeoutError) as e:
                self.__LOG.error(
                    f"Failed to connect to server {host}:{port}: {e}")

                if not retry:
                    return EResult.ConnectFailed

                continue

            if await self._handshake():
                self.connected = True
                return EResult.OK

            await self.disconnect()

            if not retry:
                return EResult.ConnectFailed

            self.__LOG.info("Retrying connection...")

    async def _select_server(self, use_fastest: bool) -> Optional[tuple[str, int]]:
        if not self.server_list:
            await self.get_server_list()

        if use_fastest or self.fastest_server[0] is not None:
            if self.fastest_server[0] is None:
                await self.__find_fastest_server()

            return self.fastest_server[0]

        for host, port in self.server_list:
            if await self.__test_server_latency(host, port) < float("inf"):
                return (host, port)

        await self.get_server_list()

        for host, port in self.server_list:
            if await self.__test_server_latency(host, port) < float("inf"):
                return (host, port)

        return None

    async def _handshake(self) -> bool:
        if self.writer is None:
            return False

        message = await self.listen()

        if message is None:
            self.__LOG.error("No response received after connecting")
            return False

        packet = SteamPacket.parse(message)
        self.__LOG.info(f"Received: {packet.emsg}")

        if packet.emsg != EMsg.ChannelEncryptRequest or packet.body is None:
            self.__LOG.error("Did not receive ChannelEncryptRequest")
            return False

        request = MsgChannelEncryptRequest(packet.body)
        _, encrypted_key = generate_session_key(request.challenge)
        crc = binascii.crc32(encrypted_key) & 0xffffffff

        response = MsgChannelEncryptResponse()
        response.key_size = len(encrypted_key)
        response.key = encrypted_key
        response.crc = crc

        header = MsgHdr()
        header.emsg = EMsg.ChannelEncryptResponse
        payload = header.pack() + response.pack()

        self.writer.write(len(payload).to_bytes(
            4, byteorder="little") + MAGIC_HEADER.encode() + payload)

        await self.writer.drain()
        message = await self.listen()

        if message is None:
            self.__LOG.error(
                "No response received after sending ChannelEncryptResponse")
            return False

        packet = SteamPacket.parse(message)

        if packet.emsg != EMsg.ChannelEncryptResult:
            self.__LOG.error(
                "Did not receive ChannelEncryptResult after sending response")
            return False

        self.__LOG.info(f"Received: {packet.emsg}")
        return True

    async def disconnect(self):
        """
        Disconnects from the current server.
        """
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

            self.writer = None
            self.reader = None

        if self.session:
            await self.session.close()
            self.session = None

        self.connected = False

    async def listen(self) -> Optional[bytes]:
        """
        Listens for incoming messages from the server.

        Returns:
            The received message as bytes, or None if an error occurs.
        """
        if not self.reader:
            self.__LOG.warning("Not connected")
            return

        try:
            length_data = await self.reader.readexactly(4)
            length = int.from_bytes(length_data, byteorder="little")
            magic_header = await self.reader.readexactly(4)

            if magic_header != MAGIC_HEADER.encode():
                self.__LOG.warning("Invalid magic header, disconnecting")
                return

            message = await self.reader.readexactly(length)
            return message

        except asyncio.IncompleteReadError:
            self.__LOG.warning("Server closed connection")
            return
        except Exception as e:
            self.__LOG.error(f"Error listening: {e}")
            return
