from .core.Builder import Builder
from .common.Logger import Logger

from os import path
import argparse


def main():
    """
        Converter command entry point.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument('-C', '--config-file', default='config.yaml',
                        help='Configuration file path (default: configs.xml)')
    parser.add_argument('-O', '--output-format', default=None,
                        help='Output format produced: NetCDF4, HDF5, metainfo,...')
    parser.add_argument('-I', '--input-format', default=None,
                        help='Input files format as produced by the Lidar: S100, V1,...')
    parser.add_argument('-D', '--input-path', default=None,
                        help='Input datasets directory path')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='explain what is being done')
    parser.add_argument('-V', '--version', action='store_true', default=False,
                        help='display version information and exit')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Shows internal error messages')
    parser.add_argument('--context', default='',
                        help='Path to which relative paths, such as config-file or data-path, are resolved.')

    args = parser.parse_args()

    Logger.set_args(args)
    Logger.header()

    if not args.version:
        args_dict = vars(args)
        args_dict.pop('verbose')
        args_dict.pop('version')
        args_dict.pop('debug')
        builder = Builder(**args_dict)
        builder.build()
    else:
        Logger.log('about')
