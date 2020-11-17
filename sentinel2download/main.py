import os
import re
import subprocess

from google.cloud import storage

from sentinel2download.downloader import Sentinel2Downloader


if __name__ == '__main__':
    print("YES")

    loader = Sentinel2Downloader()
    start_date = "2020-07-01"
    end_date = "2020-07-05"
    tiles = {'36UYB', }
    type_ = 'L1С'
    output_dir = '../data'
    cores = 2

    loader.download(type_, tiles, start_date, end_date, output_dir, cores=2)




