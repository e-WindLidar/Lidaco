from ..core.Reader import Reader
import numpy as np
import datetime

# Change this to parameters, if necessary.
doppler_index = 1
intensity_index = 2
time_index = 3
azimuth_index = 4
elevation_index = 5
pitch_index = 6
roll_index = 7


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

    def read_to(self, output_dataset, input_filepath, configs, appending):
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

            # Dimensions
            output_dataset.createDimension('range', nr_gates)
            output_dataset.createDimension('time', len(scans))

            if constant_gates:
                range_values = np.full(nr_gates, float(range_gates))
            else:
                range_values = np.array(range_gates.split(';')).astype(float)

            timestamps = (scans[:, :, time_index])[:, 0]
            start_time_kv = metadata[4]
            start_time_str = start_time_kv[start_time_kv.find('\t') + 1:start_time_kv.find('\n')]
            start_time_seconds = process_time(start_time_str)
            time_values = np.array(list(map(lambda x: process_time(x) - start_time_seconds, timestamps)))

            # Coordinate variables
            self.create_variable(output_dataset, "range", "range", range_values)
            _time = self.create_variable(output_dataset, "time", data=time_values)
            _time.long_name = 'seconds since ' + start_time_str

            # Data variables
            scan_type = self.create_variable(output_dataset, "scan_type", "time")
            scan_id = self.create_variable(output_dataset, "scan_id", "time")

            # Beam steering and location variables
            self.create_variable(output_dataset, 'azimuth_angle', 'time', (scans[:, :, azimuth_index])[:, 0])
            self.create_variable(output_dataset, 'elevation_angle', 'time', (scans[:, :, elevation_index])[:, 0])
            self.create_variable(output_dataset, 'yaw', 'time', np.zeros(len(scans)))
            self.create_variable(output_dataset, 'roll', 'time', (scans[:, :, roll_index])[:, 0])
            self.create_variable(output_dataset, 'pitch', 'time', (scans[:, :, pitch_index])[:, 0])

            # Measurement variables
            self.create_variable(output_dataset, 'VEL', data=scans[:, :, doppler_index])
            self.create_variable(output_dataset, 'INTENSITY', data=scans[:, :, intensity_index])

            invalid_scans = 0
            scan_index = 1
            for s in measurement_scenarios:
                long_name = s['scenario']
                _type = int(s['type'])
                records = s['scans']
                if long_name == 'INVALID':
                    split_scans = records.split(';')
                    for ss in split_scans:
                        invalid_scans += int(ss.split('-')[1]) - int(ss.split('-')[0]) + 1
                else:
                    scan_group = output_dataset.createGroup('scan_' + str(scan_index) + '_' + long_name)
                    _azimuth = self.create_variable(scan_group, 'azimuth_angle', 'time', np.zeros(len(scans)))
                    _elevation = self.create_variable(scan_group, 'elevation_angle', 'time', np.zeros(len(scans)))
                    self.create_variable(scan_group, 'yaw', 'time', np.zeros(len(scans)))
                    _pitch = self.create_variable(scan_group, 'pitch', 'time', np.zeros(len(scans)))
                    _roll = self.create_variable(scan_group, 'roll', 'time', np.zeros(len(scans)))
                    _doppler = self.create_variable(scan_group, 'VEL', data=np.zeros(shape=[len(scans), int(nr_gates)]))
                    _intensity = self.create_variable(scan_group, 'INTENSITY', data=np.zeros(shape=[len(scans), int(nr_gates)]))
                    split_scans = records.split(';')
                    for ss in split_scans:
                        initial_index = int(ss.split('-')[0]) - (invalid_scans + 1)
                        final_index = int(ss.split('-')[1]) - (invalid_scans + 1)
                        scan_type[initial_index:final_index + 1] = _type
                        scan_id[initial_index:final_index + 1] = scan_index
                        _azimuth[initial_index:final_index + 1] = scans[initial_index:final_index + 1, :, azimuth_index][:, 0]
                        _elevation[initial_index:final_index + 1] = scans[initial_index:final_index + 1, :, elevation_index][:, 0]
                        _pitch[initial_index:final_index + 1] = scans[initial_index:final_index + 1, :, pitch_index][:, 0]
                        _roll[initial_index:final_index + 1] = scans[initial_index:final_index + 1, :, roll_index][:, 0]
                        _doppler[initial_index:final_index + 1] = scans[initial_index:final_index + 1, :, doppler_index]
                        _intensity[initial_index:final_index + 1] = scans[initial_index:final_index + 1, :, intensity_index]
                    scan_index += 1
