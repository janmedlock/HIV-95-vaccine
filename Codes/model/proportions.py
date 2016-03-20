import numpy

from . import container
from . import simulation


def _safe_divide(a, b, fill_value = 0):
    return numpy.ma.filled(numpy.ma.divide(a, b), fill_value)

class Proportions(container.Container):
    '''
    Get the proportions diagnosed, treated, and viral suppressed from
    the current number of people in the model compartments.
    '''

    _keys = ('diagnosed', 'treated', 'suppressed')

    def __init__(self, state):
        S, A, U, D, T, V, W, Z, R = simulation.split_state(state)

        # (D + T + V + W) / (A + U + D + T + V + W)
        self.diagnosed = _safe_divide(D + T + V + W,
                                      A + U + D + T + V + W)

        # (T + V) / (D + T + V + W)
        self.treated = _safe_divide(T + V,
                                    D + T + V + W)

        # V / (T + V)
        self.suppressed = _safe_divide(V,
                                       T + V)
