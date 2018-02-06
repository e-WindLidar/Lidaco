from ..common.Utils import dict_merge, map_recursively
from ..common.Logger import Logger
from yaml import load
from os import path


class Config:
    """
    Class responsible to handle hierarchical configurations.
    Can be used as a regular dictionary.

    """

    def __init__(self, context, file_name=None, configs={}):
        """
        Loads a configuration file and the declared imports in it recursively.
        :param context: file location path
        :param file_name: configuration filename
        """
        self.configs = {}
        self.config_paths = {}
        self.context = context

        tmp_configs = {}

        if file_name:
            tmp_configs = self.load_from_file(file_name)

        dict_merge(tmp_configs, configs)  # apply argument passed configs

        if 'imports' in tmp_configs:
            self.resolve_imports(context, tmp_configs.pop('imports'))

        dict_merge(self.configs, tmp_configs)
        dict_merge(self.config_paths, map_recursively(tmp_configs, context))

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
            dict_merge(self.configs, config.get())
            dict_merge(self.config_paths, config.get_path())

    def load_from_file(self, file_name):
        full_path = ""
        try:
            full_path = path.join(self.context, file_name)
            Logger.info('loading_config', full_path.replace("/./", "/"))
            with open(full_path, 'r') as stream:
                return load(stream)
        except FileNotFoundError as e:
            Logger.error('bad_config_path', full_path.replace("/./", "/"))
        except Exception as e:
            Logger.error('bad_config_formatting', str(e))

    def merge(self, config):
        """
        Updates the current configuration data with "config"
        Overriding/Update is performed at the leaf level.
        :param config: other config structure
        :return:
        """
        dict_merge(self.configs, config)

    def get(self, *keys):
        keys = list(keys)
        tmp_value = self.configs
        while len(keys) > 0:
            tmp_value = tmp_value[keys[0]]
            keys.pop(0)

        return tmp_value

    def get_path(self, *keys):
        keys = list(keys)
        tmp_value = self.config_paths
        while len(keys) > 0:
            tmp_value = tmp_value[keys[0]]
            keys.pop(0)

        return tmp_value

    def exists(self, *keys):
        try:
            self.get(*keys)
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        """
        Returns an item from the config data.
        :param key: key name
        :return: value
        """
        return self.configs[key]

    def __contains__(self, key):
        """
        Checks if a certain key exists in the config data.
        :param key: key name
        :return: boolean
        """
        return key in self.configs

    def get_resolved(self, *key):
        return path.join(self.get_path(*key), self.get(*key))
