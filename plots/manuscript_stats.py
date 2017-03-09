#!/usr/bin/python3
'''
Generate the numbers in the manuscript text.
'''

import collections.abc
import os.path
import sys

import numpy

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common
sys.path.append('..')
import model


_vac_str = str(model.target.Vaccine())
_i = _vac_str.index('+')
_vac_str = _vac_str[_i + 2 : ]


def _convert_target(target):
    if not target.startswith('VS:'):
        parameters_type = 'sample'
        target = target.replace('SQ', 'Status Quo')
        target = target.replace('90', '90–90–90')
        target = target.replace('95', '95–95–95')
        target = target.replace('+V', ' + ' + _vac_str)
    else:
        parameters_type = 'mode'
        i = target.find('+')
        if i == -1:
            treatment_target = target[3 : ]
            rest = []
        else:
            treatment_target = target[3 : i]
            rest = target[i + 3 : -1]
            if rest == '':
                rest = []
            else:
                rest = rest.split(',')
        if treatment_target == 'SQ':
            treatment_target = model.target.StatusQuo
        elif treatment_target == '90':
            treatment_target = model.target.UNAIDS90
        elif treatment_target == '95':
            treatment_target = model.target.UNAIDS95
        kwds = {'treatment_target': treatment_target}
        for x in rest:
            k, v = x.split('=')
            v = float(v)
            if int(v) == v:
                v = int(v)
            kwds[k] = v
        if i != -1:
            target = model.target.Vaccine(**kwds)
        else:
            target = treatment_target()
    return (target, parameters_type)


def _load(loc, target, parameters_type = 'sample'):
    if (isinstance(target, collections.abc.Iterable)
        and not isinstance(target, str)):
        return [_load(loc, t) for t in target]
    else:
        target, parameters_type = _convert_target(target)
        return model.results.load(loc, target,
                                  parameters_type = parameters_type)


def _get_stat(res, stat, year = 2035):
    if isinstance(res, collections.abc.Iterable):
        return [_get_stat(r, stat, year) for r in res]
    else:
        return getattr(res, stat)[..., common.t == year]


def _print_summaries(x, scale, prec):
    if scale == 'M':
        x /= 1e6
    elif scale == 'k':
        x /= 1e3
    elif scale == '%':
        x *= 100
    elif scale is None:
        scale = ''
    elif scale != '':
        raise ValueError("Unknown scale '{}'.".format(scale))
    if len(x) == 1:
        print('{:.{prec}f}{}'.format(x[0], scale, prec = prec))
    else:
        summaries = numpy.percentile(x, [50, 25, 75])
        strs = ('{:.{prec}f}{}'.format(v, scale, prec = prec)
                for v in summaries)
        print('{} [{}, {}]'.format(*strs))


def print_stat(loc, target, stat, scale, prec = 0):
    res = _load(loc, target)
    x = _get_stat(res, stat)
    _print_summaries(x, scale, prec)


def print_diff(loc, targets, stat, scale, prec = 0):
    res = _load(loc, targets)
    x = _get_stat(res, stat)
    _print_summaries(x[0] - x[1], scale, prec)


def print_rdiff(loc, targets, stat, prec = 0, mult = 1):
    res = _load(loc, targets)
    x = _get_stat(res, stat)
    _print_summaries(mult * (x[1] - x[0]) / x[0], '%', prec)

def print_rimp(loc, targets, stat, prec = 0):
    res = _load(loc, targets)
    x = _get_stat(res, stat)
    _print_summaries((x[2] - x[0]) / (x[1] - x[0]), '', prec)


def _main():
    print('{} countries'.format(len(common.all_countries)))
    print_stat('Global', 'SQ', 'new_infections', 'M')
    print_diff('Global', ['SQ', '95'], 'new_infections', 'M')
    print_diff('Global', ['95', '95+V'], 'new_infections', 'M', 1)
    print()

    print_diff('Global', ['SQ', '90'], 'new_infections', 'M')
    print_diff('Global', ['90', '95'], 'new_infections', 'M', 1)
    print_diff('Global', ['SQ', 'SQ+V'], 'new_infections', 'M')
    print_diff('Global', ['SQ', '95+V'], 'new_infections', 'M')
    print()

    print_diff('Eastern and Southern Africa', ['SQ', 'SQ+V'],
               'new_infections', 'M', 1)
    print_diff('Eastern and Southern Africa', ['SQ', '95+V'],
               'new_infections', 'M', 1)
    print_diff('North America', ['SQ', 'SQ+V'], 'new_infections', 'k', 0)
    print_diff('North America', ['SQ', '95+V'], 'new_infections', 'k', 0)
    print()

    print_rdiff('Swaziland', ['SQ', '90'], 'infected', 0, -1)
    print_rdiff('Swaziland', ['SQ', '95'], 'infected', 0, -1)
    print_rdiff('India', ['SQ', '90'], 'infected', 0)
    print_rdiff('India', ['SQ', '95'], 'infected', 0)
    print()

    print_rdiff('Global', ['SQ', 'SQ+V'], 'infected', 0, -1)
    print_rdiff('Global', ['SQ', 'SQ+V'], 'dead', 0, -1)
    print_rdiff('Global', ['SQ', '95+V'], 'infected', 0, -1)
    print_rdiff('Global', ['SQ', '95+V'], 'dead', 0, -1)
    print_rdiff('United States of America', ['SQ', '95'],
                'incidence_per_capita', 0, -1)
    print_rdiff('United States of America', ['SQ', '95+V'],
                'incidence_per_capita', 0, -1)
    print()

    print_diff('Global', ['VS:SQ', 'VS:SQ+V()'], 'new_infections', 'M', 1)
    print_diff('Global', ['VS:SQ', 'VS:SQ+V(time_to_start=2025)'],
               'new_infections', 'M', 1)
    print_diff('Global', ['VS:SQ', 'VS:SQ+V(time_to_fifty_percent=5)'],
               'new_infections', 'M', 1)
    print_diff('Global', ['VS:SQ', 'VS:SQ+V(coverage=0.5)'],
               'new_infections', 'M', 1)
    print_diff('Global', ['VS:SQ', 'VS:SQ+V(coverage=0.9)'],
               'new_infections', 'M', 1)
    print_diff('Global', ['VS:SQ', 'VS:SQ+V(efficacy=0.3)'],
               'new_infections', 'M', 1)
    print_diff('Global', ['VS:SQ', 'VS:SQ+V(efficacy=0.7)'],
               'new_infections', 'M', 1)
    print()

    print_rdiff('Rwanda', ['SQ', '95'], 'new_infections', 0, -1)
    print_rdiff('Rwanda', ['SQ', 'SQ+V'], 'new_infections', 0, -1)
    print_rdiff('South Africa', ['SQ', '95'], 'new_infections', 0, -1)
    print_rdiff('South Africa', ['SQ', 'SQ+V'], 'new_infections', 0, -1)
    print_rimp('Rwanda', ['SQ', '95', 'SQ+V'], 'new_infections', 1)
    print_rimp('South Africa', ['SQ', '95', 'SQ+V'], 'new_infections', 1)
    print()

    print_diff('Global', ['SQ', 'SQ+V'], 'new_infections', 'M', 1)


if __name__ == '__main__':
    _main()
