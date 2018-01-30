from ..core.Reader import Reader
import numpy as np
import datetime


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def process_time(timestamp):
    y, m, d = timestamp[:10].split('-')
    h, min_, s = timestamp[11:19].split(':')
    ms = timestamp[20:]
    dt = datetime.datetime(int(y), int(m), int(d), int(h), int(min_), int(s), int(ms) * 1000)
    return dt.timestamp()


class Galion(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return filename.endswith('.scn')

    def output_filename(self, filename):
        return filename[:-4]

    def required_params(self):
        return ['n_gates', 'range_gates', 'constant_gates', 'measurement_scenarios']

    def read_to(self, output_dataset, input_filepath, configs, index):
        with open(input_filepath) as file:
            nr_gates = configs['parameters']['n_gates']
            range_gates = configs['parameters']['range_gates']
            constant_gates = configs['parameters']['constant_gates']
            measurement_scenarios = configs['parameters']['measurement_scenarios']
            raw_file = file.readlines()

            # if we can assume that the metadata is always the same length
            # If not, then it's better to add a variable to identify the number of lines that are "metadata"
            metadata = raw_file[:6]
            data = raw_file[6:]

            scans = np.array(list(chunks([row.strip().split('\t') for row in data], int(nr_gates))))

            # create the dimensions
            output_dataset.createDimension('range', nr_gates)
            output_dataset.createDimension('time', len(scans))

            # create the coordinate variables
            # range
            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            if constant_gates:
                range1[:] = np.full(nr_gates, float(range_gates))
            else:
                range1[:] = np.array(range_gates.split(';')).astype(float)
            range1.comment = ''

            # time
            time = output_dataset.createVariable('time', 'f4', ('time',))
            time.units = 's'
            start_time_kv = metadata[4]
            start_time_str = start_time_kv[start_time_kv.find('\t') + 1:start_time_kv.find('\n')]
            start_time_seconds = process_time(start_time_str)
            time.long_name = 'seconds since ' + start_time_str
            # array manipulation to obtain timestamps
            timestamps = (scans[:, :, 3])[:, 0]
            time[:] = np.array(list(map(lambda x: process_time(x) - start_time_seconds, timestamps)))
            time.comment = ''

            # create the beam steering variables
            # azimuth and elevation
            azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', 'time')
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
            azimuth_angle[:] = (scans[:, :, 4])[:, 0]
            azimuth_angle.comment = ''
            azimuth_angle.accuracy = ''
            azimuth_angle.accuracy_info = ''

            elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', 'time')
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle[:] = (scans[:, :, 5])[:, 0]
            elevation_angle.comment = ''
            elevation_angle.accuracy = ''
            elevation_angle.accuracy_info = ''

            # yaw, pitch, roll
            yaw = output_dataset.createVariable('yaw', 'f4', 'time')
            yaw.units = 'degrees'
            yaw.long_name = 'lidar_yaw_angle'
            yaw[:] = np.zeros(len(scans))
            yaw.comment = 'The home position of the lidar has been configured in a way that 0 azimuth corresponds to ' \
                          'north. '
            yaw.accuracy = ''

            pitch = output_dataset.createVariable('pitch', 'f4', 'time')
            pitch.units = 'degrees'
            pitch.long_name = 'lidar_pitch_angle'
            pitch[:] = (scans[:, :, 6])[:, 0]
            pitch.comment = ''
            pitch.accuracy = ''
            pitch.accuracy_info = 'No information on pitch accuracy available.'

            roll = output_dataset.createVariable('roll', 'f4', 'time')
            roll.units = 'degrees'
            roll.long_name = 'lidar_roll_angle'
            roll[:] = (scans[:, :, 7])[:, 0]
            roll.comment = ''
            roll.accuracy = ''
            roll.accuracy_info = 'No information on roll accuracy available.'

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i', 'time')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'

            scan_id = output_dataset.createVariable('scan_id', 'i', 'time')
            scan_id.units = 'none'
            scan_id.long_name = 'scan_id_of_the_measurement'

            # measurement variables
            # TODO verify metadata
            # Doppler and Intensity
            DOPPLER = output_dataset.createVariable('DOPPLER', 'f4', ('time', 'range'))
            DOPPLER.units = 'm.s-1'
            DOPPLER.long_name = 'doppler'
            DOPPLER[:] = (scans[:, :, 1])[:]

            INTENSITY = output_dataset.createVariable('INTENSITY', 'f4', ('time', 'range'))
            INTENSITY.units = 'm.s-1'
            INTENSITY.long_name = 'intensity'
            INTENSITY[:] = (scans[:, :, 2])[:]

            invalid_scans = 0
            scan_index = 1
            for s in measurement_scenarios:
                long_name = s['scenario']
                _type = int(s['type'])
                scans = s['scans']
                if long_name == 'INVALID':
                    split_scans = scans.split(';')
                    for ss in split_scans:
                        invalid_scans += int(ss.split('-')[1]) - int(ss.split('-')[0]) + 1
                else:
                    split_scans = scans.split(';')
                    for ss in split_scans:
                        initial_index = int(ss.split('-')[0]) - (invalid_scans + 1)
                        final_index = int(ss.split('-')[1]) - (invalid_scans + 1)
                        scan_type[initial_index:final_index + 1] = _type
                        scan_id[initial_index:final_index + 1] = scan_index
                    scan_index += 1
