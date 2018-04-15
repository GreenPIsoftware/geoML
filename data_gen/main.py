from data_acquire.geo_structures import *
from data_acquire.terrain_party import download_heightmap
from data_acquire.g_maps import download_satellite_image
import os
import zipfile

locations = [
    Location(50.842372, 14.221700)
]

def download_location(loc, path="./",overwrite=False):

    bounds = BoundingBox(loc.lat, loc.lon, 10)

    # create directory for data storage
    path = os.path.join(path, str(loc))
    if not overwrite and os.path.exists(path):
        print("already exists")
        return

    os.makedirs(path)

    temp_heightmap = os.path.join(path, "temp_heightmap")
    os.makedirs(temp_heightmap)
    download_heightmap(bounds, os.path.join(temp_heightmap, str(loc)))

    with zipfile.ZipFile(os.path.join(temp_heightmap, str(loc)) + ".zip", "r") as zip_ref:
        zip_ref.extractall()


if __name__ == '__main__':

    for location in locations:
        download_location(location, './data')