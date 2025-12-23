import aiohttp
import asyncio
import time
import struct
import logging
from typing import Optional
from utils.protobuf_manager import ProtobufManager
from enums.common import EResult
from .constants import (
    STEAM_CM_LIST_URL,
    MAGIC_HEADER,
    CONNECTION_TIMEOUT,
    MAX_CONNECTIONS
)


class CMClient:
    """
    Manages connections to Steam Connection Manager servers.
    """

    def __init__(self) -> None:
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
            logging.error(f"Failed to fetch server list: {e}")
            return []

    async def connect(self, use_fastest: bool = False) -> EResult:
        """
        Connects to a server.

        Args:
            use_fastest: If True, determines and connects to the server with the lowest latency.
                This adds initial overhead but may improve connection speed.

        Returns:
            True if connection is successful, False otherwise.
        """
        if not self.server_list:
            await self.get_server_list()

        selected_server: Optional[tuple[str, int]] = None

        if use_fastest or self.fastest_server[0] is not None:
            if self.fastest_server[0] is None:
                await self.__find_fastest_server()

            selected_server = self.fastest_server[0]
        else:
            while selected_server is None:
                for (host, port) in self.server_list:
                    if await self.__test_server_latency(host, port) < float("inf"):
                        selected_server = (host, port)
                        break

                if selected_server is None:
                    await self.get_server_list()
                else:
                    break

        if selected_server is None:
            return EResult.ConnectFailed

        host, port = selected_server

        try:
            self.reader, self.writer = await asyncio.open_connection(host, port)
        except (OSError, ValueError, TimeoutError) as e:
            logging.error(f"Failed to connect to server {host}:{port}: {e}")
            return EResult.ConnectFailed

        message = await self.listen()

        if message:
            emsg_id, = struct.unpack_from("<I", message)
            logging.debug(emsg_id)
            # TODO: Finish handshake process
            ProtobufManager(message)
            self.connected = True
        else:
            return EResult.ConnectFailed

        return EResult.OK

    async def disconnect(self) -> None:
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
            logging.warning("Not connected")
            return

        try:
            length_data = await self.reader.readexactly(4)
            length = int.from_bytes(length_data, byteorder="little")
            magic_header = await self.reader.readexactly(4)

            if magic_header != MAGIC_HEADER.encode():
                logging.warning("Invalid magic header, disconnecting")
                return

            message = await self.reader.readexactly(length)
            return message

        except asyncio.IncompleteReadError:
            logging.warning("Server closed connection")
            return
        except Exception as e:
            logging.error(f"Error listening: {e}")
            return
