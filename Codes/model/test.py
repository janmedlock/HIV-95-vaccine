'''
Tests.

.. doctest::

   >>> from numpy import isclose
   >>> from model.datasheet import Parameters
   >>> from model.simulation import Simulation
   >>> country = 'Nigeria'
   >>> simulation = Simulation(country, '909090')
   >>> assert isclose(simulation.cost, 12632984122.149424)
   >>> assert isclose(simulation.DALYs, 7469422.8645030726)
   >>> assert isclose(simulation.QALYs, 960203759.34879041)
   >>> assert all(isclose(simulation.incremental_DALYs, 1672955.8058778439))
   >>> assert all(isclose(simulation.incremental_QALYs, 1828846.4245402813))
   >>> assert all(isclose(simulation.incremental_cost, 8811460057.6051826))
   >>> assert all(isclose(simulation.ICER_DALYs, 1.6442437565747554))
   >>> assert all(isclose(simulation.ICER_QALYs, 1.5040886440377796))
'''
