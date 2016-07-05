#!/usr/bin/python3
'''
Test :mod:`model.simulation`.
'''


import cProfile
import sys

sys.path.append('..')
import model


def _main():
    country = 'South Africa'
    targets = model.TargetsVaccine()
    parameters = model.Parameters(country).mode()
    simulation = model.Simulation(parameters, targets)
    return simulation


if __name__ == '__main__':
    cProfile.run('_main()', sort = 'tottime')
