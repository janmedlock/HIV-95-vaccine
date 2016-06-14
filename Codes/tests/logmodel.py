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
    targets = '909090'
    
    parameters = model.Parameters(country).mode()

    time0 = time.time()
    simulation = model.Simulation(parameters, targets,
                                  run_baseline = False,
                                  _use_log = False)
    time1 = time.time()
    print('Non-log model took {} sec.'.format(time1 - time0))

    time0 = time.time()
    simulation_log = model.Simulation(parameters, targets,
                                      run_baseline = False,
                                      _use_log = True)
    time1 = time.time()
    print('Log model took {} sec.'.format(time1 - time0))


    # Ignore differences in the initial conditions.
    maxabserr = numpy.abs(simulation.state - simulation_log.state)[1 : ].max()
    maxrelerr = numpy.ma.divide(
        numpy.abs(simulation.state - simulation_log.state),
        simulation.state).filled(0).max()

    print('Max absolute error = {}'.format(maxabserr))
    print('Max relative error = {}'.format(maxrelerr))



if __name__ == '__main__':
    _main()
