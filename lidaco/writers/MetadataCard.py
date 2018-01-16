import netCDF4 as nc
import json

from ..core.Writer import Writer


class MetadataCard(Writer):
    nc_dataset = None

    def __init__(self, dir_path, name):
        super().__init__(dir_path, name)

    def filename(self):
        return self.name + '.json'

    def __enter__(self):
        if not self.append:
            self.nc_dataset = nc.Dataset(self.file_path(), 'w', diskless=True)

        return self.nc_dataset.__enter__()

    def __exit__(self, type, value, traceback):
        if not self.append:

            metadata_card = {}

            # Writing attributes
            for ncattr in self.nc_dataset.ncattrs():
                metadata_card[ncattr] = self.nc_dataset.getncattr(ncattr)

            with open(self.file_path(), "w") as json_file:
                json_file.write(json.dumps(metadata_card, indent=4))
