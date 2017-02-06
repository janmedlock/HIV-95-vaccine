'''
Locators to get the coordinates of a country.
'''

import numpy

# import cartopy
import os.path
import sys
sys.path.append(os.path.dirname(__file__))  # For Sphinx
import cartopy_quiet as cartopy


class _Locator:
    '''
    Abstract base class for locators.
    '''

    crs = cartopy.crs.PlateCarree()

    def get_locations(self, countries):
        '''
        Do many calls to :meth:`get_location` and stack results.
        '''

        coords = numpy.vstack(map(self.get_location, countries)).T
        return coords
    

class GeocodeLocator(_Locator):
    '''
    Use :class:`geopy.geocoders.Nominatim` to get country coordinates.
    '''

    crs = cartopy.crs.PlateCarree()

    translations = {'United Republic of Tanzania': 'Tanzania'}

    def __init__(self, *args, **kwargs):
        import geopy

        from . import _shelve

        self.geolocator = geopy.geocoders.Nominatim(*args, **kwargs)

        # cache geolocator lookups to disk for speed.
        self.get_location = _shelve.shelved(self.get_location)

    def get_location(self, country):
        country = self.translations.get(country, country)
        location = self.geolocator.geocode(dict(country = country))
        if location is None:
            raise ValueError('Couldn\'t find country "{}".'.format(country))
        return location.longitude, location.latitude


class CentroidLocator(_Locator):
    '''
    Use the centroid from the country map borders to get country coordinates.
    '''

    _equalarea_crs = cartopy.crs.AlbersEqualArea()
    def __init__(self, borders):
        self.borders = borders

        try:
            geom = next(self.borders.geometries())
        except StopIteration:
            self.crs = None
        else:
            self.crs = geom.crs

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
