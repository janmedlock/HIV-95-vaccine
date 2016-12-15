import collections

import numpy


class Container(collections.abc.MutableMapping):
    '''
    A simple class to hold attributes with an interface like
    :class:`collections.OrderedDict`.
    '''

    _keys = tuple()

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def __delitem__(self, k):
        return delattr(self, k)

    def __iter__(self):
        return iter(self._keys)

    def __len__(self):
        return len(self._keys)

    def to_records(self):
        names, arrays = zip(*self.items())
        return numpy.rec.fromarrays(arrays, names = names)


class DefaultOrderedDict(collections.OrderedDict):
    '''
    The combination of :class:`collections.OrderedDict` and
    :class:`collections.defaultdict`.
    '''
    def __init__(self, default_factory):
        super().__init__()
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        self[key] = value = self.default_factory()
        return value
