import numpy
from scipy import integrate

from . import simulation
from . import control_rates


m_80_20 = 2 * (2 * 0.8  - 1) / (1 - 0.8) ** 3

def relative_cost_of_effort(p):
    '''
    Total cost of effort p.

    Derived from marginal costs:
    1                        if p <= 0.8,
    1 + m_80_20 * (p - 0.8)  if p >= 0.8.

    Gives 80% of total cost in last 20%:
    4 * \int_0^{0.8} f(p) dp = \int_{0.8}^1 f(p) dp.
    '''
    return numpy.where(
        p < 0.8, p,
        (0.8 + (1 - 0.8 * m_80_20) * (p - 0.8)
         + m_80_20 / 2 * (p ** 2 - 0.8 ** 2)))


def get_CE_stats(t, state, target_funcs, parameters):
    QALYs_rate = state @ (parameters.QALY_rates_per_person)
    QALYs = integrate.simps(QALYs_rate, t)

    controls = control_rates.get_control_rates(t, state, target_funcs)
    target_func_values = numpy.column_stack(v(t) for v in target_funcs)
    relative_cost_of_control = relative_cost_of_effort(target_func_values)

    control_cost_rates_per_person = (
        (controls
         @ parameters.control_cost_per_transition_constant)
        + ((relative_cost_of_control * controls)
           @ parameters.control_cost_per_transition_increasing))

    state_cost_rates_per_person = (
        (relative_cost_of_control
         @ parameters.state_cost_rates_per_person_increasing)
        + parameters.state_cost_rates_per_person_constant)

    total_cost_rate = ((control_cost_rates_per_person
                        + state_cost_rates_per_person)
                       * state).sum(1)
    cost = integrate.simps(total_cost_rate, t)

    return QALYs, cost


def solve_and_get_CE_stats(target_values, parameters):
    t, state, target_funcs = simulation.solve(target_values, parameters)

    return get_CE_stats(t, state, target_funcs, parameters)


def get_incremental_CE_stats(effectiveness, cost,
                             effectiveness_base, cost_base,
                             parameters):
    incremental_effectiveness = effectiveness - effectiveness_base
    incremental_cost = cost - cost_base
    ICER = (incremental_cost
            / incremental_effectiveness
            / parameters.GDP_per_capita)
    return (incremental_effectiveness, incremental_cost, ICER)


def solve_and_get_incremental_CE_stats(target_values, parameters):
    effectiveness, cost = solve_and_get_CE_stats(target_values, parameters)

    effectiveness_base, cost_base = solve_and_get_CE_stats('base', parameters)

    return get_incremental_CE_stats(effectiveness, cost,
                                    effectiveness_base, cost_base,
                                    parameters)


def print_incremental_CE_stats(incremental_effectiveness, incremental_cost,
                               ICER, parameters):
    print('incremental effectiveness = {:g} QALYs'.format(
        incremental_effectiveness))
    print('incremental cost = {:g} USD'.format(incremental_cost))
    print('incremental cost = {:g} GDP per capita'.format(
        incremental_cost / parameters.GDP_per_capita))
    print('ICER = {:g} USD per QALY'.format(
        ICER * parameters.GDP_per_capita))
    print('ICER = {:g} GDP per capita per QALY'.format(
        ICER))


def get_net_benefit(effectiveness, cost, CE_threshold, parameters):
    if CE_threshold == 0:
        # Just cost.
        net_benefit = - cost
    elif CE_threshold == numpy.inf:
        # Just Effectiveness.
        net_benefit = effectiveness
    else:
        net_benefit = (
            effectiveness - cost / parameters.GDP_per_capita / CE_threshold)

    return net_benefit


def solve_and_get_net_benefit(target_values, CE_threshold, parameters):
     effectiveness, cost = solve_and_get_CE_stats(target_values, parameters)
     return get_net_benefit(effectiveness, cost, CE_threshold, parameters)
