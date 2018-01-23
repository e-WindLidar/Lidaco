from ..core.Reader import Reader


class Galion(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return filename.endswith('.scn')

    def output_filename(self, filename):
        return filename[:-4]

    def read_to(self, output_dataset, input_filepath, configs, index):
        print("hello")

