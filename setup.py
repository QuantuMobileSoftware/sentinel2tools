from setuptools import setup, find_packages
import subprocess
from distutils.command.install import install

__version__ = '1.1'
__author__ = 'Quantumobile'

install_requires = ['google-cloud-storage==1.32.0',
                    'geopandas==0.8.1',
                    'Rtree==0.9.4', ]


class CustomInstall(install):
    def run(self):
        install.run(self)
        subprocess.call('sen2cor_install.sh')


setup(
    name='sentinel2tools',
    version=__version__,
    author=__author__,
    description="Repository for downloading, processing Sentinel-2 satellite images",
    url="https://github.com/QuantuMobileSoftware/sentinel2tools/",
    packages=find_packages(),
    install_requires=install_requires,
    package_data={'sentinel2download': ['grid/*', ]},
    python_requires='>=3.7',
    scripts=['scripts/sen2cor_install.sh'],
    cmdclass={'install': CustomInstall}
)
