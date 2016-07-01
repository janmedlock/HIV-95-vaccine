#!/usr/bin/python3
'''
Test the loading of data from the datasheet using :mod:`model.datasheet`.
'''

import sys

sys.path.append('..')
import model


def test_one(country):
    '''
    Test loading one country's data from the datasheet.
    '''
    parameters = model.Parameters(country).mode()

    print(parameters)


def test_all():
    '''
    Test loading all data from the datasheet.
    '''
    for country in model.get_country_list():
        print(country)
        model.Parameters(country)


def _main():
    test_one('South Africa')
    
    test_all()


if __name__ == '__main__':
    _main()
