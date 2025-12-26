import asyncio
import time
from steam.client import SteamClient


async def main():
    start_time = time.time()
    client = SteamClient()
    await client.connect(retry=True)
    print(f"Connected in {time.time() - start_time} seconds")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
