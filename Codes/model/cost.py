'''
Compute cost.
'''

import unittest

import numpy
from scipy import integrate


class RelativeCostOfEffort:
    r'''
    The marginal cost of effort for level `p`,
    designed to follow the 80–20 rule.

    The marginal cost is

    .. math:: f(p) =
              \begin{cases}
              1 & \text{if $p \leq b$},
              \\
              1 + m (p - b) & \text{if $p \geq b$},
              \end{cases}

    where :math:`b` is `breakpoint`,
    and the total cost is

    .. math:: F(p) = \int_0^p f(p') \mathrm{d}p'.

    This gives proportion :math:`b` of total cost in last :math:`(1 - b)`,

    .. math:: \frac{F(1) - F(b)}{F(1)} = b,
       :label: eightytwenty

    Particularly, with :math:`b = 0.8`, it gives the 80–20 rule,
    where 80% of the total cost is to cover the last 20%.

    This only makes sense for
    :math:`0 \leq p \leq 1`
    and
    :math:`0.5 \leq b < 1`.
    (The slope is negative for :math:`b < 0.5`
    and the slope is infinite for :math:`b = 1`.)
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


class TestRelativeCostOfEffort(unittest.TestCase):
    '''
    Check that :eq:`eightytwenty` is satisfied.
    '''
    def test_relative_cost_of_effort(self):
        F = RelativeCostOfEffort.total_cost

        def G(p, b):
            I, e = integrate.quad(RelativeCostOfEffort.marginal_cost,
                                  0, p, args = (b, ), points = (b, ))
            return I

        for b in numpy.arange(0.5, 1, 0.1):
            with self.subTest(b = b):
                self.assertTrue(numpy.isclose((F(1, b) - F(b, b)) / F(1, b), b))
                self.assertTrue(numpy.isclose((G(1, b) - G(b, b)) / G(1, b), b))



'''
If we assume that susceptible people have less risk of contracting HIV
than people who have HIV, then this number should be > 0 (and < 1).
That is, susceptibles should be less likely to be tested than Undiagnosed.
'''
susceptible_testing_discount = 0

def cost(simulation):
    cost_rate = (
        (
            # One-time cost of new diagnosis,
            simulation.parameters.cost_of_testing_onetime_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for diagnosed,
            * RelativeCostOfEffort.total_cost(
                simulation.target_values.diagnosed)
            # the level of diagnosis control,
            * simulation.control_rates.diagnosis
            # and the number of Susceptible, Acute, & Undiagnosed.
            * ((1 - susceptible_testing_discount) * simulation.susceptible
               + simulation.acute
               + simulation.undiagnosed)
        ) + (
            # One-time cost of new treatment,
            simulation.parameters.cost_of_treatment_onetime_constant
            # multiplied by
            # the treatment control
            * simulation.control_rates.treatment
            # and the number of people Diagnosed.
            * simulation.diagnosed
        ) + (
            # Recurring cost of treatment,
            simulation.parameters.cost_treatment_recurring_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for treatment,
            * RelativeCostOfEffort.total_cost(simulation.target_values.treated)
            # and the number of people Treated & Suppressed.
            * (simulation.treated + simulation.viral_suppression)
        ) + (
            # Recurring cost of nonadherance,
            simulation.parameters.cost_nonadherance_recurring_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for nonadherance,
            * RelativeCostOfEffort.total_cost(
                simulation.target_values.suppressed)
            # and the number of people Treated and Suppressed.
            * (simulation.treated + simulation.viral_suppression)
        ) + (
            # Recurring cost of AIDS,
            simulation.parameters.cost_AIDS_recurring_constant
            # multiplied by
            # the number of people with AIDS.
            * simulation.AIDS
        )
    )

    cost = integrate.simps(cost_rate, simulation.t)

    return cost
