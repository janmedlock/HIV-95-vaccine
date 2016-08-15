#!/usr/bin/python3

import csv
import os.path
import sys

sys.path.append('../Codes')
sys.path.append('../Codes/plots')
import common


def _isurl(x):
    return x.startswith('http')


def _isfloat(x):
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def _format(x):
    if _isurl(x):
        return '\\url{{{}}}'.format(x)
    elif _isfloat(x):
        x = float(x)
        if x > 1:
            fmt = '{:.1f}'
        else:
            fmt = '{:.2g}'
        return '{}\\%'.format(fmt.format(x))
    elif '<' in x:
        return '$<${}'.format(_format(x.replace('<', '')))
    else:
        return x.replace('#', '\\#')


def _format_country(x):
    return common.get_country_label(x, short = True).replace('&', 'and')


def _combine_refs(row, reflen):
    refs = row[- reflen]
    for x in row[- reflen + 1 : ]:
        if x != '':
            refs += ', ' + x
    row[- reflen] = refs
    return row[ : - reflen + 1]


def _fill_empty(row):
    for i in range(len(row)):
        if row[i] == '':
            row[i] = '---'
    return row


def _convert_one(infile, reflen):
    reader = csv.reader(open(os.path.join('data_sources', infile)))
    base, _ = os.path.splitext(infile)
    outfile = '{}.tex'.format(base)
    with open(outfile, 'w') as fd:
        header = next(reader)
        header = _combine_refs(header, reflen)
        fmt = 'l' + ('r' * (len(header) - 2)) + 'l'
        headertex = ('  \\\\[-2ex]\n  \\hline\n'
                     + '  ' + ' & '.join(header) + '\\\\\n'
                     + '  \\hline\n')
        fd.write('\\begin{{longtable}}{{{}}}\n'.format(fmt))
        fd.write('  \\caption{{{}.}}\n'.format(base))
        fd.write('  \\label{{data_source_{}}}\n'.format(base))
        fd.write(headertex)
        fd.write('  \\endfirsthead\n')
        fd.write('  \\caption{(continued)}\n')
        fd.write(headertex)
        fd.write('  \\endhead\n')
        fd.write('  \\hline\n  \\endfoot\n')
        fd.write('  \\endlastfoot\n')
        for row in reader:
            row = [_format(x) for x in row]
            row[0] = _format_country(row[0])
            row = _combine_refs(row, reflen)
            row = _fill_empty(row)
            fd.write('  ' + ' & '.join(row) + '\\\\\n')
        fd.write('  \\hline\n')
        fd.write('  \\multicolumn{1}{l}{NOTES}\n')
        fd.write('\\end{longtable}\n')
        fd.write('\n%%% Local Variables:\n%%% mode: latex\n')
        fd.write('%%% TeX-master: "supplementary_text"\n%%% End:\n')


def _main():
    _convert_one('prevalence.csv', 4)


if __name__ == '__main__':
    _main()
