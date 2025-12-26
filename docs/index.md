# Steam Python Documentation

Welcome to the documentation for the Steam Python project. This library provides a fast and lightweight Python interface for interacting with Steam.

!!! warning

    `steam-python` is currently under heavy development and is not yet ready for public use.

## Getting Started

To get started, check out the [API References](references.md) to see the available classes and methods.

## Installation

You can either install the library through PyPI or our official GitHub repository.

```bash
pip install steam-python # Coming soon
```

```
pip install git+https://github.com/Steam-Style/steam-python
```

## Usage

To interact with Steam you must first connect to a Connection Manager Server and then log in.

```python
import asyncio
from client import SteamClient

async def main():
    client = SteamClient()

    # Connect to Steam
    await client.connect()

    # Login anonymously
    await client.anonymous_login()

    # ...

    # Disconnect
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```
