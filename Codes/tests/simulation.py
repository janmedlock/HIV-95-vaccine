#!/usr/bin/python3
'''
Test :mod:`model.simulation`.
'''


import sys

sys.path.append('..')
import model


def _main():
    country = 'Nigeria'

    print(country)

    simulation = model.Simulation(
        country,
        '909090',
        targets_kwds = dict(vaccine_target = model.Target(0.5, 5, 5)))

    simulation.plot()


if __name__ == '__main__':
    _main()
