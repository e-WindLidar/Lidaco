from lxml.etree import Element, ElementTree

import netCDF4 as nc

from ..core.Writer import Writer

NS = "http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2"
PREFIX = '{' + NS + '}'
NS_MAP = {'ncml': NS}


class NcML(Writer):
    nc_dataset = None

    def __init__(self, dir_path, name):
        super().__init__(dir_path, name)

    def filename(self):
        return self.name + '.ncml'

    def __enter__(self):
        if not self.append:
            self.nc_dataset = nc.Dataset(self.file_path(), 'w', diskless=True)
            self.dataset = ElementTree(Element(PREFIX + "netcdf", nsmap=NS_MAP))

        return self.nc_dataset.__enter__()
    def __exit__(self, type, value, traceback):
        if not self.append:
            # Writing dimensions
            # asdasd
            for name, dim in self.nc_dataset.dimensions.items():
                element = Element(PREFIX + 'dimension')
                element.set('name', name)
                element.set('length', str(dim.size))
                if dim.isunlimited:
                    element.set('isUnlimited', "true")
                self.dataset.getroot().append(element)

            # Writing attributes
            for ncattr in self.nc_dataset.ncattrs():
                element = Element(PREFIX + 'attribute')
                element.set('name', ncattr)
                element.set('value', self.nc_dataset.getncattr(ncattr))
                self.dataset.getroot().append(element)

            # Writing variables
            for name, var in self.nc_dataset.variables.items():

                element = Element(PREFIX + 'variable')
                element.set('name', name)
                element.set('shape', " ".join(var.dimensions))
                element.set('type', var.dtype.str[1:])

                # Writing variable attributes
                for ncattr in var.ncattrs():
                    attr_elem = Element(PREFIX + 'attribute')
                    attr_elem.set('name', ncattr)
                    attr_elem.set('value', var.getncattr(ncattr))
                    element.append(attr_elem)

                if var.chunking() != 'contiguous':
                    attr_elem = Element(PREFIX + 'attribute')
                    attr_elem.set('name', '_ChunkSizes')
                    attr_elem.set('type', 'int')
                    attr_elem.set('value', " ".join([str(s) for s in var.chunking()]))
                    element.append(attr_elem)

                    self.dataset.getroot().append(element)

            return self.dataset.write(self.file_path(), xml_declaration=True, encoding="UTF-8", pretty_print=True)
