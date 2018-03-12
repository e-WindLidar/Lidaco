from ..core.Reader import Reader


class Windscanner(Reader):

    def __init__(self):
        super().__init__(True)

    def accepts_file(self, filename):
        return filename.endswith('.txt') & (len(filename) > 14)

    def group_id(self, filename):
        return filename[:14]

    def output_filename(self, timestamp):
        return timestamp

    def required_params(self):
        return {
            'position': ['x', 'y', 'z']
        }

    def read_to(self, output_dataset, input_filepaths, configs, appending):
        scanner_file, system_file, wind_file = input_filepaths

        x = configs['parameters']['position']['x']
        y = configs['parameters']['position']['y']
        z = configs['parameters']['position']['z']



        with open(wind_file) as f:
            wind_file_data = f.readlines()

        with open(system_file) as f:
            system_file_data = f.readlines()

        with open(scanner_file) as f:
            scanner_file_data = f.readlines()

        wind_file_data = list(zip(*[row.strip().split(';') for row in wind_file_data]))
        system_file_data = list(zip(*[row.strip().split(';') for row in system_file_data]))
        scanner_file_data = list(zip(*[row.strip().split(';') for row in scanner_file_data]))

        if not appending:

            index_columns = 4 - (len(wind_file_data) % 4)
            range_list = [float(row[0]) for row in wind_file_data[index_columns + 4::4]]

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
            time = output_dataset.createVariable('time', 'f4', ('time',))
            time.units = 's'
            time.long_name = 'seconds since 1904-01-01 12:00AM UTC'
            time.comment = ''

            # create the beam steering variables

            # azimuth and elevation
            azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
            azimuth_angle.comment = ''
            azimuth_angle.accuracy = ''
            azimuth_angle.accuracy_info = ''

            #  only applicable for PPI or sweeping CT
            azimuth_sweep = output_dataset.createVariable('azimuth_sweep', 'f4')
            azimuth_sweep.units = 'degrees'
            azimuth_sweep.long_name = 'azimuth_sector_swept_during_accumulation'
            azimuth_sweep.comment = ''
            azimuth_sweep[:] = 0
            azimuth_sweep.accuracy = ''
            azimuth_sweep.accuracy_info = ''

            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle.comment = ''
            elevation_angle.accuracy = ''
            elevation_angle.accuracy_info = ''

            #  only applicable for RHI or sweeping CT
            elevation_sweep = output_dataset.createVariable('elevation_sweep', 'f4')
            elevation_sweep.units = 'degrees'
            elevation_sweep.long_name = 'elevation_sector_swept_during_accumulation'
            elevation_sweep.comment = 'Elevation sweeping from approximately 0 to 15 degrees.'
            elevation_sweep[:] = 2
            elevation_sweep.accuracy = ''
            elevation_sweep.accuracy_info = ''

            # yaw, pitch, roll
            yaw = output_dataset.createVariable('yaw', 'f4')
            yaw.units = 'degrees'
            yaw.long_name = 'lidar_yaw_angle'
            yaw[:] = 0
            yaw.comment = 'The home position of the lidar has been configured in a way that 0 azimuth corresponds to north.'
            yaw.accuracy = ''
            yaw.accuracy_info = 'No information on yaw accuracy available.'

            pitch = output_dataset.createVariable('pitch', 'f4')
            pitch.units = 'degrees'
            pitch.long_name = 'lidar_pitch_angle'
            pitch[:] = 0
            pitch.comment = ''
            pitch.accuracy = ''
            pitch.accuracy_info = 'No information on pitch accuracy available.'

            roll = output_dataset.createVariable('roll', 'f4')
            roll.units = 'degrees'
            roll.long_name = 'lidar_roll_angle'
            roll[:] = 0
            roll.comment = ''
            roll.accuracy = ''
            roll.accuracy_info = 'No information on roll accuracy available.'

            # create the location variables x,y,z
            position_x = output_dataset.createVariable('position_x', 'f4')
            position_x.units = 'm'
            position_x.long_name = 'x_position_of_lidar'
            position_x.comment = 'Measured by GPS. Coordinates are UTM 32 N.'
            position_x[:] = x
            position_x.accuracy = '<1m'
            position_x.accuracy_info = 'Coordinates taken by a hand-held Garmin GPS device.'

            position_y = output_dataset.createVariable('position_y', 'f4')
            position_y.units = 'm'
            position_y.long_name = 'y_position_of_lidar'
            position_y.comment = 'Measured by GPS. Coordinates are UTM 32 N.'
            position_y[:] = y
            position_y.accuracy = '<1m'
            position_y.accuracy_info = 'Coordinates taken by a hand-held Garmin GPS device.'

            position_z = output_dataset.createVariable('position_z', 'f4')
            position_z.units = 'meters'
            position_z.long_name = 'z_position_of_lidar'
            position_z.comment = 'Taken from a digital elevation model for the measured x,y position.'
            position_z[:] = z
            position_z.accuracy = '<1m'
            position_z.accuracy_info = 'The digital elevation model was prepared under the use of airborne lidar data and verified against a federal digital elevation model.'

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'
            scan_type[:] = 4

            scan_id = output_dataset.createVariable('scan_id', 'i')
            scan_id.units = 'none'
            scan_id.long_name = 'scan_id_of_the_measurement'
            scan_id[:] = 1

            accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
            accumulation_time.units = 'seconds'
            accumulation_time.long_name = 'time_for_spectral_accumulation'
            accumulation_time[:] = 2
            accumulation_time.comment = ''

            n_spectra = output_dataset.createVariable('n_spectra', 'f4')
            n_spectra.units = 'none'
            n_spectra.long_name = 'number_of_pulses'
            n_spectra[:] = 0
            n_spectra.comment = 'No information available on number of spectra.'

            # create the measurement variables VEL, CNR, WIDTH
            VEL = output_dataset.createVariable('VEL', 'f4', ('time', 'range'))
            VEL.units = 'm.s-1'
            VEL.long_name = 'radial velocity'
            VEL.comment = ''
            VEL.accuracy = ''
            VEL.accuracy_info = ''

            CNR = output_dataset.createVariable('CNR', 'f4', ('time', 'range'))
            CNR.units = 'dB'
            CNR.long_name = 'carrier-to-noise ratio'
            CNR.comment = ''
            CNR.accuracy = ''
            CNR.accuracy_info = ''

            WIDTH = output_dataset.createVariable('WIDTH', 'f4', ('time', 'range'))
            WIDTH.units = 'm.s-1'
            WIDTH.long_name = 'doppler spectrum width'
            WIDTH.comment = ''
            WIDTH.accuracy = ''
            WIDTH.accuracy_info = ''

            # fill values from dataset
            output_dataset.variables['time'][:] = [float(value) for value in wind_file_data[index_columns]]
            output_dataset.variables['azimuth_angle'][:] = [float(value) for value in wind_file_data[6]]
            output_dataset.variables['elevation_angle'][:] = [float(value) for value in wind_file_data[7]]

            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['VEL'][:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 5::4]]))
            output_dataset.variables['WIDTH'][:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 6::4]]))
            output_dataset.variables['CNR'][:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 7::4]]))

        else:
            index_columns = 4 - (len(wind_file_data) % 4)

            ntime = len(output_dataset.dimensions["time"])

            output_dataset.variables['time'][ntime:] = [float(value) for value in wind_file_data[index_columns]]
            output_dataset.variables['azimuth_angle'][ntime:] = [float(value) for value in wind_file_data[6]]
            output_dataset.variables['elevation_angle'][ntime:] = [float(value) for value in wind_file_data[7]]

            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['VEL'][ntime:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 5::4]]))
            output_dataset.variables['WIDTH'][ntime:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 6::4]]))
            output_dataset.variables['CNR'][ntime:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 7::4]]))
