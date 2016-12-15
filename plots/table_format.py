#!/usr/bin/python3
'''
Make a LaTeX-formatted table from the simulation output.
'''

import locale
import os.path
import sys

import numpy
import pandas

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import common


country_label_replacements = {'United States of America': 'United States',
                              'Democratic Republic of the Congo': 'DR Congo',
                              'Bolivia (Plurinational State of)': 'Bolivia',
                              'Iran (Islamic Republic of)': 'Iran',
                              "Lao People's Democratic Republic": 'Laos',
                              'Republic of Moldova': 'Moldova',
                              'Venezuela (Bolivarian Republic of)': 'Venezuela'
}


def _format_number(x):
    if not numpy.isnan(x):
        return locale.format('%d', x, grouping = True)
    else:
        return '------'


def _format_target(t):
    return t.replace('%', '\%').replace('_', ' ')


def normalize(c):
    x = common.get_country_label(c)
    y = country_label_replacements.get(x, x)
    return y

if __name__ == '__main__':
    locale.setlocale(locale.LC_NUMERIC, 'en_US.utf8')

    df = pandas.read_csv('table.csv',
                         index_col = [0, 1],
                         header = [0, 1, 2])

    countries = common.all_regions_and_countries

    targets = df.index.levels[1]

    with open('table_sub.tex', 'w') as fd:
        colfmt = 'r@{ [\\,}r@{, }r@{\\,] }'
        fd.write('\\begin{{tabu}}{{ll|[3pt]{}|[1.5pt]{}|[1.5pt]{}|[3pt]{}|[1.5pt]{}|[1.5pt]{}|[3pt]}}'.format(
            *(6 * (colfmt, ))))

        fd.write('\\tabucline[3pt]{3-}\n')
        fd.write('\\multicolumn{2}{l|[3pt]}{} & ')
        fd.write('\\multicolumn{9}{c|[3pt]}{\\textbf{As of 2025}} & ')
        fd.write('\\multicolumn{9}{c|[3pt]}{\\textbf{As of 2035}}\n')
        fd.write('\\\\\n')

        fd.write('\\multicolumn{2}{l|[3pt]}{} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{New Infections} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{PLHIV} & ')
        fd.write('\\multicolumn{3}{c|[3pt]}{People with AIDS} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{New Infections} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{PLHIV} & ')
        fd.write('\\multicolumn{3}{c|[3pt]}{People with AIDS}\n')
        fd.write('\\\\\n')

        for (x, c) in enumerate(countries):
            if x == 0:
                fd.write('\\tabucline[3pt]{-}\n')
            else:
                fd.write('\\tabucline[1.5pt]{-}\n')

            for (i, target) in enumerate(targets):
                v = df.loc[(c, target)]

                if i == len(targets) - 1:
                    s = '\\raisebox{{1.5ex}}[0pt]{{\\textbf{{{}}}}} & '
                    fd.write(s.format(normalize(c)))
                else:
                    fd.write(' & ')
                fd.write('{}'.format(_format_target(target)))

                for j in range(len(v) // 3):
                    fd.write(' & {} & {} & {}'.format(
                        *map(_format_number, v[3 * j : 3 * j + 3])))
                fd.write('\n')
                fd.write('\\\\\n')

        fd.write('\\tabucline[3pt]{-}\n')
        fd.write('\\multicolumn{2}{l|[3pt]}{} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{New Infections} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{PLHIV} & ')
        fd.write('\\multicolumn{3}{c|[3pt]}{People with AIDS} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{New Infections} & ')
        fd.write('\\multicolumn{3}{c|[1.5pt]}{PLHIV} & ')
        fd.write('\\multicolumn{3}{c|[3pt]}{People with AIDS}\n')
        fd.write('\\\\\n')

        fd.write('\\multicolumn{2}{l|[3pt]}{} & ')
        fd.write('\\multicolumn{9}{c|[3pt]}{\\textbf{As of 2025}} & ')
        fd.write('\\multicolumn{9}{c|[3pt]}{\\textbf{As of 2035}}\n')
        fd.write('\\\\\n')
        fd.write('\\tabucline[3pt]{3-}\n')

        fd.write('\\end{tabu}\n')
