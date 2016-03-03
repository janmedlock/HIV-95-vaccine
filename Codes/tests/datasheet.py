#!/usr/bin/python3

'''
Test the loading of data from the datasheet using :mod:`model.datasheet`.
'''

import sys

sys.path.append('..')
import model


def _main():
    country = 'Nigeria'

    parameters = model.Parameters(country)

    print(parameters)


if __name__ == '__main__':
    _main()
