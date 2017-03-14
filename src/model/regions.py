'''
Countries by region.
'''

import collections.abc

from . import datasheet


_regions = {
    'Eastern and Southern Africa':
    ['Angola', 'Botswana', 'Burundi', 'Eritrea', 'Ethiopia', 'Kenya',
     'Lesotho', 'Madagascar', 'Malawi', 'Mozambique', 'Namibia', 'Rwanda',
     'Somalia', 'South Africa', 'South Sudan', 'Swaziland', 'Uganda',
     'Zambia', 'Zimbabwe'],

    'Western and Central Africa':
    ['Benin', 'Burkina Faso', 'Cameroon', 'Cape Verde',
     'Central African Republic', 'Democratic Republic of the Congo',
     'Equatorial Guinea', 'Gabon', 'Gambia', 'Ghana', 'Guinea',
     "Côte d'Ivoire", 'Liberia', 'Mali', 'Mauritania', 'Niger', 'Nigeria',
     'Senegal', 'Sierra Leone', 'Republic of Congo', 'Togo'],

    'Middle East and North Africa':
    ['Afghanistan', 'Algeria', 'Egypt', 'Iran (Islamic Republic of)',
     'Lebanon', 'Morocco', 'Sudan', 'Tunisia', 'Yemen'],

    'Asia and The Pacific':
    ['Australia', 'Bangladesh', 'Bhutan', 'Cambodia', 'China', 'Timor-Leste',
     'India', 'Indonesia', "Lao People's Democratic Republic", 'Malaysia',
     'Mongolia', 'Myanmar', 'Nepal', 'New Zealand', 'Papua New Guinea',
     'Philippines', 'Sri Lanka', 'Thailand', 'Viet Nam'],

    'Eastern Europe and Central Asia':
    ['Belarus', 'Bulgaria', 'Kazakhstan', 'Kyrgyzstan', 'Republic of Moldova',
     'Russian Federation', 'Tajikistan', 'Ukraine', 'Uzbekistan'],

    'Western and Central Europe':
    ['Austria', 'Belgium', 'Denmark', 'Estonia', 'France', 'Greece',
     'Italy', 'Spain', 'Sweden', 'Switzerland',
     'United Kingdom of Great Britain and Northern Ireland'],

    'North America':
    ['Canada', 'United States of America'],

    'Caribbean':
    ['Barbados', 'Cuba', 'Dominican Republic', 'Haiti', 'Jamaica',
     'Saint Lucia', 'The Bahamas', 'Trinidad and Tobago'],

    'Latin America':
    ['Argentina', 'Bolivia (Plurinational State of)', 'Brazil', 'Chile',
     'Colombia', 'Costa Rica', 'Ecuador', 'El Salvador', 'Guatemala',
     'Haiti', 'Honduras', 'Mexico', 'Nicaragua', 'Panama', 'Paraguay',
     'Peru', 'Uruguay', 'Venezuela (Bolivarian Republic of)']
}


class _Regions(collections.abc.Mapping):
    '''
    Delay evaluation of 'Global'
    so that datasheet.CountryDataShelf does not get built
    when this module is imported.
    '''
    @property
    def Global(self):
        return datasheet.get_country_list()

    def __getitem__(self, k):
        try:
            return getattr(self, k)
        except AttributeError:
            return _regions[k]

    def __iter__(self):
        return iter(['Global'] + sorted(_regions.keys()))

    def __len__(self):
        return 1 + len(_regions)


regions = _Regions()


def is_region(x):
    return (x in regions)


def is_country(x):
    return (x not in regions)
