#!/usr/bin/python3
'''
Map the initial proportions diagnosed, treated, and viral suppressed.
'''

import os.path
import sys

import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model
import mapplot


def _main():
    data = model.datasheet.InitialConditions.get_all()

    countries = data.columns

    # People with HIV.
    nHIV = data.iloc[1 :].sum(0)
    pHIV = nHIV / data.sum(0)


    ###############################
    # Non-overlapping proportions #
    # I.e. should sum to 1.       #
    ###############################
    p = pandas.DataFrame(index = countries)
    p['undiagnosed'] = data.loc[['A', 'U']].sum(0) / nHIV
    p['diagnosed'] = data.loc['D'] / nHIV
    p['treated'] = data.loc['T'] / nHIV
    p['suppressed'] = data.loc['V'] / nHIV


    ##############################################################
    # Proportions of people with HIV with the different statuses #
    # I.e. the treatment cascade.                                #
    # These overlap: treated people are also diagnosed, etc.     #
    ##############################################################
    p_overlapping = pandas.DataFrame(index = countries)
    p_overlapping['all'] = 1
    p_overlapping['diagnosed'] \
        = p[['diagnosed', 'treated', 'suppressed']].sum(1)
    p_overlapping['treated'] = p[['treated', 'suppressed']].sum(1)
    p_overlapping['suppressed'] = p['suppressed']


    # Easy-to-read colors.
    cp = mapplot.seaborn.color_palette('Set1')
    colors = (cp[0], cp[1], cp[4], cp[2])

    m = mapplot.Basemap()

    m.barhs(countries, p_overlapping,
            widthscale = 4.5, heightscale = 1.5, color = colors)

    # Legend
    X, Y = (-158, -30)
    m.rectangle_coords(X - 5.5, Y - 8.5, 87, 14,
                       facecolor = 'white', linewidth = 0.1)
    m.barh_coords(X, Y, [1, 0.9, 0.9 ** 2, 0.9 ** 3],
                  widthscale = 2 * 4.5, heightscale = 2 * 1.5,
                  color = colors)
    labels = ('Proportion Living with HIV (all countries scaled to length 1)',
              'Proportion Diagnosed',
              'Proportion Treated',
              'Proportion with Viral Suppression')
    X_ = X + 6.5
    Y_ = Y - 6
    dY_ = 3
    for (l, c) in zip(labels, colors):
        m.text_coords(X_, Y_, l,
                      fontdict = dict(color = c, size = 4),
                      verticalalignment = 'center',
                      horizontalalignment = 'left')
        Y_ += dY_

    m.tighten()

    common.savefig(m.fig, '{}.pdf'.format(common.get_filebase()))
    common.savefig(m.fig, '{}.png'.format(common.get_filebase()))

    m.show()


if __name__ == '__main__':
    _main()
