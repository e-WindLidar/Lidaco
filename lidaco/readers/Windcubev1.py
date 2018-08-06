import datetime
import numpy as np
from pathlib import Path
from ..core.Reader import Reader
import os




class Windcubev1(Reader):

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
        return filename.endswith(('.sta','.rtd'))

    def output_filename(self, filename):
        return filename[:-4]
    
    def read_to(self, output_dataset, input_filepath, configs, appending):
        # read file
        with open(input_filepath, encoding='latin-1') as f:
            try:
                data = f.readlines()
                filetype = input_filepath[-3:]
                # get parameters from header
                temp_HeaderSize = int(data[0].split(sep='=')[1])
                parameters = [line[:-1].split(sep='=') for line in data[0:temp_HeaderSize]]
                parameters = {line[0]: Windcubev1.str_to_num(line[1]) for line in parameters if len(line) == 2}
                parameters['Altitudes(m)'] = [Windcubev1.str_to_num(element) for element in
                                               parameters['Altitudes(m)'].strip().split('\t')]
               
                if filetype == 'rtd':
                    parameters['first_timestamp'] = datetime.datetime.strptime(
                        data[parameters['HeaderLength'] + 2].split('\t')[0][:-3],
                        '%d/%m/%Y %H:%M:%S')
                else:
                    parameters['first_timestamp'] = datetime.datetime.strptime(
                        data[parameters['HeaderLength'] + 2].split('\t')[0],
                        '%d/%m/%Y %H:%M:%S')
    
                # general data set description
                output_dataset.site = parameters['Localisation']
    
                # create the dimensions
                output_dataset.createDimension('range', len(parameters['Altitudes(m)']))
                output_dataset.createDimension('time', None)
    
                # create the coordinate variables
                range1 = output_dataset.createVariable('range', 'f4', ('range',))
                range1.units = 'm'
                range1.long_name = 'range_gate_distance_from_lidar'
                range1[:] = np.array(parameters['Altitudes(m)'])
    
    
                time = output_dataset.createVariable('time', str, ('time',))
                time.units = 's'
                time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'            
    
                # create the beam steering and location variables
                yaw = output_dataset.createVariable('yaw', 'f4')
                yaw.units = 'degrees'
                yaw.long_name = 'lidar_yaw_angle'
                yaw[:] = parameters['DirectionOffset(°)']
    
                pitch = output_dataset.createVariable('pitch', 'f4')
                pitch.units = 'degrees'
                pitch.long_name = 'lidar_pitch_angle'
                pitch[:] = parameters['PitchAngle(°)']
    
                roll = output_dataset.createVariable('roll', 'f4')
                roll.units = 'degrees'
                roll.long_name = 'lidar_roll_angle'
                roll[:] = parameters['RollAngle(°)']
    
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
                n_spectra[:] = parameters['NumberOfAveragedShots']
    
                # high resolution rtd files
                if filetype == 'rtd':
                    VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
                    VEL.units = 'm.s-1'
                    VEL.long_name = 'radial_velocity'
                    
                    azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
                    azimuth_angle.units = 'degrees'
                    azimuth_angle.long_name = 'azimuth_angle_of_lidar_beam'
        
                    elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
                    elevation_angle.units = 'degrees'
                    elevation_angle.long_name = 'elevation_angle_of_lidar_beam'
    
                    CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
                    CNR.units = 'dB'
                    CNR.long_name = 'carrier_to_noise_ratio'
                    
                    WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
                    WIDTH.units = 'm.s-1'
                    WIDTH.long_name = 'doppler_spectrum_width'
                    
                    T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
                    T_internal.units = 'degrees C'
                    T_internal.long_name = 'internal_temperature'
                    
                    wiper_state = output_dataset.createVariable('wiper_state', 'f4', ('time',))
                    wiper_state.units = ''
                    wiper_state.long_name = 'wiper_state'
                
                # 10 minute mean data sta files
                else:
                    WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
                    WS.units = 'm.s-1'
                    WS.long_name = 'mean_of_scalar_wind_speed'
                    
                    WSstd = output_dataset.createVariable('WSstd', 'f4', ('time', 'range'))
                    WSstd.units = 'm.s-1'
                    WSstd.long_name = 'standard_deviation_of_scalar_wind_speed'
                    
                    WSmax = output_dataset.createVariable('WSmax', 'f4', ('time', 'range'))
                    WSmax.units = 'm.s-1'
                    WSmax.long_name = 'maximum_of_scalar_wind_speed'
                    
                    WSmin = output_dataset.createVariable('WSmin', 'f4', ('time', 'range'))
                    WSmin.units = 'm.s-1'
                    WSmin.long_name = 'minimum_of_scalar_wind_speed'
                    
                    DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
                    DIR.units = 'degrees'
                    DIR.long_name = 'mean_wind_direction'
                    
                    u = output_dataset.createVariable('u', 'f4', ('time', 'range'))
                    u.units = 'm.s-1'
                    u.long_name = 'mean_u_component_of_wind_speed'
                    
                    ustd = output_dataset.createVariable('ustd', 'f4', ('time', 'range'))
                    ustd.units = 'm.s-1'
                    ustd.long_name = 'standard_deviation_of_u_component_of_wind_speed'
                    
                    v = output_dataset.createVariable('v', 'f4', ('time', 'range'))
                    v.units = 'm.s-1'
                    v.long_name = 'mean_v_component_of_wind_speed'
                    
                    vstd = output_dataset.createVariable('vstd', 'f4', ('time', 'range'))
                    vstd.units = 'm.s-1'
                    vstd.long_name = 'standard_deviation_of_v_component_of_wind_speed'
                    
                    w = output_dataset.createVariable('w', 'f4', ('time', 'range'))
                    w.units = 'm.s-1'
                    w.long_name = 'mean_w_component_of_wind_speed'
                    
                    wstd = output_dataset.createVariable('wstd', 'f4', ('time', 'range'))
                    wstd.units = 'm.s-1'
                    wstd.long_name = 'standard_deviation_of_w_component_of_wind_speed'
                    
                    CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
                    CNR.units = 'dB'
                    CNR.long_name = 'mean_carrier_to_noise_ratio'
                                
                    CNRstd = output_dataset.createVariable('CNRstd', 'f4', ('time', 'range'))
                    CNRstd.units = 'dB'
                    CNRstd.long_name = 'standard_deviation_of_carrier_to_noise_ratio'
                    
                    CNRmax = output_dataset.createVariable('CNRmax', 'f4', ('time', 'range'))
                    CNRmax.units = 'dB'
                    CNRmax.long_name = 'maximum_carrier_to_noise_ratio'
                                
                    CNRmin = output_dataset.createVariable('CNRmin', 'f4', ('time', 'range'))
                    CNRmin.units = 'dB'
                    CNRmin.long_name = 'minimum_carrier_to_noise_ratio'
                    
                    WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
                    WIDTH.units = 'm.s-1'
                    WIDTH.long_name = 'mean_doppler_spectrum_width'
                    
                    WIDTHstd = output_dataset.createVariable('WIDTHstd', 'f4', ('time', 'range'))
                    WIDTHstd.units = 'm.s-1'
                    WIDTHstd.long_name = 'standard_deviation_of_doppler_spectrum_width'
                    
                    T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
                    T_internal.units = 'degrees C'
                    T_internal.long_name = 'mean_internal_temperature'
                    
                    Availability = output_dataset.createVariable('Availability', 'f4', ('time','range'))
                    Availability.units = 'percent'
                    Availability.long_name = '10_minute_availability'
                    
                    wiper_count = output_dataset.createVariable('wiper_count', 'f4', ('time',))
                    wiper_count.units = ''
                    wiper_count.long_name = 'wiper_count'
    
    
                # fill values from dataset
                data_timeseries = [row.strip().split('\t') for row in data[parameters['HeaderLength'] + 2:]]
                
                # e.g. radial velocity starts at 5th column and is then repeated every 9th column
                
                
                if filetype == 'rtd':
                    timestamp_input = [datetime.datetime.strptime(row[0][:-3],'%d/%m/%Y %H:%M:%S') for row in data_timeseries]
                    timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
                    output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
                    output_dataset.variables['T_internal'][:] = [float(row[2]) for row in data_timeseries]           
                    output_dataset.variables['wiper_state'][:] = np.array([row[3] for row in data_timeseries]) == 'On'
                    output_dataset.variables['azimuth_angle'][:] = [float(row[1]) for row in data_timeseries]
                    output_dataset.variables['elevation_angle'][:] = [parameters['ScanAngle(°)'] for row in data_timeseries]
                    output_dataset.variables['VEL'][:, :] = [[float(value) for value in row[7::8]] for row in data_timeseries]
                    output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[5::8]] for row in data_timeseries]
                    output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[4::8]] for row in data_timeseries]                
                    
                else: # filetype == 'sta' 10 minute mean values
                    timestamp_input = [datetime.datetime.strptime(row[0],'%d/%m/%Y %H:%M:%S') for row in data_timeseries]
                    timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
                    output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
                    output_dataset.variables['wiper_count'][:] = [float(row[1]) for row in data_timeseries]
                    output_dataset.variables['T_internal'][:] = [float(row[2]) for row in data_timeseries]
                    output_dataset.variables['WS'][:, :] = [[float(value) for value in row[3::19]] for row in data_timeseries]
                    output_dataset.variables['WSstd'][:, :] = [[float(value) for value in row[4::19]] for row in data_timeseries]
                    output_dataset.variables['WSmax'][:, :] = [[float(value) for value in row[5::19]] for row in data_timeseries]
                    output_dataset.variables['WSmin'][:, :] = [[float(value) for value in row[6::19]] for row in data_timeseries]
                    output_dataset.variables['DIR'][:, :] = [[float(value) for value in row[7::19]] for row in data_timeseries]
                    output_dataset.variables['u'][:, :] = [[float(value) for value in row[8::19]] for row in data_timeseries]
                    output_dataset.variables['ustd'][:, :] = [[float(value) for value in row[9::19]] for row in data_timeseries]
                    output_dataset.variables['v'][:, :] = [[float(value) for value in row[10::19]] for row in data_timeseries]
                    output_dataset.variables['vstd'][:, :] = [[float(value) for value in row[11::19]] for row in data_timeseries]
                    output_dataset.variables['w'][:, :] = [[float(value) for value in row[12::19]] for row in data_timeseries]
                    output_dataset.variables['wstd'][:, :] = [[float(value) for value in row[13::19]] for row in data_timeseries]
                    output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[14::19]] for row in data_timeseries]
                    output_dataset.variables['CNRstd'][:, :] = [[float(value) for value in row[15::19]] for row in data_timeseries]
                    output_dataset.variables['CNRmax'][:, :] = [[float(value) for value in row[16::19]] for row in data_timeseries]
                    output_dataset.variables['CNRmin'][:, :] = [[float(value) for value in row[17::19]] for row in data_timeseries]
                    output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[18::19]] for row in data_timeseries]
                    output_dataset.variables['WIDTHstd'][:, :] = [[float(value) for value in row[19::19]] for row in data_timeseries]
                    output_dataset.variables['Availability'][:, :] = [[float(value) for value in row[20::19]] for row in data_timeseries]
                    
            except Exception as err:
                print('Error ocurred while converting %s. See error.log for details.' % input_filepath)
           
                with open(Path(output_dataset.filepath()).parent / 'error.log','a') as logfile:
                    logfile.write( '%s'%output_dataset.filepath() +'\n')
                    

