class DoubleArrayBuilderUnit(object):
    def __init__(self):
        self.unit = 0

    def set_has_leaf(self, has_leaf):
        """
        :param has_leaf: bool
        """
        if has_leaf:
            self.unit |= 1 << 8
        else:
            self.unit &= ~(1 << 8)

    def set_value(self, value):
        """
        :param value: int
        """
        self.unit = value | (1 << 31)

    def set_label(self, label):
        """
        :param label: bytes
        """
        self.unit = (self.unit & ~0xFF) | int(label)

    def set_offset(self, offset):
        self.unit &= (1 << 31) | (1 << 8) | 0xFF
        if offset < 1 << 21:
            self.unit |= (offset << 10)
        else:
            self.unit |= (offset << 2) | (1 << 9)
