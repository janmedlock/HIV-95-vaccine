#!/usr/bin/python3

import numpy
import itertools
import collections.abc
import shelve
import os
import inspect
from matplotlib import pyplot

# Silence warnings from matplotlib trigged by seaborn and cartopy
import warnings

warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('axes.color_cycle is deprecated '
               'and replaced with axes.prop_cycle; '
               'please use the latter.'))
import seaborn

warnings.filterwarnings(
    'ignore',
    module = 'matplotlib',
    message = ('This has been deprecated in mpl 1.5, please use the\n'
               'axes property.  A removal date has not been set.'))
import cartopy

# Change cartopy cache from ~/.local/share
# to a subdirectory so it'll go in Google Drive.
cartopy.config['data_dir'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '__cartopy__')


class Locator:
    def get_locations(self, countries):
        'Do many calls to get_location() and stack results.'
        coords = numpy.vstack(map(self.get_location, countries)).T
        return coords
    

class shelved:
    def __init__(self, func):
        self._func = func

        # Put the cache file in the same directory as the caller.
        funcdir = os.path.dirname(inspect.getfile(self._func))
        cachedir = os.path.join(funcdir, '__shelve__')
        if not os.path.exists(cachedir):
            os.mkdir(cachedir)

        # Name the cache file func.__name__
        cachefile = os.path.join(cachedir,
                                 str(self._func.__name__))
        self.cache = shelve.open(cachefile)

    def __call__(self, *args, **kwargs):
        key = str((args, set(kwargs.items())))
        
        try:
            'Try to get value from the cache.'
            val = self.cache[key]
        except KeyError:
            'Get the value and store it in the cache.'
            val = self.cache[key] = self._func(*args, **kwargs)
        return val


class GeocodeLocator(Locator):
    def __init__(self, *args, **kwargs):
        import geopy

        self.geolocator = geopy.geocoders.Nominatim(*args, **kwargs)

        # cache geolocator lookups to disk for speed.
        self.get_location = shelved(self.get_location)

    def get_location(self, country):
        location = self.geolocator.geocode(dict(country = country))
        if location is None:
            raise ValueError('Couldn\'t find country "{}".'.format(country))
        return location.longitude, location.latitude


class CentroidLocator(Locator):
    equalarea_crs = cartopy.crs.AlbersEqualArea()
    def __init__(self, borders):
        self.borders = borders

    def get_location(self, country):
        border = self.borders[country]

        centroids = []
        areas = []
        for g in border.geometries():
            centroids.append(g.centroid.xy)
            areas.append(
                self.equalarea_crs.project_geometry(g, border.crs).area)

        centroid = numpy.average(centroids, weights = areas,
                                 axis = 0).squeeze()
        return centroid


class Basemap:
    def __init__(self,
                 extent = (-180, 180, -60, 85),
                 rect = (0, 0, 1, 1),
                 central_longitude = 11,
                 fig = None,
                 *args, **kwargs):
        '''
        Set up the basic map.
        extent is the map limits in longitude and latitude.
        rect is the shape of plot in (0, 1) coordinates.
        '''
        self.fig = fig or pyplot.gcf()

        proj = cartopy.crs.PlateCarree(
            central_longitude = central_longitude)

        self.ax = self.fig.add_axes(rect, projection = proj,
                                    axis_bgcolor = 'none')

        self.ax.set_extent(extent, proj)

        self.ax.background_patch.set_visible(False)
        self.ax.outline_patch.set_visible(False)

        self.do_basemap()

        self.load_borders()

        # self.locator = CentroidLocator(self.borders)
        self.locator = GeocodeLocator()


    def do_basemap(self,
                   zorder = 0,
                   land_color = cartopy.feature.COLORS['land_alt1'],
                   ocean_color = cartopy.feature.COLORS['water'],
                   *args, **kwargs):
        self.ax.add_feature(cartopy.feature.LAND,
                            facecolor = land_color,
                            zorder = zorder)
        self.ax.add_feature(cartopy.feature.OCEAN,
                            facecolor = ocean_color,
                            zorder = zorder)
        self.ax.add_feature(cartopy.feature.COASTLINE, zorder = zorder)
        self.ax.add_feature(cartopy.feature.BORDERS, zorder = zorder)
        # self.ax.add_feature(cartopy.feature.LAKES, alpha=0.5, zorder = zorder)
        # self.ax.add_feature(cartopy.feature.RIVERS, zorder = zorder)


    def load_borders(self):
        border_feature = cartopy.io.shapereader.natural_earth(
            resolution = '110m',
            category = 'cultural',
            name = 'admin_0_countries')
        # The Natural Earth coordinate system
        self.border_crs = cartopy.crs.PlateCarree()

        border_reader = cartopy.io.shapereader.Reader(border_feature)
        self.borders = {}
        for record in border_reader.records():
            country = record.attributes['subunit']
            # country = record.attributes['iso_a3']
            self.borders[country] = cartopy.feature.ShapelyFeature(
                record.geometry, self.border_crs)


    def set_fig_size_for_ax_aspect_ratio(self):
        # Adjust aspect ratio of the figure to match the map.
        # self.fig.canvas.draw()
        self.ax.autoscale_view()
        axw, axh = self.ax.get_position().size
        fw, fh = self.fig.get_size_inches()
        axaspect = axw * fw / axh / fh
        fw_ = fh * axaspect
        self.fig.set_size_inches(fw_, fh, forward = True)


    def choropleth(self, countries, values, *args, **kwargs):
        '''
        Color whole countries depending on the values.
        '''
        cmap_norm = pyplot.cm.ScalarMappable(
            norm = kwargs.pop('norm', None),
            cmap = kwargs.pop('cmap', None))
        cmap_norm.alpha = kwargs.get('alpha')
        vmin = kwargs.pop('vmin', min(values))
        vmax = kwargs.pop('vmax', max(values))
        cmap_norm.set_clim(vmin, vmax)
        cmap_norm.set_array(values)

        for (c, v) in zip(countries, values):
            color = cmap_norm.to_rgba(v)
            try:
                border = self.borders[c]
            except KeyError:
                print('Country "{}" borders not in records.'.format(c))
            self.ax.add_feature(border,
                                facecolor = color,
                                *args,
                                **kwargs)

        # Make pyplot.colorbar() work.
        self.ax._current_image = cmap_norm

        return cmap_norm


    def scatter(self, countries, *args, **kwargs):
        x, y = self.locator.get_locations(countries)
        self.ax.scatter(x, y,
                        transform = self.border_crs,
                        *args,
                        **kwargs)


    def pies(self, countries, values, s = 20,
             wedgeprops = dict(linewidth = 0),
             startangle = 90,
             counterclock = False,
             colors = seaborn.color_palette('bright'),
             *args, **kwargs):
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        radius = numpy.sqrt(s) / numpy.pi
        if not isinstance(radius, collections.abc.Iterable):
            radius = itertools.repeat(radius)
        for (xyz, v, r) in zip(coords_t, numpy.asarray(values), radius):
            x, y, z = xyz
            # Drop NaN's and Inf's.
            v_ = v[numpy.isfinite(v)]
            if len(v_) > 0:
                self.ax.pie(v_,
                            center = (x, y),
                            frame = True,
                            radius = r,
                            wedgeprops = wedgeprops,
                            startangle = startangle,
                            counterclock = counterclock,
                            colors = colors,
                            *args,
                            **kwargs)

    def bars(self, countries, values,
             color = seaborn.color_palette('bright'),
             widthscale = 1,
             heightscale = 1,
             linewidth = 0,
             frame = False,
             *args, **kwargs):
        values = numpy.asarray(values)

        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        for (xyz, v) in zip(coords_t, values):
            x, y, z = xyz

            width = widthscale
            heights = v * heightscale
            # Center on y
            bottom = y - max(heights) / 2
            # Center on x
            N = len(v)
            lefts = x + width * (numpy.arange(N) - N / 2)

            self.ax.bar(lefts, heights, width, bottom,
                        color = color,
                        linewidth = linewidth,
                        *args,
                        **kwargs)

            if frame:
                # draw a box around of height 1 around the bars for scale.
                xmin = min(lefts)
                xmax = max(lefts) + width
                ymin = bottom
                ymax = bottom + heightscale
                self.ax.plot((xmin, xmin, xmax, xmax, xmin),
                             (ymin, ymax, ymax, ymin, ymin),
                             color = 'black',
                             linewidth = 0.5,
                             *args,
                             **kwargs)


    def barhs(self, countries, values,
              color = seaborn.color_palette('bright'),
              widthscale = 1,
              heightscale = 1,
              linewidth = 0,
              frame = False,
              *args, **kwargs):
        values = numpy.asarray(values)

        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        for (xyz, v) in zip(coords_t, values):
            x, y, z = xyz

            height = heightscale
            widths = v * widthscale
            # Center on y
            N = len(v)
            bottoms = y + height * (numpy.arange(N) - N / 2)
            # Center on x
            left = x - max(widths) / 2

            self.ax.barh(bottoms, widths, height, left,
                         color = color,
                         linewidth = linewidth,
                         *args,
                         **kwargs)

            if frame:
                # draw a box around of height 1 around the bars for scale.
                xmin = left
                xmax = left + widthscale
                ymin = min(bottoms)
                ymax = max(bottoms) + height
                self.ax.plot((xmin, xmin, xmax, xmax, xmin),
                             (ymin, ymax, ymax, ymin, ymin),
                             color = 'black',
                             linewidth = 0.5,
                             *args,
                             **kwargs)


    def barhls(self, countries, values,
               color = seaborn.color_palette('bright'),
               widthscale = 1,
               heightscale = 1,
               linewidth = 0,
               frame = False,
               *args, **kwargs):
        values = numpy.asarray(values)

        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        for (xyz, v) in zip(coords_t, values):
            x, y, z = xyz

            height = heightscale
            widths = v * widthscale
            # Center on y
            N = len(v)
            bottoms = y + height * (numpy.arange(N) - N / 2)
            # Center on x
            lefts = x + max(widths) / 2 - widths

            self.ax.barh(bottoms, widths, height, lefts,
                         color = color,
                         linewidth = linewidth,
                         *args,
                         **kwargs)

            if frame:
                # draw a box around of height 1 around the bars for scale.
                xmax = max(lefts + widths)
                xmin = max(lefts + widths) - widthscale
                ymin = min(bottoms)
                ymax = max(bottoms) + height
                self.ax.plot((xmin, xmin, xmax, xmax, xmin),
                             (ymin, ymax, ymax, ymin, ymin),
                             color = 'black',
                             linewidth = 0.5,
                             *args,
                             **kwargs)


    def pyramids(self, countries, values,
             color = seaborn.color_palette('bright'),
             widthscale = 1,
             heightscale = 1,
             linewidth = 0,
             *args, **kwargs):
        values = numpy.asarray(values)

        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        for (xyz, v) in zip(coords_t, values):
            x, y, z = xyz

            height = heightscale
            widths = v * widthscale
            # Center on y
            N = len(v)
            bottoms = y + height * (numpy.arange(N) - N / 2)
            # Center on x
            lefts = x - widths / 2

            self.ax.barh(bottoms, widths, height, lefts,
                         color = color,
                         linewidth = linewidth,
                         *args,
                         **kwargs)


    def star(self, values,
             center = (0, 0),
             scale = 1,
             linewidth = 0.5,
             # linestyle = (0, (1, 2)),
             *args, **kwargs):
        values = numpy.asarray(values)

        kwargs['linewidth'] = linewidth
        # kwargs['linestyle'] = linestyle

        angles = numpy.linspace(0, 2 * numpy.pi, len(values),
                                endpoint = False)
        units = (scale
                 * numpy.array([(numpy.sin(a), numpy.cos(a)) for a in angles]))

        pts = center + values[:, numpy.newaxis] * units
        self.ax.fill(pts[:, 0], pts[:, 1],
                     *args, **kwargs)

        # # Plot envelope.
        # envelope = center + units
        # envelope = numpy.vstack((envelope, envelope[0]))  # Close the polygon.
        # self.ax.plot(envelope[:, 0], envelope[:, 1],
        #              *args, **kwargs)

        # Plot spines.
        color_ = kwargs.pop('color', None)
        # for p in units:
        #     q = center + p
        for p in pts:
            q = p
            self.ax.plot((center[0], q[0]), (center[1], q[1]),
                         color = 'black',
                         # linestyle = ':',
                         *args, **kwargs)


    def stars(self, countries, values,
              scale = 1,
              *args, **kwargs):
        values = numpy.asarray(values)

        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        for (xyz, v) in zip(coords_t, values):
            x, y, z = xyz
            self.star(v,
                      center = (x, y),
                      scale = scale,
                      *args, **kwargs)


    def label(self, countries,
              horizontalalignment = 'center',
              verticalalignment = 'center',
              *args, **kwargs):
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.border_crs, X, Y)
        for (xyz, country) in zip(coords_t, countries):
            x, y, z = xyz
            self.ax.text(x, y, country,
                         horizontalalignment = horizontalalignment,
                         verticalalignment = verticalalignment,
                         *args,
                         **kwargs)


if __name__ == '__main__':
    countries = ('Canada', 'United States of America', 'Mexico',
                 'Guatemala', 'Honduras', 'El Salvador', 'Belize',
                 'Costa Rica', 'Nicaragua', 'Panama')

    data = numpy.random.uniform(size = (len(countries), 5))

    m = Basemap()

    m.choropleth(countries, data[:, 0], zorder = 1)

    m.scatter(countries, c = data[:, 1], s = 40 * data[:, 2],
              zorder = 2)

    data_normalized = data[:, 0 : -1] / data[:, 0 : -1].sum(1)[:, numpy.newaxis]
    m.pies(countries, data_normalized,
           s = 40 * data[-1],
           wedgeprops = dict(linewidth = 0, zorder = 3))
    
    pyplot.show()
