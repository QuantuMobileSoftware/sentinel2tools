# sentinel2tools

## Repository for downloading, basic processing sentinel2 satellite images

* Downloading images from [sentinel2 google data storage](https://cloud.google.com/storage/docs/public-datasets/sentinel-2)
* Using [Google Api Key](https://support.google.com/googleapi/answer/6251787?hl=en)

### Installation
1. Install [libspatialindex](https://libspatialindex.org/en/latest/). Add it to base docker image <br>
`apt-get install -y gcc libspatialindex-dev python3-dev`
2. Add to requirements.txt in the project or use `pip install`:<br>
`git+ssh://git@github.com/QuantumobileSoftware/sentinel2tools.git@<branch-name>`, where `branch-name` - 
`main, master or actual one`.

### Usage

```
from sentinel2download.downloader import Sentinel2Downloader
from sentinel2download.overlap import Sentinel2Overlap


aoi_path = "aoi.geojson" # input geojson 

overlap = Sentinel2Overlap(aoi_path) 
tiles = overlap.overlap() # finds tiles to load

api_key = "key.json" # path to google api key

loader = Sentinel2Downloader(api_key)

product_type = 'L2A'  # or L1C. L2A prefferable 
start_date = "2020-01-01"
end_date = "2020-01-03"
output_dir = '../sentinel2imagery' # path to dir for saving images

BANDS = {'TCI', } # Bands to load

loaded = loader.download(product_type,
                         tiles,
                         start_date=start_date,
                         end_date=end_date,
                         output_dir=output_dir,
                         bands=BANDS, )
                          

print(f"Load information")
for item in loaded:
    print(item)

print("Execution ended")
```

##### For more parameters see docs in download() method
