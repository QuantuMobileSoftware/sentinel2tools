from sentinel2download import __version__, __author__
from setuptools import setup, find_packages

install_requires = ['google-cloud-storage==1.32.0',
                    'geopandas==0.8.1',
                    'Rtree==0.9.4', ]

setup(
    name='sentinel2tools',
    version=__version__,
    author=__author__,
    packages=find_packages(),
    # setup_requires=install_requires,
    install_requires=['google-cloud-storage==1.32.0',
                    'geopandas==0.8.1',
                    'Rtree==0.9.4', ],
    # package_data={'sentinel2download': ['grid/*', '../requirements-dev.txt']},
    python_requires='>=3.7',
    dependency_links=['git+ssh://git@github.com/QuantumobileSoftware/sentinel2tools.git@13723_vy_load_sentinel_setup']

)
