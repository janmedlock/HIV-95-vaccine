#!/usr/bin/python3
'''
Test :mod:`model.simulation`.
'''


import sys

sys.path.append('..')
import model


def _main():
    country = 'South Africa'
    targets = model.targets.Vaccine()
    print(country)
    parameters = model.parameters.Parameters(country).mode()
    simulation = model.simulation.Simulation(parameters, targets)
    simulation.plot()
    return simulation


if __name__ == '__main__':
    sim = _main()
