class WordParameterList(object):
    def __init__(self, bytes_, offset):
        self.ELEMENT_SIZE = 2 * 3

        self.bytes = bytes_
        bytes_.seek(offset)
        self.size = int.from_bytes(bytes_.read(4), 'little')
        self.offset = offset + 4
        self.is_copied = False

    def storage_size(self):
        return 4 + self.ELEMENT_SIZE * self.size

    def get_size(self):
        return self.size

    def get_left_id(self, word_id):
        self.bytes.seek(self.offset + self.ELEMENT_SIZE * word_id)
        return int.from_bytes(self.bytes.read(2), 'little')

    def get_right_id(self, word_id):
        self.bytes.seek(self.offset + self.ELEMENT_SIZE * word_id + 2)
        return int.from_bytes(self.bytes.read(2), 'little')

    def get_cost(self, word_id):
        self.bytes.seek(self.offset + self.ELEMENT_SIZE * word_id + 4)
        return int.from_bytes(self.bytes.read(2), 'little', signed=True)

    def set_cost(self, word_id, cost):
        if not self.is_copied:
            self.copy_buffer()
        self.bytes.seek(self.offset + self.ELEMENT_SIZE * word_id + 4)
        self.bytes.write(2, cost.to_bytes(2, 'little', signed=True))
