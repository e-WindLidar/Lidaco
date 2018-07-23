# Adapted from Windcubev2, but not yet tested

import datetime
import numpy as np
from ..core.Reader import Reader


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
    
    # remove this from params but set it manually here
#    def required_params(self):
#        return ['position_x_input', 'position_y_input', 'position_z_input']

    def read_to(self, output_dataset, input_filepath, configs, appending):


        # read file
        with open(input_filepath, encoding='latin-1') as f:
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
            time.long_name = 'seconds since ' + parameters['first_timestamp'].strftime('%Y/%m/%d') + ' 00:00:00'
            

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
            scan_type[:] = 1

            accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
            accumulation_time.units = 'seconds'
            accumulation_time.long_name = 'time_for_spectral_accumulation'
            accumulation_time[:] = 1.0

            n_spectra = output_dataset.createVariable('n_spectra', 'f4')
            n_spectra.units = 'none'
            n_spectra.long_name = 'number_of_pulses'
            n_spectra[:] = parameters['NumberOfAveragedShots']




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
            
            else:
                WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
                WS.units = 'm.s-1'
                WS.long_name = 'mean of scalar wind speed'
                
                
                
                
                
            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier-to-noise ratio'

            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'doppler_spectrum_width'

            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'temperature'
            
            wiper = output_dataset.createVariable('wiper', 'f4', ('time',))
            wiper.units = 'V'
            wiper.long_name = 'Wiper count Vbatt'
            

            # fill values from dataset
            data_timeseries = [row.strip().split('\t') for row in data[parameters['HeaderLength'] + 3:]]
            
            # check if Windcubev2.util_process_time works here, should be the same as for Windcube v2
            # check implementation of azimuth, elevation, ...
            
            #  check if this is correct
            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            if filetype == 'rtd':
                timestamp_input = [datetime.datetime.strptime(row[0][:-3],'%d/%m/%Y %H:%M:%S') for row in data_timeseries]
                timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
                output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
                output_dataset.variables['T_internal'][:] = [float(row[2]) for row in data_timeseries]
                output_dataset.variables['wiper'][:] = [float(row[3]) for row in data_timeseries]       #needs to be validated with a rtd-File!!!!!!!!!!!!!!!!!!
                output_dataset.variables['azimuth_angle'][:] = [float(row[1]) for row in data_timeseries]
                output_dataset.variables['elevation_angle'][:] = [parameters['ScanAngle(°)'] for row in data_timeseries]
                
                output_dataset.variables['VEL'][:, :] = [[float(value) for value in row[7::8]] for row in data_timeseries]
                output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[5::8]] for row in data_timeseries]
                output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[4::8]] for row in data_timeseries]
                
                
            else:
                timestamp_input = [datetime.datetime.strptime(row[0],'%d/%m/%Y %H:%M:%S') for row in data_timeseries]
                timestamp_iso8601 = [value.isoformat()+'Z' for value in timestamp_input]
                output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
                output_dataset.variables['wiper'][:] = [float(row[1]) for row in data_timeseries]
                output_dataset.variables['WS'][:, :] = [[float(value) for value in row[3::19]] for row in data_timeseries]
                output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[18::19]] for row in data_timeseries]
                output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[14::19]] for row in data_timeseries]
