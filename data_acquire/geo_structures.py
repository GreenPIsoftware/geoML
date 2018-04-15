import math


# degrees to radians
def deg2rad(degrees):
    return math.pi * degrees / 180.0


# radians to degrees
def rad2deg(radians):
    return 180.0 * radians / math.pi


# Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]


# Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
def WGS84EarthRadius(lat):
    # http://en.wikipedia.org/wiki/Earth_radius
    An = WGS84_a * WGS84_a * math.cos(lat)
    Bn = WGS84_b * WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt((An * An + Bn * Bn) / (Ad * Ad + Bd * Bd))


class Location:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def str_lon_lat(self):
        return "%s,%s" % (self.lon, self.lat)

    def __str__(self):
        return "%s,%s" % (self.lat, self.lon)


class BoundingBox:

    def __init__(self, lat, lon, length):
        lat_rad = deg2rad(lat)
        lon_rad = deg2rad(lon)
        half_side = 1000.0 * length/2.0

        # Radius of Earth at given latitude
        radius = WGS84EarthRadius(lat_rad)
        # Radius of the parallel at given latitude
        p_radius = radius * math.cos(lon_rad)

        lat_min = lat_rad - half_side / radius
        lat_max = lat_rad + half_side / radius
        lon_min = lon_rad - half_side / p_radius
        lon_max = lon_rad + half_side / p_radius

        self.min = Location(rad2deg(lat_min), rad2deg(lon_min))
        self.max = Location(rad2deg(lat_max), rad2deg(lon_max))
        self.center = Location(lat, lon)
