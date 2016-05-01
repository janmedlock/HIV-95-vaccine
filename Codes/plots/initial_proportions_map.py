#!/usr/bin/python3
'''
Map the initial proportions diagnosed, treated, and viral suppressed.
'''

import os.path
import sys

import pandas

sys.path.append('..')
import model
sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import mapplot


def _main():
    data = model.InitialConditionSheet.read_all()

    countries = data.index

    # People with HIV.
    nHIV = data.iloc[:, 1 : ].sum(1)
    pHIV = nHIV / data.sum(1)


    ###############################
    # Non-overlapping proportions #
    # I.e. should sum to 1.       #
    ###############################
    p = pandas.DataFrame(index = countries)
    p['undiagnosed'] = data['Undiagnosed'] / nHIV
    p['diagnosed'] = data['Diagnosed but not on treatment'] / nHIV
    p['treated'] = data['Treated but not virally suppressed'] / nHIV
    p['suppressed'] = data['Virally Suppressed'] / nHIV


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
    X, Y = (-155, -30)
    m.rectangle_coords(X - 5.5, Y - 7, 78, 14,
                       facecolor = 'white', linewidth = 0.1)
    m.barh_coords(X, Y, [1, 0.9, 0.9 ** 2, 0.9 ** 3],
                  widthscale = 2 * 4.5, heightscale = 2 * 1.5,
                  color = colors)
    labels = ('Proportion Living with HIV (all countries scaled to length 1)',
              'Proportion Diagnosed',
              'Proportion Treated',
              'Proportion with Viral Suppression')
    X_ = X + 6.5
    Y_ = Y - 4.5
    dY_ = 3
    for (l, c) in zip(labels, colors):
        m.text_coords(X_, Y_, l,
                      fontdict = dict(color = c, size = 4),
                      verticalalignment = 'center',
                      horizontalalignment = 'left')
        Y_ += dY_

    m.tighten()

    m.savefig('{}.pdf'.format(os.path.splitext(__file__)))

    m.show()


if __name__ == '__main__':
    _main()
