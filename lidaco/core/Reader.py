from abc import ABC, abstractmethod
from os import listdir
from itertools import groupby
from lidaco.common.Logger import Logger


class Reader(ABC):
    """
    Specifies a reader class API and implements some common methods.
    """

    out_path = ''

    def __init__(self, data_grouping):
        """
        Constructor.
        :param data_grouping: If data_grouping is True then group_id method must be implemented.
        """
        super().__init__()
        self.data_grouping = data_grouping
        self.configs = None

    def fetch_input_files(self, dir_path):
        """
        Lists and filters input data files. If the reader specifies a group_by function,
        it also groups files by that value, return a dictionary group => [files].
        :param dir_path: directory containing input data files
        :return: [files] | {group => [files]}
        """
        Logger.info('searching_in_path', dir_path)
        files = [f for f in listdir(dir_path) if self.accepts_file(f)]
        [Logger.info('found', f) for f in files]

        if len(files) == 0:
            Logger.error('files_not_found')

        if self.data_grouping:
            Logger.info('grouping')
            files.sort()
            input_files = []

            for k, g in groupby(files, self.group_id):
                input_files.append({'id': k, 'files': list(g)})
        else:
            input_files = [{'id': f, 'files': f} for f in files]

        input_files.sort(key=lambda group: group['id'])
        return input_files

    @abstractmethod
    def accepts_file(self, filename):
        """
        Checks if a file is valid. Used by the converter to filter applicable files.
        :param filename: e.g., 20161211135000_wind.txt, WLS7-164_2016_09_19__00_00_00.rtd
        :return: boolean
        """
        pass

    @abstractmethod
    def output_filename(self, input_filename):
        """
        Checks if a file is valid. Used by the converter to filter applicable files.
        :param input_filename: input filename or group name when group_by is used.
        When output_block_size is set, the output_filename is set wrt the first file/group's name
        :return: output filename (without extension)
        """
        pass

    def required_params(self):
        """
        Specifies what parameters the user must specify in the configuration files.
        It should be overriten by the reader implementation when needed.
        The conversion will halt if any of these are not specified.
        :return: a list with the parameters names
        """
        return []

    def verify_parameters(self):
        def verify_block(block, path):
                if type(block) == dict :
                    for k, value in block.items():
                        verify_block(value, path + [k])
                elif type(block) == list:
                    for value in block:
                        verify_block(value, path)
                else:
                    args = path + [block]
                    try:
                        self.configs.get(*args)
                    except Exception as e:
                        Logger.error('missing_reader_param', '/'.join(args), type(self).__name__)
        verify_block(self.required_params(), ['parameters'])

    @abstractmethod
    def read_to(self, output_dataset, input, configurations, index):
        """
        Reads an input file/group to the correspondent output dataset.
        :param output_dataset: cdm/netcdf4 dataset.
        :param input: is file path.
        When group_by is used, a tuple containing the group file paths.
        :param configurations: configurations read from .yaml files
        :param index:
        :return: void
        """
        pass

    def group_id(self, filename):
        """
        Used by the converter to group by the converter to combine multiple files into a group.
        :param filename: e.g., 20161211135000_wind.txt
        :return: group name e.g. 20161211135000
        """
        pass

    def config(self, *keys):
        return self.configs.get('parameters', *keys)

    def set_configs(self, configs):
        self.configs = configs
