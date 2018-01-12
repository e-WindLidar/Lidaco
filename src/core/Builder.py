from os import path
from .Utils import is_str, common_iterable
from .Logger import Logger
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

    def __init__(self, context, args):
        """
        Initialization block. Loads a main config.yaml file, a reader, a writer and the remaining
        "meta-data" configurations. Overrides main configurations with the terminal arguments.
        :param context: this executable path
        :param args: terminal arguments
        :return: void
        """

        self.args = args

        absolute_path = path.join(context, args.config_file)
        import_dir_path = path.dirname(absolute_path)
        import_filename = path.basename(absolute_path)
        self.configs = Config(import_dir_path, import_filename)

        try:
            self.input_dir_path = path.join(context, self.params('data_path'))
        except Exception as e:
            Logger.debug(e)
            Logger.error('data_path_missing')

        try:
            self.module_loader.load_reader(self.params('input_format'))
            Logger.info('input_format_detected', self.params('input_format'))
        except Exception as e:
            Logger.debug(e)
            Logger.error('bad_inp_format', self.params('input_format'))

        try:
            self.module_loader.load_writer(self.params('output_format'))
            Logger.info('output_format_detected', self.params('output_format'))
        except Exception as e:
            Logger.debug(e)
            Logger.error('bad_out_format', self.params('output_format'))

    def params(self, key=None, default=None):
        """
        Retrieves a configuration parameter.
        If the correspondent terminal argument is set, then the terminal argument is used.
        :param key: parameters key.
        :param default:
        :return:
        """

        if key is None:
            return self.configs['parameters']
        elif hasattr(self.args, key) and getattr(self.args, key) is not None:
            return getattr(self.args, key)
        else:
            return self.configs['parameters'].get(key, default)

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

    def build(self):
        """
        Main loop - connects the reader with the writer.
        Iterates over input data files / file groups:
            - Reading meta attributes from "meta-data" configurations
        :return:
        """
        writer = None
        out_complete = ''

        reader = self.module_loader.get_reader(self.params('input_format'))()
        reader.verify_parameters(self.params())
        files = reader.fetch_input_files(self.params('data_path'))

        for key, file, i in common_iterable(files):

            is_first = (i == 0) if (self.params('output_block_size', 1) is None) \
                else (i % self.params('output_block_size', 1) == 0)

            if is_first:
                output_name = reader.output_filename(file if is_str(file) else key)
                writer = self.module_loader.get_writer(self.params('output_format'))(self.input_dir_path, output_name)
                out_complete = writer.file_path()

            Logger.log('started_r_files', file if is_str(file) else tuple(file))

            with writer.appending(not is_first) as dataset:
                self.read_attributes(dataset)

                if is_str(file):
                    complete_path = path.join(self.input_dir_path, file)
                    reader.read_to(dataset, complete_path, self.configs, index=i)
                else:
                    complete_paths = tuple([path.join(self.input_dir_path, f) for f in file])
                    reader.read_to(dataset, complete_paths, self.configs, index=i)

                Logger.log('writing_file', out_complete, '' if i == 0 else '(appending)')

        Logger.info('done')
