import asyncio
import time
from client import SteamClient


async def main():
    start_time = time.time()
    client = SteamClient()
    await client.connect()
    print(f"Connected in {time.time() - start_time} seconds")
    await client.disconnect()
    await client.connect()
    client.anonymous_login()
    client.logout()
    await client.disconnect()
    client.anonymous_login()

if __name__ == "__main__":
    asyncio.run(main())
