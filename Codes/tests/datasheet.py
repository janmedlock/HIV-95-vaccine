#!/usr/bin/python3

'Test the loading of data from the datasheet using :mod:`model.datasheet`.'


if __name__ == '__main__':
    import sys
    sys.path.append('..')

    import model


    country = 'Nigeria'

    parameters = model.Parameters(country)

    print(parameters)
