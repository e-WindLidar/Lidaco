from abc import ABC, abstractmethod
from os import path


class Writer(ABC):
    """
    Specifies a writer class API and implements some common methods.
    """

    dir_path = None
    name = None

    def __init__(self, dir_path, name):
        """
        Constructor.
        :param dir_path: directory to save the file into.
        :param name: file name suggestion (without extension)
        :param append: should be the data appended or a new file writen
        """
        super().__init__()
        self.dir_path = dir_path
        self.name = name
        self.append = False

    def file_path(self):
        """
        Complete file (to be written to) path.
        :return: file path
        """
        return path.join(self.dir_path, self.filename())

    @abstractmethod
    def filename(self):
        """
        Returns the filename (with extension) of the file to be writen.
        :return: filename
        """
        pass

    def appending(self, append):
        """
        Sets the writer appending mode.
        :param append: boolean
        :return: the writer itself.
        """
        self.append = append
        return self

    @abstractmethod
    def __enter__(self):
        """
        Requests an CDM object reference that is used to represent the dataset file
        :return: the dataset object
        """
        pass

    @abstractmethod
    def __exit__(self, type, value, traceback):
        """
        Closes/Writes the dataset
        :param type:
        :param value:
        :param traceback:
        :return:
        """
        pass
