'''
Store and retrieve results from simulations with parameter modes.
'''

import os.path

from . import common
from . import tables_dict


def load(mode = 'r'):
    return tables_dict.open_file(os.path.join(common.resultsdir,
                                              'modes.h5'),
                                 mode = mode)

def load_vaccine_sensitivity(mode = 'r'):
    return tables_dict.open_file(os.path.join(common.resultsdir,
                                              'vaccine_sensitivity.h5'),
                                 mode = mode)
