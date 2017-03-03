'''
Make nice graphs on maps.
'''

from collections import abc
import itertools

import cartopy
from matplotlib import animation
from matplotlib import cm
from matplotlib import patches
from matplotlib import pyplot
import numpy
import seaborn
import shapely.geometry
import shapely.ops

from . import locators


_east_hemis = shapely.geometry.box(180, -90, 0, 90)
_west_hemis = shapely.geometry.box(-180, -90, 0, 90)


country_replacements = {
    'Bolivia (Plurinational State of)': 'Bolivia',
    'Congo': 'Republic of Congo',
    "Côte d'Ivoire": 'Ivory Coast',
    'Iran (Islamic Republic of)': 'Iran',
    "Lao People's Democratic Republic": 'Laos',
    'Republic of Moldova': 'Moldova',
    'Russian Federation': 'Russia',
    'Timor-Leste': 'East Timor',
    'United Kingdom of Great Britain and Northern Ireland': 'United Kingdom',
    'Venezuela (Bolivarian Republic of)': 'Venezuela',
    'Viet Nam': 'Vietnam',
}

country_replacements_inv = {v: k for (k, v) in country_replacements.items()}


def convert_country(country, inverse = False):
    '''
    Convert country names used in the datasheet to those used in the maps
    or vice versa.
    '''
    if inverse:
        return country_replacements_inv.get(country, country)
    else:
        return country_replacements.get(country, country)


def convert_countries(countries, inverse = False):
    '''
    Convert multiple country names used in the datasheet
    to those used in the maps or vice versa.
    '''
    return [convert_country(c, inverse = inverse) for c in countries]


def _in_west_hemis(p):
    return p.intersects(_west_hemis)


def _in_east_hemis(p):
    return p.intersects(_east_hemis)


def _wrap_line(line, direction):
    '''
    Move a line that has some points on one side of ±180 longitude
    to entirely one side or the other.
    '''
    if direction.lower() == 'east':
        shift = [360, 0]
    elif direction.lower() == 'west':
        shift = [-360, 0]
    else:
        raise ValueError("Unknown direction '{}'!".format(direction))
    return numpy.asarray(line.coords) + shift


def _wrap_polygon(poly, direction):
    '''
    Move a polygon that has some points on one side of ±180 longitude
    to entirely one side or the other.
    '''
    e = _wrap_line(poly.exterior, direction)
    i = list(map(_wrap_line, poly.interiors, direction))
    return shapely.geometry.Polygon(e, i)


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
                                    anchor = 'N',
                                    facecolor = 'none')
        self.ax.set_extent(extent, proj)
        self.ax.background_patch.set_visible(False)
        self.ax.outline_patch.set_visible(False)
        self._do_basemap()
        self._load_borders()
        self._load_tiny_points()
        # self.locator = locators.CentroidLocator(self.borders)
        self.locator = locators.GeocodeLocator()

    def _do_basemap(self,
                    zorder = 0,
                    land_color = cartopy.feature.COLORS['land_alt1'],
                    ocean_color = cartopy.feature.COLORS['water'],
                    *args, **kwargs):
        LAND = cartopy.feature.LAND
        OCEAN = cartopy.feature.OCEAN
        # LAND = cartopy.feature.NaturalEarthFeature('physical',
        #                                            'land',
        #                                            '50m',
        #                                            edgecolor = 'face')
        # OCEAN = cartopy.feature.NaturalEarthFeature('physical',
        #                                             'ocean',
        #                                             '50m',
        #                                             edgecolor = 'face')
        self.ax.add_feature(LAND,
                            facecolor = land_color,
                            zorder = zorder)
        self.ax.add_feature(OCEAN,
                            facecolor = ocean_color,
                            zorder = zorder)

        # self.ax.add_feature(cartopy.feature.COASTLINE, zorder = zorder)
        # self.ax.add_feature(cartopy.feature.BORDERS, zorder = zorder)
        # self.ax.add_feature(cartopy.feature.LAKES, alpha=0.5, zorder = zorder)
        # self.ax.add_feature(cartopy.feature.RIVERS, zorder = zorder)

    def _load_natural_earth(self, attr_for_key, resolution, category, name):
        feature = cartopy.io.shapereader.natural_earth(
            resolution = resolution,
            category = category,
            name = name)
        # The Natural Earth coordinate system
        crs = cartopy.crs.PlateCarree()
        reader = cartopy.io.shapereader.Reader(feature)
        geometries = {}
        for record in reader.records():
            country = record.attributes[attr_for_key]
            if country not in geometries:
                geometries[country] = record.geometry
            else:
                geometries[country] = geometries[country].union(record.geometry)
        return {k: cartopy.feature.ShapelyFeature([v], crs)
                for (k, v) in geometries.items()}

    def _load_borders(self):
        self.borders = self._load_natural_earth('sovereignt',
                                                '110m',
                                                'cultural',
                                                'admin_0_countries')

        # Use higher resolution if missing in lower resolution.
        borders1 = self._load_natural_earth('sovereignt',
                                            '50m',
                                            'cultural',
                                            'admin_0_countries')
        for (k, v) in borders1.items():
            if k not in self.borders:
                self.borders[k] = v

        self._tweak_borders()

    def _tweak_borders(self):
        self._append_somaliland_to_somalia()

        # Make Russia continuous across longitude 180
        # by mapping it all to the Eastern Hemisphere.
        self._map_to_hemisphere('Russia', 'east')

        # Make USA continuous across longitude 180
        # by mapping it all to the Western Hemisphere.
        self._map_to_hemisphere('United States of America', 'west')

        self._tweak_antarctica()

    def _append_somaliland_to_somalia(self):
        b_somalia = self.borders['Somalia']
        # Remove Somaliland from dict.
        b_somaliland = self.borders.pop('Somaliland')
        mp = b_somalia._geoms[0].union(b_somaliland._geoms[0])
        self.borders['Somalia'] = cartopy.feature.ShapelyFeature([mp],
                                                                 b_somalia.crs)

    def _map_to_hemisphere(self, country, hemisphere):
        if hemisphere.lower() == 'east':
            in_other_hemis = _in_west_hemis
        elif hemisphere.lower() == 'west':
            in_other_hemis = _in_east_hemis
        else:
            raise ValueError("Unknown hemisphere '{}'!".format(hemisphere))
        polygons = self.borders[country]._geoms[0].geoms
        mp = shapely.geometry.MultiPolygon()
        for p in polygons:
            if in_other_hemis(p):
                p = _wrap_polygon(p, hemisphere)
            mp = mp.union(p)
        self.borders[country] = cartopy.feature.ShapelyFeature(
            [mp], self.borders[country].crs)

    def _tweak_antarctica(self):
        central_longitude = self.ax.projection.proj4_params['lon_0']
        map_edge_l = central_longitude - 180
        map_edge_r = central_longitude + 180
        south_pole = shapely.geometry.Point((0, -90))
        polygons = self.borders['Antarctica']._geoms[0].geoms
        mp = shapely.geometry.MultiPolygon()
        for p in polygons:
            if p.intersects(south_pole):
                # Dope dupe closing point at end.
                x, y = numpy.asarray(p.exterior.coords)[ : -1].T
                # Find and remove any South Poles.
                ix = numpy.isclose(y, -90)
                x = numpy.compress(~ix, x)
                y = numpy.compress(~ix, y)
                # Transform points to be on the correct side of map LR edge.
                x = numpy.where(x < map_edge_l, x + 360, x)
                x = numpy.where(x > map_edge_r, x - 360, x)
                xy = numpy.column_stack((x, y))
                # Add South Pole and edge points in the right place.
                map_edge_y = numpy.interp(map_edge_l, x, y, period = 360)
                i = x.argmax()
                XY = numpy.vstack((xy[ : i + 1],
                                   (map_edge_r, map_edge_y),
                                   (map_edge_r, -90),
                                   (map_edge_l, -90),
                                   (map_edge_l, map_edge_y),
                                   xy[i + 1 : ]))

                p = shapely.geometry.Polygon(XY, list(p.interiors))
            mp = mp.union(p)
        self.borders['Antarctica'] = cartopy.feature.ShapelyFeature(
            [mp], self.borders['Antarctica'].crs)

    def _load_tiny_points(self):
        self.tiny_points = self._load_natural_earth('subunit',
                                                    '50m',
                                                    'cultural',
                                                    'admin_0_tiny_countries')

    def _get_colors(self, c):
        if isinstance(c, str):
            return seaborn.color_palette(c)
        else:
            return c

    def tighten(self, aspect_adjustment = 1):
        '''
        Adjust aspect ratio of the figure to match the map.
        '''
        # self.fig.canvas.draw()
        self.ax.autoscale_view()
        w, h = self.fig.get_size_inches()
        extent = self.ax.get_extent()
        aspect = ((extent[3] - extent[2]) / (extent[1] - extent[0])
                  * aspect_adjustment)
        self.fig.set_size_inches(w, w * aspect, forward = True)

    def draw_borders(self, countries, zorder = 0, facecolor = 'None',
                     *args, **kwargs):
        for c in countries:
            try:
                border = self.borders[c]
            except KeyError:
                print('Country "{}" borders not in records.'.format(c))
            else:
                self.ax.add_feature(border, facecolor = 'None',
                                    zorder = zorder,
                                    *args, **kwargs)

    def choropleth(self, countries, values, tiny_points_size = 0,
                   *args, **kwargs):
        '''
        Color whole countries depending on the values.
        '''
        cmap_norm = cm.ScalarMappable(norm = kwargs.pop('norm', None),
                                      cmap = kwargs.pop('cmap', None))
        cmap_norm.alpha = kwargs.get('alpha')
        vmin = kwargs.pop('vmin', min(values))
        vmax = kwargs.pop('vmax', max(values))
        cmap_norm.set_clim(vmin, vmax)
        cmap_norm.set_array(values)
        for (c, v) in zip(countries, values):
            if numpy.isfinite(v):
                color = cmap_norm.to_rgba(v)
                try:
                    border = self.borders[c]
                except KeyError:
                        print('Country "{}" borders not in records.'.format(c))
                else:
                    self.ax.add_feature(border,
                                        facecolor = color,
                                        *args,
                                        **kwargs)

            if tiny_points_size > 0:
                try:
                    point = self.tiny_points[c]
                except KeyError:
                    pass
                else:
                    x, y = zip(*(p.xy for p in point.geometries()))
                    self.ax.scatter(x, y,
                                    transform = point.crs,
                                    facecolor = color,
                                    s = tiny_points_size,
                                    *args,
                                    **kwargs)

        # Make pyplot.colorbar() work.
        self.ax._current_image = cmap_norm
        return cmap_norm

    def choropleth_animate(self, countries, t, values,
                           label_coords = None,
                           *args, **kwargs):
        self.choropleth_preinit(countries, t, values,
                                label_coords = label_coords,
                                *args, **kwargs)
        return animation.FuncAnimation(self.fig,
                                       self.choropleth_update,
                                       frames = len(values),
                                       init_func = self.choropleth_init,
                                       repeat = False,
                                       blit = True)

    def choropleth_preinit(self, countries, t, values,
                           label_coords = None,
                           *args, **kwargs):
        '''
        Set up animated choropleth.
        '''
        self.cmap_norm = cm.ScalarMappable(norm = kwargs.pop('norm', None),
                                           cmap = kwargs.pop('cmap', None))
        self.cmap_norm.alpha = kwargs.get('alpha')
        self.cmap_norm.set_clim(vmin = kwargs.pop('vmin', None),
                                vmax = kwargs.pop('vmax', None))
        self.cmap_norm.set_array(values)
        self._countries = countries
        self._t = t
        self._values = values
        self._artists = []
        self._artist_map = {}
        for (i, c) in enumerate(self._countries):
            try:
                border = self.borders[c]
            except KeyError:
                print('Country "{}" borders not in records.'.format(c))
            else:
                self._artists.append(self.ax.add_feature(border,
                                                         facecolor = 'None',
                                                         *args,
                                                         **kwargs))
                self._artist_map[c] = i
        if label_coords is not None:
            X, Y = label_coords
            self._label = self.text_coords(X, Y, '',
                                           fontdict = dict(size = 20,
                                                           weight = 'bold'),
                                           horizontalalignment = 'left')
        else:
            self._label = None
        # Make pyplot.colorbar() work.
        self.ax._current_image = self.cmap_norm

    def choropleth_init(self):
        retval = []
        if self._label is not None:
            retval.append(self._label)
        retval.extend(self._artists)
        return retval

    def choropleth_update(self, i):
        '''
        Update country colors.
        '''
        retval = []
        if self._label is not None:
            print('Make frame for t = {:g}.'.format(self._t[i]))
            self._label.set_text(int(self._t[i]))
            self._label.stale = True
            retval.append(self._label)
        for (c, v) in zip(self._countries, self._values[i]):
            ix = self._artist_map[c]
            self._artists[ix]._kwargs['facecolor'] = self.cmap_norm.to_rgba(v)
            self._artists[ix].stale = True
        retval.extend(self._artists)
        return retval

    def scatter(self, countries, *args, **kwargs):
        x, y = self.locator.get_locations(countries)
        self.ax.scatter(x, y,
                        transform = self.locator.crs,
                        *args,
                        **kwargs)
        self.draw_borders(countries)

    def pies(self, countries, values, s = 20,
             wedgeprops = dict(linewidth = 0),
             startangle = 90,
             counterclock = False,
             colors = 'bright',
             *args, **kwargs):
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.locator.crs, X, Y)
        radius = numpy.sqrt(s) / numpy.pi
        if not isinstance(radius, abc.Iterable):
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
                            colors = self._get_colors(colors),
                            *args,
                            **kwargs)
        self.draw_borders(countries)

    def bars(self, countries, values,
             color = 'bright',
             widthscale = 1,
             heightscale = 1,
             linewidth = 0,
             frame = False,
             *args, **kwargs):
        values = numpy.asarray(values)
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.locator.crs, X, Y)
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
                        color = self._get_colors(color),
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
        self.draw_borders(countries)

    def barhs(self, countries, values,
              color = 'bright',
              widthscale = 1,
              heightscale = 1,
              linewidth = 0,
              frame = False,
              *args, **kwargs):
        values = numpy.asarray(values)
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.locator.crs, X, Y)
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
                         color = self._get_colors(color),
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
        self.draw_borders(countries)

    def barh_coords(self, X, Y, values,
                    color = 'bright',
                    widthscale = 1,
                    heightscale = 1,
                    linewidth = 0,
                    frame = False,
                    *args, **kwargs):
        values = numpy.asarray(values)
        x, y = self.ax.projection.transform_point(
            X, Y, self.locator.crs)
        height = heightscale
        widths = values * widthscale
        # Center on y
        N = len(values)
        bottoms = y + height * (numpy.arange(N) - N / 2)
        # Center on x
        left = x - max(widths) / 2
        self.ax.barh(bottoms, widths, height, left,
                     color = self._get_colors(color),
                     linewidth = linewidth,
                     *args,
                     **kwargs)

    def barhls(self, countries, values,
               color = 'bright',
               widthscale = 1,
               heightscale = 1,
               linewidth = 0,
               frame = False,
               *args, **kwargs):
        values = numpy.asarray(values)
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.locator.crs, X, Y)
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
                         color = self._get_colors(color),
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
        self.draw_borders(countries)

    def pyramids(self, countries, values,
             color = 'bright',
             widthscale = 1,
             heightscale = 1,
             linewidth = 0,
             *args, **kwargs):
        values = numpy.asarray(values)
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.locator.crs, X, Y)
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
                         color = self._get_colors(color),
                         linewidth = linewidth,
                         *args,
                         **kwargs)
        self.draw_borders(countries)

    def _star(self, values,
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
            self.locator.crs, X, Y)
        for (xyz, v) in zip(coords_t, values):
            x, y, z = xyz
            self._star(v,
                       center = (x, y),
                       scale = scale,
                       *args, **kwargs)
        self.draw_borders(countries)

    def label(self, countries,
              horizontalalignment = 'center',
              verticalalignment = 'center',
              replace = {'Democratic Republic of the Congo': 'DR Congo'},
              fontdict = dict(size = 3,
                              color = 'black',
                              weight = 'bold'),
              *args, **kwargs):
        X, Y = self.locator.get_locations(countries)
        coords_t = self.ax.projection.transform_points(
            self.locator.crs, X, Y)
        for (xyz, country) in zip(coords_t, countries):
            x, y, z = xyz
            if country in replace:
                label = replace[country]
            else:
                label = country
            self.ax.text(x, y, label,
                         horizontalalignment = horizontalalignment,
                         verticalalignment = verticalalignment,
                         fontdict = fontdict,
                         *args,
                         **kwargs)
        # self.draw_borders(countries)

    def text_coords(self, X, Y, s,
                   *args, **kwargs):
        x, y = self.ax.projection.transform_point(
            X, Y, self.locator.crs)
        return self.ax.text(x, y, s, *args, **kwargs)

    def rectangle_coords(self, X, Y, w, h, *args, **kwargs):
        xy = self.ax.projection.transform_point(
            X, Y, self.locator.crs)
        self.ax.add_patch(patches.Rectangle(xy, w, h, *args, **kwargs))

    def colorbar(self, orientation = 'horizontal', fraction = 0.2,
                 pad = 0, shrink = 0.8, panchor = False,
                 *args, **kwargs):
        cbar = self.fig.colorbar(self.ax._current_image,
                                 orientation = orientation,
                                 fraction = fraction,
                                 pad = pad,
                                 shrink = shrink,
                                 panchor = panchor,
                                 *args, **kwargs)
        # Try to work around ugliness from viewer bugs.
        cbar.solids.set_edgecolor('face')
        cbar.solids.drawedges = False
        return cbar

    def savefig(self, *args, **kwargs):
        self.fig.savefig(*args, **kwargs)

    def show(self, *args, **kwargs):
        pyplot.show(*args, **kwargs)
