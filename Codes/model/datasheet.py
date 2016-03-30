'''
Load data from the datafile.
'''

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


class CountryData:
    '''
    Data from the datasheet for a country.
    '''
    def __init__(self, country):
        self.country = country
        self.country_on_datasheet = convert_country(self.country,
                                                    inverse = True)
        with pandas.ExcelFile(datapath) as self._data:
            self.read_parameters_sheet()
            self.read_initial_conditions_sheet()
            self.read_costs_sheet()
            self.read_GDP_sheet()

    def _get_sheet_data(self, sheetname, nparams, allow_missing = False):
        sheet = self._data.parse(sheetname)
        try:
            data = sheet[self.country_on_datasheet]
        except KeyError:
            if allow_missing:
                data = (numpy.nan, ) * nparams
            else:
                raise
        return data[: nparams]

    def read_parameters_sheet(self):
        nparams = 12
        parameters_ = self._get_sheet_data('Parameters', nparams)
        (self.birth_rate,
         self.death_rate,
         self.progression_rate_acute,
         self.progression_rate_unsuppressed,
         self.suppression_rate,
         self.death_rate_AIDS,
         self.death_years_lost_by_supression,
         self.transmission_per_coital_act_acute,
         self.transmission_per_coital_act_unsuppressed,
         self.transmission_per_coital_act_reduction_by_suppression,
         self.partners_per_year,
         self.coital_acts_per_year) = parameters_
        self.progression_rate_acute = float(self.progression_rate_acute)

    def read_initial_conditions_sheet(self):
        nparams = 6
        initial_conditions = self._get_sheet_data('Initial Conditions',
                                                  nparams)
        self.initial_conditions = initial_conditions
        self.initial_conditions.index = ('S', 'A', 'U', 'D', 'T', 'V')

    def read_costs_sheet(self):
        nparams = 6
        costs = self._get_sheet_data('Costs', nparams, allow_missing = True)
        (self.cost_test,
         self.cost_CD4,
         self.cost_viral_load,
         self.cost_ART_annual,
         self.cost_AIDS_annual,
         self.cost_AIDS_death) = costs

    def read_GDP_sheet(self):
        nparams = 2
        GDP = self._get_sheet_data('GDP', nparams, allow_missing = True)
        (self.GDP_per_capita,
         self.GDP_PPP_per_capita) = GDP

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
    with pandas.ExcelFile(datapath) as data:
        # Skip header column
        if sheet == 'Parameters':
            data_ = data.parse('Parameters').iloc[ : 12, 1 : ]
        elif sheet == 'Costs':
            data_ = data.parse('Costs').iloc[ : 6, 1 : ]
        elif sheet == 'Initial Conditions':
            data_ = data.parse('Initial Conditions').iloc[ : 6, 1 : ]
        elif sheet == 'GDP':
            data_ = data.parse('GDP').iloc[ : 2, 1 : ]
    ix = data_.notnull().all(0)
    return convert_countries(data_.columns[ix])


def read_all_initial_conditions():
    with pandas.ExcelFile(datapath) as data:
        df = data.parse('Initial Conditions', index_col = 0).T
    index = convert_countries(df.index)
    df.index = index
    return df
