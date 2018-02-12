import json
from abc import ABC, abstractmethod
from os import listdir
from itertools import groupby
from ..common.Logger import Logger


class Reader(ABC):
    """
    Specifies a reader class API and implements some common methods.
    """

    common_variables = {}
    out_path = ''

    def __init__(self, data_grouping):
        """
        Constructor.
        :param data_grouping: If data_grouping is True then group_id method must be implemented.
        """
        super().__init__()
        self.data_grouping = data_grouping

    def fetch_input_files(self, dir_path):
        """
        Lists and filters input data files. If the reader specifies a group_by function,
        it also groups files by that value, return a dictionary group => [files].
        :param dir_path: directory containing input data files
        :return: [files] | {group => [files]}
        """
        variables_file = open('./lidaco/core/variables.json')
        variables_str = variables_file.read()
        self.common_variables = json.loads(variables_str)

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

    def verify_parameters(self, params):
        for param in self.required_params():
            if param not in params:
                Logger.error('missing_reader_param', param, type(self).__name__)

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

    def create_variable(self, dataset, var_name, dim_spec=None, data=None):
        """
        Creates a layer of abstraction to create a variable, by defining automatically the attributes using the
        previously defined dictionary
        :param dataset:
        :param var_name:
        :param dim_spec:
        :param data:
        :return:
        """
        if data is None:
            data = []

        if var_name in self.common_variables:
            var = self.common_variables.get(var_name)
        else:
            raise ValueError('The variable ' + var_name + ' doesn\'t exist in the dictionary.')

        if dim_spec is not None:
            nc_variable = dataset.createVariable(var['name'], var['type'], dim_spec)
        elif 'dimensions' in var:
            dimensions = var['dimensions']
            nc_variable = dataset.createVariable(var['name'], var['type'], tuple(dimensions))
        else:
            nc_variable = dataset.createVariable(var['name'], var['type'])

        nc_variable[:] = data
        for key, value in var.items():
            nc_variable.setncattr(key, value)
        return nc_variable
