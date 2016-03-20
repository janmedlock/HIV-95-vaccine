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

    simulation = model.Simulation(country, '909090')

    simulation.plot()


if __name__ == '__main__':
    _main()
