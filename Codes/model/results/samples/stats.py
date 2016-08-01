'''
Retrieve statistics from simulations with parameter distrubtions.
'''

import os.path

from .. import common
from .. import tables_dict


def load(mode = 'r'):
    return tables_dict.open_file(os.path.join(common.resultsdir,
                                              'samples_stats.h5'),
                                 mode = mode)
