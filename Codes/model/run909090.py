'''
Run the 90-90-90 policy.
'''

import numpy

from . import datasheet
from . import simulation


class Results:
    '''
    Empty object off of which to hang results.
    '''
    pass


def run909090(country, target = '909090', target_base = 'base', t_end = 15,
              debug = True):
    results = Results()

    parameters = datasheet.Parameters(country)

    results.solution = simulation.solve(target,
                                        parameters,
                                        t_end = t_end)

    results.solution_base = simulation.solve(target_base,
                                             parameters,
                                             t_end = t_end)

    if debug:
        print('{}'.format(country))

    return results
