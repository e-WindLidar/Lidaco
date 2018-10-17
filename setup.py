from setuptools import setup, find_packages


# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='lidaco',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    version='0.0.28',
    description='Wind Lidar Data Converter.',
    author='e-WindLidar',
    entry_points={
        'console_scripts': [
            'lidaco = lidaco.__main__:main'
        ],
    },
    # scripts=['bin/lidaco'],
    author_email='e-windlidar@googlegroups.com',
    url='https://github.com/e-WindLidar/Lidaco',  # use the URL to the github repo
    # download_url='https://github.com/e-WindLidar/Lidaco/archive/v0.0.1.tar.gz',
    keywords=['wind', 'lidar', 'data', 'converter'],  # arbitrary keywords
    classifiers=[],
    install_requires=[
        'pyyaml',
        'netCDF4',
        'lxml'
    ]
)
