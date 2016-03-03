#!/usr/bin/python3

'''
Map the initial proportions diagnosed, treated, and viral suppressed.
'''

import pandas

import model
import mapplot


def _main():
    data = model.read_all_initial_conditions()

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
    p['suppressed'] = data['Virally suppressed'] / nHIV


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

    # Two rows & two columns of choropleths to show
    # 4 different values for each country.
    # nrows = 2
    # ncols = 2
    # mapplot.pyplot.clf()
    # for i in range(p.shape[-1]):
    #     height = 1 / nrows
    #     width = 1 / ncols
    #     left = (i % ncols) * width
    #     bottom = (1 - i // nrows) * height
    #     m = mapplot.Basemap(rect = (left, bottom, height, width))
    #     m.choropleth(countries, p.iloc[:, i],
    #                  vmin = 0, vmax = 1)

    # m.pies(countries, p, s = 35, colors = colors)

    # m.stars(countries, p_overlapping, scale = 5, color = 'green')

    # m.bars(countries, p_overlapping,
    #        widthscale = 1.5, heightscale = 4.5, color = colors)
    m.barhs(countries, p_overlapping,
            widthscale = 4.5, heightscale = 1.5, color = colors)
    # m.barhls(countries, p_overlapping,
    #          widthscale = 4.5, heightscale = 1.5, color = colors)

    # m.pyramids(countries, p_overlapping,
    #            widthscale = 6, heightscale = 1.5, color = colors)


    mapplot.pyplot.show()


if __name__ == '__main__':
    _main()
