# !/usr/bin/env python
# encoding: utf-8
"""
Halo Stream Line data reader for Lidaco
=======================================
The reader reads the Halo Stream Line .hpl file containing the Doppler velocity, intensity (SNR+1) and Beta/Backscatter (m-1 sr-1) for each range gate

A file looks like this (header and first lines of data only)

Filename:	User5_96_20190308_200500.hpl
System ID:	96
Number of gates:	150
Range gate length (m):	30.0
Gate length (pts):	10
Pulses/ray:	2000
No. of rays in file:	16
Scan type:	S_windycities_24pt_repeat22 - stepped
Focus range:	65535
Start time:	20190308 20:05:03.76
Resolution (m/s):	0.0382
Altitude of measurement (center of gate) = (range gate + 0.5) * Gate length
Data line 1: Decimal time (hours)  Azimuth (degrees)  Elevation (degrees) Pitch (degrees) Roll (degrees)
f9.6,1x,f6.2,1x,f6.2
Data line 2: Range Gate  Doppler (m/s)  Intensity (SNR + 1)  Beta (m-1 sr-1)
i3,1x,f6.4,1x,f8.6,1x,e12.6 - repeat for no. gates
****
20.084231  39.81  -0.00 -0.20 0.10
  0 -0.2173 1.135933  7.655162E-6
  1 -0.2173 1.127027  7.154400E-6
  2 -0.2173 1.116684  6.572640E-6
  3 -0.0645 1.106170  5.981129E-6
  4 15.1091 1.094162  5.305355E-6
  ...

:ignore
Created: Maayen Wigger on 2019-06-05
         Stuttgart Wind Energy
         University of Stuttgart

Changes:
    2019-06-05:
        - First approach changing the galion reader to readn stream line data di not work
    2019-08-01
        -
	2023-07-04
		Fixed incorrect assignment of channel data (pitch, roll, etc.)
		Gunhild Thorsen & Elliot Simon (DTU)

Todo:
    - range gate distance not calculated correctly if gate overlapping is used
:ignore
"""

# import builtin packages
from _datetime import datetime

# import pypi packages
import numpy as np

# import user packages
from ..core.Reader import Reader


def get_scan_type(file_name):

    if file_name.startswith('User'):
        return 0
    elif file_name.startswith('Stare'):
        return 1
    elif file_name.startswith('DBS'):
        return 2
    elif file_name.startswith('VAD'):
        return 3
    elif file_name.startswith('PPI'):
        return 4
    elif file_name.startswith('RHI'):
        return 5


def decimaltime2sec(dt, day):
    """convert decimal time to str"""
    time_hours = dt
    time_minutes = time_hours * 60
    time_seconds = time_minutes * 60

    hours_part = (time_hours % 60).astype(int)
    minutes_part = (time_minutes % 60).astype(int)
    seconds_part = (time_seconds % 60).astype(int)
    microsec_part = (((time_seconds % 60) - seconds_part) * 1.E6).astype(int)
    alltime = []
    for i, j, k, l in zip(hours_part, minutes_part, seconds_part, microsec_part):
        date = day + ' ' + "{h:02d}:{m:02d}:{s:02d}.{ms:06d}".format(h=i, m=j, s=k, ms=l)
        date = datetime.strptime(date, '%Y%m%d %H:%M:%S.%f')
        alltime.append(date.timestamp())
    return np.array(alltime)


class StreamLine(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return filename.endswith('.hpl')

    def output_filename(self, filename):
        return filename[:-4]

    def required_params(self):
        return ['n_gates', 'range_gates', 'constant_gates', 'measurement_scenarios']

    @staticmethod
    def read_header(fd):
        header = {}
        line = fd.readline()
        parameter = line.split(':')
        header[parameter[0]] = ':'.join([i.lstrip().rstrip() for i in parameter[1:]])
        while 'Resolution (m/s)' not in line:
            line = fd.readline()
            parameter = line.split(':')
            header[parameter[0]] = ':'.join([i.lstrip().rstrip() for i in parameter[1:]])
        # convert header values to appropriate type
        for key, value in header.items():
            try:
                header[key] = float(value)
            except ValueError:
                pass
        return header

    def read_to(self, dataset, input_filepath, configs, appending):

        # read required parameters from config
        nr_gates = configs['parameters']['n_gates']
        range_gates = configs['parameters']['range_gates']

        # for every file to read open and process it
        with open(input_filepath, 'r') as file:
            # read in header
            header = self.read_header(file)

            # skip next lines
            line = file.readline()
            while '****' not in line:
                line = file.readline()

            # read rest of file containing measurement data
            raw_file = file.readlines()
        # file closed

        # check variables in header
        assert float(nr_gates) == header['Number of gates']
        assert float(range_gates) == header['Range gate length (m)']

        # split the info line for every ray from the rest of the data
        # measured_info contains timestamp, azimut, elevation, pitch and roll
        # i.e. 20.084231  39.81  -0.00 -0.20 0.10
        # all lines n*n_gates with 0 <= n < number of rays
        measured_info_s = raw_file[::int(nr_gates) + 1]

        # convert the measured info from list of str to numpy array
        measured_info = np.empty((len(measured_info_s), 5))
        # for i in range(len(measured_info_s)):
        #     measured_info[i, :] = np.fromstring(measured_info_s[i], dtype='f4', sep=' ')
        for i, line in enumerate(measured_info_s):
            measured_info[i, :] = np.fromstring(line, dtype='f4', sep=' ')

        # convert the time stamp from decimal hour of day to epoch double format
        header_day = header['Start time'].split(' ')[0]
        measured_info[:, 0] = decimaltime2sec(measured_info[:, 0], header_day)

        # the rest is the actual data with range gate number, doppler,
        # intensity and backscatter
        # i.e.   0 -0.2173 1.135933  7.655162E-6
        #        1 -0.2173 1.127027  7.154400E-6
        del(raw_file[::int(nr_gates+1)])
        measured_data_s = [x.lstrip().rstrip() for x in raw_file]

        # convert measured data from list of str to numpy array
        measured_data = np.empty((len(measured_data_s), 4))
        # for i in range(len(measured_data_s)):
        #     measured_data[i, :4] = np.fromstring(measured_data_s[i], dtype='f4', sep=' ')
        for i, line in enumerate(measured_data_s):
            measured_data[i, :4] = np.fromstring(line, dtype='f4', sep=' ')

        # Dimensions
        n_rays = int(measured_info.shape[0])
        n_gates = int(header['Number of gates'])

        # Initialize the data set if not appending to existing data
        if not appending:
            # create the dimensions
            dataset.createDimension('range', header['Number of gates'])
            # the time dimension must be without limits (None) to append later
            dataset.createDimension('time', None)

            # create the coordinate variables

            # range
            # see header of measurement file
            # Center of gate = (range gate + 0.5) * Gate length
            gate_length = header['Range gate length (m)']
            _range_dist = (measured_data[0:nr_gates, 0] + 0.5) * gate_length
            range_dist = dataset.createVariable('range', 'f4', ('range',))
            range_dist.units = 'm'
            range_dist.long_name = 'range_gate_distance_from_lidar'
            range_dist[:] = _range_dist
            range_dist.comment = 'distance to center of probe volume'

            # time
            # get start time for storing the campaign start (first measurement)
            # timestamp in comment
            start_time = datetime.utcfromtimestamp(measured_info[0, 0]).isoformat() + 'Z'
            # timestamps are stored as seconds since campaign start
            _time = measured_info[:, 0] - measured_info[0, 0]
            time = dataset.createVariable('time', 'f4', ('time',))
            time.units = 's'
            time.long_name = 'time stamp'
            time[:] = _time
            time.comment = 'seconds since campaign start at ' + start_time

            # create the data variables
            # TODO: get the scan type from data
            scan_type = dataset.createVariable('scan_type', 'i', 'time')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'
            scan_type[:] = np.ones((n_rays, 1)) * get_scan_type(header['Filename'])

            # TODO: define scan ID
            scan_id = dataset.createVariable('scan_id', 'i', 'time')
            scan_id.units = 'none'
            scan_id.long_name = 'scan_id_of_the_measurement'

            #
            scan_cycle = dataset.createVariable('scan_cycle', 'i', 'time')
            scan_cycle.units = 'none'
            scan_cycle.long_name = 'scan_cycle_number'
            scan_cycle[:] = np.ones((n_rays, 1))

            # create the beam steering variables
            # azimuth
            _azimuth = measured_info[:, 1]
            azimuth_angle = dataset.createVariable('azimuth_angle', 'f4', 'time')
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar_beam'
            azimuth_angle[:] = _azimuth
            azimuth_angle.comment = 'clock-wise angle from north'
            azimuth_angle.accuracy = ''
            azimuth_angle.accuracy_info = 'max resolution 0.00072 degrees'

            # elevation
            _elevation = measured_info[:, 2]
            elevation_angle = dataset.createVariable('elevation_angle', 'f4', 'time')
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle[:] = _elevation
            elevation_angle.comment = 'upwards angle from horizontal'
            elevation_angle.accuracy = ''
            elevation_angle.accuracy_info = 'max resolution 0.00144 degrees'

            # yaw, pitch, roll
            # yaw is not available
            _yaw = np.zeros(measured_info[:, 3].shape)
            yaw = dataset.createVariable('yaw', 'f4', 'time')
            yaw.units = 'degrees'
            yaw.long_name = 'lidar_yaw_angle'
            yaw[:] = _yaw
            yaw.comment = 'The home position is configured in a way that 0 ' \
                          'azimuth corresponds to north.'
            yaw.accuracy = ''

            _pitch = measured_info[:, 3]
            pitch = dataset.createVariable('pitch', 'f4', 'time')
            pitch.units = 'degrees'
            pitch.long_name = 'lidar_pitch_angle'
            pitch[:] = _pitch
            pitch.comment = ''
            pitch.accuracy = ''
            pitch.accuracy_info = 'No information on pitch accuracy available.'

            _roll = measured_info[:, 4]
            roll = dataset.createVariable('roll', 'f4', 'time')
            roll.units = 'degrees'
            roll.long_name = 'lidar_roll_angle'
            roll[:] = _roll
            roll.comment = ''
            roll.accuracy = ''
            roll.accuracy_info = 'No information on roll accuracy available.'

            # measurement variables

            # Doppler velocity
            DOPPLER = dataset.createVariable('VEL', 'f4', ('time', 'range'))
            DOPPLER.units = 'm.s-1'
            DOPPLER.long_name = 'doppler'
            DOPPLER[:, :] = measured_data[:, 1].reshape(n_rays, n_gates)

            INTENSITY = dataset.createVariable('INTENSITY', 'f4', ('time', 'range'))
            INTENSITY.units = ''
            INTENSITY.long_name = 'intensity'
            INTENSITY.comment = 'snr + 1'
            INTENSITY[:] = measured_data[:, 2].reshape(n_rays, n_gates)

            BACKSCATTER = dataset.createVariable('BACKSCATTER', 'f4', ('time', 'range'))
            BACKSCATTER.units = 'm-1.s-1'
            BACKSCATTER.long_name = 'backscatter'
            BACKSCATTER[:] = measured_data[:, 3].reshape(n_rays, n_gates)

        else:
            # get current number of stored measurements
            n_times = len(dataset.dimensions['time'])

            # time
            #get campaign start time
            _start_time = dataset.variables['time'].comment
            start_time = datetime.strptime(_start_time[-27:], "%Y-%m-%dT%H:%M:%S.%fZ")
            _time = measured_info[:, 0] - start_time.timestamp()
            dataset.variables['time'][n_times:] = _time

            # scan type
            _scan_type = np.ones((n_rays, 1)) * get_scan_type(header['Filename'])
            dataset.variables['scan_type'][n_times:] = _scan_type

            # scan cycle
            _last_scan_cycle = dataset.variables['scan_cycle'][n_times - 1]
            _scan_cycle = np.ones((n_rays, 1)) * (_last_scan_cycle + 1)
            dataset.variables['scan_cycle'][n_times:] = _scan_cycle


            # azimuth
            _azimuth = measured_info[:, 1]
            dataset.variables['azimuth_angle'][n_times:] = _azimuth

            # elevation
            _elevation = measured_info[:, 2]
            dataset.variables['elevation_angle'][n_times:] = _elevation

            # yaw is not available
            _yaw = np.zeros(measured_info[:, 3].shape)
            dataset.variables['yaw'][n_times:] = _yaw

            # pitch
            _pitch = measured_info[:, 3]
            dataset.variables['pitch'][n_times:] = _pitch

            # roll
            _roll = measured_info[:, 4]
            dataset.variables['roll'][n_times:] =  _roll

            # doppler
            _doppler = measured_data[:, 1].reshape(n_rays, n_gates)
            dataset.variables['VEL'][n_times:] = _doppler

            # intensity
            _intensity = measured_data[:, 2].reshape(n_rays, n_gates)
            dataset.variables['INTENSITY'][n_times:] = _intensity

            # backscatter
            _backscatter = measured_data[:, 3].reshape(n_rays, n_gates)
            dataset.variables['BACKSCATTER'][n_times:] = _backscatter
