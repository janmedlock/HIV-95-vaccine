#!/usr/bin/python3
'''
Test :mod:`model.simulation`.
'''


import sys

sys.path.append('..')
import model


def _main():
    country = 'South Africa'
    target = model.target.Vaccine()
    parameters = model.parameters.Parameters(country).mode()
    simulation = model.simulation.Simulation(parameters, target)
    simulation.plot()
    return simulation


if __name__ == '__main__':
    sim = _main()
