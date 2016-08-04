'''
Add a dict interface to :mod:`tables`.
Add default compression and checksum filters.
'''

import warnings

import tables


def dump(h5file, obj):
    with warnings.catch_warnings():
        warnings.filter_warnings('ignore',
                                 category = tables.NoSuchNodeError)
        for key in obj.keys():
            val = getattr(self, key)
            group = '/{}/{}'.format(self.country, str(self.targets))
            path = '{}/{}'.format(group, key)
            if path in h5file:
                arr = h5file.get_node(group, key)
                arr[:] = val
            else:
                results.create_carray(group, key, obj = val,
                                      createparents = True)


# Add some methods to tables.File

def file_getitem(h5file, key):
    return getattr(h5file.root, key)

def file_contains(h5file, key):
    return (key in h5file.root)

def file_keys(h5file):
    return [g._v_name for g in h5file.root]

def file_dump(h5file, obj):
    return dump(h5file, obj)

setattr(tables.File, '__getitem__', file_getitem)
setattr(tables.File, '__contains__', file_contains)
setattr(tables.File, 'keys', file_keys)
setattr(tables.File, 'dump', file_dump)


# Add some methods to tables.Group

def group_getitem(group, key):
    return getattr(group, key)

def group_keys(group):
    return [g._v_name for g in group]

setattr(tables.Group, '__getitem__', group_getitem)
setattr(tables.Group, 'keys', group_keys)


def open_file(filename, mode = 'r', filters = None, **kwds):
    '''
    Open a h5file with default compression and checksum filters.
    '''
    if filters is None:
        filters = tables.Filters(complevel = 4,
                                 complib = 'zlib',
                                 shuffle = True,
                                 fletcher32 = True)
    return tables.open_file(filename,
                            mode = mode,
                            filters = filters,
                            **kwds)
