# Steam Python

![Documentation](https://img.shields.io/badge/Docs-brightgreen?link=https%3A%2F%2Fpython.steam.style)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A fast and lightweight Python interface for interacting with Steam. Largely inspired by [Valve Python's Steam package](https://github.com/ValvePython/steam) and [the fork by Solstice Game Studios](https://github.com/solsticegamestudios/steam), this library introduces various tweaks to modernize and improve the structure, including complete typing support and modern dependencies. Some logic is also taken from [SteamRE's SteamKit](https://github.com/SteamRE/SteamKit).

> [!IMPORTANT]
>
> `steam-python` is currently under heavy development and is not yet ready for public use.

## Installation

```bash
pip install steam-python # Coming soon
```

or

```bash
pip install git+https://github.com/Steam-Style/steam-python
```

## Usage

To interact with Steam you must first connect to a Connection Manager Server and then log in.

```python
import asyncio
from steam.client import SteamClient

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

## Development

To set up the development environment:

1. Clone the repository.
2. Install dependencies:

```bash
pip install -r dev_requirements.txt -r requirements.txt
```

---

<div align="center">

**🌟 If this project helps you, please consider giving it a star or sponsoring us!**

[![GitHub Stars](https://img.shields.io/github/stars/Steam-Style/website?style=social)](https://github.com/Steam-Style/website/stargazers)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/Steam-Style?style=social)](https://github.com/sponsors/Steam-Style)

Made with ❤️ by the Steam Style team

[Report an Issue](https://github.com/Steam-Style/website/issues) • [Visit Steam Style](https://steam.style)

</div>
