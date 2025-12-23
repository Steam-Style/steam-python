import struct
import logging
from enums.emsgs import EMsg
from .constants import PROTOBUF_MASK


class ProtobufManager:
    """
    Manages Steam Protobuf messages.
    """

    def __init__(self, message: bytes) -> None:
        emsg_id = struct.unpack_from("<I", message)[0]

        if (int(emsg_id) & PROTOBUF_MASK) > 0:
            emsg_id = self.remove_mask(emsg_id)

        try:
            emsg_id = EMsg(emsg_id)
        except ValueError:
            logging.error(f"Invalid EMsg received: {emsg_id}")
            return

        self.emsg_id: EMsg = emsg_id
        self.message: bytes = message

    def add_mask(self, emsg_id: int) -> int:
        """
        Sets the protobuf mask on the given emsg_id.

        Args:
            emsg_id: The original integer emsg_id.

        Returns:
            The integer emsg_id with the protobuf mask applied.
        """
        return emsg_id | PROTOBUF_MASK

    def remove_mask(self, emsg_id: int) -> int:
        """
        Clears the protobuf mask from the given emsg_id.

        Args:
            emsg_id: The integer emsg_id with the protobuf mask.

        Returns:
            The integer emsg_id without the protobuf mask.
        """
        return emsg_id & ~PROTOBUF_MASK
