#!/usr/bin/python3
'''
Plot the effectiveness of interventions in all countries.
'''

import os.path
import sys

from matplotlib import pyplot
from matplotlib.backends import backend_pdf

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
import effectiveness
sys.path.append('..')
import model


def plot_all(**kwargs):
    with model.results.samples.stats.open_() as results:
        filename = '{}.pdf'.format(common.get_filebase())
        with backend_pdf.PdfPages(filename) as pdf:
            for region_or_country in common.all_regions_and_countries:
                print(region_or_country)
                fig = effectiveness._plot_one(results,
                                              region_or_country,
                                              **kwargs)
                pdf.savefig(fig)
                pyplot.close(fig)

    common.pdfoptimize(filename)
    # Use pdftk to add author etc.
    common.pdf_add_info(filename, Author = common.author)


if __name__ == '__main__':
    plot_all()
