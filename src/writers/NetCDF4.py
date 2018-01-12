import netCDF4 as  nc

from ..core.Writer import Writer


class NetCDF4(Writer):
    dataset = None

    def __init__(self, dir_path, name):
        super().__init__(dir_path, name)

    def filename(self):
        return self.name + '.nc'

    def __enter__(self):
        self.dataset = nc.Dataset(self.file_path(), 'a' if self.append else 'w', format='NETCDF4')
        return self.dataset.__enter__()

    def __exit__(self, type, value, traceback):
        return self.dataset.__exit__(type, value, traceback)
