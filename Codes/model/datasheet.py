'''
Load parameter data from the datafile.
'''

import inspect
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
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    'United States': 'United States of America'
}


def convert_country(country):
    '''
    Convert country names used in the datasheet to those used in the maps.
    '''
    return country_replacements.get(country, country)
    

def convert_countries(countries):
    '''
    Convert multiple country names used in the datasheet
    to those used in the maps.
    '''
    return map(convert_country, countries)


class Parameters:
    '''
    Convert parameter data in datafile into object for use in simulations.

    .. todo:: Check that transmission is high enough.
              Perhaps compute :math:`R_0`
              or maybe just run with no treatment.

    .. todo:: Check all parameters.
              In particular, check `progression_rate_suppressed`
              and `death_rate*`.
    '''
    def __init__(self, country):
        self.country_name_in_datasheet = country
        self.country = convert_country(self.country_name_in_datasheet)

        with pandas.ExcelFile(datapath) as data:
            self.read_parameters_sheet(data)
            self.read_initial_conditions_sheet(data)
            self.read_costs_sheet(data)
            self.read_GDP_sheet(data)

    def read_parameters_sheet(self, data):
        parameters_raw \
            = data.parse('Parameters')[self.country_name_in_datasheet]

        # Columns in the spreadsheet.
        (birth_rate, death_rate, progression_rate_acute,
         progression_rate_unsuppressed, suppression_rate,
         death_rate_AIDS, death_years_lost_by_supression,
         transmission_per_coital_act_acute,
         transmission_per_coital_act_unsuppressed,
         transmission_per_coital_act_reduction_by_suppression,
         partners_per_year, coital_acts_per_year) = parameters_raw[ : 12]

        self.birth_rate = birth_rate
        self.death_rate = death_rate
        self.progression_rate_acute = progression_rate_acute
        self.progression_rate_unsuppressed = progression_rate_unsuppressed
        self.suppression_rate = suppression_rate

        self.death_rate_AIDS = death_rate_AIDS

        life_span = 1 / self.death_rate
        time_with_AIDS = 1 / self.death_rate_AIDS
        time_in_suppression = (life_span
                               - death_years_lost_by_supression
                               - time_with_AIDS)
        self.progression_rate_suppressed = 1 / time_in_suppression

        coital_acts_per_partner = coital_acts_per_year / partners_per_year

        self.transmission_rate_acute = (
            partners_per_year
            * (1 -
               (1 - transmission_per_coital_act_acute)
               ** coital_acts_per_partner))

        self.transmission_rate_unsuppressed = (
            partners_per_year
            * (1 -
               (1 - transmission_per_coital_act_unsuppressed)
               ** coital_acts_per_partner))

        self.transmission_rate_suppressed = (
            partners_per_year
            * (1 -
               (1 -
                transmission_per_coital_act_reduction_by_suppression
                * transmission_per_coital_act_unsuppressed)
               ** coital_acts_per_partner))


    def read_initial_conditions_sheet(self, data):
        initial_conditions \
            = data.parse('Initial Conditions')[self.country_name_in_datasheet][0 : 6]
        initial_conditions.index = ('S', 'A', 'U', 'D', 'T', 'V')

        # Compute number of people with AIDS,
        # and move them from the non-AIDS states to the AIDS state.
        # initial_conditions['W'] = 0
        # for k in ('U', 'D', 'T', 'V'):
        #     if k in ('U', 'D', 'T'):
        #         progression_rate = self.progression_rate_unsuppressed
        #     elif k == 'V':
        #         progression_rate = self.progression_rate_suppressed
        #     else:
        #         raise ValueError
                
        #     proportionAIDS = 1 / (1 + self.death_rate_AIDS / progression_rate)
        #     newAIDS = proportionAIDS * initial_conditions[k]
        #     initial_conditions['W'] += newAIDS
        #     initial_conditions[k]   -= newAIDS
        # Take AIDS people out of D only.
        proportionAIDS = (1 / (1
                               + self.death_rate_AIDS
                               / self.progression_rate_unsuppressed))
        newAIDS = proportionAIDS * initial_conditions['D']
        initial_conditions['W'] = newAIDS
        initial_conditions['D'] -= newAIDS

        # Add people dead from AIDS.
        initial_conditions['Z'] = 0
        # Add new infections.
        initial_conditions['R'] = 0

        # Now convert to numpy object for speed.
        self.initial_conditions = initial_conditions.as_matrix()


    def read_costs_sheet(self, data):
        try:
            costs_raw = data.parse('Costs')[self.country_name_in_datasheet]
        except KeyError:
            costs_raw = (numpy.nan, ) * 6

        (cost_test,
         cost_CD4,
         cost_viral_load,
         cost_ART_annual,
         cost_AIDS_annual,
         cost_AIDS_death) = costs_raw[ : 6]

        # One-time cost of new diagnosis.
        self.cost_of_testing_onetime_increasing = cost_test

        # One-time cost of new treatment.
        self.cost_of_treatment_onetime_constant = cost_CD4 + cost_viral_load

        ###############################################
        # Note: No cost for the nonadherence control! #
        ###############################################
        # Recurring cost of nonadherance.
        self.cost_nonadherance_recurring_increasing = 0

        # Recurring cost of treatment.
        # Treatment is ART + 1 viral load test per year
        # + 2 CD4 tests per year.
        self.cost_treatment_recurring_increasing = (cost_ART_annual
                                                    + cost_viral_load
                                                    + 2 * cost_CD4)

        # Recurring cost of AIDS.
        #
        # This is calculated as the annual cost of living with AIDS
        # (cost_AIDS_annual) plus the cost of AIDS death
        # (cost_AIDS_death * death_rate_AIDS).
        self.cost_AIDS_recurring_constant = (cost_AIDS_annual
                                             + (self.death_rate_AIDS
                                                * cost_AIDS_death))

        # Disability weights, assuming 1 year in symptomatic phase.
        years_in_symptomatic = 1
        disability_D = (
            ((1 - years_in_symptomatic * self.progression_rate_unsuppressed)
             * 0.038)
            + (years_in_symptomatic * self.progression_rate_unsuppressed
               * 0.274))
        disability_T = (
            ((1 - years_in_symptomatic * self.progression_rate_unsuppressed)
             * 0.078)
            + (years_in_symptomatic * self.progression_rate_unsuppressed
               * 0.314))
        disability_V = (
            ((1 - years_in_symptomatic * self.progression_rate_suppressed)
             * 0.039)
            + (years_in_symptomatic * self.progression_rate_suppressed
               * 0.157))

        # Entries are states S, A, U, D, T, V, W, Z,
        # but not R.
        disability = numpy.array((0,            # S
                                  0.16,         # A
                                  0.038,        # U
                                  disability_D, # D
                                  disability_T, # T
                                  disability_V, # V
                                  0.582,        # W
                                  1))           # Z

        self.QALY_rates_per_person = 1 - disability

        self.DALY_rates_per_person = disability


    def read_GDP_sheet(self, data):
        try:
            GDP_raw = data.parse('GDP')[self.country_name_in_datasheet]
        except KeyError:
            GDP_raw = (numpy.nan, ) * 2

        GDP_per_capita, GDP_PPP_per_capita = GDP_raw[ : 2]

        self.GDP_per_capita = GDP_per_capita
        self.GDP_PPP_per_capita = GDP_PPP_per_capita


    def __repr__(self):
        retval = 'country = {}\n'.format(self.country)
        retval += '\n'.join('{} = {}'.format(k, getattr(self, k))
                            for k in dir(self)
                            if ((k != 'country')
                                and (not k.startswith('_'))
                                and (not callable(getattr(self, k)))))
        return retval


def get_country_list(sheet = 'Parameters'):
    with pandas.ExcelFile(datapath) as data:
        # Skip header column
        if sheet == 'Parameters':
            data = data.parse('Parameters').iloc[ : 12, 1 : ]
        elif sheet == 'Costs':
            data = data.parse('Costs').iloc[ : 6, 1 : ]
        elif sheet == 'Initial Conditions':
            data = data.parse('Initial Conditions').iloc[ : 6, 1 : ]
        elif sheet == 'GDP':
            data = data.parse('GDP').iloc[ : 2, 1 : ]

    ix = data.notnull().all(0)
    return data.columns[ix]


def read_all_initial_conditions():
    with pandas.ExcelFile(datapath) as data:
        df = data.parse('Initial Conditions', index_col = 0).T
    index = convert_countries(df.index)
    df.index = index
    return df
