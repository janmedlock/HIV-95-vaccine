'''
Compute the value of the control rates.
'''

import numpy

from . import container
from . import proportions
from . import targets


class ControlRatesMax:
    '''
    Maximum control rates.
    '''
    diagnosis = 1
    treatment = 10
    nonadherance = 1
    vaccination = 1


def ramp(x, tol = 0.0001):
    r'''
    Piecewise linear

    .. math:: f(x) =
              \begin{cases}
              0 & \text{if $x \leq 0$},
              \\
              \frac{x}{\epsilon} & \text{if $0 \leq x \leq \epsilon$},
              \\
              1 & \text{if $x \geq \epsilon$},
              \end{cases}

    where :math:`\epsilon` is `tol`.
    '''
    return numpy.clip(x / tol, 0, 1)


class ControlRates(container.Container):
    r'''
    Rates for diagnosis, treatment, nonadherance, & vaccination
    are piecewise constant.

    The diagnosis rate is:

    .. math:: r_{\text{diagnosis}} =
              \begin{cases}
              R_{\text{diagnosis}}
              &
              \text{if $p_{\text{diagnosed}} < T_{\text{diagnosed}}(t)$},
              \\
              0 & \text{otherwise}.
              \end{cases}

    The treatment rate is

    .. math:: r_{\text{treatment}} =
              \begin{cases}
              R_{\text{treatment}}
              &
              \text{if $p_{\text{treated}} < T_{\text{treated}}(t)$},
              \\
              0 & \text{otherwise}.
              \end{cases}

    The nonadherance rate is

    .. math:: r_{\text{nonadherance}} =
              \begin{cases}
              0 &
              \text{if $p_{\text{suppressed}} < T_{\text{suppressed}}(t)$},
              \\
              R_{\text{nonadherance}} & \text{otherwise}.
              \end{cases}

    The vaccination rate is

    .. math:: r_{\text{vaccination}} =
              \begin{cases}
              R_{\text{vaccination}} &
              \text{if $p_{\text{vaccinated}} < T_{\text{vaccinated}}(t)$},
              \\
              R_{\text{vaccination}} & \text{otherwise}.
              \end{cases}

    The :math:`R`'s are :class:`ControlRatesMax`.

    OK, so we actually use the piecewise linear function :func:`ramp`
    that smooths the transition in a tiny region.
    '''

    _keys = ('diagnosis', 'treatment', 'nonadherance', 'vaccination')

    def __init__(self, t, state, targets_, parameters):
        proportions_ = proportions.Proportions(state)

        target_values = targets.TargetValues(t, targets_, parameters)

        self.diagnosis = (ControlRatesMax.diagnosis
                          * ramp(target_values.diagnosed
                                 - proportions_.diagnosed))

        self.treatment = (ControlRatesMax.treatment
                          * ramp(target_values.treated
                                 - proportions_.treated))

        self.nonadherance = (ControlRatesMax.nonadherance
                             * ramp(proportions_.suppressed
                                    - target_values.suppressed))

        self.vaccination = (ControlRatesMax.vaccination
                            * ramp(target_values.vaccinated
                                   - proportions_.vaccinated))

