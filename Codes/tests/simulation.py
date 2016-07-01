#!/usr/bin/python3
'''
Test :mod:`model.simulation`.
'''


import sys

sys.path.append('..')
import model


def _main():
    country = 'South Africa'
    targets = model.Targets909090
    print(country)
    parameters = model.Parameters(country).mode()
    simulation = model.Simulation(parameters, targets)
    simulation.plot()
    return simulation


if __name__ == '__main__':
    s = _main()
