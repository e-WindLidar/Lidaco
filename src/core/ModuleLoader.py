import importlib


class ModuleLoader:
    """
    Dynamically handles "add-on" modules (readers and writers) loading.
    """

    reader_modules = {}
    writer_modules = {}

    def __init__(self):
        super().__init__()

    @staticmethod
    def load(path, name):
        """
        Dynamically loads a module with name "name" and retrieves
        the class with the same name declared in that file.
        :param path: should be 'reader' or 'writer'
        :param name: worker name e.g. windscanner, windcubev2, netcdf4 etc.
        Check out the available ones at readers/writers sub directories.
        :return: loaded class.
        """
        return getattr(importlib.import_module(path + name, __package__), name)

    def load_reader(self, name):
        """
        Loads a reader and stores it into reader_modules dictionary.
        :param name: reader name
        :return: void
        """
        self.reader_modules[name] = self.load('..readers.', name)

    def load_writer(self, name):
        """
        Loads a writer and stores it into writer_modules dictionary.
        :param name: writer name
        :return: void
        """
        self.writer_modules[name] = self.load('..writers.', name)

    def get_reader(self, name):
        """
        Returns a reader class.
        :param name: reader name
        :return: class reference
        """
        return self.reader_modules[name]

    def get_writer(self, name):
        """
        Returns a writer class.
        :param name: writer name
        :return: class reference
        """
        return self.writer_modules[name]
