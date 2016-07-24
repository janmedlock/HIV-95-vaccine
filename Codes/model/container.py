import collections.abc


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
