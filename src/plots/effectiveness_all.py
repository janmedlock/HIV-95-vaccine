#!/usr/bin/python3
'''
Plot the effectiveness of interventions in all countries.
'''

import os.path
import sys
import unicodedata

import matplotlib
from matplotlib import pyplot

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
import effectiveness


# [H] requires \usepackage{float}
template = r'''
\begin{{figure}}[H]
  \centering
  \input{{{figfile:}}}
  \caption{{{region_or_country:} model outcomes under the different
    diagnosis, treatment, and vaccination scenarios.  Central curves
    show the medians over model runs with 1000 samples from parameter
    distributions, shaded regions show the 1st and 3rd quartiles
    (i.e.~25th and 75th percentiles), and vertical bars to the right of
    each axis show the 5th and 95th percentiles at the end time, 2035.
    Regional and global outcomes were aggregated from the country-level
    model outcomes.}}
  \label{{effectiveness_{base:}}}
\end{{figure}}
'''


fontsize = 8
matplotlib.rc('font', size = fontsize)
matplotlib.rc('figure', titlesize = fontsize + 1)
matplotlib.rc('axes', titlesize = fontsize + 1,
              labelsize = fontsize + 1)
matplotlib.rc('xtick', labelsize = fontsize - 1)
matplotlib.rc('ytick', labelsize = fontsize - 1)
matplotlib.rc('legend', fontsize = fontsize)


def _get_filebase(country):
    # Remove spaces.
    retval = country.replace(' ', '_')
    # Remove single quotes.
    retval = retval.replace("'", '')
    # Remove accents.
    retval = ''.join(c for c in unicodedata.normalize('NFKD', retval)
                     if not unicodedata.combining(c))
    return retval


def plot_all(plotevery = 10, **kwargs):
    path = common.get_filebase()
    for region_or_country in common.all_regions_and_countries:
        print(region_or_country)
        fig = effectiveness.plot_one(region_or_country,
                                     plotevery = plotevery,
                                     **kwargs)
        filebase = _get_filebase(region_or_country)
        filename = os.path.join(path, '{}.pgf'.format(filebase))
        common.savefig(fig, filename)
        pyplot.close(fig)


def combine(prefix = '../src/plots'):
    path = common.get_filebase()
    outfile = os.path.join(path, 'all.tex')
    with open(outfile, 'w') as fd:
        isfirst = True
        for region_or_country in common.all_regions_and_countries:
            filebase = _get_filebase(region_or_country)
            filename = os.path.join(prefix, path,
                                    '{}.pgf'.format(filebase))
            filename = os.path.normpath(filename)
            if isfirst:
                isfirst = False
            else:
                fd.write('\n')
            fd.write(template[1 : ].format(
                figfile = filename,
                base = filebase,
                region_or_country = region_or_country))


if __name__ == '__main__':
    plot_all()
    combine()
