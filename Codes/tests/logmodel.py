#!/usr/bin/python3
'''
Test solving the log model :func:`model.simulation.ODEs_log`
versus the non-log model :func:`model.simulation.ODEs`
for correctness and speed.
'''

import sys
import time

import numpy

sys.path.append('..')
import model


def _main():
    country = 'Nigeria'

    parameters = model.Parameters(country)

    time0 = time.time()
    solution = model.solve('909090', parameters, use_log = False)
    time1 = time.time()
    print('Non-log model took {} sec.'.format(time1 - time0))

    time0 = time.time()
    solution_log = model.solve('909090', parameters, use_log = True)
    time1 = time.time()
    print('Log model took {} sec.'.format(time1 - time0))


    # Ignore differences in the initial conditions.
    maxabserr = numpy.abs(solution.state - solution_log.state)[1 : ].max()
    maxrelerr = (numpy.abs(solution.state - solution_log.state)
                 / solution.state)[1 : ].max()

    print('Max absolute error = {}'.format(maxabserr))
    print('Max relative error = {}'.format(maxrelerr))



if __name__ == '__main__':
    _main()
