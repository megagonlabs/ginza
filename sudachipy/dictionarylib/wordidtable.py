import struct


class WordIdTable(object):
    def __init__(self, bytes_, offset):
        self.bytes = bytes_
        bytes_.seek(offset)
        self.size = int.from_bytes(bytes_.read(4), 'little')
        self.offset = offset + 4

    def storage_size(self):
        return 4 + self.size

    def get(self, index):
        length = self.bytes[self.offset + index]
        index += 1
        result = struct.unpack_from("<{}I".format(length), self.bytes, self.offset + index)
        return result
