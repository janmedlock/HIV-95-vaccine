'''
Load data from the datafile.
'''

import collections.abc
import itertools
import os.path
import sys

import numpy
import pandas

from . import picklefile

datafile = '../DataSheet.xlsx'
# It's relative to this module file,
# not files that might import it.
datapath = os.path.join(os.path.dirname(__file__), datafile)


country_replacements = {
    'Bolivia (Plurinational State of)': 'Bolivia',
    'Bahamas': 'The Bahamas',
    'Congo': 'Republic of Congo',
    "Côte d'Ivoire": 'Ivory Coast',
    'Iran (Islamic Republic of)': 'Iran',
    "Lao People's Democratic Republic": 'Laos',
    'Republic of Moldova': 'Moldova',
    'Russian Federation': 'Russia',
    'Timor-Leste': 'East Timor',
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    'Venezuela (Bolivarian Republic of)': 'Venezuela',
    'Viet Nam': 'Vietnam',
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
    # By default, don't allow a country to have no data.
    allow_missing = False

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
        '''
        Read data for all countries from the Excel file.
        '''
        if wb is None:
            wb = pandas.ExcelFile(datapath)
        sheet_ = wb.parse(cls.sheetname, index_col = 0)
        sheet = cls.clean(sheet_)
        sheet.index = cls.get_index(sheet)
        sheet.columns = cls.get_columns(sheet)
        return sheet

    @classmethod
    def get_data_name(cls):
        '''
        The class name lower cased, and with any inner capital letters
        replaced by '_' followed by the lower-cased letter.
        '''
        name = cls.__name__
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
    def get_empty(cls):
        return pandas.Series(index = cls.parameter_names)

    @classmethod
    def get_country_data(cls, country, wb = None, allow_missing = None):
        '''
        `allow_missing = None` uses the class default.
        '''
        if allow_missing is None:
            allow_missing = cls.allow_missing
        sheet = cls.get_all(wb = wb)
        try:
            data = sheet[country]
        except KeyError:
            if allow_missing:
                data = cls.get_empty()
            else:
                raise
        data.name = cls.get_data_name()
        return data

    @classmethod
    def set_attrs(cls, country_data, data):
        for n, v in zip(cls.parameter_names, data):
            setattr(country_data, n, v)

    @classmethod
    def get_country_data_and_set_attrs(cls, country_data, wb = None,
                                       allow_missing = None):
        country = country_data.country
        data = cls.get_country_data(country, wb = wb,
                                    allow_missing = allow_missing)
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


class Parameters(Sheet):
    sheetname = 'Parameters'
    parameter_names = ('birth_rate', 'death_rate')


class InitialConditions(Sheet):
    sheetname = 'Initial Conditions'
    parameter_names = ('S', 'A', 'U', 'D', 'T', 'V')

    @staticmethod
    def set_attrs(country_data, data):
        setattr(country_data, data.name, data)

    @classmethod
    def clean(cls, sheet):
        '''
        Drop junk columns and rows at end of sheet.
        '''
        sheet_ = super().clean(sheet)
        goodcols = [c for c in sheet_.columns if not c.startswith('Unnamed: ')]
        return sheet_[goodcols]


class Cost(Sheet):
    sheetname = 'Costs'
    parameter_names = ('cost_test', 'cost_CD4', 'cost_viral_load',
                       'cost_ART_annual', 'cost_AIDS_annual',
                       'cost_AIDS_death')
    allow_missing = True


class GDP(Sheet):
    sheetname = 'GDP'
    parameter_names = ('GDP_per_capita', 'GDP_PPP_per_capita')
    allow_missing = True


class IncidencePrevalence(Sheet):
    sheetname = 'Incidence/Prevalence'

    _incidence_start_string = 'INCIDENCE (15-49)'
    _prevalence_start_string = 'PREVALENCE (15-49)'

    @classmethod
    def _clean_entry(cls, x):
        '''
        Strip trailing '*' etc.
        '''
        # Strip trailing '*'
        if x.endswith('*'):
            x = x.rstrip('*')
        # Patterns like '0.01 *0.001459'
        if '*' in x:
            # Only keep first part
            x = x.split('*')[0]
        # Drop parentheses and everything after.
        if ('(' in x) and (')' in x):
            a = x.find('(')
            x = x[ : a]
        # Drop square brackets and everything inside.
        if ('[' in x) and (']' in x):
            a = x.find('[')
            x = x[ : a]
        if ' ' in x:
            # Catch space as a thousands seperator.
            x = x.replace(' ', '')
        return x

    @classmethod
    def parse_entry(cls, x):
        '''
        First, strip any trailing '*' etc.
        Next, map any ranges '`a` - `b`' to the mean of `a` and `b`.
        Next, replace '<`x`' with `x / 2`.
        Finally, divide everything by 100 because data use percent.
        '''
        if isinstance(x, str):
            x = cls._clean_entry(x)
            if '-' in x and not ('E-' in x or 'e-' in x):
                y = x.split('-')
                # Recursively call this function in case
                # there's a '<' in one of the pieces.
                x = numpy.mean(list(map(cls.parse_entry, y)))
            elif x.startswith('<'):
                x = float(x.replace('<', '')) / 2
            elif x.strip() == '':
                x = numpy.nan
            else:
                try:
                    x = float(x)
                except ValueError:
                    raise
        # Divide every cell by 100 because data use percent.
        return x / 100

    @classmethod
    def clean(cls, sheet):
        '''
        Rearrange data so that (country, incidence/prevalence) are columns
        and years are rows.
        '''
        goodrows = {}
        years = []
        indata = False
        for (i, v) in enumerate(sheet.index):
            if v == cls._incidence_start_string:
                datatype = 'incidence_per_capita'
                indata = True
            elif v == cls._prevalence_start_string:
                datatype = 'prevalence'
                indata = True
            elif indata:
                if isyear(v):
                    if datatype not in goodrows:
                        goodrows[datatype] = []
                    # Record integer location index because multiple
                    # years (the pandas.Index index) will appear twice
                    # in the same column, once for incidence and once
                    # for prevalence.
                    goodrows[datatype].append(i)
                    if v not in years:
                        years.append(v)
                else:
                    indata = False

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
                try:
                    sheet_.loc[year, col] = cls.parse_entry(val)
                except ValueError:
                    raise ValueError('country = {}, row = {}: {}'.format(
                        country, i, val))
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
    def get_empty():
        return pandas.DataFrame(columns = ['prevalence',
                                           'incidence_per_capita'])

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
    
    @classmethod
    def get_empty(cls):
        return pandas.Series()


class Population(AnnualSheet):
    sheetname = 'Population (15-49)'


class Treated(AnnualSheet):
    sheetname = 'ARV'
    allow_missing = True

    @classmethod
    def parse_entry(cls, x):
        '''
        Strip trailing '(`x`)' etc.
        '''
        if isinstance(x, str):
            if ('(' in x) and (')' in x):
                # Drop parentheses and everything after.
                a = x.find('(')
                x = x[ : a]
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
        # Parse each entry to clean.
        for year in sheet_.index:
            for country in sheet_.columns:
                sheet_.loc[year, country] = cls.parse_entry(
                    sheet_.loc[year, country])
        return sheet_.astype(float)


sheets = (
    Parameters,
    InitialConditions,
    IncidencePrevalence,
    # Cost,
    # GDP,
    Population,
    # Treated,
)


class CountryData:
    '''
    Data from the datasheet for a country.
    '''
    def __init__(self, country, wb = None, allow_missing = None):
        '''
        `allow_missing = None` uses Sheet defaults.
        '''
        self.country = country
        self.country_on_datasheet = convert_country(self.country,
                                                    inverse = True)

        if wb is None:
            wb = pandas.ExcelFile(datapath)

        for cls in sheets:
            cls.get_country_data_and_set_attrs(self, wb = wb,
                                               allow_missing = allow_missing)

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


class CountryDataShelf(collections.abc.Mapping):
    '''
    Disk cache for :class:`CountryData` for speed.
    '''
    def __init__(self):
        root, _ = os.path.splitext(datapath)
        self._shelfpath = '{}.pkl'.format(root)
        # Delay opening shelf.
        # self._open_shelf()

    def _open_shelf(self):
        assert not hasattr(self, '_shelf')
        if self._is_current():
            self._shelf = picklefile.load(self._shelfpath)
        else:
            self._build_all()

    def _open_shelf_if_needed(self):
        if not hasattr(self, '_shelf'):
            self._open_shelf()

    def _build_all(self):
        print('Rebuilding cache of {}.'.format(os.path.relpath(datapath)))
        with pandas.ExcelFile(datapath) as wb:
            countries = _get_country_list('all', wb = wb)
            self._shelf = {country: CountryData(country,
                                                wb = wb,
                                                allow_missing = True)
                           for country in countries}
            picklefile.dump(self._shelf, self._shelfpath)

    def _is_current(self):
        mtime_data = os.path.getmtime(datapath)
        try:
            mtime_shelf = os.path.getmtime(self._shelfpath)
        except FileNotFoundError:
            return False
        else:
            return (mtime_data <= mtime_shelf)

    def __getitem__(self, country):
        self._open_shelf_if_needed()
        return self._shelf[country]

    def __len__(self):
        self._open_shelf_if_needed()
        return len(self._shelf)

    def __iter__(self):
        self._open_shelf_if_needed()
        return iter(self._shelf)


data = CountryDataShelf()


def _get_country_list(sheet = 'all', wb = None):
    if sheet == 'all':
        # Return countries that are in *all* sheets that
        # must be present (allow_missing == False).
        if wb is None:
            wb = pandas.ExcelFile(datapath)
        lists = (cls.get_country_list(wb = wb) for cls in sheets
                 if not cls.allow_missing)
        sets = (set(l) for l in lists)
        intersection = set.intersection(*sets)
        return sorted(intersection)
    elif sheet == 'any':
        # Return countries that are in *any* sheet.
        if wb is None:
            wb = pandas.ExcelFile(datapath)
        lists = (cls.get_country_list(wb = wb) for cls in sheets)
        sets = (set(l) for l in lists)
        union = set.union(*sets)
        return sorted(union)
    else:
        try:
            cls = getattr(sys.modules[__name__], sheet)
            return cls.get_country_list(wb = wb)
        except AttributeError:
            msg = ("I don't know how to parse '{}' sheet from DataSheet!  "
                   + "Valid sheets are {}.").format(sheet, sheets)
            raise AttributeError(msg)


def get_country_list(sheet = 'all', wb = None):
    if sheet == 'all':
        return sorted(data.keys())
    else:
        return _get_country_list(sheet = sheet, wb = wb)


def whats_missing(country, wb = None):
    if wb is None:
        wb = pandas.ExcelFile(datapath)
    missing = []
    for cls in sheets:
        if not cls.allow_missing:
            if country not in cls.get_country_list(wb = wb):
                missing.append(cls.__name__)
    return missing
