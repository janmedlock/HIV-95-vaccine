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
from matplotlib import ticker
import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import transmission_rate
sys.path.append('..')
import model
sys.path.append('../plots')
import common

# Here because code to suppress warnings is in common.
import seaborn


countries = model.get_country_list('IncidencePrevalence')


def plot_transmission_rate(Estimator, quantile_level = 0.01, scale = 0.8):
    fig, ax = pyplot.subplots(figsize = (8.5, 11))
    n = len(countries)
    colors = seaborn.color_palette('husl', n)
    for (i, country) in enumerate(countries):
        # Plot from top instead of bottom.
        j = n - 1 - i
        print(country)
        e = Estimator(country)
        tr = e.parameters.transmission_rate
        # Catch tr = NaN.
        try:
            a, b = tr.ppf([quantile_level / 2, 1 - quantile_level / 2])
        except AttributeError:
            pass
        else:
            x = numpy.linspace(a, b, 101)
            y = tr.pdf(x) / n * scale
            ax.fill_between(x, j + y, j - y,
                            linewidth = 0,
                            facecolor = colors[i],
                            alpha = 0.7)
        try:
            pts = tr.mode
        except AttributeError:
            pts = tr
        finally:
            ax.scatter(pts, j,
                       marker = '|', s = 30, linewidth = 1,
                       color = 'black')
    ax.set_xlabel('Transmission rate (per year)')
    ax.set_xlim(left = 0)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.set_ylim(-1.5, n + 0.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels(reversed(countries), fontdict = dict(size = 6))
    ax.grid(False, axis = 'y')
    fig.tight_layout()
    return fig, ax


def plot_all_estimators(Estimators = None):
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        fig = None
        for E in Estimators:
            fig, ax = plot_transmission_rate(E)
            ax.set_title(E.__name__)
            pdf.savefig(fig)

        for country in countries:
            print(country)
            fig = pyplot.figure(figsize = (11, 8.5))
            transmission_rate.plot_all_estimators(country,
                                                  Estimators = Estimators,
                                                  fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


def plot_all_countries(Estimator):
    return plot_all_estimators([Estimator])


if __name__ == '__main__':
    # E = transmission_rate.EWLognormal
    # plot_transmission_rate(E)
    # plot_all_countries(E)

    plot_all_estimators([transmission_rate.Rakai,
                         transmission_rate.EWLognormal])

    # pyplot.show()
