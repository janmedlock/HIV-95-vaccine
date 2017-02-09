'''
Countries by region.
'''

from . import datasheet


regions = {
    'Global':
    datasheet.get_country_list(),

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


all_ = sorted(regions.keys())
# Move Global to front.
all_.remove('Global')
all_.insert(0, 'Global')


def is_region(x):
    return (x in all_)


def is_country(x):
    return (not is_region(x))
