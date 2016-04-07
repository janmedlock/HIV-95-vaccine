'''
Load data from the datafile.
'''

import itertools
import os.path

import numpy
import pandas


datafile = '../DataSheet.xlsx'
# It's relative to this module file,
# not files that might import it.
datapath = os.path.join(os.path.dirname(__file__), datafile)


country_replacements = {
    'Bahamas': 'The Bahamas',
    'Congo': 'Republic of Congo',
    "Côte d'Ivoire": 'Ivory Coast',
    'Iran (Islamic Republic of)': 'Iran',
    "Lao People's Democratic Republic": 'Laos',
    'Republic of Moldova': 'Moldova',
    'Timor-Leste': 'East Timor',
    # 'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    # 'United States': 'United States of America'
}

country_replacements_inv = {v: k for (k, v) in country_replacements.items()}


def convert_country(country, inverse = False):
    '''
    Convert country names used in the datasheet to those used in the maps
    or vice versa.
    '''
    if inverse:
        return country_replacements_inv.get(country, country)
    else:
        return country_replacements.get(country, country)


def convert_countries(countries, inverse = False):
    '''
    Convert multiple country names used in the datasheet
    to those used in the maps or vice versa.
    '''
    return [convert_country(c, inverse = inverse) for c in countries]


class Sheet:
    @classmethod
    def get_data(cls, p, allow_missing = False):
        sheet = p._wb.parse(cls.sheetname)
        try:
            data = sheet[p.country_on_datasheet]
        except KeyError:
            if allow_missing:
                data = itertools.repeat(numpy.nan, len(cls.parameter_names))
            else:
                raise
        for n, v in zip(cls.parameter_names, data):
            setattr(p, n, v)

    @classmethod
    def get_country_list(cls):
        with pandas.ExcelFile(datapath) as _wb:
            data = _wb.parse(cls.sheetname)
            # Skip header column and drop junk rows at end.
            data_ = data.iloc[: len(cls.parameter_names), 1 :]
            ix = data_.notnull().all(0)
            return convert_countries(data_.columns[ix])

    @classmethod
    def read_all(cls):
        with pandas.ExcelFile(datapath) as data:
            df = data.parse(cls.sheetname, index_col = 0).T
        index = convert_countries(df.index)
        df.index = index
        return df


class ParameterSheet(Sheet):
    sheetname = 'Parameters'
    parameter_names = ('birth_rate', 'death_rate')


class InitialConditionSheet(Sheet):
    sheetname = 'Initial Conditions'
    parameter_names = ('S', 'A', 'U', 'D', 'T', 'V')

    @classmethod
    def get_data(cls, p, allow_missing = False):
        sheet = p._wb.parse(cls.sheetname)
        try:
            data = sheet[p.country_on_datasheet]
        except KeyError:
            if allow_missing:
                data = pandas.Series(
                    itertools.repeat(numpy.nan,
                                     len(cls.parameter_names)))
            else:
                raise
        data.index = cls.parameter_names
        setattr(p, 'initial_conditions', data)


class CostSheet(Sheet):
    sheetname = 'Costs'
    parameter_names = ('cost_test', 'cost_CD4', 'cost_viral_load',
                       'cost_ART_annual', 'cost_AIDS_annual',
                       'cost_AIDS_death')

    @classmethod
    def get_data(cls, p, allow_missing = True):
        return super().get_data(p, allow_missing = allow_missing)


class GDPSheet(Sheet):
    sheetname = 'GDP'
    parameter_names = ('GDP_per_capita', 'GDP_PPP_per_capita')

    @classmethod
    def get_data(cls, p, allow_missing = True):
        return super().get_data(p, allow_missing = allow_missing)


class CountryData:
    '''
    Data from the datasheet for a country.
    '''
    def __init__(self, country):
        self.country = country
        self.country_on_datasheet = convert_country(self.country,
                                                    inverse = True)
        with pandas.ExcelFile(datapath) as self._wb:
            ParameterSheet.get_data(self)
            InitialConditionSheet.get_data(self)
            CostSheet.get_data(self)
            GDPSheet.get_data(self)

    def __repr__(self):
        cls = self.__class__
        retval = '<{}.{}: country = {}\n'.format(cls.__module,
                                                 cls.__name__,
                                                 self.country)
        retval += '\n'.join('{} = {}'.format(k, getattr(self, k))
                            for k in dir(self)
                            if ((k != 'country')
                                and (not k.startswith('_'))
                                and (not callable(getattr(self, k)))))
        retval += '>'
        return retval


def get_country_list(sheet = 'Parameters'):
    if sheet == 'Parameters':
        cls = ParameterSheet
    elif sheet == 'Costs':
        cls = CostSheet
    elif sheet == 'Initial Conditions':
        cls = InitialConditionSheet
    elif sheet == 'GDP':
        cls = GDPSheet
    else:
        raise ValueError("Unknown sheet '{}'!".format(sheet))
    return cls.get_country_list()
