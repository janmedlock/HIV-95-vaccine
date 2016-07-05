#!/usr/bin/python3
'''
Plot new infections.
'''

import pickle
import sys

from matplotlib import gridspec
from matplotlib import lines
from matplotlib import pyplot
from matplotlib import ticker
import numpy

sys.path.append('..')
import common
# import seaborn
import seaborn_quiet as seaborn
sys.path.append('../..')
import model


countries_to_plot = (
    'United States of America',
    'India',
    'Haiti',
    'Rwanda',
    'South Africa',
    'Uganda',
    'Global',
)


keys_ordered = (
    ('baseline', 0),
    ('baseline', 0.75, 0.5, 5, 2),
    # ('baseline', 0.75, 0.5, 5, 5),
    ('909090', 0),
    ('909090', 0.75, 0.5, 5, 2),
    # ('909090', 0.75, 0.5, 5, 5)
)


linestyles = {'baseline': 'dashed',
              '909090': 'solid'}
cp = seaborn.color_palette('colorblind')
colors = {(0, ): cp[2],
          (0.75, 0.5, 5, 2): cp[0],
          (0.75, 0.5, 5, 5): cp[1]}
# cp = seaborn.color_palette('Dark2')
# colors = {(0, ): cp[1],
#           (0.75, 0.5, 5, 2): cp[0]}
styles = {(kl, ) + kc: dict(linestyle = vl, color = vc)
          for (kl, vl) in linestyles.items()
          for (kc, vc) in colors.items()}


def getlabel(k):
    if k[0] == 'baseline':
        label = 'Status quo'
    elif k[0] == '909090':
        label = '90–90–90'
    else:
        raise ValueError
    if k[1] > 0:
        label += ' + vaccine'
    return label


def getfield(results, field):
    retval = {}
    for (k, v) in results.items():
        t = v.t
        if field == 'incidence':
            ni = numpy.asarray(v.new_infections)
            retval[k] = numpy.diff(ni) / numpy.diff(t)
        elif field == 'incidence_per_capita':
            ni = numpy.asarray(v.new_infections)
            n = numpy.asarray(v.alive)
            retval[k] = numpy.diff(ni) / numpy.diff(t) / n[..., 1 :]
        elif field.endswith('_per_capita'):
            field_ = field.replace('_per_capita', '')
            x = numpy.asarray(getattr(v, field_))
            n = numpy.asarray(v.alive)
            retval[k] = x / n
        else:
            retval[k] = getattr(v, field)
    if field.startswith('incidence'):
        t = t[1 : ]
    return (t, retval)


def build_global(results):
    global_ = {}
    for (c, r) in results.items():
        for (k, v) in r.items():
            if k not in global_:
                global_[k] = model.global_._GlobalSuper()
                global_[k].t = v.t
            for j in global_[k].keys():
                global_[k]._add(j, v)
    for v in global_.values():
        v._normalize()
    return global_


def plotcell(ax, tx,
             scale = 1, percent = False,
             xlabel = None, ylabel = None, title = None, legend = True):
    t, x = tx

    if percent:
        scale = 1 / 100
    elif scale == 'auto':
        if max(max(x) for x in stats.values()) > 1e6:
            scale = 1e6
        else:
            scale = 1e3

    for k in keys_ordered:
        v = x[k]
        ax.plot(t, v / scale, label = getlabel(k),
                **styles[k])

    ax.set_xlim(t[0], t[-1])
    ax.grid(True, which = 'both', axis = 'both')
    # Every 10 years.
    ax.set_xticks(range(int(t[0]), int(t[-1]), 10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins = 5))
    ax.tick_params(labelsize = 'large')
    if percent:
        ax.yaxis.set_major_formatter(common.PercentFormatter())
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel, size = 'x-large')
    if title is not None:
        ax.set_title(title, size = 'x-large')
    if legend:
        ax.legend(loc = 'upper left')


def plot_selected(results):
    fig = pyplot.figure(figsize = (24, 12))
    
    gs = gridspec.GridSpec(5, len(countries_to_plot),
                           height_ratios = ((1, ) * 4
                                            + (0.1, )))
    for (i, country) in enumerate(countries_to_plot):
        if country == 'Global':
            r = build_global(results)
        else:
            r = results[country]

        if country == 'United States of America':
            title = 'United States'
        else:
            title = country

        axis = fig.add_subplot(gs[0, i])
        plotcell(axis,
                 getfield(r, 'infected'),
                 scale = 1e6,
                 # legend = (i == 0),
                 legend = False,
                 ylabel = ('People Living with HIV\n(M)'
                           if (i == 0) else None),
                 title = title)
        axis.tick_params(labelbottom = False)

        axis = fig.add_subplot(gs[1, i])
        plotcell(axis,
                 getfield(r, 'AIDS'),
                 scale = 1e3,
                 legend = False,
                 ylabel = ('People with AIDS\n(1000s)'
                           if (i == 0) else None))
        axis.tick_params(labelbottom = False)

        axis = fig.add_subplot(gs[2, i])
        plotcell(axis,
                 getfield(r, 'incidence_per_capita'),
                 scale = 1e-6,
                 legend = False,
                 ylabel = ('HIV Incidence\n(per M people per y)'
                           if (i == 0) else None))
        axis.tick_params(labelbottom = False)

        axis = fig.add_subplot(gs[3, i])
        plotcell(axis,
                 getfield(r, 'prevalence'),
                 percent = True,
                 legend = False,
                 ylabel = ('HIV Prevelance\n'
                           if (i == 0) else None))

    lines_ = [lines.Line2D([0], [0], **styles[k])
              for k in keys_ordered]
    labels = [getlabel(k) for k in keys_ordered]
    axis = fig.add_subplot(gs[-1, :], axis_bgcolor = 'none')
    axis.tick_params(labelbottom = False, labelleft = False)
    axis.grid(False)
    axis.legend(lines_, labels,
                loc = 'center',
                ncol = len(labels),
                frameon = True,
                fontsize = 'x-large')

    fig.tight_layout()

    fig.savefig('{}.pdf'.format(common.get_filebase()))
    fig.savefig('{}.png'.format(common.get_filebase()))


if __name__ == '__main__':
    results = pickle.load(open('results.pkl', 'rb'))

    plot_selected(results)

    pyplot.show()
