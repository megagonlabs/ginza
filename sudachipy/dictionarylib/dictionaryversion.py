def constant(f):

    def fset(self, value):
        raise TypeError

    def fget(self):
        return f()

    return property(fget, fset)


class _DictionaryVersion:

    @constant
    def SYSTEM_DICT_VERSION():
        return 0x7366d3f18bd111e7

    @constant
    def USER_DICT_VERSION():
        return 0xa50f31188bd211e7

    @constant
    def USER_DICT_VERSION_2():
        return 0x9fdeb5a90168d868


DictionaryVersion = _DictionaryVersion()
