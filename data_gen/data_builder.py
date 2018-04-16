from time import sleep

from data_acquire.geo_structures import *
from data_acquire.terrain_party import download_heightmap
from data_acquire.g_maps import download_satellite_image
import os
import zipfile
from shutil import copyfile
import random
import numpy as np
from keras.preprocessing.image import load_img, img_to_array
from keras import backend as K
from PIL import Image

def get_random_locations(count, bounds, seed=7):
    random.seed(seed)
    i = 0
    while i < count:
        i += 1
        yield Location(
            bounds.min.lat + random.uniform(0, 1) * (bounds.max.lat - bounds.min.lat),
            bounds.min.lon + random.uniform(0, 1) * (bounds.max.lon - bounds.min.lon)
        )


def find_file_path(parent_dir, name_fragment):
    for file in os.listdir(parent_dir):
        if name_fragment in file:
            return os.path.join(parent_dir, file)


def download_location(loc, path="./",overwrite=False):

    bounds = BoundingBox(loc.lat, loc.lon, 10)

    # create directory for data storage
    DATA_SET_DIRECTORY = os.path.join(path, str(loc))
    DOWNLOAD_DIRECTORY = os.path.join(DATA_SET_DIRECTORY, "download")
    ZIP_FILE = os.path.join(DOWNLOAD_DIRECTORY, "terrain_party.zip")
    EXTRACTED_ZIP_FILE = os.path.join(DOWNLOAD_DIRECTORY, "terrain_party")

    SATELLITE_IMG = os.path.join(DATA_SET_DIRECTORY, "satellite.png")
    HEIGHTMAP_IMG = os.path.join(DATA_SET_DIRECTORY, "heightmap.png")

    if not overwrite and os.path.exists(DATA_SET_DIRECTORY):
        print("already exists")
        return

    os.makedirs(DATA_SET_DIRECTORY)
    os.makedirs(DOWNLOAD_DIRECTORY)

    download_heightmap(bounds, ZIP_FILE)

    with zipfile.ZipFile(ZIP_FILE, "r") as zip_ref:
        zip_ref.extractall(path=EXTRACTED_ZIP_FILE)

    merged_heightmap_path = find_file_path(EXTRACTED_ZIP_FILE, "Merged")
    copyfile(merged_heightmap_path, HEIGHTMAP_IMG)

    download_satellite_image(bounds, SATELLITE_IMG)

def load_training_data(target_size, root_path="./data"):

    x = []
    y = []

    table = [i / 256 for i in range(65536)]

    for data_folder in os.listdir(root_path):
        temp_path = os.path.join(root_path, data_folder)
        satellite_path = os.path.join(temp_path, "satellite.png")
        heightmap_path = os.path.join(temp_path, "heightmap.png")

        if not os.path.exists(satellite_path) or not os.path.exists(heightmap_path):
            continue

        satellite_image = Image.open(heightmap_path)
        satellite_image = satellite_image.point(table, 'L')
        satellite_image = satellite_image.resize(target_size, Image.ANTIALIAS)

        x.append(
            np.asarray(
                satellite_image,
                dtype=K.floatx()
            )
        )
        y.append(
            np.asarray(
                load_img(satellite_path,
                         grayscale=True, target_size=target_size, interpolation='bilinear'),
                dtype=K.floatx()
            )
        )

    return np.array(x), np.array(y)


if __name__ == '__main__':

    for location in get_random_locations(5000, BoundingBox(47.040469, 7.952049, 500)):
        print(str(location))
        download_location(location, './data')