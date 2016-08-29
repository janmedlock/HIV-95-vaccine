'''
Compute proportions diagnosed, treated, viral suppressed, and vaccinated.
'''

import warnings

import numpy

from . import ODEs


def _safe_divide(a, b, fill_value = 0):
    '''
    Return a / b,
    unless b == a == 0, then return 0.
    '''
    # Ignore divide-by-zero warnings.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',
                                module = 'numpy',
                                message = ('divide by zero encountered in '
                                           'true_divide'))
        return numpy.where((a == 0) & (b == 0), 0, numpy.divide(a, b))


def get(state):
    '''
    Get the proportions diagnosed, treated, viral suppressed, and vaccinated
    from the current number of people in the model compartments.
    '''

    S, Q, A, U, D, T, V, W, Z, R = ODEs.split_state(state)

    # (D + T + V + W) / (A + U + D + T + V + W)
    diagnosed = _safe_divide(D + T + V + W,
                             A + U + D + T + V + W)

    # (T + V + W) / (D + T + V + W)
    treated = _safe_divide(T + V + W,
                           D + T + V + W)

    # V / (T + V)
    suppressed = _safe_divide(V,
                              T + V)

    # Q / (S + Q)
    vaccinated = _safe_divide(Q,
                              S + Q)

    return numpy.rec.fromarrays(
        [diagnosed, treated, suppressed, vaccinated],
        names = ['diagnosed', 'treated', 'suppressed', 'vaccinated'])
