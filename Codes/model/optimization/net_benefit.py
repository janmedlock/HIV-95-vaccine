'''
Find target values that maximize the net benefit.
'''

import functools
import operator

import joblib
import numpy
from scipy import optimize

from .. import parameters
from .. import simulation


def _objective_function(targets, country, CE_threshold, parameters_,
                        scale = 1):
    sim = simulation.Simulation(country, targets,
                                parameters_ = parameters_,
                                run_baseline = False)
    return - sim.net_benefit(CE_threshold) / scale


def _lower_bound(b, i, x):
    return x[i] - b[0]

def _upper_bound(b, i, x):
    return b[1] - x[i]


def _do_minimize(*args, **kwds):
    '''
    :mod:`multiprocessing` is having trouble with the hess_inv attribute
    of the result.  This function converts that to a dense matrix.
    '''
    res = optimize.minimize(*args, **kwds)

    try:
        res.hess_inv = res.hess_inv.todense()
    except AttributeError:
        pass

    return res
    

def maximize(country, CE_threshold,
             method = 'l-bfgs-b', nruns = 8,
             debug = False, parallel = True):
    '''
    Find the targets that maximize the net benefit in the country.
    
    Valid values for `method`
    are ``'cobyla'``, ``'l-bfgs-b'``, ``'tnc'``, ``'slsqp'``.

    Uses `nruns` random uniform restarts.
    '''
    parameters_ = parameters.Parameters(country)

    # All variables are between 0 and 1.
    bounds = ((0, 1), ) * 3

    # Get an approximate scale to normalize the objective values
    # by running at the lower bounds (0, 0, 0).
    targets0 = [b[0] for b in bounds]
    scale = numpy.abs(_objective_function(targets0,
                                          country,
                                          CE_threshold,
                                          parameters_))

    args = (country, CE_threshold, parameters_, scale)

    options = dict(disp = debug)

    kwds = dict(args = args,
                method = method,
                bounds = bounds,
                options = options)

    # 'cobyla' uses constraint functions instead of box-constraint bounds.
    # 'slsqp' can also use constraints functions
    # instead of box-constraint bounds.
    if method == 'cobyla':
        # Convert bounds into contraint functions.
        constraints = ([dict(type = 'ineq',
                             fun = functools.partial(_lower_bound, b, i))
                        for (i, b) in enumerate(bounds)]
                       + [dict(type = 'ineq',
                               fun = functools.partial(_upper_bound, b, i))
                          for (i, b) in enumerate(bounds)])

        kwds.update(constraints = constraints)
        del kwds['bounds']

        # rhobeg is the first change to the optimization variables.
        # I guess setting this makes the optimization a little faster.
        kwds['options'].update(rhobeg = 0.1)

    # Uniform random starting guesses inside the bounds.
    initial_guesses = numpy.random.uniform(*zip(*bounds),
                                           size = (nruns, len(bounds)))

    if parallel:
        # verbose = 100 if debug else 0
        verbose = 0
        # Parallel, using all available processors.
        with joblib.Parallel(n_jobs = -1, verbose = verbose) as parallel:
            # res = parallel(
            #     joblib.delayed(optimize.minimize)(_objective_function,
            #                                       x0,
            #                                       **kwds)
            #     for x0 in initial_guesses)
            #
            # multiprocessing is having trouble with the sparse hess_inv
            # attribute of the optimization result.
            res = parallel(
                joblib.delayed(_do_minimize)(_objective_function, x0, **kwds)
                for x0 in initial_guesses)
    else:
        res = [optimize.minimize(_objective_function, x0, **kwds)
               for x0 in initial_guesses]

    if debug:
        print('\n\n'.join(map(str, res)))

    # Keep the result of the runs that has the minimum function value.
    best = min(res, key = operator.attrgetter('fun'))

    # Make sure that one actually succeeded in finding the minimum.
    assert best.success, ('The lowest function value is from '
                          + 'a run with res.success = False.')

    targets = best.x

    net_benefit = - best.fun * scale

    sim = simulation.Simulation(country, targets,
                                parameters_ = parameters_)

    return (targets, sim.incremental_net_benefit(CE_threshold))
