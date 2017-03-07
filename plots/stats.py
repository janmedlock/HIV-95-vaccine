'''
Calculate PRCCs, etc.
'''

import warnings

import numpy
import scipy.stats


def median(X, axis = 0):
    '''
    Handle NaNs when finding median.
    '''
    X = numpy.ma.array(X, mask = numpy.isnan(X))
    return numpy.ma.median(X, axis = axis).filled(numpy.nan)


def quantile(X, q, axis = 0):
    '''
    Handle NaNs when finding quantiles.
    '''
    if not numpy.isscalar(q):
        q = numpy.asarray(q)
    # Suppress warnings about NaNs.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        Y = numpy.percentile(X, 100 * q, axis = axis)
    isnanX = numpy.all(numpy.isnan(X), axis = axis)
    isnanY = numpy.isnan(Y)
    if isnanY.ndim > isnanX.ndim:
        isnanY = numpy.any(isnanY, axis = 0)
    assert all(isnanX == isnanY)
    return Y


def confidence_interval(X, level, axis = 0):
    '''
    Finding confidence interval using quantiles.
    '''
    q = [(1 - level) / 2, (1 + level) / 2]
    return quantile(X, q, axis = axis)


def rankdata(X, axis = 0):
    return numpy.apply_along_axis(scipy.stats.rankdata, axis, X)


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
    residuals = b - A @ coefs
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


def pcc_CI(rho, N, alpha = 0.05):
    p = 1
    z = numpy.arctanh(rho)
    z_crit = scipy.stats.norm.ppf([alpha / 2, 1 - alpha / 2])
    z_CI = z[..., numpy.newaxis] + z_crit / numpy.sqrt(N - p - 3)
    return numpy.tanh(z_CI)


def prcc_CI(rho, N, alpha = 0.05):
    return pcc_CI(rho, N, alpha = alpha)
