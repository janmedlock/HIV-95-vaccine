import numpy
import pandas
import os.path
import inspect


datafile = '../DataSheet.xlsx'
# It's relative to this module file,
# not files that might import it.
datapath = os.path.join(os.path.dirname(__file__), datafile)


class Parameters:
    '''
    Convert parameter data in datafile into object for use in simulations.
    '''

    def __init__(self, country):
        self.country = country

        with pandas.ExcelFile(datapath) as data:
            self.read_parameters_sheet(data)
            self.read_initial_conditions_sheet(data)
            self.read_costs_sheet(data)
            self.read_GDP_sheet(data)

    def read_parameters_sheet(self, data):
        parameters_raw = data.parse('Parameters')[self.country]

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
            = data.parse('Initial Conditions')[self.country][0 : 6]
        initial_conditions.index = ('S', 'A', 'U', 'D', 'T', 'V')

        # Compute number of people with AIDS,
        # and move them from the non-AIDS states to the AIDS state.
        initial_conditions['W'] = 0
        for k in ('U', 'D', 'T', 'V'):
            if k in ('U', 'D', 'T'):
                progression_rate = self.progression_rate_unsuppressed
            elif k == 'V':
                progression_rate = self.progression_rate_suppressed
            else:
                raise ValueError
                
            proportionAIDS = 1 / (1 + self.death_rate_AIDS / progression_rate)
            newAIDS = proportionAIDS * initial_conditions[k]
            initial_conditions['W'] += newAIDS
            initial_conditions[k]   -= newAIDS

        # Now convert to numpy object for speed.
        self.initial_conditions = initial_conditions.as_matrix()


    def read_costs_sheet(self, data):
        costs_raw = data.parse('Costs')[self.country]

        (cost_test,
         cost_CD4,
         cost_viral_load,
         cost_ART_annual,
         cost_AIDS_annual,
         cost_AIDS_death) = costs_raw[ : 6]

        # Costs for control transistions that don't have increasing marginal
        # costs.
        # Rows are controls p_D, p_T, p_V.
        # Columns are states S, A, U, D, T, V, W.
        self.control_cost_per_transition_constant = numpy.zeros((3, 7))
        # Cost of moving D->T (treatment),
        # controlled by control[1] (p_T),
        # per person in state[3] (D).
        self.control_cost_per_transition_constant[1, 3] = (cost_CD4
                                                           + cost_viral_load)

        # Costs for control transistions that have increasing marginal costs.
        # Rows are controls p_D, p_T, p_V.
        # Columns are states S, A, U, D, T, V, W.
        self.control_cost_per_transition_increasing = numpy.zeros((3, 7))
        # Cost of moving U->D (diagnosis),
        # controlled by control[0] (p_D),
        # per person in state[2] (U).
        self.control_cost_per_transition_increasing[0, 2] = cost_test

        # treatment is ART + 1 viral load test per year + 2 CD4 tests per year.
        cost_treatment_annual = (cost_ART_annual
                                 + cost_viral_load
                                 + 2 * cost_CD4)

        cost_AIDS_annual_total = (cost_AIDS_annual
                                  + self.death_rate_AIDS * cost_AIDS_death)

        # Cost rates for being in each state that don't have increasing
        # marginal costs.
        # Entries are states S, A, U, D, T, V, W
        self.state_cost_rates_per_person_constant = numpy.array(
            (0, 0, 0, 0, 0, 0, cost_AIDS_annual_total))

        # Cost rates for being in each state that have increasing
        # marginal costs.
        # Rows are controls p_D, p_T, p_V.
        # Columns are states S, A, U, D, T, V, W.
        self.state_cost_rates_per_person_increasing = numpy.zeros((3, 7))
        # Cost rate of treatment,
        # controlled by control[1] (p_T),
        # for state[4] (T).
        self.state_cost_rates_per_person_increasing[1, 4] \
            = cost_treatment_annual
        # Cost rate of treatment,
        # controlled by control[1] (p_T),
        # for state[5] (V).
        self.state_cost_rates_per_person_increasing[1, 5] \
            = cost_treatment_annual

        # No cost yet of p_V.
        # This would show up as p_V -> V
        # self.state_cost_rates_per_person_increasing[2, 5] \
        #     = cost_adherence_annual
        # and maybe as p_V -> T
        # self.state_cost_rates_per_person_increasing[2, 4] \
        #     = cost_adherence_annual

        years_in_symptomatic = 1
        DALY_rate_D = (
            ((1 - years_in_symptomatic * self.progression_rate_unsuppressed)
             * 0.038)
            + (years_in_symptomatic * self.progression_rate_unsuppressed
               * 0.274))
        DALY_rate_T = (
            ((1 - years_in_symptomatic * self.progression_rate_unsuppressed)
             * 0.078)
            + (years_in_symptomatic * self.progression_rate_unsuppressed
               * 0.314))
        DALY_rate_V = (
            ((1 - years_in_symptomatic * self.progression_rate_suppressed)
             * 0.039)
            + (years_in_symptomatic * self.progression_rate_suppressed
               * 0.157))

        # Entries are states S, A, U, D, T, V, W
        self.DALY_rates_per_person = numpy.array(
            (0,           # S
             0.16,        # A
             0.038,       # U
             DALY_rate_D, # D
             DALY_rate_T, # T
             DALY_rate_V, # V
             0.582))      # W

        # Entries are states S, A, U, D, T, V, W
        self.QALY_rates_per_person = 1 - self.DALY_rates_per_person


    def read_GDP_sheet(self, data):
        GDP_raw = data.parse('GDP')[self.country]

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


def get_country_list():
    with pandas.ExcelFile(datapath) as data:
        # Skip header column
        costs = data.parse('Costs').iloc[0 : 6, 1 : ]

    ix = costs.notnull().all(0)
    countries = list(costs.columns[ix])
    return countries


def read_all_initial_conditions():
    with pandas.ExcelFile(datapath) as data:
        return data.parse('Initial Conditions', index_col = 0).T
