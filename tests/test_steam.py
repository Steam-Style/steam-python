import pytest
from steam.utils.vdf import VDFParser
from steam.client import SteamClient


class TestVDFParser:
    def test_parse_simple(self):
        vdf = '"root"\n{\n"key" "value"\n}'
        result = VDFParser.parse(vdf)
        assert result == {"root": {"key": "value"}}

    def test_parse_nested(self):
        vdf = '"root"\n{\n"nested"\n{\n"key" "value"\n}\n}'
        result = VDFParser.parse(vdf)
        assert result == {"root": {"nested": {"key": "value"}}}


@pytest.mark.asyncio
class TestSteamClient:
    async def test_integration(self):
        client = SteamClient()

        try:
            await client.connect(retry=True)
            assert client.connected

            await client.anonymous_login()
            assert client.logged_in

            product_info = await client.get_product_info([440])
            assert product_info is not None

            if product_info:
                assert 440 in product_info
                assert "appinfo" in product_info[440]
                assert "common" in product_info[440]["appinfo"]
                assert product_info[440]["appinfo"]["common"]["name"] == "Team Fortress 2"

        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")
        finally:
            await client.disconnect()
