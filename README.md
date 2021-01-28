# sentinel2tools

## Repository for downloading, processing Sentinel-2 satellite images

* Downloading images from [Sentinel-2 google data storage](https://cloud.google.com/storage/docs/public-datasets/sentinel-2)
* Using [Google Api Key](https://support.google.com/googleapi/answer/6251787?hl=en)

### Installation
1. Install dependencies, see Dockerfile
2. Add to requirements.txt in the project or use `pip install`:<br>
`git+https://github.com/QuantuMobileSoftware/sentinel2tools.git@<commit-ref>`
<br> or
`git+ssh://git@github.com/QuantumobileSoftware/sentinel2tools.git@<commit-ref>`

### Usage

See `examples/download.py` on how to download Sentinel-2 images. 
For more details see docs in `Sentinel2Downloader.download()` method

See `examples/conversion.py` on how to convert raw Sentinel-2 L1C products into L2A products. 
In order to convert Sentinel-2 products need to be fully downloaded (.SAFE folder), 
to achieve it use _**full_download**_ option of `Sentinel2Downloader`.
