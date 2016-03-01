#!/usr/bin/python3

import numpy
import time

import sys
sys.path.append('..')

import model


country = 'Nigeria'

parameters = model.Parameters(country)

time0 = time.time()
t, state = model.solve('909090', parameters, use_log = False)
time1 = time.time()
print('Non-log model took {} sec.'.format(time1 - time0))

time0_ = time.time()
t_, state_ = model.solve('909090', parameters, use_log = True)
time1_ = time.time()
print('Log model took {} sec.'.format(time1_ - time0_))


# Ignore differences in the initial conditions.
maxabserr = numpy.abs(state - state_)[1 : ].max()
maxrelerr = (numpy.abs(state - state_) / state)[1 : ].max()

print('Max absolute error = {}'.format(maxabserr))
print('Max relative error = {}'.format(maxrelerr))
