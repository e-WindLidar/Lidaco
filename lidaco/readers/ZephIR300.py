import numpy as np
from ..core.Reader import Reader
import datetime

class ZephIR300(Reader):

    def __init__(self):
        super().__init__(False)

    @staticmethod
    def util_process_time(timestring):
        hour = timestring[:2]
        minute = timestring[3:5]
        seconds = timestring[6:11]
        time = int(hour) * 3600
        time += int(minute) * 60
        time += float(seconds)
        return time

    @staticmethod
    def str_to_num(string1):
        try:
            return int(string1)
        except ValueError:
            try:
                return float(string1)
            except ValueError:
                return string1

    def accepts_file(self, filename):
        return filename.endswith('.csv')

    def output_filename(self, filename):
        return filename[:-4]


    def clean_string(string1):
        replace_dict={',':'.','#N/A':'NaN'}
        for key in replace_dict:
            string1=string1.replace(key,replace_dict[key])

        return string1

    def read_to(self, output_dataset, input_filepath, configs, appending):

        # read file
        with open(input_filepath, encoding='latin-1') as f:
            data = f.readlines()

            # get parameters from header
            header = data[0].split(';')
            parameters = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in header if ':' in line}
            
            parameters['Measurement heights'] = [int(element.strip()) for element in parameters['Measurement heights'].split('m') if (element != '')]
            parameters['Measurement heights'].append(1)

            # create the dimensions
            output_dataset.createDimension('range', len(parameters['Measurement heights']))
            output_dataset.createDimension('time', None)

            # create the coordinate variables
            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            range1[:] = np.array(parameters['Measurement heights'])

            time = output_dataset.createVariable('time', str, ('time',))
            time.units = 's'
            time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'
            scan_type[:] = 2
			
            # create the measurement variables            
            # tilt of Zephir lidar is always pitch or roll, depending on what is larger
            tilt = output_dataset.createVariable('tilt', 'f4', ('time',))
            tilt.units = 'degrees north'
            tilt.long_name = 'either pitch or roll depending on higher value'

            T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
            T_external.units = 'degrees C'
            T_external.long_name = 'temperature'

            yaw = output_dataset.createVariable('yaw', 'f4', ('time',))
            yaw.units = 'degrees'
            yaw.long_name = 'lidar_yaw_angle'

            rh = output_dataset.createVariable('rh', 'f4', ('time',))
            rh.units = 'degrees'
            rh.long_name = 'lidar_yaw_angle'
            
            p = output_dataset.createVariable('p', 'f4', ('time',))
            p.units = 'degrees'
            p.long_name = 'lidar_yaw_angle'

            WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
            WS.units = 'm.s-1'
            WS.long_name = 'mean of scalar wind speed'
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees north'
            DIR.long_name = 'wind direction from north'

            # fill values from dataset
            data_timeseries = [row.strip().split(';') for row in data[2:]]

            #---------------------------------------------------------------------------
            timestamp_input = [datetime.datetime.strptime(row[1],'%d.%m.%Y %H:%M:%S') for row in data_timeseries]
            timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
            output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
            #---------------------------------------------------------------------------
            
            output_dataset.variables['T_external'][:] = [float(ZephIR300.clean_string(row[13])) for row in data_timeseries]
            output_dataset.variables['tilt'][:] = [float(ZephIR300.clean_string(row[12])) for row in data_timeseries]
            output_dataset.variables['yaw'][:] = [float(ZephIR300.clean_string(row[11])) for row in data_timeseries]
            output_dataset.variables['rh'][:] = [float(ZephIR300.clean_string(row[15])) for row in data_timeseries]
            output_dataset.variables['p'][:] = [float(ZephIR300.clean_string(row[14])) for row in data_timeseries]

            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            ws_list = [[float(ZephIR300.clean_string(value)) for value in row[20::3]] for row in data_timeseries]
            dir_list = [[float(ZephIR300.clean_string(value)) for value in row[19:-1:3]] for row in data_timeseries]
            met_ws_list = [float(ZephIR300.clean_string(row[13])) for row in data_timeseries] #MET Wind Speed
            met_dir_list = [float(ZephIR300.clean_string(row[13])) for row in data_timeseries]
            
            ws_list = np.column_stack((np.array(ws_list),np.array(met_ws_list)))
            dir_list = np.column_stack((np.array(dir_list),np.array(met_dir_list)))

            output_dataset.variables['WS'][:, :] = ws_list
            output_dataset.variables['DIR'][:, :] = dir_list