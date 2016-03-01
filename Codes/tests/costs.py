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
                         (955467770.93036532, 12129758069.573009)))


CE_stats_base = model.solve_and_get_CE_stats('base',
                                             parameters)

assert all(numpy.isclose(CE_stats_base,
                         (953452163.1009798, 3639335661.0555468)))


ICE_stats = model.get_incremental_CE_stats(*CE_stats, *CE_stats_base,
                                           parameters)

assert all(numpy.isclose(ICE_stats,
                         (2015607.829385519, 8490422408.5174627,
                          1.3150009112952812)))

# model.print_incremental_CE_stats(*ICE_stats, parameters)
