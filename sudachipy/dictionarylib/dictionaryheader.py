import struct

from sudachipy.dictionarylib.jtypedbytebuffer import JTypedByteBuffer


class DictionaryHeader:

    __DESCRIPTION_SIZE = 256
    __STORAGE_SIZE = 8 + 8 + __DESCRIPTION_SIZE

    def __init__(self, version, create_time, description):
        self.version = version
        self.create_time = create_time
        self.description = description

    @classmethod
    def from_bytes(cls, bytes_, offset):
        version, create_time = struct.unpack_from("<2Q", bytes_, offset)
        offset += 16

        len_ = 0
        while len_ < cls.__DESCRIPTION_SIZE:
            if bytes_[offset + len_] == 0:
                break
            len_ += 1
        description = bytes_[offset:offset + len_].decode("utf-8")
        return cls(version, create_time, description)

    def to_bytes(self):
        buf = JTypedByteBuffer(b'\x00' * (16 + self.__DESCRIPTION_SIZE))
        buf.seek(0)
        buf.write_int(self.version, 'long', signed=False)
        buf.write_int(self.create_time, 'long')
        bdesc = self.description.encode('utf-8')
        if len(bdesc) > self.__DESCRIPTION_SIZE:
            raise ValueError('description is too long')
        buf.write(bdesc)
        return buf.getvalue()

    def storage_size(self):
        return self.__STORAGE_SIZE
