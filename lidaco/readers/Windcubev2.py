import numpy as np
from pathlib import Path
from ..core.Reader import Reader
import datetime

class Windcubev2(Reader):

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
        return filename.endswith(('.sta','.rtd','.stdsta'))

    def output_filename(self, filename):
        return filename[:-4]

    def read_to(self, output_dataset, input_filepath, configs, appending):
        try:
            # read file
            with open(input_filepath, encoding='latin-1') as f:
                data = f.readlines()
    
                # get parameters from header
                filetype = input_filepath[-3:]
                temp_HeaderSize = int(data[0].split(sep='=')[1])
                parameters = [line[:-1].split(sep='=') for line in data[0:temp_HeaderSize]]
                parameters = {line[0]: Windcubev2.str_to_num(line[1]) for line in parameters if len(line) == 2}
                parameters['Altitudes (m)'] = [Windcubev2.str_to_num(element) for element in parameters['Altitudes (m)'].strip().split('\t')] 
    
                
                if filetype == 'rtd':
                    parameters['first_timestamp'] = datetime.datetime.strptime(
                        data[parameters['HeaderSize'] + 2].split('\t')[0][:-3],
                        '%Y/%m/%d %H:%M:%S')
                
                else:
                    parameters['first_timestamp'] = datetime.datetime.strptime(
                        data[parameters['HeaderSize'] + 2].split('\t')[0],
                        '%Y/%m/%d %H:%M')
    
                # general data set description
                output_dataset.site = parameters['Location']
    
                # create the dimensions
                output_dataset.createDimension('range', len(parameters['Altitudes (m)']))
                output_dataset.createDimension('time', None)
    
                # create the coordinate variables
                range1 = output_dataset.createVariable('range', 'f4', ('range',))
                range1.units = 'm'
                range1.long_name = 'range_gate_distance_from_lidar'
                range1[:] = np.array(parameters['Altitudes (m)'])
    
                time = output_dataset.createVariable('time', str, ('time',))
                time.units = 's'
                time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'
    
                # create the beam steering and location variables
                yaw = output_dataset.createVariable('yaw', 'f4')
                yaw.units = 'degrees'
                yaw.long_name = 'lidar_yaw_angle'
                yaw[:] = parameters['DirectionOffset (°)']
    
                pitch = output_dataset.createVariable('pitch', 'f4')
                pitch.units = 'degrees'
                pitch.long_name = 'lidar_pitch_angle'
                pitch[:] = parameters['PitchAngle (°)']
    
                roll = output_dataset.createVariable('roll', 'f4')
                roll.units = 'degrees'
                roll.long_name = 'lidar_roll_angle'
                roll[:] = parameters['RollAngle (°)']
    
                # create the data variables
                scan_type = output_dataset.createVariable('scan_type', 'i')
                scan_type.units = 'none'
                scan_type.long_name = 'scan_type_of_the_measurement'
    
                scan_type[:] = 2
    
                accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
                accumulation_time.units = 'seconds'
                accumulation_time.long_name = 'time_for_spectral_accumulation'
                accumulation_time[:] = 1.0
    
                n_spectra = output_dataset.createVariable('n_spectra', 'f4')
                n_spectra.units = 'none'
                n_spectra.long_name = 'number_of_pulses'
                n_spectra[:] = parameters['Pulses / Line of Sight']
    
                # create the measurement variables
                if filetype == 'rtd':
                    VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
                    VEL.units = 'm.s-1'
                    VEL.long_name = 'radial_velocity'
                    
                    azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
                    azimuth_angle.units = 'degrees'
                    azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
                    
                    elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
                    elevation_angle.units = 'degrees'
                    elevation_angle.long_name = 'elevation_angle_of_lidar beam'
                    				
                    T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
                    T_internal.units = 'degrees C'
                    T_internal.long_name = 'internal_temperature'
                    
                    T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
                    T_external.units = 'degrees C'
                    T_external.long_name = 'external_temperature'
                    
                    p = output_dataset.createVariable('p', 'f4', ('time',))
                    p.units = 'hPa'
                    p.long_name = 'pressure'
                    
                    Rh = output_dataset.createVariable('Rh', 'f4', ('time',))
                    Rh.units = 'percent'
                    Rh.long_name = 'relative_humidity'
    
                    CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
                    CNR.units = 'dB'
                    CNR.long_name = 'carrier_to_noise_ratio'
                    				
                    WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
                    WIDTH.units = 'm.s-1'
                    WIDTH.long_name = 'doppler_spectrum_width'
                                    
                    wiper = output_dataset.createVariable('wiper', 'f4', ('time',))
                    wiper.units = 'V'
                    wiper.long_name = 'Wiper count Vbatt'
                
                else:
                    WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
                    WS.units = 'm.s-1'
                    WS.long_name = 'mean_of_scalar_wind_speed'
                    				
                    WSstd = output_dataset.createVariable('WSstd', 'f4', ('time', 'range'))
                    WSstd.units = 'm.s-1'
                    WSstd.long_name = 'standard_deviation_of_scalar_wind_speed'
                    				
                    WSmin = output_dataset.createVariable('WSmin', 'f4', ('time', 'range'))
                    WSmin.units = 'm.s-1'
                    WSmin.long_name = 'minimum_of_scalar_wind_speed'
                    				
                    WSmax = output_dataset.createVariable('WSmax', 'f4', ('time', 'range'))
                    WSmax.units = 'm.s-1'
                    WSmax.long_name = 'maximum_of_scalar_wind_speed'
                    
                    DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
                    DIR.units = 'degrees'
                    DIR.long_name = 'mean_wind_direction'
                    
                    w = output_dataset.createVariable('w', 'f4', ('time', 'range'))
                    w.units = 'm.s-1'
                    w.long_name = 'mean_w_component_of_scalar_wind_speed'
                    				
                    wstd = output_dataset.createVariable('wstd', 'f4', ('time', 'range'))
                    wstd.units = 'm.s-1'
                    wstd.long_name = 'standard_deviation_of_w_component_of_scalar_wind_speed'
                    				
                    CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
                    CNR.units = 'dB'
                    CNR.long_name = 'mean_carrier_to_noise_ratio'
                    
                    CNRmin = output_dataset.createVariable('CNRmin', 'f4', ('time', 'range'))
                    CNRmin.units = 'dB'
                    CNRmin.long_name = 'minimum_carrier_to_noise_ratio'
                    				
                    WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
                    WIDTH.units = 'm.s-1'
                    WIDTH.long_name = 'mean_doppler_spectrum_width'
                    
                    Availability = output_dataset.createVariable('Availability', 'f4', ('time', 'range'))
                    Availability.units = 'percent'
                    Availability.long_name = 'data_availability'
                    				
                    T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
                    T_internal.units = 'degrees C'
                    T_internal.long_name = 'mean_internal_temperature'
                    				
                    T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
                    T_external.units = 'degrees C'
                    T_external.long_name = 'mean_external_temperature'
                    
                    p = output_dataset.createVariable('p', 'f4', ('time',))
                    p.units = 'hPa'
                    p.long_name = 'pressure'
                    
                    Rh = output_dataset.createVariable('Rh', 'f4', ('time',))
                    Rh.units = 'percent'
                    Rh.long_name = 'relative_humidity'	
                    
                    wiper = output_dataset.createVariable('wiper', 'f4', ('time',))
                    wiper.units = 'V'
                    wiper.long_name = 'Wiper count Vbatt'
    
                # fill values from dataset
                data_timeseries = [row.strip().split('\t') for row in data[parameters['HeaderSize'] + 2:]]
                
                if filetype == 'rtd': # high resolution data
                
                    timestamp_input = [datetime.datetime.strptime(row[0][:-3],'%Y/%m/%d %H:%M:%S') for row in data_timeseries]
                    timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
                    output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
                    output_dataset.variables['T_internal'][:] = [float(row[2]) for row in data_timeseries]
                    output_dataset.variables['wiper'][:] = [float(row[3]) for row in data_timeseries]
                    output_dataset.variables['azimuth_angle'][:] = [float(row[1]) if row[1] != 'V' else 0 for row in
                                                                    data_timeseries]
                    output_dataset.variables['elevation_angle'][:] = [90 - parameters['ScanAngle (°)'] if row[1] != 'V' else 90
                                                                      for
                                                                      row
                                                                      in data_timeseries]
                    output_dataset.variables['VEL'][:, :] = [[float(value) for value in row[5::9]] for row in data_timeseries]
                    output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[6::9]] for row in data_timeseries]
                    output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[4::9]] for row in data_timeseries]
                    
    			# filetype == 'sta' # 10 minute mean values
                else:
                    timestamp_input = [datetime.datetime.strptime(row[0],'%Y/%m/%d %H:%M') for row in data_timeseries]
                    timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
                    output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
                    output_dataset.variables['T_internal'][:] = [float(row[1]) for row in data_timeseries]
                    output_dataset.variables['T_external'][:] = [float(row[2]) for row in data_timeseries]
                    output_dataset.variables['p'][:] = [float(row[3]) for row in data_timeseries]
                    output_dataset.variables['Rh'][:] = [float(row[4]) for row in data_timeseries]				
                    output_dataset.variables['WS'][:, :] = [[float(value) for value in row[7::12]] for row in data_timeseries]
                    output_dataset.variables['WSstd'][:, :] = [[float(value) for value in row[8::12]] for row in data_timeseries]
                    output_dataset.variables['WSmin'][:, :] = [[float(value) for value in row[9::12]] for row in data_timeseries]
                    output_dataset.variables['WSmax'][:, :] = [[float(value) for value in row[10::12]] for row in data_timeseries]
                    output_dataset.variables['DIR'][:, :] = [[float(value) for value in row[11::12]] for row in data_timeseries]
                    output_dataset.variables['w'][:, :] = [[float(value) for value in row[12::12]] for row in data_timeseries]
                    output_dataset.variables['wstd'][:, :] = [[float(value) for value in row[13::12]] for row in data_timeseries]
                    output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[14::12]] for row in data_timeseries]
                    output_dataset.variables['CNRmin'][:, :] = [[float(value) for value in row[15::12]] for row in data_timeseries]				
                    output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[16::12]] for row in data_timeseries]
                    output_dataset.variables['Availability'][:, :] = [[float(value) for value in row[17::12]] for row in data_timeseries]
                    output_dataset.variables['wiper'][:] = [float(row[6]) for row in data_timeseries]

        except Exception as err:
            print('Error ocurred while converting %s. See error.log for details.' % input_filepath)
       
            with open(Path(output_dataset.filepath()).parent / 'error.log','a') as logfile:
                logfile.write( '%s'%output_dataset.filepath() +'\n')
