import struct


class DictionaryHeader:
    description_size = 256
    storage_size = 8 + 8 + description_size

    def __init__(self, bytes_, offset):
        self.version, self.create_time = struct.unpack_from("<2Q", bytes_, offset)
        offset += 16
        self.description = bytes_[offset:offset+self.description_size].decode("utf-8")
