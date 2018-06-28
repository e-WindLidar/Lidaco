from ..core.Reader import Reader
from datetime import datetime, timedelta
import numpy as np


class Windscanner(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return filename.endswith('wind.txt') & (len(filename) > 14)

    def output_filename(self, timestamp):
        return timestamp[:-9]

    def read_to(self, output_dataset, input_filepaths, parameters, appending):
        wind_file = input_filepaths

        with open(wind_file) as f:
            wind_file_data = f.readlines()

        wind_file_data = list(zip(*[row.strip().split(';') for row in wind_file_data]))

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
            time = output_dataset.createVariable('time', str, ('time',))
            time.units = 's'
            time.long_name = 'Time UTC in ISO 8601 format yyyy-mm-ddThh:mm:ssZ'
            time.comment = ''

            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'


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


            #%% get timestamps in ISO 8601 format
            start_date = datetime(1904,1,1)
            timestamp_seconds = [int(float(value.strip())) for value in wind_file_data[index_columns]]
            timestamp_iso8601 = [ (start_date+timedelta(seconds=value)).isoformat()+'Z' for value in timestamp_seconds]
            output_dataset.variables['time'][:] = np.array(timestamp_iso8601)
            
            #%% calculate azimuth and elevation sweeps
            azimuth_angle_temp = [float(value) for value in wind_file_data[6]]
            elevation_angle_temp = [float(value) for value in wind_file_data[7]]
            azimuth_sweep_temp = np.insert(np.abs(np.diff(azimuth_angle_temp)),0,np.nan)
            elevation_sweep_temp = np.insert(np.abs(np.diff(elevation_angle_temp)),0,np.nan)

            #%% check if a sweep is existing and writing data accordingly
            changing_azimuth = False
            changing_elevation = False
            beam_sweeping = (parameters['attributes']['beam_sweeping'] == 'true')
            
            if np.nanmedian(azimuth_sweep_temp) > 0:
                changing_azimuth = True
                azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4', ('time'))
            
                azimuth_sweep = output_dataset.createVariable('azimuth_sweep', 'f4', ('time'))
                azimuth_sweep.units = 'degrees'
                azimuth_sweep.long_name = 'azimuth_sector_swept_during_accumulation'
                azimuth_sweep.comment = ''
                azimuth_sweep.accuracy = ''
                azimuth_sweep.accuracy_info = ''
            
                output_dataset.variables['azimuth_angle'][:] = azimuth_angle_temp
                output_dataset.variables['azimuth_sweep'][:] = azimuth_sweep_temp
                
            else:
                azimuth_angle = output_dataset.createVariable('azimuth_angle', 'f4')
                output_dataset.variables['azimuth_angle'][:] = np.nanmedian(azimuth_angle_temp)
            
            
            if np.nanmedian(elevation_sweep_temp) > 0:
                changing_elevation = True
                elevation_angle = output_dataset.createVariable('elevation_angle', 'f4', ('time'))
        
                elevation_sweep = output_dataset.createVariable('elevation_sweep', 'f4', ('time'))
                elevation_sweep.units = 'degrees'
                elevation_sweep.long_name = 'elevation_sector_swept_during_accumulation'
                elevation_sweep.comment = 'Elevation sweeping from approximately 0 to 15 degrees.'
                elevation_sweep.accuracy = ''
                elevation_sweep.accuracy_info = ''
        
                output_dataset.variables['elevation_angle'][:] = elevation_angle_temp
                output_dataset.variables['elevation_sweep'][:] = elevation_sweep_temp
            else:
                elevation_angle = output_dataset.createVariable('elevation_angle', 'f4')
                output_dataset.variables['elevation_angle'][:] = np.nanmedian(elevation_angle_temp)
            
            azimuth_angle.units = 'degrees'
            azimuth_angle.long_name = 'azimuth_angle_of_lidar beam'
            azimuth_angle.comment = ''
            azimuth_angle.accuracy = ''
            azimuth_angle.accuracy_info = ''
            
            elevation_angle.units = 'degrees'
            elevation_angle.long_name = 'elevation_angle_of_lidar beam'
            elevation_angle.comment = ''
            elevation_angle.accuracy = ''
            elevation_angle.accuracy_info = ''

            #%% setting scan_type according to sweeps            
            if (not changing_azimuth) & (not changing_elevation): #case LOS
                scan_type[:] = 1
            elif (changing_azimuth) & (not changing_elevation) & (not beam_sweeping): #case DBS
                scan_type[:] = 2
            elif (changing_azimuth) & (not changing_elevation) & (beam_sweeping): #case PPI
                scan_type[:] = 4
            elif (not changing_azimuth) & (changing_elevation) & (beam_sweeping): #case RHI
                scan_type[:] = 5
            else: #case other
                scan_type[:] = 0
            
         
            #%% read vel, width, cnr out of dataset
            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['VEL'][:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 5::4]]))
            output_dataset.variables['WIDTH'][:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 7::4]]))
            output_dataset.variables['CNR'][:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 6::4]]))
            
        #%% case appending
        else: 
            index_columns = 4 - (len(wind_file_data) % 4)
            ntime = len(output_dataset.dimensions["time"])
            
            start_date = datetime(1904,1,1)
            timestamp_seconds = [int(float(value.strip())) for value in wind_file_data[index_columns]]
            timestamp_iso8601 = [ (start_date+timedelta(seconds=value)).isoformat()+'Z' for value in timestamp_seconds]
            output_dataset.variables['time'][ntime:] = np.array(timestamp_iso8601)
            
            if 'azimuth_sweep' in output_dataset.variables :
                azimuth_angle_temp = [float(value) for value in wind_file_data[6]]
                azimuth_sweep_temp = np.insert(np.abs(np.diff(azimuth_angle_temp)),0,np.nan)
                output_dataset.variables['azimuth_angle'][ntime:] = azimuth_angle_temp
                output_dataset.variables['azimuth_sweep'][ntime:] = azimuth_sweep_temp

            if 'elevation_sweep' in output_dataset.variables :
                elevation_angle_temp = [float(value) for value in wind_file_data[7]]
                elevation_sweep_temp = np.insert(np.abs(np.diff(elevation_angle_temp)),0,np.nan)
                output_dataset.variables['elevation_angle'][ntime:] = elevation_angle_temp
                output_dataset.variables['elevation_sweep'][ntime:] = elevation_sweep_temp


            # e.g. radial velocity starts at 5th column and is then repeated every 9th column
            output_dataset.variables['VEL'][ntime:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 5::4]]))
            output_dataset.variables['WIDTH'][ntime:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 7::4]]))
            output_dataset.variables['CNR'][ntime:, :] = list(
                zip(*[[float(value) for value in row] for row in wind_file_data[index_columns + 6::4]]))
