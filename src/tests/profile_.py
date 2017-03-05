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
    target = model.target.Vaccine()
    parameters = model.parameters.Mode.from_country(country)
    simulation = model.simulation.Simulation(parameters, target)
    return simulation


if __name__ == '__main__':
    cProfile.run('_main()', sort = 'tottime')
