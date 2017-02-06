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



def cost(simulation):
    r'''
    If :math:`q` is the proportion of the total population who have been
    tested ("ever tested"), :math:`p_{\mathrm{HIV}}` is the prevalence,
    :math:`p_{\mathrm{diagnosed}}` is the proportion of HIV-positive people who
    are diagnosed (i.e. tested), and :math:`\rho` is the proportion of
    HIV-negative people who have been tested, then

    .. math:: q = \rho (1 - p_{\mathrm{HIV}})
              + p_{\mathrm{diagnosed}} \cdot p_{\mathrm{HIV}}

    so the relative likelihood of testing of HIV-negative
    vs. HIV-positive people is

    .. math:: z = \frac{\rho}{p_{\mathrm{diagnosed}}}
              = \frac{1}{1 - p_{\mathrm{HIV}}}
              \left(\frac{q}{p_{\mathrm{diagnosed}}}
              - p_{\mathrm{HIV}}\right).

    If we assume that this relative risk of testing :math:`z`
    stays constant from the initial time, then
    cost rate of diagnosis (i.e. testing) is

    .. math:: f(p_{\mathrm{diagnosed}}) r_{\mathrm{diagnosis}}
              \left[U + z (S + Q + A)\right],

    where :math:`f` is :meth:`RelativeCostOfEffort.total_cost`.

    .. todo:: Collect data on proportion of people ever tested
              and implement the relative risk of testing HIV-negative
              vs HIV-postive people.
    '''
    # Relative risk of testing negatives, relative to positives.
    # Should be < 1.
    # See docstring for an alternative if proportion of the population
    # who have been tested is collected.
    relative_risk_of_testing_negatives = 1

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
            # and the number of Susceptible, Vaccinated, Acute, & Undiagnosed.
            * (relative_risk_of_testing_negatives
               * (simulation.susceptible + simulation.vaccinated
                  + simulation.acute)
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
            # Recurring cost of nonadherence,
            simulation.parameters.cost_nonadherence_recurring_increasing
            # multiplied by
            # the relative cost of effort (increasing marginal costs)
            # for nonadherence,
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
