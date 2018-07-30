from ..core.Reader import Reader
from datetime import datetime, timedelta
import numpy as np
import re

class Triton(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return filename.startswith('TritonExport') & (len(filename) > 14) & filename.endswith('.csv')

    def output_filename(self, timestamp):
        return timestamp[:-9]

    def read_to(self, output_dataset, input_filepaths, parameters, appending):
        wind_file = input_filepaths        
        
        with open(wind_file) as f:
            wind_file_data = f.readlines()

        wind_file_data = [row.strip().split(';') for row in wind_file_data]
        wind_file_data_T = list(zip(*wind_file_data[4:]))


        if not appending:

            
            range_list=[]
            for column in wind_file_data[2]:
                temp = re.findall('\d+(?=m)',column)
                if len(temp) > 0:
                    range_list.append(int(temp[0]))

            range_list = list(set(range_list))
            range_list.sort()
            
            # create the dimensions
            output_dataset.createDimension('range', len(range_list))
            output_dataset.createDimension('time', None)

            # create the coordinate variables

            # range
            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            range1[:] = range_list
            range1.comment = ''

            # time
            time = output_dataset.createVariable('time', str, ('time',))
            time.units = 's'
            time.long_name = 'seconds since 1904-01-01 12:00AM UTC'
            time.comment = ''

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'


            # create the measurement variables VEL, Quality, WIDTH
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial velocity'
            VEL.comment = ''
            VEL.accuracy = ''
            VEL.accuracy_info = ''
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees north'
            DIR.long_name = 'wind direction from north'
            
            
            Quality = output_dataset.createVariable('Quality', 'f4', ('time', 'range'))
            Quality.units = 'percent'
            Quality.long_name = 'quality_value'
            Quality.comment = ''
            Quality.accuracy = ''
            Quality.accuracy_info = ''

            w = output_dataset.createVariable('w', 'f4', ('time', 'range'))
            w.units = 'm.s-1'
            w.long_name = 'vertical_wind_speed'
            w.comment = ''
            w.accuracy = ''
            w.accuracy_info = ''
            
            #%% get timestamps in ISO 8601 format

            timestamp_list = [datetime.strptime(value, '%d.%m.%Y %H:%M') for value in wind_file_data_T[0]]
            timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_list]
            output_dataset.variables['time'][:] = np.array(timestamp_iso8601)

            #%% read vel, width, Quality out of dataset
            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            
            def str2float(astring):
                if len(astring) > 0:
                    return float(astring.replace(',','.'))
                else:
                    return 0

            
            output_dataset.variables['VEL'][:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[2:len(range_list)*4+1:4]]))
            output_dataset.variables['DIR'][:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[1:len(range_list)*4+1:4]]))
            output_dataset.variables['w'][:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[3:len(range_list)*4+1:4]]))
            output_dataset.variables['Quality'][:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[4:len(range_list)*4+1:4]]))
            
        #%% case appending
        else: 
            ntime = len(output_dataset.dimensions["time"])
            
            timestamp_list = [datetime.strptime(value, '%d.%m.%Y %H:%M') for value in wind_file_data_T[0]]
            timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_list]
            output_dataset.variables['time'][ntime:] = np.array(timestamp_iso8601)

            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['VEL'][ntime:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[2:len(range_list)*4+1:4]]))
            output_dataset.variables['DIR'][ntime:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[1:len(range_list)*4+1:4]]))
            output_dataset.variables['w'][ntime:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[3:len(range_list)*4+1:4]]))
            output_dataset.variables['Quality'][ntime:, :] = list(
                zip(*[[str2float(value) for value in row] for row in wind_file_data_T[4:len(range_list)*4+1:4]]))
