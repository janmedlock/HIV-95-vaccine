#!/usr/bin/python3
'''
Profile :mod:`model.simulation`.
'''


import cProfile
import sys

sys.path.append('..')
import model


def _main():
    country = 'South Africa'
    targets = model.targets.Vaccine()
    parameters = model.parameters.Parameters(country).mode()
    simulation = model.simulation.Simulation(parameters, targets)
    return simulation


if __name__ == '__main__':
    cProfile.run('_main()', sort = 'tottime')
