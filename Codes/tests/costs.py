#!/usr/bin/python3

import numpy

import sys
sys.path.append('..')

import model


country = 'Nigeria'

parameters = model.Parameters(country)

CE_stats = model.solve_and_get_CE_stats('909090',
                                        parameters)

assert all(numpy.isclose(CE_stats,
                         (955467777.79964602, 12129763689.265448)))


CE_stats_base = model.solve_and_get_CE_stats('base',
                                             parameters)

assert all(numpy.isclose(CE_stats_base,
                         (953452134.68817425, 3639328708.8262973)))


ICE_stats = model.get_incremental_CE_stats(*CE_stats, *CE_stats_base,
                                           parameters)

assert all(numpy.isclose(ICE_stats,
                         (2015643.1114717722, 8490434980.4391499,
                          1.3149798404551829)))

# model.print_incremental_CE_stats(*ICE_stats, parameters)
