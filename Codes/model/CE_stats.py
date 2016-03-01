import numpy
from scipy import integrate

from . import simulation
from . import control_rates


def relative_cost_of_effort(p, breakpoint = 0.8):
    '''
    Total cost of effort p.

    This total cost is the integral of the marginal cost
    f = { 1                if p <= b,
        { 1 + m * (p - b)  if p >= b.
    I.e.

               / 1 + m (1 - b)
    1 ________/

     0        b  1

    Gives proportion b of total cost in last (1 - b):
    (F(1) - F(b)) / F(1) = b

    This only makes sense for
    0 <= p <= 1
    and
    0.5 <= b < 1
    (the slope is negative for b < 0.5
    and the slope is infinity for b = 1).
    '''
    assert (0.5 <= breakpoint < 1)
    assert numpy.all((0 <= p) & (p <= 1))
    
    slope = 2 * (2 * breakpoint  - 1) / (1 - breakpoint) ** 3

    return numpy.where(
        p < breakpoint, p,
        p + slope / 2 * (p - breakpoint) ** 2)


def test_relative_cost_of_effort(b):
    assert numpy.isclose((relative_cost_of_effort(1, breakpoint = b)
                          - relative_cost_of_effort(b, breakpoint = b))
                         / relative_cost_of_effort(1, breakpoint = b),
                         b)

test_relative_cost_of_effort(0.8)
test_relative_cost_of_effort(0.9)


def get_CE_stats(t, state, target_funcs, parameters):
    QALYs_rate = state @ parameters.QALY_rates_per_person
    QALYs = integrate.simps(QALYs_rate, t)

    controls = control_rates.get_control_rates(t, state, target_funcs)

    # Note: No cost for the nonadherence control!
    control_cost_rate = (
        (
            # Cost of new diagnosis,
            parameters.cost_of_testing_onetime_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for diagnosis (target_func[0]),
            * relative_cost_of_effort(target_funcs[0](t))
            # the level of diagnosis control (controls[0]),
            * controls[..., 0]
            # and the number of people Undiagnosed (state[2])
            * state[..., 2]
            # SHOULD THIS BE Susceptible + Acute + Diagnosed INSTEAD?
            # * state[..., 0 : 3].sum(-1)
        ) + (
            # Cost of new treatment,
            parameters.cost_of_treatment_onetime_constant
            # multiplied by the treatment control (controls[1])
            * controls[..., 1]
            # and the number of people Diagnosed (state[3]).
            * state[..., 3]
        )
    )

    target_func_values = numpy.column_stack(v(t) for v in target_funcs)
    relative_cost_of_control = relative_cost_of_effort(target_func_values)

    state_cost_rates_per_person = (
        (relative_cost_of_control
         @ parameters.state_cost_rates_per_person_increasing)
        + parameters.state_cost_rates_per_person_constant)

    total_cost_rate = (control_cost_rate
                       + (state_cost_rates_per_person * state).sum(1))
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
