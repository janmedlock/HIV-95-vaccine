#!/usr/bin/python3


if __name__ == '__main__':
    import sys
    sys.path.append('..')

    import model


    country = 'Nigeria'

    parameters = model.Parameters(country)

    print(parameters)
