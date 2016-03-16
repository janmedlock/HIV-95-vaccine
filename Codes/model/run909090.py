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


def run909090(country, t_end = 15):
    results = Results()

    results.parameters = datasheet.Parameters(country)

    results.target = '909090'

    results.t, results.state = simulation.solve(results.target,
                                                results.parameters,
                                                t_end = t_end)

    results.target_base = 'base'

    _, results.state_base = simulation.solve(results.target_base,
                                             results.parameters,
                                             t_end = t_end)

    print('{}'.format(country))

    return (country, results)
