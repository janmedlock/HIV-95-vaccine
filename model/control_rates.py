'''
Compute the value of the control rates.
'''

import numpy

from . import proportions


class ControlRatesMax:
    '''
    Maximum control rates.
    '''
    diagnosis = 1
    treatment = 10
    nonadherence = 1
    vaccination = 1


def ramp(x, tol = 0.001):
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


def get(t, state, target, parameters):
    r'''
    Calculate control rates from the current proportions diagnosed, etc.

    Rates for diagnosis, treatment, nonadherence, & vaccination
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

    The nonadherence rate is

    .. math:: r_{\text{nonadherence}} =
              \begin{cases}
              0 &
              \text{if $p_{\text{suppressed}} < T_{\text{suppressed}}(t)$},
              \\
              R_{\text{nonadherence}} & \text{otherwise}.
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
    proportions_ = proportions.get(state)

    target_values = target(t, parameters)

    names = []
    arrays = []
    
    names.append('diagnosis')
    arrays.append(ControlRatesMax.diagnosis
                  * ramp(target_values.diagnosed
                         - proportions_.diagnosed))

    names.append('treatment')
    arrays.append(ControlRatesMax.treatment
                  * ramp(target_values.treated
                         - proportions_.treated))

    names.append('nonadherence')
    arrays.append(ControlRatesMax.nonadherence
                  * ramp(proportions_.suppressed
                         - target_values.suppressed))

    names.append('vaccination')
    arrays.append(ControlRatesMax.vaccination
                  * ramp(target_values.vaccinated
                         - proportions_.vaccinated))

    return numpy.rec.fromarrays(arrays, names = names)
