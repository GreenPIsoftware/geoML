import shutil
import requests
from data_acquire.geo_structures import *


def download_heightmap(box, name):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'terrain.party',
        'Referer': 'http://terrain.party/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
    }

    params = (
        ('box', box.min.str_lon_lat() + "," + box.max.str_lon_lat()),
        ('name', str(box.center)),
    )

    response = requests.get('http://terrain.party/api/export', headers=headers, params=params, stream=True)
    if response.status_code == 200:
        with open(name, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
    else:
        raise Exception("server responded with: " + str(response.status_code))

if __name__ == '__main__':
    #13.673211537245582,51.013227975509665,13.816273262754414,51.10305945245227
    download_heightmap(BoundingBox(51.058499, 13.744305, 10), "Dresden1")
