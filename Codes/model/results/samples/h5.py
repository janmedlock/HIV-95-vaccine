'''
Retrieve statistics from simulations with parameter distrubtions.
'''

import os.path

from .. import common
from .. import tables_dict


def open_(mode = 'r'):
    # return tables_dict.open_file(os.path.join(common.resultsdir,
    #                                           'samples.h5'),
    #                              mode = mode)
    return tables_dict.open_file('/media/backup2/samples.h5',
                                 mode = mode)
