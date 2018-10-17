from os import path
import pathlib

from lidaco.core.Writer import Writer

from lidaco.core.Reader import Reader

from ..common.Utils import is_str
from ..common.Logger import Logger
from .ModuleLoader import ModuleLoader
from .Config import Config


class Builder:
    """
    Main class. Orchestrates all the conversion steps.

    """

    module_loader = ModuleLoader()
    logger = None
    input_dir_path = None
    configs = {}
    args = {}

    def __init__(self,
                 config_file=None,
                 input_path=None,
                 output_format=None,
                 input_format=None,
                 context='',
                 ):
        """
        Initialization block. Loads a main config.yaml file, a reader, a writer and the remaining
        "meta-data" configurations. Overrides main configurations with the terminal arguments.
        :param context: this executable path
        :param args: terminal arguments
        :return: void
        """

        absolute_path = path.join(context, config_file)
        import_dir_path = path.dirname(absolute_path)
        import_filename = path.basename(absolute_path)

        root_configs = {
            'imports': [
                import_filename
            ],
            'parameters': {
                'input': {},
                'output': {}
            },
        }

        if input_path is not None:
            root_configs['parameters']['input']['path'] = input_path

        if input_format is not None:
            root_configs['parameters']['input']['format'] = input_format

        if output_format is not None:
            root_configs['parameters']['output']['format'] = output_format

        self.configs = Config(import_dir_path, configs=root_configs)

        try:
            self.input_dir_path = path.join(context, self.params('input', 'path'))
        except Exception as e:
            Logger.debug(e)
            Logger.error('inp_path_missing')

        try:
            self.configs.get('parameters', 'output', 'path')
        except Exception as e:
            # setting the default output folder
            # this could be generalized and encapsulated as a setter on the config class
            self.configs.configs['parameters']['output']['path'] = 'output'
            self.configs.config_paths['parameters']['output']['path'] = context

        reader = self.params('input', 'format')
        if not is_str(reader) and issubclass(reader, Reader):
            self.module_loader.set_reader(reader)
        else:
            try:
                self.module_loader.load_reader(reader)
                Logger.info('input_format_detected', self.params('input', 'format'))
            except KeyError as e:
                Logger.debug(e)
                Logger.error('inp_format_missing')
            except Exception as e:
                Logger.debug(e)
                Logger.error('bad_inp_format', self.params('input', 'format'), str(e))

        writer = self.params('output', 'format')
        if not is_str(writer) and issubclass(writer, Writer):
            self.module_loader.set_writer(writer)
        else:
            try:
                self.module_loader.load_writer(writer)
                Logger.info('output_format_detected', self.params('output', 'format'))
            except KeyError as e:
                Logger.debug(e)
                Logger.error('out_format_missing')
            except Exception as e:
                Logger.debug(e)
                Logger.error('bad_out_format', self.params('output', 'format'), str(e))

    def params(self, *keys):
        return self.configs.get('parameters', *keys)

    def read_attributes(self, dataset):
        """
        Reads attributes into the dataset. The attributes should be specified in the .yaml configuration
        files under 'attributes:' key.
        :param dataset: a core data model / netcdf4 dataset object.
        :return: void
        """
        if 'attributes' in self.configs:
            for key, value in self.configs['attributes'].items():
                setattr(dataset, key, value)
                
    def read_variables(self, dataset):
        """
        Reads variables into the dataset. The variables should be specified in the .yaml configuration
        files under 'variables:' key.
        :param dataset: a core data model / netcdf4 dataset object.
        :return: void
        """
        if 'variables' in self.configs:
            for variable_name, variable_dict in self.configs['variables'].items():
                if variable_name not in dataset.variables:
                    temp_var = dataset.createVariable(variable_name, self.configs['variables'][variable_name]['data_type'])
                    temp_var[:] = self.configs['variables'][variable_name]['value']
                    
                    for key, value in variable_dict.items():
                        if (key != 'data_type') and (key != 'value'):
                            setattr(temp_var, key, value)


    def build(self):
        """
        Main loop - connects the reader with the writer.
        Iterates over input data files / file groups:
        - Reading meta attributes from "meta-data" configurations
        :return:
        """
        writer = None
        out_complete = ''

        reader = self.module_loader.get_reader()()
        reader.set_configs(self.configs)
        reader.verify_parameters()
        input_path = self.configs.get_resolved('parameters', 'input', 'path')
        output_path = self.configs.get_resolved('parameters', 'output', 'path')
        pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
        
        files = reader.fetch_input_files(input_path)

        for i, group in enumerate(files):

            obs = self.params('output_block_size') if self.configs.exists('parameters', 'output_block_size') else 1
            if obs is None:
                obs = len(files)

            first_of_batch = (i % obs == 0)

            if first_of_batch:
                output_name = reader.output_filename(group['id'])
                writer = self.module_loader.get_writer()(output_path, output_name)
                out_complete = writer.file_path()

            Logger.log('started_r_files', group['files'])

            with writer.appending(not first_of_batch) as dataset:
                Logger.log('writing_file', out_complete, '' if first_of_batch else '(appending)')
                
                self.read_attributes(dataset)
                self.read_variables(dataset)
                
                if reader.data_grouping:
                    complete_path = tuple([path.join(input_path, f) for f in group['files']])
                else:
                    complete_path = path.join(input_path, group['files'])
                reader.read_to(dataset, complete_path, self.configs, not first_of_batch)

        Logger.info('done')


def build(**args):
    builder = Builder(**args)
    builder.build()