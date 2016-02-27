#!/usr/bin/python3

import sys
sys.path.append('..')

import model


country = 'Nigeria'

parameters = model.Parameters(country)

print(parameters)
