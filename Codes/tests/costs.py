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
                         (955467777.4644835, 12706118534.633265)))


CE_stats_base = model.solve_and_get_CE_stats('base',
                                             parameters)

assert all(numpy.isclose(CE_stats_base,
                         (953452147.986305, 3652246123.4073505)))


ICE_stats = model.get_incremental_CE_stats(*CE_stats, *CE_stats_base,
                                           parameters)

assert all(numpy.isclose(ICE_stats,
                         (2015629.4781785011, 9053872411.225914,
                          1.4022532713128841)))

# model.print_incremental_CE_stats(*ICE_stats, parameters)
