'''
Add a dict interface to :mod:`tables`.
Add default compression and checksum filters.
'''

import numbers
import warnings

import numpy
import tables

from . import container


def _dump_val(h5file, group, name, val):
    # tables requires the value be at least 1d,
    # i.e. no scalars.
    val = numpy.atleast_1d(val)

    if isinstance(val, (numbers.Number, numpy.ndarray, numpy.record)):
        if name in group:
            arr = h5file.get_node(group, name)
            arr[:] = val
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore',
                                        category = tables.NaturalNameWarning)
                arr = h5file.create_carray(group, name, obj = val,
                                           createparents = True)
        return arr
    elif isinstance(val, container.Container):
        # Get a Group() with the current name.
        try:
            namegroup = h5file.get_node(group, name)
        except tables.NoSuchNodeError:
            namegroup = h5file.create_group(group, name)
        # Recurse through the keys.
        for key in val.keys():
            subval = getattr(val, key)
            _dump_val(h5file, namegroup, key, subval)
        return namegroup
    elif isinstance(val, list):
        # This is for MultiSim().
        raise NotImplementedError
    else:
        raise ValueError("Unknown type '{}'!".format(type(val)))


def _get_group(h5file, *groups):
    if len(groups) == 0:
        group = h5file.root
    elif isinstance(groups[0], tables.Group):
        msg = "I don't know what to do with multiple tables.Group()s!"
        assert len(groups) == 1, msg
        group = groups[0]
    else:
        groupname = '/' + '/'.join(map(str, groups))
        try:
            group = h5file.get_node(groupname)
        except tables.NoSuchNodeError:
            # Make the group.
            idx = groupname.rfind('/')
            lastname = groupname[idx + 1 : ]
            firstnames = groupname[ : idx]
            with warnings.catch_warnings():
                warnings.filter_warnings('ignore',
                                         category = tables.NaturalNameWarning)
                group = h5file.create_group(firstnames, lastname,
                                            createparents = True)
    return group


def dump(h5file, obj, *groups):
    group = _get_group(h5file, *groups)
    for key in obj.keys():
        _dump_val(hd5file, group, key, getattr(obj, key))
    return group


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
