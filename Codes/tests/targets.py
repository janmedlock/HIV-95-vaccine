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
    targets = model.targets.TargetsVaccine()
    times = [2015, 2020, 2021, 2022, 2023, 2025, 2030]
    target_values = targets(parameters, times)
    print_container(target_values)
    state = numpy.vstack(len(times) * (parameters.mode().initial_conditions, ))
    control_rates = target_values.control_rates(state)
    print_container(control_rates)