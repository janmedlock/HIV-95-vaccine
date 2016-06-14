#!/usr/bin/python3
'''
Preliminary tests for fitting incidence.
'''

import sys
import warnings

from matplotlib import pyplot
import numpy

# Silence warnings from matplotlib trigged by seaborn.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

sys.path.append('..')
import model

def _main():
    p = model.Parameters('South Africa').mode()

    s = model.Simulation(p, 'baseline',
                         t_end = -25,
                         run_baseline = False,
                         _use_log = False,
                         integrator = 'dop853')
    s.incidence = numpy.diff(s.new_infections) / numpy.diff(s.t)
    s.incidence_per_capita = s.incidence / s.alive[...,  : -1]

    fig, ax = pyplot.subplots()
    ax.scatter(p.incidence.index, p.incidence)
    ax.plot(s.t[ : -1] + 2015, s.incidence_per_capita)
    ax.set_ylabel('Incidence per capita')
    ax.set_ylim(0, max(p.incidence) * 1.5)

    pyplot.show()

    return s


if __name__ == '__main__':
    s = _main()
