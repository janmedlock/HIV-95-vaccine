#!/usr/bin/python3
'''
Check the countries in the datasheet to see what data they have missing.
'''

import pandas

import model.datasheet


if __name__ == '__main__':
    wb = pandas.ExcelFile(model.datasheet.datapath)

    countries_any = model.datasheet.get_country_list('any', wb)
    countries_all = model.datasheet.get_country_list('all', wb)

    print('Country: Missing Datasheets')
    for c in countries_any:
        if (c not in countries_all) and (c != 'Global'):
            missing = model.datasheet.whats_missing(c, wb)
            print('{}: {}'.format(c, ', '.join(missing)))
