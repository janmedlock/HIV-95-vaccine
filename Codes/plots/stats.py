'''
Calculate PRCCs, etc.
'''

import numpy
import scipy.stats


def rankdata(X):
    if numpy.ndim(X) == 0:
        raise ValueError('Need at least 1-D data.')
    elif numpy.ndim(X) == 1:
        return (scipy.stats.rankdata(X) - 1) / (len(X) - 1)
    else:
        return numpy.stack([rankdata(X[..., i])
                            for i in range(numpy.shape(X)[-1])],
                           axis = -1)


def cc(X, y):
    result = (scipy.stats.pearsonr(y, x) for x in X.T)
    rho, p = zip(*result)
    return rho, p


def rcc(X, y):
    result = (scipy.stats.spearmanr(y, x) for x in X.T)
    rho, p = zip(*result)
    return rho, p


def get_residuals(Z, b):
    # Add a column of ones for intercept term.
    A = numpy.column_stack((numpy.ones_like(Z[..., 0]), Z))
    result = numpy.linalg.lstsq(A, b)
    coefs = result[0]
    # residuals = b - A @ coefs  # Stupid Sphinx bug.
    residuals = b - numpy.dot(A, coefs)
    return residuals


def pcc(X, y):
    n = numpy.shape(X)[-1]

    rho = numpy.empty(n)
    for i in range(n):
        # Separate ith column from other columns.
        mask = numpy.array([j == i for j in range(n)])
        x = numpy.squeeze(X[..., mask])
        Z = X[..., ~mask]
        x_res = get_residuals(Z, x)
        y_res = get_residuals(Z, y)
        rho[i], _ = scipy.stats.pearsonr(x_res, y_res)
    return rho


def prcc(X, y):
    return pcc(rankdata(X), rankdata(y))
