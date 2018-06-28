from setuptools import setup, find_packages

setup(
    name='lidaco',
    packages=find_packages(),
    version='0.0.15',
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
