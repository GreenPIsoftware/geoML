import shutil

import numpy as np
import math
import requests
from data_acquire.geo_structures import BoundingBox

# Specifies the size of the map (in pixels).
TILE_SIZE = 256
# This is the Maps API key for running on localhost:8080
GM_STATIC_API_KEY = 'AIzaSyCNfHEobjXhaLIIIlLzkTr_0uhXdmwBOKc'


def radec2latlon(radec):
    """
radec2latlon(radec)

    Convert R.A./Dec to Lat./Lon.

    """
    # latlon = np.zeros(2.)
    latlon = np.array([radec[1], 360. - radec[0]])
    # latlon = np.array([radec[1],(360.-radec[0])/np.cos(radec[1]/360.*2*np.pi)])
    # latlon = np.array([radec[1],radec[0]])
    return latlon


class Point:
    """
Stores a simple (x,y) point.  It is used for storing x/y pixels.

Attributes:
    x: An int for a x value.
    y: An int for a y value.

http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py

    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilex = x * 1. / TILE_SIZE
        self.tiley = y * 1. / TILE_SIZE

    def __str__(self):
        return '(%s, %s)' % (self.x, self.y)

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return other.x == self.x and other.y == self.y


class MercatorProjection:
    """
  MercatorProjection

  Calculates map zoom levels based on bounds or map points.

  This class contains functions that are required for calculating the zoom
  level for a point or a group of points on a static map.  Usually the Maps API
  does the zoom for you when you specify a point, but not on static maps.

  Attributes:
      pixels_per_lon_degree: A list for the number of pixels per longitude
        degree for each zoom.
      pixels_per_lon_radian: A list for the number of pixels per longitude
        radian for each zoom.
      pixel_origo: List of number of x,y pixels per zoom.
      pixel_range: The range of pixels per zoom.
      pixels: Number of pixels per zoom.
      zoom_levels: A list of numbers representing each zoom level to test.

  http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py

    """

    def __init__(self, zoom_levels=18):
        self.pixels_per_lon_degree = []
        self.pixels_per_lon_radian = []
        self.pixel_origo = []
        self.pixel_range = []
        self.pixels = TILE_SIZE
        zoom_levels = list(range(0, zoom_levels))
        for z in zoom_levels:
            origin = self.pixels / 2.0
            self.pixels_per_lon_degree.append(self.pixels / 360.0)
            self.pixels_per_lon_radian.append(self.pixels / (2.0 * np.pi))
            self.pixel_origo.append(Point(origin, origin))
            self.pixel_range.append(self.pixels)
            self.pixels *= 2.0

    def CalcWrapWidth(self, zoom):
        return self.pixel_range[zoom]

    def FromLatLngToPixel(self, lat_lng, zoom):
        """Given lat/lng and a zoom level, returns a Point instance.

        This method takes in a lat/lng and a _test_ zoom level and based on that it
        calculates at what pixel this lat/lng would be on the map given the zoom
        level.  This method is used by CalculateBoundsZoomLevel to see if this
        _test_ zoom level will allow us to fit these bounds in our given map size.

        Args:
          lat_lng: A list of a lat/lng point [lat, lng]
          zoom: A list containing the width/height in pixels of the map.

        Returns:
          A Point instance in pixels.
        """
        o = self.pixel_origo[zoom]
        x = round(o.x + lat_lng.lon * self.pixels_per_lon_degree[zoom])
        siny = bound(np.sin(np.deg2rad(lat_lng.lat)),
                     -0.9999, 0.9999)
        y = round(o.y + 0.5 * np.log((1 + siny) /
                                     (1 - siny)) * -self.pixels_per_lon_radian[zoom])
        return Point(x, y)

    def CalculateBoundsZoomLevel(self, bounds):
        """Given lat/lng bounds, returns map zoom level.

        This method is used to take in a bounding box (southwest and northeast
        bounds of the map view we want) and a map size and it will return us a zoom
        level for our map.  We use this because if we take the bottom left and
        upper right on the map we want to show, and calculate what pixels they
        would be on the map for a given zoom level, then we can see how many pixels
        it will take to display the map at this zoom level.  If our map size is
        within this many pixels, then we have the right zoom level.

        Args:
          bounds: A list of length 2, each holding a list of length 2. It holds
            the southwest and northeast lat/lng bounds of a map.  It should look
            like this: [[southwestLat, southwestLat], [northeastLat, northeastLng]]
          view_size: A list containing the width/height in pixels of the map.

        Returns:
          An int zoom level.
        """
        zmax = 18
        zmin = 0
        bottom_left = bounds.min
        top_right = bounds.max
        backwards_range = list(range(zmin, zmax))
        backwards_range.reverse()
        for z in backwards_range:
            bottom_left_pixel = self.FromLatLngToPixel(bottom_left, z)
            top_right_pixel = self.FromLatLngToPixel(top_right, z)
            if bottom_left_pixel.x > top_right_pixel.x:
                bottom_left_pixel.x -= self.CalcWrapWidth(z)
            if abs(top_right_pixel.x - bottom_left_pixel.x) <= TILE_SIZE \
                    and abs(top_right_pixel.y - bottom_left_pixel.y) <= TILE_SIZE:
                return z
        return 0


def bound(value, opt_min, opt_max):
    """
    Returns value if in min/max, otherwise returns the min/max.

  Args:
    value: The value in question.
    opt_min: The minimum the value can be.
    opt_max: The maximum the value can be.

  Returns:
    An int that is either the value passed in or the min or the max.

  http://code.google.com/p/google-ajax-examples/source/browse/trunk/nonjslocalsearch/localSearch.py
    """
    if opt_min is not None:
        value = max(value, opt_min)
    if opt_max is not None:
        value = min(value, opt_max)
    return value


def download_satellite_image(bounding_box, path=""):
    zoom_level = MercatorProjection().CalculateBoundsZoomLevel(
        bounding_box
    )

    query_string = "https://maps.googleapis.com/maps/api/staticmap?center=" + str(bounding_box.center) + "&zoom=" + str(
        zoom_level) + "&size=" + str(TILE_SIZE) + "x" + str(
        TILE_SIZE) + "&maptype=satellite&key=" + GM_STATIC_API_KEY

    response = requests.get(query_string, stream=True)

    if response.status_code != 200:
        raise Exception("server returned status: " + response.status_code)

    with open(path, 'wb') as f:
        shutil.copyfileobj(response.raw, f)


def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def get_approximate_img(location, zoom):

    x, y = deg2num(location.lat, location.lon, zoom)
    query_string = "http://mt1.google.com/vt/lyrs=s&x=" + str(x) + "&y=" + str(y) + "&z=" + str(zoom)

    response = requests.get(query_string, stream=True)

    if response.status_code != 200:
        raise Exception("server returned status: " + response.status_code)

    with open("img.png", 'wb') as f:
        shutil.copyfileobj(response.raw, f)


if __name__ == '__main__':
    download_satellite_image(
        BoundingBox(51.058499, 13.744305, 10)
    )
