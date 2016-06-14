#!/usr/bin/python3
'''
Get :math:`R_0` for each country.
'''

import sys

sys.path.append('..')
import model


def _main():
    for country in model.get_country_list():
        p = model.Parameters(country).mode()
        print('{}: R_0 = {:g}'.format(country, p.R0))


if __name__ == '__main__':
    _main()
