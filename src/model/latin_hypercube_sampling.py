'''
Latin Hypercube sampling.
'''

import numpy


def _get_one(rv, nsamples):
    # Pick random quantiles in [0, 1/n), [1/n, 2/n), ..., [(n-1)/n, 1).
    bounds = numpy.linspace(0, 1, nsamples + 1)
    quantiles = numpy.random.uniform(bounds[ : -1], bounds[1 : ])
    # Convert those quantiles into RV values.
    samples = rv.ppf(quantiles)
    # Shuffle.
    return numpy.random.permutation(samples)


def lhs(rvs, nsamples):
    samples = [_get_one(rv, nsamples) for rv in rvs]
    return numpy.asarray(samples).T


if __name__ == '__main__':
    from scipy import stats

    nsamples = 10

    rvs = 2 * (stats.norm(), )

    samples = lhs(rvs, nsamples)
