#!/usr/bin/python3
'''
Make a PDF with a page of all estimator plots for each country
with data in the IncidencePrevalence datasheet.

`Estimators = None` uses all defined estimators.
'''

import os.path
import sys

from matplotlib.backends import backend_pdf
from matplotlib import pyplot
import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import transmission_rates
sys.path.append('..')
import model
sys.path.append('../plots')
import common

# Here because code to suppress warnings is in common.
import seaborn


countries = model.get_country_list('IncidencePrevalence')


def plot_transmission_rates(Estimator, quantile_level = 0.01, scale = 0.8):
    fig, ax = pyplot.subplots(figsize = (8.5, 11))
    n = len(countries)
    colors = seaborn.color_palette('husl', n)
    for (i, country) in enumerate(countries):
        print(country)
        e = Estimator(country)
        tr = e.parameters.transmission_rates
        # Catch tr = NaN.
        try:
            a, b = tr.ppf([quantile_level / 2, 1 - quantile_level / 2])
            x = numpy.linspace(a, b, 101)
            y = tr.pdf(x) / n * scale
            j = n - 1 - i
            ax.fill_between(x, j + y, j - y,
                            linewidth = 0,
                            facecolor = colors[i],
                            alpha = 0.7)
            ax.scatter(tr.mode, j,
                       marker = '|', s = 30, linewidth = 1,
                       color = 'black')
        except AttributeError:
            pass
    ax.set_xlim(0)
    ax.set_xlabel('Transmission rate (per year)')
    ax.set_ylim(-1.5, n + 0.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(reversed(countries), fontdict = dict(size = 6))
    ax.grid(False, axis = 'y')
    fig.tight_layout()
    fig.savefig('{}.pdf'.format(common.get_filebase()))
    return fig


def plot_all_estimators(Estimators = None):
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            fig = pyplot.figure(figsize = (11, 8.5))
            transmission_rates.plot_all_estimators(country,
                                                   Estimators = Estimators,
                                                   fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    E = transmission_rates.ExponentiallyWeightedLognormal
    # plot_transmission_rates(E)

    plot_all_estimators([E])

    # pyplot.show()
