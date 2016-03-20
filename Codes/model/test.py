'''
Tests.

.. doctest::

   >>> from numpy import isclose
   >>> from model.datasheet import Parameters
   >>> from model.simulation import Simulation
   >>> country = 'Nigeria'
   >>> simulation = Simulation(country, '909090')
   >>> assert isclose(simulation.cost, 19579571706.41235)
   >>> assert isclose(simulation.DALYs, 13807040.061347544)
   >>> assert isclose(simulation.QALYs, 1542178864.3872309)
   >>> assert isclose(simulation.incremental_cost, 14362126332.038065)
   >>> assert isclose(simulation.incremental_DALYs, 4564739.0117855407)
   >>> assert isclose(simulation.incremental_QALYs, 5248944.484855175)
   >>> assert isclose(simulation.ICER_DALYs, 0.98221278690875868)
   >>> assert isclose(simulation.ICER_QALYs, 0.85418030981532012)
'''
