# Steam Client Documentation

Welcome to the documentation for the Steam Client Python project. This library provides a fast and lightweight Python interface for interacting with Steam.

## Getting Started

To get started, check out the [API References](references.md) to see the available classes and methods.

## Installation

You can either install the library through PyPI or our official GitHub repository.

```bash
pip install steam-python
```

```
pip install git+https://github.com/Steam-Style/steam-python
```

## Usage

To interact with Steam you must first connect to a Connection Manager Server and then log in.

```python
from steam.client import SteamClient

client = SteamClient()
client.connect()
client.anonymous_login()
# ...
```
