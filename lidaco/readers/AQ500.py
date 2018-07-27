import numpy as np
from ..core.Reader import Reader
import datetime

class AQ500(Reader):

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

    def correct_ws(ws_array,range_array):
        corr_array = np.ones_like(ws_array)
        
        bool_mask_80=(range_array <=80)
        corr_array[:,bool_mask_80]=0.98
        
        bool_mask_140=(range_array >= 140)
        corr_array[:,bool_mask_140]=0.97

        bool_mask_between = (~bool_mask_80) & (~bool_mask_140)
        corr_array[:,bool_mask_between] = np.tile(range_array[bool_mask_between]*(-1/6000)+(149/150), (len(ws_array),1) )

        return ws_array * corr_array

    def accepts_file(self, filename):
        return filename.endswith('.txt')

    def output_filename(self, filename):
        return filename[:-4]

    def read_to(self, output_dataset, input_filepath, configs, appending):

        # read file
        with open(input_filepath, encoding='latin-1') as f:
            data = f.readlines()
            data = [line.strip() for line in data]
            temp_headerlength = data.index('[EOH]')
            parameters = {line.split('=')[0]: line.split('=')[1].strip() for line in data[:temp_headerlength] if ('=' in line)}
            parameters['HeaderLength'] = temp_headerlength
            parameters['Measurement heights'] = np.arange(int(parameters['Lowest level(LL m)']),int(parameters['Highest level(HL m)'])+1,int(parameters['Interval(m)']) )

        	#create datafield dictionary  {column_name:np.array(columns)}
            datafield = {line.split(':')[1].strip() : np.array((line.split(':')[0][11:]).split(','),dtype=int)-2 for line in data[:temp_headerlength] if (':' in line)}
            
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
            scan_type[:] = 1

            accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
            accumulation_time.units = 'seconds'
            accumulation_time.long_name = 'time_for_spectral_accumulation'
            accumulation_time[:] = 1.0

            # create the measurement variables
            T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
            T_external.units = 'degrees C'
            T_external.long_name = 'temperature'

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
            
            signal_quality = output_dataset.createVariable('signal_quality', 'f4', ('time', 'range'))
            signal_quality.units = 'percent'
            signal_quality.long_name = 'signal quality'

            # create np.array of dataset without timestamp and cast to float
            data_timeseries = [line[:-1].split(',') for line in data[temp_headerlength+2:-2]]
            data_timeseries_array = np.array(data_timeseries)[:,1:].astype(float)
            
            timestamp_input = [datetime.datetime.strptime(row[0],'%Y%m%d %H:%M') for row in data_timeseries]
            timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
            output_dataset.variables['time'][:] = np.array(timestamp_iso8601)

            output_dataset.variables['T_external'][:] = data_timeseries_array[:,datafield['Temperature sensor(deg C * 10)=True']]
            output_dataset.variables['rh'][:] = data_timeseries_array[:,datafield['Humidity sensor(%RH)=True']]
            output_dataset.variables['p'][:] = data_timeseries_array[:,datafield['Pressure sensor(Hp)=False']]

            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['WS'][:, :] = AQ500.correct_ws(data_timeseries_array[:,datafield['Speed m/s(LL to HL)']], parameters['Measurement heights'])
            output_dataset.variables['DIR'][:, :] = data_timeseries_array[:,datafield['Dir degrees(LL to HL)']]
            
            # there is an error reading signal_quality for our data because there are only 30 columns, but 31 heights
            # we commented it out but it might be useful for future measurements
            # output_dataset.variables['signal_quality'][:, :] = data_timeseries_array[:,datafield['Quality(S/N*10)(LL to HL)']]