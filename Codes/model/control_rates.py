import numpy

from . import proportions
from . import targets


def ramp(x, tol = 0.0001):
    r'''
    Piecewise linear:

    .. math:: f(x) =
              \begin{cases}
              0 & \text{if $x \leq 0$},
              \\
              \frac{x}{\epsilon} & \text{if $0 \leq x \leq \epsilon$},
              \\
              1 & \text{if $x \geq \epsilon$}.
              \end{cases}
    '''

    return numpy.clip(x / tol, 0, 1)


# diagnosis, treatment, nonadherance
control_rates_max = numpy.array([1, 10, 1])


def get_control_rates(t, state, targs, parameters):
    r'''
    Rates for diagnosis, treatment, & nonadherance are piecewise constant.

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

    OK, so we actually use the piecewise linear function :func:`ramp`
    that smooths the transition in a tiny region.
    '''

    current_proportions = proportions.get_proportions(state)

    target_values = targets.get_target_values(t, targs, parameters)

    control_rates = numpy.empty(state.shape[ : -1] + (3, ), numpy.float64)

    # diagnosis
    control_rates[..., 0] = (control_rates_max[0]
                             * ramp(target_values[..., 0]
                                    - current_proportions[..., 0]))

    # treatment
    control_rates[..., 1] = (control_rates_max[1]
                             * ramp(target_values[..., 1]
                                    - current_proportions[..., 1]))

    # nonadherance
    control_rates[..., 2] = (control_rates_max[2]
                             * ramp(current_proportions[..., 2]
                                    - target_values[..., 2]))

    return control_rates
