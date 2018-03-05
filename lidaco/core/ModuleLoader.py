import importlib


class ModuleLoader:
    """
    Dynamically handles "add-on" modules (readers and writers) loading.
    """

    def __init__(self):
        super().__init__()
        self.reader_module = None
        self.writer_module = None

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
        self.reader_module = self.load('..readers.', name)

    def load_writer(self, name):
        """
        Loads a writer and stores it into writer_modules dictionary.
        :param name: writer name
        :return: void
        """
        self.writer_module = self.load('..writers.', name)

    def get_reader(self):
        """
        Returns the reader class.
        :return: class reference
        """
        return self.reader_module

    def get_writer(self):
        """
        Returns the writer class.
        :return: class reference
        """
        return self.writer_module


    def set_reader(self, reader):
        self.reader_module = reader

    def set_writer(self, writer):
        self.writer_module = writer
