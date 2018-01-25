from ..core.Reader import Reader
import pprint


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


class Galion(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return filename.endswith('.scn')

    def output_filename(self, filename):
        return filename[:-4]

    def read_to(self, output_dataset, input_filepath, configs, index):
        with open(input_filepath) as file:
            range_gates = 42
            raw_file = file.readlines()

            # if we can assume that the metadata is always the same length
            # If not, then it's better to add a variable to identify the number of lines that are "metadata"
            metadata = raw_file[:6]
            data = raw_file[6:]

            # It is useful to have defined the number of ranges per scan
            scans = list(chunks([row.strip().split('\t') for row in data], range_gates))
            pprint.pprint(scans)

            # create the dimensions
            output_dataset.createDimension('range', range_gates)
            output_dataset.createDimension('time', None)

            # create the coordinate variables
            # range
            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            range1[:] = 0
            range1.comment = ''

            # time
            time = output_dataset.createVariable('time', 'f4', ('time',))
            time.units = 's'
            time.long_name = 'seconds since 1904-01-01 12:00AM UTC'
            time.comment = ''

            # create the beam steering variables
            # azimuth and elevation
            azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', 'time')
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
            azimuth_angle.comment = ''
            azimuth_angle.accuracy = ''
            azimuth_angle.accuracy_info = ''

            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', 'time')
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle.comment = ''
            elevation_angle.accuracy = ''
            elevation_angle.accuracy_info = ''

            # yaw, pitch, roll
            yaw = output_dataset.createVariable('yaw', 'f4')
            yaw.units = 'degrees'
            yaw.long_name = 'lidar_yaw_angle'
            yaw[:] = 0
            yaw.comment = 'The home position of the lidar has been configured in a way that 0 azimuth corresponds to north.'
            yaw.accuracy = ''

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

            # create the measurement variables VEL, CNR, WIDTH

