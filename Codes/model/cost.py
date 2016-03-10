'''
Compute cost.

.. doctest::

   >>> from numpy import isclose
   >>> from model.datasheet import Parameters
   >>> from model.cost import solve_and_get_cost
   >>> country = 'Nigeria'
   >>> parameters = Parameters(country)
   >>> cost_ = solve_and_get_cost('909090', parameters)
   >>> assert isclose(cost_, 12706118534.633265)
'''

import numpy
from scipy import integrate

from . import control_rates
from . import simulation
from . import targets


class RelativeCostOfEffort:
    r'''
    The marginal cost of effort for level `p`,
    designed to follow the 80–20 rule.

    The marginal cost is

    .. math::
       f(p) =
       \begin{cases}
       1 & \text{if $p \leq b$},
       \\
       1 + m (p - b) & \text{if $p \geq b$},
       \end{cases}

    where :math:`b` is `breakpoint`,
    and the total cost is

    .. math::
      F(p) = \int_0^p f(p') \mathrm{d}p'.

    This gives proportion :math:`b` of total cost in last :math:`(1 - b)`,

    .. math::
       \frac{F(1) - F(b)}{F(1)} = b,
       :label: eightytwenty

    Particularly, with :math:`b = 0.8`, it gives the 80–20 rule,
    where 80% of the total cost is to cover the last 20%.

    This only makes sense for
    :math:`0 \leq p \leq 1`
    and
    :math:`0.5 \leq b < 1`.
    (The slope is negative for :math:`b < 0.5`
    and the slope is infinite for :math:`b = 1`.)

    :Testing:

    Check that these functions satisfy :eq:`eightytwenty`:

    .. doctest::

       >>> from numpy import arange, isclose
       >>> from scipy.integrate import quad
       >>> from model.cost import RelativeCostOfEffort
       >>> F = RelativeCostOfEffort.total_cost
       >>> def G(p, b):
       ...     return quad(RelativeCostOfEffort.marginal_cost,
       ...                 0, p, args = (b, ), points = (b, ))[0]
       >>> for b in arange(0.5, 1, 0.1):
       ...    assert isclose((F(1, b) - F(b, b)) / F(1, b), b)
       ...    assert isclose((G(1, b) - G(b, b)) / G(1, b), b)
    '''
    @staticmethod
    def marginal_cost(p, breakpoint = 0.8):
        assert (0.5 <= breakpoint < 1), 'Bad breakpoint = {}.'.format(
            breakpoint)
        # assert numpy.all((0 <= p) & (p <= 1)), 'Bad p = {}.'.format(p)

        slope = 2 * (2 * breakpoint  - 1) / (1 - breakpoint) ** 3

        p = numpy.asarray(p)

        return numpy.where(
            p < breakpoint, 1,
            1 + slope * (p - breakpoint))

    @staticmethod
    def total_cost(p, breakpoint = 0.8):
        assert (0.5 <= breakpoint < 1), 'Bad breakpoint = {}.'.format(
            breakpoint)
        # assert numpy.all((0 <= p) & (p <= 1)), 'Bad p = {}.'.format(p)

        slope = 2 * (2 * breakpoint  - 1) / (1 - breakpoint) ** 3

        p = numpy.asarray(p)

        return numpy.where(
            p < breakpoint, p,
            p + slope / 2 * (p - breakpoint) ** 2)


'''
If we assume that susceptible people have less risk of contracting HIV
than people who have HIV, then this number should be > 0 (and < 1).
That is, susceptibles should be less likely to be tested than Undiagnosed.
'''
susceptible_testing_discount = 0

def get_cost(t, state, targs, parameters):
    target_values = targets.get_target_values(t, targs, parameters)
    controls = control_rates.get_control_rates(t, state, targs, parameters)

    cost_rate = (
        (
            # One-time cost of new diagnosis,
            parameters.cost_of_testing_onetime_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for diagnosis (target_values[0]),
            * RelativeCostOfEffort.total_cost(target_values[..., 0])
            # the level of diagnosis control (controls[0]),
            * controls[..., 0]
            # and the number of Susceptible, Acute, & Undiagnosed
            # (state[[0, 1, 2]]).
            * ((1 - susceptible_testing_discount) * state[..., 0]
               + state[..., [1, 2]].sum(-1))
        ) + (
            # One-time cost of new treatment,
            parameters.cost_of_treatment_onetime_constant
            # multiplied by
            # the treatment control (controls[1])
            * controls[..., 1]
            # and the number of people Diagnosed (state[3]).
            * state[..., 3]
        ) + (
            # Recurring cost of treatment,
            parameters.cost_treatment_recurring_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for treatment (target_values[1]),
            * RelativeCostOfEffort.total_cost(target_values[..., 1])
            # and the number of people Treated & Suppressed
            # (state[[4, 5]]).
            * state[..., [4, 5]].sum(-1)
        ) + (
            # Recurring cost of nonadherance,
            parameters.cost_nonadherance_recurring_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for nonadherance (target_values[2]),
            * RelativeCostOfEffort.total_cost(target_values[..., 2])
            # and the number of people Treated and Suppressed
            # (state[[4, 5]]).
            * state[..., [4, 5]].sum(-1)
        ) + (
            # Recurring cost of AIDS,
            parameters.cost_AIDS_recurring_constant
            # multiplied by
            # the number of people with AIDS (state[6])
            * state[..., 6]
        )
    )

    cost = integrate.simps(cost_rate, t)

    return cost


def solve_and_get_cost(targs, parameters):
    t, state = simulation.solve(targs, parameters)
    return get_cost(t, state, targs, parameters)