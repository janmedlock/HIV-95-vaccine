#!/usr/bin/python3
'''
Test the estimation of transmission rates using
:mod:`model.transmission_rate`.
'''

import sys
import warnings

from matplotlib import pyplot
import numpy
import pandas

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
from model import transmission_rate


def test_one(country):
    p = model.Parameters(country)
    transmission_rate.plot(p, show = False)


def build_data_all():
    countries = model.get_country_list('IncidencePrevalence')
    transmission_rates = {}
    transmission_rates_vs_time = {}
    for country in countries:
        print('Estimating transmission rate for {}'.format(country))
        p = model.Parameters(country)
        transmission_rates[country] = transmission_rate.estimate(p)
        transmission_rates_vs_time[country] \
            = transmission_rate.estimate_vs_time(p)
    transmission_rates_vs_time = pandas.DataFrame(transmission_rates_vs_time)
    return (transmission_rates, transmission_rates_vs_time)


def plot_all(transmission_rates, transmission_rates_vs_time):
    country_replacements = {'Democratic Republic of the Congo': 'DR Congo',
                            'Republic of Congo': 'Rep of Congo',
                            'The Bahamas': 'Bahamas',
                            'United Kingdom': 'UK',
                            'United States of America': 'USA'}

    # Convert keys for later sorting.
    transmission_rates_ = {}
    for country in transmission_rates.keys():
        country_ = country_replacements.get(country, country)
        transmission_rates_[country_] = transmission_rates[country]

    # Add ' (N = {})' to the country name for plot labels.
    labels = []
    for country in transmission_rates_vs_time.columns:
        country_ = country_replacements.get(country, country)
        labels.append('{} (N = {})'.format(
            country_,
            len(transmission_rates_vs_time[country].dropna())))
    # Make a copy since I'm messing with the indices
    # for the plot labels.
    transmission_rates_vs_time_ = transmission_rates_vs_time.copy()
    transmission_rates_vs_time_.columns = labels
    transmission_rates_vs_time_.sort_index(axis = 1, inplace = True)

    fig, ax = pyplot.subplots(figsize = (8.5, 11))
    seaborn.violinplot(data = transmission_rates_vs_time_,
                       cut = 0,
                       inner = 'stick',
                       scale = 'count',
                       orient = 'h',
                       ax = ax)
    median = []
    err = []
    for k in sorted(transmission_rates_.keys()):
        T = transmission_rates_[k]
        m = T.median()
        q = T.ppf([0.25, 0.75])
        median.append(m)
        err.append([m - q[0], q[1] - m])
    ax.errorbar(median, range(len(median)),
                xerr = numpy.array(err).T,
                linestyle = 'none',
                marker = 'o',
                markersize = 5,
                markeredgewidth = 1.5,
                markeredgecolor = 'black',
                markerfacecolor = 'none',
                ecolor = 'black',
                elinewidth = 1.5)
    ax.set_xlabel('Transmission rate (per year)')
    ax.set_ylabel('')
    fig.tight_layout()
    fig.savefig('transmission_rates.pdf')
    return (fig, ax)


def test_all():
    transmission_rates, transmission_rates_vs_time = build_data_all()
    (fig, ax) = plot_all(transmission_rates, transmission_rates_vs_time)
    return (fig, ax)


if __name__ == '__main__':
    # country = 'South Africa'
    # test_one(country)
    (fig, ax) = test_all()
    pyplot.show()
