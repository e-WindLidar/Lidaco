from .Utils import dict_merge
from .Logger import Logger
from yaml import YAMLError, load
from os import path


class Config:
    """
    Class responsible to handle hierarchical configurations.
    Can be used as a regular dictionary.

    """

    def __init__(self, dir_path, filename):
        """
        Loads a configuration file and the declared imports in it recursively.
        :param dir_path: file location path
        :param filename: configuration filename
        """
        self.data = {}
        configs = {}
        full_path = ""

        try:
            full_path = path.join(dir_path, filename)
            with open(full_path, 'r') as stream:
                configs = load(stream)
            Logger.info('loading_config', full_path.replace("/./", "/"))
        except FileNotFoundError as e:
            Logger.error('bad_config_path', full_path.replace("/./", "/"))
        except Exception as e:
            Logger.error('bad_config_formatting', str(e))

        if 'imports' in configs:
            self.resolve_imports(dir_path, configs.pop('imports'))

        self.merge(configs)

    def resolve_imports(self, dir_path, imports):
        """

        :param dir_path:
        :param imports:
        :return:
        """
        for relative_path in imports:
            absolute_path = path.join(dir_path, relative_path)
            import_dir_path = path.dirname(absolute_path)
            import_filename = path.basename(absolute_path)

            config = Config(import_dir_path, import_filename)
            self.merge(config.get())

    def merge(self, config):
        """
        Updates the current configuration data with "config"
        Overriding/Update is performed at the leaf level.
        :param config: other config structure
        :return:
        """
        dict_merge(self.data, config)

    def get(self, key=None, default=None):

        """
        Similar to a regular .get(), with the exception that if no key is defined,
        then all config data is returned.
        :param key:
        :param default:
        :return: value
        """
        if key is None:
            return self.data
        else:
            return self.data.get(key, default)

    def __getitem__(self, key):
        """
        Returns an item from the config data.
        :param key: key name
        :return: value
        """
        return self.data[key]

    def __contains__(self, key):
        """
        Checks if a certain key exists in the config data.
        :param key: key name
        :return: boolean
        """
        return key in self.data
