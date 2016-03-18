'''
Run the 90-90-90 policy.
'''

import numpy

from . import cost_effectiveness
from . import datasheet
from . import effectiveness
from . import simulation


class Results:
    '''
    Empty object off of which to hang results.
    '''
    pass


def run909090(country, target = '909090', target_base = 'base', t_end = 15):
    results = Results()

    results.solution = simulation.solve(target,
                                        parameters,
                                        t_end = t_end)

    results.solution_base = simulation.solve(target_base,
                                             parameters,
                                             t_end = t_end)

    print('{}'.format(country))

    return (country, results)
