'''
Add a dict interface to :mod:`tables` and default compression
and checksum filters.
'''

import warnings

import tables


def root_getitem(h5file, key):
    return getattr(h5file.root, key)

def root_contains(h5file, key):
    return (key in h5file.root)

def root_keys(h5file):
    return [g._v_name for g in h5file.root]

setattr(tables.File, '__getitem__', root_getitem)
setattr(tables.File, '__contains__', root_contains)
setattr(tables.File, 'keys', root_keys)


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
