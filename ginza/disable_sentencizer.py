# encoding: utf8
from collections import OrderedDict

import srsly

from spacy import util


__all__ = [
    "DisableSentencizer",
]



class DisableSentencizer:
    def __init__(self, nlp):
        self.nlp = nlp

    def __call__(self, doc):
        for t in doc:
            t.is_sent_start = False
        return doc

    def _get_config(self):
        return {}

    def _set_config(self, config=None):
        pass

    def to_bytes(self, **_kwargs):
        serializers = OrderedDict(
            (
                ("cfg", lambda: srsly.json_dumps(self._get_config())),
            )
        )
        return util.to_bytes(serializers, [])

    def from_bytes(self, data, **_kwargs):
        deserializers = OrderedDict(
            (
                ("cfg", lambda b: self._set_config(srsly.json_loads(b))),
            )
        )
        util.from_bytes(data, deserializers, [])
        return self

    def to_disk(self, path, **_kwargs):
        path = util.ensure_path(path)
        serializers = OrderedDict(
            (
                ("cfg", lambda p: srsly.write_json(p, self._get_config())),
            )
        )
        return util.to_disk(path, serializers, [])

    def from_disk(self, path, **_kwargs):
        path = util.ensure_path(path)
        serializers = OrderedDict(
            (
                ("cfg", lambda p: self._set_config(srsly.read_json(p))),
            )
        )
        util.from_disk(path, serializers, [])
