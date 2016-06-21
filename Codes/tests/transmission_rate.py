#!/usr/bin/python3
'''
Test the estimation of transmission rates using
:mod:`model.transmission_rate`.
'''

import sys
import warnings

from matplotlib import pyplot
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
    
    transmission_rates = pandas.Series(index = countries)
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

    # Add ' (N = {})' to the country name for plot labels.
    labels = []
    for country, vals in transmission_rates_vs_time.items():
        labels.append('{} (N = {})'.format(
            country_replacements.get(country, country),
            len(vals.dropna())))

    # Make copies since I'm messing with the indices
    # for the plot labels.
    transmission_rates_ = transmission_rates.copy()
    transmission_rates_vs_time_ = transmission_rates_vs_time.copy()
    transmission_rates_.index = labels
    transmission_rates_vs_time_.columns = labels
    transmission_rates_.sort_index(inplace = True)
    transmission_rates_vs_time_.sort_index(axis = 1, inplace = True)

    fig, ax = pyplot.subplots(figsize = (8.5, 11))
    seaborn.violinplot(data = transmission_rates_vs_time_,
                       cut = 0,
                       inner = 'stick',
                       scale = 'count',
                       orient = 'h',
                       ax = ax)
    ax.plot(transmission_rates_, range(len(transmission_rates_)),
            linestyle = 'none', marker = 'o', markersize = 5,
            markeredgewidth = 1.5, markeredgecolor = 'black',
            markerfacecolor = 'none')
    ax.set_xlabel('Transmission rate (per year)')
    ax.set_ylabel('')
    fig.tight_layout()
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
