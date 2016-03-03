'''
Locators to get the coordinates of a country.
'''

import warnings

import numpy

# Silence warnings from matplotlib trigged by cartopy.
warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('This has been deprecated in mpl 1.5, please use the\n'
               'axes property.  A removal date has not been set.'))
import cartopy


class Locator:
    '''
    Abstract base class for locators.
    '''

    def get_locations(self, countries):
        '''
        Do many calls to get_location() and stack results.
        '''

        coords = numpy.vstack(map(self.get_location, countries)).T
        return coords
    

class GeocodeLocator(Locator):
    '''
    Use :mod:`geopy.geocoders.Nominatim` to get country coordinates.
    '''

    def __init__(self, *args, **kwargs):
        import geopy

        from . import _shelve

        self.geolocator = geopy.geocoders.Nominatim(*args, **kwargs)

        # cache geolocator lookups to disk for speed.
        self.get_location = _shelve.shelved(self.get_location)

    def get_location(self, country):
        location = self.geolocator.geocode(dict(country = country))
        if location is None:
            raise ValueError('Couldn\'t find country "{}".'.format(country))
        return location.longitude, location.latitude


class CentroidLocator(Locator):
    '''
    Use the centroid from the country map borders to get country coordinates.
    '''

    _equalarea_crs = cartopy.crs.AlbersEqualArea()
    def __init__(self, borders):
        self.borders = borders

    def get_location(self, country):
        border = self.borders[country]

        centroids = []
        areas = []
        for g in border.geometries():
            centroids.append(g.centroid.xy)
            areas.append(
                self._equalarea_crs.project_geometry(g, border.crs).area)

        centroid = numpy.average(centroids, weights = areas,
                                 axis = 0).squeeze()
        return centroid
