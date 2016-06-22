'''
Load data from the datafile.
'''

import collections.abc
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


def isyear(x):
    try:
        return (1900 < x < 2100)
    except TypeError:
        return False


class Sheet:
    @classmethod
    def clean(cls, sheet):
        '''
        Drop junk rows at end of sheet.
        '''
        return sheet.iloc[: len(cls.parameter_names)].copy()

    @classmethod
    def get_index(cls, sheet):
        return cls.parameter_names

    @staticmethod
    def get_columns(sheet):
        # Convert country names.
        return convert_countries(sheet.columns)

    @classmethod
    def get_all(cls, wb = None):
        if wb is None:
            wb = pandas.ExcelFile(datapath)
            should_close = True
        else:
            should_close = False
        sheet_ = wb.parse(cls.sheetname, index_col = 0)
        if should_close:
            wb.close()

        sheet = cls.clean(sheet_)
        sheet.index = cls.get_index(sheet)
        sheet.columns = cls.get_columns(sheet)
        return sheet

    @classmethod
    def get_data_name(cls):
        '''
        The class name with the ending 'Sheet' removed,
        then lower cased, and with any inner capital letters
        replaced by '_' followed by the lower-cased letter.
        '''
        # Start with the 
        name = cls.__name__.replace('Sheet', '')
        if len(name) > 0:
            name = name[0].lower() + name[1 : ]
            i = 1
            while (i < len(name)):
                if name[i].isupper():
                    rep = '_' + name[i].lower() + name[i + 1 : ]
                    name = name[ : i] + rep
                    i += 1  # Since we added the '_'
                i += 1
        return name

    @classmethod
    def get_country_data(cls, country, allow_missing = False, wb = None):
        sheet = cls.get_all(wb = wb)
        try:
            data = sheet[country]
        except KeyError:
            if allow_missing:
                data = pandas.Series(index = cls.parameter_names)
            else:
                raise
        data.name = cls.get_data_name()
        return data

    @classmethod
    def set_attrs(cls, country_data, data):
        for n, v in zip(cls.parameter_names, data):
            setattr(country_data, n, v)

    @classmethod
    def get_country_data_and_set_attrs(cls, country_data, *args, **kwargs):
        country = country_data.country
        wb = getattr(country_data, '_wb', None)
        data = cls.get_country_data(country, wb = wb, *args, **kwargs)
        cls.set_attrs(country_data, data)

    @staticmethod
    def has_data(sheet):
        '''
        Select columns where all data is present.
        '''
        return sheet.notnull().all(0)

    @classmethod
    def get_country_list(cls, wb = None):
        sheet = cls.get_all(wb = wb)
        hasdata = cls.has_data(sheet)
        return list(sheet.columns[hasdata])


class ParameterSheet(Sheet):
    sheetname = 'Parameters'
    parameter_names = ('birth_rate', 'death_rate')


class InitialConditionsSheet(Sheet):
    sheetname = 'Initial Conditions'
    parameter_names = ('S', 'A', 'U', 'D', 'T', 'V')

    @staticmethod
    def set_attrs(country_data, data):
        setattr(country_data, data.name, data)


class CostSheet(Sheet):
    sheetname = 'Costs'
    parameter_names = ('cost_test', 'cost_CD4', 'cost_viral_load',
                       'cost_ART_annual', 'cost_AIDS_annual',
                       'cost_AIDS_death')

    @classmethod
    def get_country_data(cls, country, allow_missing = True, wb = None):
        '''
        Changing default allow_missing to True.
        '''
        return super().get_country_data(country,
                                        allow_missing = allow_missing,
                                        wb = wb)


class GDPSheet(Sheet):
    sheetname = 'GDP'
    parameter_names = ('GDP_per_capita', 'GDP_PPP_per_capita')

    @classmethod
    def get_country_data(cls, country, allow_missing = True, wb = None):
        '''
        Changing default allow_missing to True.
        '''
        return super().get_country_data(country,
                                        allow_missing = allow_missing,
                                        wb = wb)


class IncidencePrevalenceSheet(Sheet):
    sheetname = 'IncidencePrevalence'

    _incidence_start_string = 'INCIDENCE (15-49)'
    _prevalence_start_string = 'PREVALENCE (15-49)'

    @staticmethod
    def _clean_entry(x):
        '''
        Strip trailing *'s etc.
        '''
        if x.endswith('*'):
            return x[-1]
        # Patterns like '0.01 *0.001459'
        elif '*' in x:
            # Only keep first part
            return x.split('*')[0]
        elif ('(' in x) and (')' in x):
            # Drop parentheses and everything inside.
            a = x.find('(')
            b = x.find(')')
            return (x[ : a] + x[b + 1 : ])
        else:
            return x

    @classmethod
    def parse_entry(cls, x):
        '''
        First, strip any trailing '*' etc.
        Next, map any ranges 'a - b' to the mean of a and b.
        Next, replace '<x' with x / 2.
        Finally, divide everything by 100 because data use percent.
        '''
        if isinstance(x, str):
            x = cls._clean_entry(x)
            if '-' in x:
                y = x.split('-')
                # Recursively call this function in case
                # there's a '<' in one of the pieces.
                x = numpy.mean(list(map(cls.parse_entry, y)))
            elif x.startswith('<'):
                x = float(x.replace('<', '')) / 2
            elif x.strip() == '':
                x = numpy.nan
            else:
                x = float(x)
        # Divide every cell by 100 because data use percent.
        return x / 100

    @classmethod
    def clean(cls, sheet):
        '''
        Rearrange data so that (country, incidence/prevalence) are columns
        and years are rows.
        '''
        datatype = None
        goodrows = {}
        years = []
        for (i, v) in enumerate(sheet.index):
            if v == cls._incidence_start_string:
                datatype = 'incidence'
            elif v == cls._prevalence_start_string:
                datatype = 'prevalence'
            elif isyear(v):
                assert (datatype is not None)
                if datatype not in goodrows:
                    goodrows[datatype] = []
                # Record integer location index because multiple years
                # (the pandas.Index index) will appear twice in the same column,
                # once for incidence and once for prevalence.
                goodrows[datatype].append(i)
                if v not in years:
                    years.append(v)

        countries = sheet.columns
        datatypes = goodrows.keys()
        mdx = pandas.MultiIndex.from_product([countries, datatypes])
        sheet_ = pandas.DataFrame(index = years,
                                  columns = mdx,
                                  dtype = float)
        for col in sheet_.columns:
            country, datatype = col
            # These are integer location indices, not pandas.Index indices.
            rows = goodrows[datatype]
            for i in rows:
                year = sheet.index[i]
                val = sheet[country].iloc[i]
                if isinstance(val, str):
                    val = val.rstrip('*')
                sheet_.loc[year, col] = cls.parse_entry(val)
        return sheet_

    @staticmethod
    def get_index(sheet):
        '''
        Keep current index values (i.e. years).
        '''
        return sheet.index

    @staticmethod
    def get_columns(sheet):
        '''
        Convert country names and add data type (incidence or prevalence).
        '''
        tuples = []
        for (country, datatype) in sheet.columns.values:
            tuples.append((convert_country(country), datatype))
        return pandas.MultiIndex.from_tuples(tuples)

    @staticmethod
    def set_attrs(country_data, data):
        # drop years with no incidence or prevalence data
        data_ = data.dropna(how = 'all', axis = 0)
        for (name, vals) in data_.items():
            setattr(country_data, name, vals)

    @staticmethod
    def has_data(sheet):
        '''
        Select columns where data for at least one year is present
        for both incidence and prevalence.
        '''
        return sheet.notnull().any(0).any(level = 0)

    @classmethod
    def get_country_list(cls, wb = None):
        sheet = cls.get_all(wb = wb)
        hasdata = cls.has_data(sheet)
        countries = sheet.columns.levels[0]
        return list(countries[hasdata])


class AnnualSheet(Sheet):
    @staticmethod
    def clean(sheet):
        '''
        Drop rows that don't have a year index.
        '''
        goodrows = [isyear(x) for x in sheet.index]
        sheet_ = sheet.loc[goodrows].copy()
        # Convert to int.
        sheet_.index = pandas.Index(sheet_.index.values, dtype = int)
        try:
            return sheet_.astype(int)
        except ValueError:
            return sheet_

    @staticmethod
    def get_index(sheet):
        '''
        Keep current index values (i.e. years).
        '''
        return sheet.index

    @staticmethod
    def set_attrs(country_data, data):
        # Drop years with no data
        data_ = data.dropna()
        setattr(country_data, data.name, data_)

    @staticmethod
    def has_data(sheet):
        '''
        Select columns where data for at least one year is present
        for population.
        '''
        return sheet.notnull().any(0)
    

class PopulationSheet(AnnualSheet):
    sheetname = 'Population (15-49)'


class TreatedSheet(AnnualSheet):
    sheetname = 'ARV'

    @classmethod
    def parse_entry(cls, x):
        '''
        Strip trailing (x)'s etc.
        '''
        if isinstance(x, str):
            if ('(' in x) and (')' in x):
                # Drop parentheses and everything inside.
                a = x.find('(')
                b = x.find(')')
                x = x[ : a] + x[b + 1 : ]
            elif ' ' in x:
                # Keep first of two numbers 'x y'.
                x = x.split(' ')[0]
            x = float(x)
        return x

    @classmethod
    def clean(cls, sheet):
        '''
        Drop rows that don't have a year index.
        '''
        goodrows = [isyear(x) for x in sheet.index]
        sheet_ = sheet.loc[goodrows].copy()
        # Convert to int.
        sheet_.index = pandas.Index(sheet_.index.values, dtype = int)
        # Header row has 'Year' in left column.
        countries = sheet.loc['Year']
        sheet_.columns = countries
        # Parse each entry to clean.
        for year in sheet_.index:
            for country in sheet_.columns:
                sheet_.loc[year, country] = cls.parse_entry(
                    sheet_.loc[year, country])
        return sheet_.astype(float)


class CountryData:
    '''
    Data from the datasheet for a country.
    '''
    _sheets = (ParameterSheet, InitialConditionsSheet,
               IncidencePrevalenceSheet, CostSheet, GDPSheet,
               PopulationSheet, TreatedSheet)

    def __init__(self, country):
        self.country = country
        self.country_on_datasheet = convert_country(self.country,
                                                    inverse = True)
        # Share workbook for speed.
        with pandas.ExcelFile(datapath) as self._wb:
            for cls in self._sheets:
                cls.get_country_data_and_set_attrs(self)

    def __repr__(self):
        cls = self.__class__
        retval = '<{}.{}: country = {}\n'.format(cls.__module__,
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
        cls = InitialConditionsSheet
    elif sheet == 'GDP':
        cls = GDPSheet
    elif sheet == 'IncidencePrevalence':
        cls = IncidencePrevalenceSheet
    elif sheet == 'Treated':
        cls = TreatedSheet
    elif sheet == 'Population':
        cls = PopulationSheet
    else:
        raise ValueError("Unknown sheet '{}'!".format(sheet))
    return cls.get_country_list()
