#!/usr/bin/python3
'''
Test :mod:`model.target`.
'''

import sys

import numpy

sys.path.append('..')
import model


if __name__ == '__main__':
    parameters = model.parameters.Mode.from_country('South Africa')
    target = model.target.Vaccine()
    times = [2015, 2020, 2021, 2022, 2023, 2025, 2030]
    target_values = target(times, parameters)
    print(list(zip(target_values.diagnosed,
                   target_values.treated,
                   target_values.suppressed,
                   target_values.vaccinated)))
    state = numpy.vstack(len(times) * (parameters.initial_conditions, ))
    control_rates = model.control_rates.get(times, state, target, parameters)
    print(control_rates)
