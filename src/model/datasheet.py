'''
Load data from the datafile.

.. todo:: Report which countries have been updated when there's
          a new version of the datasheet.
'''

import abc
import collections.abc
import os.path
import pickle
import sys

import numpy
import pandas

from . import output_dir


datasheet = '../data_sheet.xlsx'
# It is relative to this module file,
# not to files that might import it.
datasheet = os.path.join(os.path.dirname(__file__), datasheet)


def isyear(x):
    try:
        return (1900 < x < 2100)
    except TypeError:
        return False


class _Sheet(metaclass = abc.ABCMeta):
    '''
    An abstract base class for workbook sheets.
    '''

    # By default, don't allow a country to have no data.
    allow_missing = False

    @property
    @abc.abstractmethod
    def sheetname(self):
        '''
        Must be defined by subclasses.
        '''
        pass

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
    def get_all(cls, alldata = None, wb = None):
        '''
        Read data for all countries from the Excel file.
        '''
        if alldata is not None:
            sheet = alldata[cls.__name__]
        else:
            if wb is None:
                wb = CountryData.open_wb()
            sheet = wb.parse(cls.sheetname, index_col = 0)
            sheet = cls.clean(sheet)
            sheet.index = cls.get_index(sheet)
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
    def get_country_data(cls, country, alldata = None, wb = None,
                         allow_missing = None):
        '''
        `allow_missing = None` uses the class default.
        '''
        if allow_missing is None:
            allow_missing = cls.allow_missing
        sheet = cls.get_all(alldata = alldata, wb = wb)
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
        for n, v in data.items():
            setattr(country_data, n, v)

    @classmethod
    def get_country_data_and_set_attrs(cls, country_data, alldata = None,
                                       wb = None, allow_missing = None):
        country = country_data.country
        data = cls.get_country_data(country, alldata = alldata, wb = wb,
                                    allow_missing = allow_missing)
        cls.set_attrs(country_data, data)

    @staticmethod
    def has_data(sheet):
        '''
        Select columns where all data is present.
        '''
        return sheet.notnull().all(0)

    @classmethod
    def get_country_list(cls, alldata = None):
        sheet = cls.get_all(alldata = alldata)
        hasdata = cls.has_data(sheet)
        return list(sheet.columns[hasdata])


class Parameters(_Sheet):
    sheetname = 'Parameters'
    parameter_names = ('birth_rate', 'death_rate')


class InitialConditions(_Sheet):
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


class Cost(_Sheet):
    sheetname = 'Costs'
    parameter_names = ('cost_test', 'cost_CD4', 'cost_viral_load',
                       'cost_ART_annual', 'cost_AIDS_annual',
                       'cost_AIDS_death')
    allow_missing = True


class GDP(_Sheet):
    sheetname = 'GDP'
    parameter_names = ('GDP_per_capita', 'GDP_PPP_per_capita')
    allow_missing = True


class IncidencePrevalence(_Sheet):
    sheetname = 'IncidencePrevalence'

    incidence_start_string = 'INCIDENCE (15-49)'
    prevalence_start_string = 'PREVALENCE (15-49)'

    @classmethod
    def clean_entry(cls, x):
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
            x = cls.clean_entry(x)
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
            if v == cls.incidence_start_string:
                datatype = 'incidence_per_capita'
                indata = True
            elif v == cls.prevalence_start_string:
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
    def get_country_list(cls, alldata = None):
        sheet = cls.get_all(alldata = alldata)
        hasdata = cls.has_data(sheet)
        countries = sheet.columns.levels[0]
        return list(countries[hasdata])


class _AnnualSheet(_Sheet):
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


class Population(_AnnualSheet):
    sheetname = 'Population (15-49)'


class Treated(_AnnualSheet):
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
    def __init__(self, country, alldata = None, allow_missing = None):
        '''
        `allow_missing = None` uses _Sheet defaults.
        '''
        self.country = country

        if alldata is None:
            alldata = self.get_all()

        for cls in sheets:
            cls.get_country_data_and_set_attrs(self, alldata = alldata,
                                               allow_missing = allow_missing)

    @staticmethod
    def open_wb():
        '''
        Open the datasheet.
        '''
        return pandas.ExcelFile(datasheet)

    @classmethod
    def get_all(cls):
        '''
        For speed, load all the sheets at once.
        '''
        with cls.open_wb() as wb:
            alldata = {cls.__name__: cls.get_all(wb = wb)
                       for cls in sheets}
        return alldata

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
        _, basename = os.path.split(datasheet)
        root, _ = os.path.splitext(basename)
        filename = '{}.pkl'.format(root)
        self.shelfpath = os.path.join(output_dir.output_dir, filename)
        # Delay opening shelf.
        # self.open_shelf()

    def open_shelf(self):
        assert not hasattr(self, 'shelf')
        if self.is_current():
            with open(self.shelfpath, 'rb') as fd:
                try:
                    self.shelf = pickle.load(fd)
                except:
                    self.build_all()
        else:
            self.build_all()

    def open_shelf_if_needed(self):
        if not hasattr(self, 'shelf'):
            self.open_shelf()

    def build_all(self):
        print('Rebuilding cache of {}.'.format(os.path.relpath(datasheet)))
        alldata = CountryData.get_all()
        countries = get_country_list_noshelf('all', alldata = alldata)
        self.shelf = {country: CountryData(country,
                                           alldata = alldata,
                                           allow_missing = True)
                      for country in countries}
        with open(self.shelfpath, 'wb') as fd:
            pickle.dump(self.shelf, fd, protocol = -1)

    def is_current(self):
        mtime_data = os.path.getmtime(datasheet)
        try:
            mtime_shelf = os.path.getmtime(self.shelfpath)
        except FileNotFoundError:
            return False
        else:
            return (mtime_data <= mtime_shelf)

    def __getitem__(self, country):
        self.open_shelf_if_needed()
        return self.shelf[country]

    def __len__(self):
        self.open_shelf_if_needed()
        return len(self.shelf)

    def __iter__(self):
        self.open_shelf_if_needed()
        return iter(self.shelf)


shelf = CountryDataShelf()


def get_country_data(country):
    return shelf[country]


def get_country_list_noshelf(sheet = 'all', alldata = None):
    if sheet in ('all', 'any'):
        if alldata is None:
            alldata = CountryData.get_all()
    if sheet == 'all':
        # Return countries that are in *all* sheets that
        # must be present (allow_missing == False).
        lists = (cls.get_country_list(alldata = alldata) for cls in sheets
                 if not cls.allow_missing)
        sets = (set(l) for l in lists)
        intersection = set.intersection(*sets)
        return sorted(intersection)
    elif sheet == 'any':
        # Return countries that are in *any* sheet.
        lists = (cls.get_country_list(alldata = alldata) for cls in sheets)
        sets = (set(l) for l in lists)
        union = set.union(*sets)
        return sorted(union)
    else:
        # Use datasheet worksheet named in variable sheet.
        try:
            cls = getattr(sys.modules[__name__], sheet)
            return cls.get_country_list(alldata = alldata)
        except AttributeError:
            msg = ("I don't know how to parse '{}' sheet from datasheet!  "
                   + "Valid sheets are {}.").format(sheet, sheets)
            raise AttributeError(msg)


def get_country_list(sheet = 'all', alldata = None):
    if sheet == 'all':
        return sorted(shelf.keys())
    else:
        return get_country_list_noshelf(sheet = sheet, alldata = alldata)


def whats_missing(country, alldata = None):
    if alldata is None:
        alldata = CountryData.get_all()
    missing = []
    for cls in sheets:
        if not cls.allow_missing:
            if country not in cls.get_country_list(alldata = alldata):
                missing.append(cls.__name__)
    return missing
