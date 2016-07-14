'''
Compute the incidence.
'''

import numpy


def compute(t, new_infections):
    '''
    Compute the incidence from new_infections and time.
    '''
    # Put a NaN in front to make it align with t.
    return numpy.hstack((numpy.nan,
                         (numpy.diff(numpy.asarray(new_infections))
                          / numpy.diff(t))))
