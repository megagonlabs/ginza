class KeySet(object):
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values

    def size(self):
        return len(self.keys)

    def get_key(self, id):
        return self.keys[id]

    def get_key_byte(self, key_id, byte_id):
        if byte_id >= len(self.keys[key_id]):
            return 0
        return self.keys[key_id][byte_id]

    def has_values(self):
        return self.values is not None

    def get_value(self, id):
        return self.values[id] if self.has_values() else id
