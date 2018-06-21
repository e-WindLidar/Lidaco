from ..core.Reader import Reader
from datetime import datetime
import numpy as np


class WLS70(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return (filename[-4:] == '.txt') & (len(filename) > 14) & (filename[:5] == 'WLS70')

    def output_filename(self, timestamp):
        return timestamp[:-9]
    
    def read_to(self, output_dataset, input_filepaths, parameters, appending):
        wind_file = input_filepaths

        with open(wind_file) as f:
            input_file_data = [line.strip() for line in f.readlines()]
            

        
        ordered_data=np.reshape(np.array(input_file_data)[39:-1],(-1,17))
        range_list = np.unique(ordered_data[:,9].astype(float)).astype(int)
        
        time_array = ordered_data[::len(range_list),1:7].astype(int)
        datetime_array = [datetime(*line) for line in time_array]
        iso8601_array = [date.isoformat()+'Z' for date in datetime_array]


        if not appending:

            output_dataset.createDimension('range', len(range_list))
            output_dataset.createDimension('time', None)

            time = output_dataset.createVariable('time', str, ('time',))
            time.units = 's'
            time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'
            time.comment = ''
            time[:] = np.array(iso8601_array)

            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time','range'))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'temperature'
            T_internal[:] = np.reshape(ordered_data[:,7].astype(float),(len(iso8601_array),len(range_list)))
            
            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time','range'))
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle[:] = np.reshape(ordered_data[:,8].astype(float),(len(iso8601_array),len(range_list)))

            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            range1.comment = ''
            range1[:] = range_list
            
            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier-to-noise ratio'
            CNR.comment = ''
            CNR.accuracy = ''
            CNR.accuracy_info = ''
            CNR[:] = np.reshape(ordered_data[:,10].astype(float),(len(iso8601_array),len(range_list)))
            
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial velocity'
            VEL.comment = ''
            VEL.accuracy = ''
            VEL.accuracy_info = ''
            VEL[:] = np.reshape(ordered_data[:,11].astype(float),(len(iso8601_array),len(range_list)))
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees north'
            DIR.long_name = 'wind direction from north'
            DIR[:] = np.reshape(ordered_data[:,12].astype(float),(len(iso8601_array),len(range_list)))
            
        else: 
            ntime = len(output_dataset.dimensions["time"])
            output_dataset.variables['time'][ntime:] = np.array(iso8601_array)
            output_dataset.variables['T_internal'][ntime:] = np.reshape(ordered_data[:,7].astype(float) , (len(iso8601_array),len(range_list)))
            output_dataset.variables['elevation_angle'][ntime:] = np.reshape(ordered_data[:,8].astype(float) , (len(iso8601_array),len(range_list)))
            output_dataset.variables['CNR'][ntime:] = np.reshape(ordered_data[:,10].astype(float) , (len(iso8601_array),len(range_list)))
            output_dataset.variables['VEL'][ntime:] = np.reshape(ordered_data[:,11].astype(float)  ,(len(iso8601_array),len(range_list)))        
            output_dataset.variables['DIR'][ntime:] = np.reshape(ordered_data[:,12].astype(float),(len(iso8601_array),len(range_list)))