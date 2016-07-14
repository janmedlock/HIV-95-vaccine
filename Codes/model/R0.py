'''
Calculate R0.
'''

import numpy


def compute(parameters):
    diagnosis_rate = treatment_rate = nonadherence_rate = vaccine_coverage = 0
    vaccine_efficacy = 0

    z0 = (1 - vaccine_coverage) + vaccine_coverage * vaccine_efficacy

    F = numpy.zeros((6, 6))
    F[0] = [parameters.transmission_rate_acute * z0,
            parameters.transmission_rate_unsuppressed * z0,
            parameters.transmission_rate_unsuppressed * z0,
            parameters.transmission_rate_unsuppressed * z0,
            parameters.transmission_rate_suppressed * z0,
            0]

    V = numpy.array(
        [[parameters.progression_rate_acute + parameters.death_rate,
          0, 0, 0, 0, 0],
         [- parameters.progression_rate_acute,
          diagnosis_rate + parameters.progression_rate_unsuppressed
          + parameters.death_rate,
          0, 0, 0, 0],
         [0, - diagnosis_rate,
          treatment_rate + parameters.progression_rate_unsuppressed
          + parameters.death_rate,
          - nonadherence_rate, - nonadherence_rate, 0],
         [0, 0, - treatment_rate,
          nonadherence_rate + parameters.suppression_rate
          + parameters.progression_rate_unsuppressed + parameters.death_rate,
          0, 0],
         [0, 0, 0, - parameters.suppression_rate,
          nonadherence_rate + parameters.progression_rate_suppressed
          + parameters.death_rate,
          0],
         [0, - parameters.progression_rate_unsuppressed,
          - parameters.progression_rate_unsuppressed,
          - parameters.progression_rate_unsuppressed,
          - parameters.progression_rate_suppressed,
          parameters.death_rate_AIDS]])

    G = numpy.dot(F, numpy.linalg.inv(V))

    if numpy.isfinite(G).all():
        evals = numpy.linalg.eigvals(G)

        i = numpy.argmax(numpy.abs(evals))
        R0 = numpy.asscalar(numpy.real_if_close(evals[i]))

        assert numpy.isreal(R0)
        assert (R0 > 0)
    else:
        if numpy.isnan(G).any():
            R0 = numpy.nan
        else:
            assert not numpy.isneginf(G).any()
            R0 = numpy.inf

    return R0
