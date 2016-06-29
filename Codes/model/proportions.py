'''
Compute proportions diagnosed, treated, viral suppressed, and vaccinated.
'''

import warnings

import numpy

from . import container
from . import ODEs


def _safe_divide(a, b, fill_value = 0):
    '''
    Return a / b,
    unless b == a == 0, then return 0.
    '''
    # Ignore divide-by-zero warnings.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return numpy.where((a == 0) & (b == 0), 0, numpy.divide(a, b))

class Proportions(container.Container):
    '''
    Get the proportions diagnosed, treated, viral suppressed, and vaccinated
    from the current number of people in the model compartments.
    '''

    _keys = ('diagnosed', 'treated', 'suppressed', 'vaccinated')

    def __init__(self, state):
        S, Q, A, U, D, T, V, W, Z, R = ODEs.split_state(state)

        # (D + T + V + W) / (A + U + D + T + V + W)
        self.diagnosed = _safe_divide(D + T + V + W,
                                      A + U + D + T + V + W)

        # (T + V + W) / (D + T + V + W)
        self.treated = _safe_divide(T + V + W,
                                    D + T + V + W)

        # V / (T + V + W)
        self.suppressed = _safe_divide(V,
                                       T + V + W)

        # Q / (S + Q)
        self.vaccinated = _safe_divide(Q,
                                       S + Q)
