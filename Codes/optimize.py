#!/usr/bin/python3

import numpy
from scipy import optimize
import joblib
import operator
import functools

import datasheet
import simulation


def get_net_benefit(qalys, cost, CE_threshold, parameters):
    if CE_threshold == 0:
        # Just cost.
        net_benefit = - cost
    elif CE_threshold == numpy.inf:
        # Just QALYs.
        net_benefit = qalys
    else:
        net_benefit = (
            qalys - (cost / CE_threshold / parameters.GDP_per_capita))

    return net_benefit


def objective_function(target_values, CE_threshold, parameters, scale = 1):
    qalys, cost = simulation.solve_and_get_qalys_and_cost(
        target_values, parameters)

    net_benefit = get_net_benefit(qalys, cost, CE_threshold, parameters)

    return - net_benefit / scale


def lower_bound(b, i, x):
    return x[i] - b[0]

def upper_bound(b, i, x):
    return b[1] - x[i]


def do_minimize(*args, **kwds):
    '''
    multiprocessing is having trouble with the hess_inv attribute
    of the result.  This function converts that to a dense matrix.
    '''
    res = optimize.minimize(*args, **kwds)

    try:
        res.hess_inv = res.hess_inv.todense()
    except AttributeError:
        pass

    return res
    

def maximize_incremental_net_benefit(country, CE_threshold,
                                     method = 'l-bfgs-b', nruns = 8,
                                     debug = False):
    '''
    Find the target_values that maximize the net benefit in the country.
    
    Possible methods are 'cobyla', 'l-bfgs-b', 'tnc', 'slsqp'.

    Uses nruns random uniform restarts.
    '''
    parameters = datasheet.Parameters(country)

    # All variables are between 0 and 1.
    bounds = ((0, 1), ) * 3

    # Get an approximate scale to normalize the objective values.
    scale = objective_function((b[0] for b in bounds),
                               CE_threshold,
                               parameters)

    args = (CE_threshold, parameters, scale)

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
                             fun = functools.partial(lower_bound, b, i))
                        for (i, b) in enumerate(bounds)]
                       + [dict(type = 'ineq',
                               fun = functools.partial(upper_bound, b, i))
                          for (i, b) in enumerate(bounds)])

        kwds.update(constraints = constraints)
        del kwds['bounds']

        # rhobeg is the first change to the optimization variables.
        # I guess setting this makes the optimization a little faster.
        kwds['options'].update(rhobeg = 0.1)

    # Uniform random starting guesses inside the bounds.
    initial_guesses = numpy.random.uniform(*zip(*bounds),
                                           size = (nruns, len(bounds)))

    # Parallel, using all available processors.
    # with joblib.Parallel(n_jobs = -1, verbose = 100 if debug else 0) \
    #      as parallel:
    with joblib.Parallel(n_jobs = -1) as parallel:
        # res = parallel(
        #     joblib.delayed(optimize.minimize)(objective_function,
        #                                       x0,
        #                                       **kwds)
        #     for x0 in initial_guesses)
        #
        # multiprocessing is having trouble with the sparse hess_inv
        # attribute of the optimization result.
        res = parallel(
            joblib.delayed(do_minimize)(objective_function, x0, **kwds)
            for x0 in initial_guesses)

    if debug:
        print('\n\n'.join(map(str, res)))

    # Keep the result of the runs that has the minimum function value.
    best = min(res, key = operator.attrgetter('fun'))

    # Make sure that one actually succeeded in finding the minimum.
    assert best.success, ('The lowest function value is from '
                          + 'a run with res.success = False.')

    target_values = best.x

    net_benefit = - best.fun * scale

    qalys, cost = simulation.solve_and_get_qalys_and_cost(
        target_values, parameters)

    qalys_base, cost_base = simulation.solve_and_get_qalys_and_cost(
        'base', parameters)
    net_benefit_base = get_net_benefit(qalys_base, cost_base,
                                       CE_threshold, parameters)

    incremental_qalys = qalys - qalys_base
    incremental_cost = cost - cost_base
    incremental_net_benefit = net_benefit - net_benefit_base

    return (target_values, incremental_qalys, incremental_cost,
            incremental_net_benefit)


if __name__ == '__main__':
    country = 'India'

    # 0 is just cost.
    # inf is just QALYs.
    # Other values are multiples of per-capita GDP.
    CE_threshold = 1

    (target_values,
     incremental_qalys,
     incremental_cost,
     incremental_net_benefit) = maximize_incremental_net_benefit(
         country,
         CE_threshold,
         method = 'cobyla',
         debug = True)

    print('target values = {}'.format(target_values))
    print('incremental effectiveness = {:g} QALYs gained'.format(
        incremental_qalys))
    print('incremental cost = {:g} USD'.format(incremental_cost))
    print('incremental net benefit = {:g} QALYs'.format(
        incremental_net_benefit))
