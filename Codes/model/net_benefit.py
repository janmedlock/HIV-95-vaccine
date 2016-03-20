import numpy


def net_benefit(simulation, cost_effectiveness_threshold,
                effectiveness = 'DALYs'):
    r'''Net benefit is

    .. math:: N = E - \frac{C}{T G},

    where :math:`E` is `effectiveness`, :math:`C` is `cost`, :math:`T`
    is `cost_effectiveness_threshold`, and :math:`G` is
    :attr:`model.datasheet.Parameters.GDP_per_capita`.
    '''
    if effectiveness == 'DALYs':
        effectiveness = - simulation.DALYs
    elif effectiveness == 'QALYs':
        effectiveness = simulation.QALYs

    if cost_effectiveness_threshold == 0:
        # Just cost.
        return - simulation.cost
    elif cost_effectiveness_threshold == numpy.inf:
        # Just effectiveness.
        return effectiveness
    else:
        return (effectiveness - (simulation.cost
                                 / simulation.parameters.GDP_per_capita
                                 / cost_effectiveness_threshold))
