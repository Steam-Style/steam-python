import struct
import io
from typing import Optional, Union
from steam.enums.emsgs import EMsg
from .protobuf_manager import ProtobufManager
from .structs import MsgHdr


class SteamPacket:
    """
    Represents a Steam network packet, either Protobuf or non-Protobuf.
    """

    def __init__(self, emsg: Union[EMsg, int], data: bytes, is_protobuf: bool):
        self.emsg: Union[EMsg, int] = emsg
        self.is_protobuf: bool = is_protobuf
        self.header: Optional[MsgHdr] = None
        self.body: Optional[bytes] = None

        if is_protobuf and isinstance(emsg, EMsg):
            stream = io.BytesIO(data)
            header_len = struct.unpack("<I", stream.read(4))[0]
            stream.read(header_len)  # TODO: Parse Protobuf Header
            proto_class = ProtobufManager.get_protobuf(emsg)

            if proto_class:
                self.body = proto_class()  # type: ignore
                self.body.ParseFromString(stream.read())  # type: ignore
            else:
                self.body = stream.read()
        else:
            header_data = struct.pack("<I", int(emsg)) + data[:16]
            self.header = MsgHdr(header_data)
            self.body = data[16:]

    @classmethod
    def parse(cls, data: bytes) -> "SteamPacket":
        """
        Parses raw data into a SteamPacket instance.

        Args:
            data: The raw bytes of the packet.

        Returns:
            A SteamPacket instance.
        """
        emsg_id = struct.unpack_from("<I", data)[0]
        is_protobuf = False

        if ProtobufManager.is_protobuf(emsg_id):
            is_protobuf = True
            emsg_id = ProtobufManager.remove_mask(emsg_id)

        try:
            emsg = EMsg(emsg_id)
        except ValueError:
            emsg = emsg_id

        return cls(emsg, data[4:], is_protobuf)
