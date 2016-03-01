import numpy

from . import simulation


def get_proportions(state):
    S, A, U, D, T, V, W = simulation.split_state(state)

    proportions = numpy.ma.empty(state.shape[ : -1] + (3, ))

    # diagnosed
    # (D + T + V + W) / (A + U + D + T + V + W)
    proportions[..., 0] = numpy.ma.divide(D + T + V + W, A + U + D + T + V + W)

    # treated
    # (T + V) / (D + T + V + W)
    proportions[..., 1] = numpy.ma.divide(T + V, D + T + V + W)

    # suppressed
    # V / (T + V)
    proportions[..., 2] = numpy.ma.divide(V, T + V)

    return proportions.filled(0)
