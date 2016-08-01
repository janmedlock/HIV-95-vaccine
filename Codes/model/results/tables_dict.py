'''
Add a dict interface to :mod:`tables` and default compression
and checksum filters.
'''

import tables


def root_getitem(h5file, key):
    '''
    Add a dict interface to :class:`tables.File`.
    '''
    return getattr(h5file.root, key)

setattr(tables.File, '__getitem__', root_getitem)


def group_getitem(group, key):
    '''
    Add a dict interface to :class:`tables.Group`.
    '''
    return getattr(group, key)

setattr(tables.Group, '__getitem__', group_getitem)


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
