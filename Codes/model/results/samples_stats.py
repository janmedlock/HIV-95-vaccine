'''
Retrieve statistics from simulations with parameter distrubtions.
'''

import os.path

import tables

from . import common


def load_samples_stats(mode = 'r'):
    # Use compression and checksums.
    filters = tables.Filters(complevel = 4,
                             complib = 'zlib',
                             shuffle = True,
                             fletcher32 = True)
    return tables.open_file(os.path.join(common.resultsdir,
                                         'samples_stats.h5'),
                            mode = mode,
                            filters = filters)
