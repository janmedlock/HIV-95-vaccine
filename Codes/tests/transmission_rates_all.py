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

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import transmission_rates
sys.path.append('..')
import model
sys.path.append('../plots')
import common

# Here because code to suppress warnings is in common.
import seaborn


def _main(Estimators = None):
    countries = model.get_country_list('IncidencePrevalence')
    filename = '{}.pdf'.format(common.get_filebase())
    with backend_pdf.PdfPages(filename) as pdf:
        for country in countries:
            print(country)
            fig = pyplot.figure()
            transmission_rates.plot_all_estimators(country,
                                                   Estimators = Estimators,
                                                   fig = fig)
            pdf.savefig(fig)
            pyplot.close(fig)


if __name__ == '__main__':
    _main()
