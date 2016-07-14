class Container:
    '''
    A simple class to hold attributed with an interface like
    :class:`collections.OrderedDict`.
    '''

    _keys = tuple()

    def keys(self):
        return self._keys

    def items(self):
        return ((k, getattr(self, k)) for k in self._keys)

    def values(self):
        return (getattr(self, k) for k in self._keys)

    def __len__(self):
        return len(self._keys)

    def __contains__(self, k):
        return (k in self._keys)

    def __iter__(self):
        return self.keys()

    def __getitem__(self, k):
        return getattr(self, k)
