'''
Retrieve statistics from simulations with parameter distrubtions.
'''

import os.path

import tables

from . import common


def load_samples_stats(mode = 'r'):
    return tables.open_file(os.path.join(common.resultsdir,
                                         'samples_stats.h5'),
                            mode = mode)
