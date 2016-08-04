'''
Store and retrieve results from simulations with parameter modes.
'''

import os.path

from . import common
from .. import h5


def open_(mode = 'r'):
    return h5.open_file(os.path.join(common.resultsdir, 'modes.h5'),
                        mode = mode)

def open_vaccine_sensitivity(mode = 'r'):
    return h5.open_file(os.path.join(common.resultsdir,
                                     'vaccine_sensitivity.h5'),
                        mode = mode)
