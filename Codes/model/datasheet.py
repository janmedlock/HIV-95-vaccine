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

    @classmethod
    def get_columns(cls, sheet):
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

    @classmethod
    def set_attrs(cls, country_data, data):
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


class IncidenceSheet(Sheet):
    sheetname = 'Incidence'

    # The smallest incidence is reported with this string.
    _smallest = '<0.01'
    # Covert to (the string representation of) an actual float
    # that is halfway to 0.
    # E.g. '<0.01' -> 0.005.
    _smallest_rep = float(_smallest.replace('<', '')) / 2

    @classmethod
    def parse_entry(cls, x):
        '''
        Divide everything by 100 because Amber used percent.

        Replace {} with {} and then map any ranges 'a - b'
        to the mean of a and b.
        '''.format(cls._smallest, cls._smallest_rep)

        if isinstance(x, str):
            if x.startswith(cls._smallest):
                x = x.replace(cls._smallest, str(cls._smallest_rep))

            if '-' in x:
                y = x.split('-')
                x = numpy.mean(list(map(float, y)))

            try:
                x = float(x)
            except ValueError:
                return x

        # Divide every cell by 100
        # because Amber used percent.
        return x / 100

    _incidence_strings = ['incidence', 'new infections', 'new cases',
                          '# positive hiv test reports', 'new hiv cases',
                          'new diagnoses']
    _prevalence_strings = ['prevalence', 'reported # hiv infections']
    @classmethod
    def _get_datatype(cls, note):
        if pandas.isnull(note) or (note == ''):
            # Empty.  Assume incidence
            return 'incidence'
        else:
            note_ = note.lower()
            for v in cls._incidence_strings:
                if v in note_:
                    return 'incidence'
            for v in cls._prevalence_strings:
                if v in note_:
                    return 'prevalence'
            raise ValueError("Unknown data type!  note = '{}'.".format(note))

    @classmethod
    def clean(cls, sheet):
        '''
        Drop rows whose index is not a valid year,
        and parse the notes to detemine which columns
        have prevalence instead of incidence.
        '''
        def isyear(x):
            try:
                return (1900 < x < 2100)
            except TypeError:
                return False

        goodrows = numpy.array(list(map(isyear, sheet.index)))
        sheet_ = sheet[goodrows].copy()

        # Parse each entry.
        for i in sheet_.index:
            for j in sheet_.columns:
                sheet_.loc[i, j] = cls.parse_entry(sheet_.loc[i, j])

        # Build a multi-index with (countryname, datatype),
        # where datatype is 'incidence' or 'prevalence'
        # Depending on what's in the notes.
        notes = sheet.loc['NOTES']
        tuples = []
        for country in sheet_.columns:
            tuples.append((country, cls._get_datatype(notes[country])))
        mdx = pandas.MultiIndex.from_tuples(tuples)
        sheet_.columns = mdx
        return sheet_

    @classmethod
    def get_index(cls, sheet):
        '''
        Keep current index values (i.e. years).
        '''
        return sheet.index

    @classmethod
    def get_columns(cls, sheet):
        '''
        Convert country names,
        but keep data type (incidence or prevalence).
        '''
        tuples = []
        for (country, datatype) in sheet.columns.values:
            tuples.append((convert_country(country), datatype))
        return pandas.MultiIndex.from_tuples(tuples)

    @staticmethod
    def has_data(sheet):
        '''
        Select columns where data for at least one year is present.
        '''
        return sheet.notnull().any(0)

    @classmethod
    def get_country_data(cls, country, allow_missing = False, wb = None):
        '''
        Deal with multiindex.
        '''
        data = super().get_country_data(country,
                                        allow_missing = allow_missing,
                                        wb = wb)

        # Make sure we get exactly 1 column.
        assert data.shape[1] == 1

        # Return that 1 column as a Series.
        return data.iloc[:, 0]

    @classmethod
    def set_attrs(cls, country_data, data):
        data_ = data[data.notnull()]
        setattr(country_data, data_.name, data_)


class CountryData:
    '''
    Data from the datasheet for a country.
    '''
    def __init__(self, country):
        self.country = country
        self.country_on_datasheet = convert_country(self.country,
                                                    inverse = True)
        # Share workbook for speed.
        with pandas.ExcelFile(datapath) as self._wb:
            ParameterSheet.get_country_data_and_set_attrs(self)
            InitialConditionsSheet.get_country_data_and_set_attrs(self)
            IncidenceSheet.get_country_data_and_set_attrs(self)
            CostSheet.get_country_data_and_set_attrs(self)
            GDPSheet.get_country_data_and_set_attrs(self)

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
    elif sheet == 'Incidence':
        cls = IncidenceSheet
    else:
        raise ValueError("Unknown sheet '{}'!".format(sheet))
    return cls.get_country_list()
