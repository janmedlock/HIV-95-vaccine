#!/usr/bin/python3
'''
Get :math:`R_0` for each country.
'''

import sys

sys.path.append('..')
import model


def _main():
    for country in model.datasheet.get_country_list():
        p = model.parameters.Parameters(country).mode()
        print('{}: R_0 = {:g}'.format(country, p.R0))


if __name__ == '__main__':
    _main()
