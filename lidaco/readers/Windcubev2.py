import datetime
import numpy as np
from ..core.Reader import Reader


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
        return filename.endswith('.rtd')

    def output_filename(self, filename):
        return filename[:-4]

    def required_params(self):
        return {
            'position': ['x', 'y', 'z']
        }

    def read_to(self, output_dataset, input_filepath, configs, appending):
        position_x_input = configs['parameters']['position']['x']
        position_y_input = configs['parameters']['position']['y']
        position_z_input = configs['parameters']['position']['z']

        # read file
        with open(input_filepath, encoding='latin-1') as f:
            data = f.readlines()

            # get parameters from header
            temp_HeaderSize = int(data[0].split(sep='=')[1])
            parameters = [line[:-1].split(sep='=') for line in data[0:temp_HeaderSize]]
            parameters = {line[0]: Windcubev2.str_to_num(line[1]) for line in parameters if len(line) == 2}
            parameters['Altitudes (m)'] = [Windcubev2.str_to_num(element) for element in
                                           parameters['Altitudes (m)'].strip().split('\t')]
            parameters['first_timestamp'] = datetime.datetime.strptime(
                data[parameters['HeaderSize'] + 2].split('\t')[0][:-3],
                '%Y/%m/%d %H:%M:%S')

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

            time = output_dataset.createVariable('time', 'f4', ('time',))
            time.units = 's'
            time.long_name = 'seconds since ' + parameters['first_timestamp'].strftime('%Y/%m/%d') + ' 00:00:00'

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

            position_x = output_dataset.createVariable('position_x', 'f4')
            position_x.units = 'degrees east'
            position_x.long_name = 'x_position_of_lidar'
            position_x[:] = position_x_input

            position_y = output_dataset.createVariable('position_y', 'f4')
            position_y.units = 'degrees north'
            position_y.long_name = 'y_position_of_lidar'
            position_y[:] = position_y_input

            position_z = output_dataset.createVariable('position_z', 'f4')
            position_z.units = 'meters'
            position_z.long_name = 'z_position_of_lidar'
            position_z[:] = position_z_input

            azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'

            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'
            scan_type[:] = 1

            scan_id = output_dataset.createVariable('scan_id', 'i')
            scan_id.units = 'none'
            scan_id.long_name = 'scan_id_of_the_measurement'
            scan_id[:] = 1

            accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
            accumulation_time.units = 'seconds'
            accumulation_time.long_name = 'time_for_spectral_accumulation'
            accumulation_time[:] = 1.0

            n_spectra = output_dataset.createVariable('n_spectra', 'f4')
            n_spectra.units = 'none'
            n_spectra.long_name = 'number_of_pulses'
            n_spectra[:] = parameters['Pulses / Line of Sight']

            # create the measurement variables
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial_velocity'

            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier-to-noise ratio'

            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'doppler_spectrum_width'

            T_internal = output_dataset.createVariable('T_internal', 'f4', ('time',))
            T_internal.units = 'degrees C'
            T_internal.long_name = 'temperature'

            # fill values from dataset
            data_timeseries = [row.strip().split('\t') for row in data[parameters['HeaderSize'] + 2:]]

            output_dataset.variables['time'][:] = [Windcubev2.util_process_time(row[0][11:]) for row in data_timeseries]
            output_dataset.variables['T_internal'][:] = [float(row[2]) for row in data_timeseries]
            output_dataset.variables['azimuth_angle'][:] = [float(row[1]) if row[1] != 'V' else 0 for row in
                                                            data_timeseries]
            output_dataset.variables['elevation_angle'][:] = [90 - parameters['ScanAngle (°)'] if row[1] != 'V' else 90
                                                              for
                                                              row
                                                              in data_timeseries]

            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['VEL'][:, :] = [[float(value) for value in row[5::9]] for row in data_timeseries]
            output_dataset.variables['WIDTH'][:, :] = [[float(value) for value in row[6::9]] for row in data_timeseries]
            output_dataset.variables['CNR'][:, :] = [[float(value) for value in row[4::9]] for row in data_timeseries]
