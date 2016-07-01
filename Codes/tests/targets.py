#!/usr/bin/python3

import sys

import numpy

sys.path.append('..')
import model


def print_container(c):
    print('\n'.join('{} = {}'.format(k, v)
                    for (k, v) in c.items()))


if __name__ == '__main__':
    parameters = model.Parameters('South Africa')
    Targets = model.targets.TargetsVaccine
    targets = Targets(parameters,
                      [2015, 2020, 2025, 2030])
    print_container(targets)
    state = numpy.vstack(4 * (parameters.mode().initial_conditions, ))
    control_rates = targets.control_rates(state)
    print_container(control_rates)
