'''
Compute the incidence.
'''

import numpy

from . import simulation


def compute(new_infections):
    incidence = (numpy.diff(numpy.asarray(new_infections))
                 / numpy.diff(simulation.t))
    # Put NaNs in the first column to make it align with t.
    if numpy.ndim(new_infections) == 1:
        pad = numpy.nan
    else:
        pad = numpy.nan * numpy.ones(numpy.shape(new_infections)[: -1] + (1, ))
    return numpy.hstack((pad, incidence))
