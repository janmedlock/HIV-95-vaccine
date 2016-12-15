'''
Retrieve statistics from simulations with parameter distrubtions.
'''

import os.path

from .. import common
from ... import h5


def open_(mode = 'r'):
    return h5.open_file(os.path.join(common.resultsdir, 'samples.h5'),
                        mode = mode)
