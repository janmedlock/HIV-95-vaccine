#!/usr/bin/python3
'''
Map the initial proportions diagnosed, treated, and viral suppressed.
'''

import os.path
import sys

import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model
import mapplot


def _main():
    data = model.InitialConditionsSheet.get_all()

    countries = data.columns

    # People with HIV.
    nHIV = data.iloc[1 :].sum(0)
    pHIV = nHIV / data.sum(0)
    for (k, v) in pHIV.items():
        print(k, v)

    m = mapplot.Basemap()

    m.choropleth(countries, pHIV.apply(numpy.log10), cmap = 'Oranges')

    m.tighten()

    m.show()


if __name__ == '__main__':
    _main()
