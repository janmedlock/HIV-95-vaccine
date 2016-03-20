import numpy

from . import container
from . import simulation


class Proportions(container.Container):
    '''
    Get the proportions diagnosed, treated, and viral suppressed from
    the current number of people in the model compartments.
    '''

    _keys = ('diagnosed', 'treated', 'suppressed')

    def __init__(self, state):
        S, A, U, D, T, V, W, Z, R = simulation.split_state(state)

        # (D + T + V + W) / (A + U + D + T + V + W)
        self.diagnosed = numpy.ma.divide(D + T + V + W,
                                         A + U + D + T + V + W)

        # (T + V) / (D + T + V + W)
        self.treated = numpy.ma.divide(T + V,
                                       D + T + V + W)

        # V / (T + V)
        self.suppressed = numpy.ma.divide(V,
                                          T + V)
