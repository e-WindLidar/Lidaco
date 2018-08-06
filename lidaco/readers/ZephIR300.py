import numpy as np
from ..core.Reader import Reader
import datetime
import pandas as pd
import re
from pathlib import Path

class ZephIR300(Reader):

    def __init__(self):
        super().__init__(False)

    def accepts_file(self, filename):
        return (filename.endswith(('.csv','.CSV')) & filename.startswith('Wind'))

    def output_filename(self, filename):
        return filename[:-4]

    def parse_time(string1):
            try:
                temp = datetime.datetime.strptime(string1,'%d.%m.%Y %H:%M:%S')
            except:
                try:
                    temp = datetime.datetime.strptime(string1,'%d/%m/%Y %H:%M:%S')
                except:
                    temp = datetime.datetime.strptime(string1,'%d.%m.%Y %H:%M')
            temp = temp.isoformat() +'Z'
            return temp

#    def required_params(self):
#        return ['position_x_input', 'position_y_input', 'position_z_input']

    def read_to(self, output_dataset, input_filepath, configs, appending):
       
        # read file
        
        ten_min_file = (re.findall(r'(?<=\\)\w+(?=_\d+@)',input_filepath)[0] == r'Wind10')
#
        try:
            f = open(input_filepath)
            f.readline()
            header = f.readline()
            header = header.split('Checksum')
            myCols = header[0].split(';')
            df=pd.read_csv(input_filepath,sep=';',skiprows=1,decimal=',',usecols=range(len(myCols)),index_col=False)   
            
    
            with open(input_filepath,'r',encoding='latin-1') as f: # get parameters from header
                header = f.readline()
                header=header.split(';')
                parameters = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in header if ':' in line}
                parameters['Measurement heights'] = [int(element.strip()) for element in parameters['Measurement heights'].split('m') if (element != '')]
                parameters['Measurement heights'].append(1)
    
    
            # create the dimensions
            output_dataset.createDimension('range', len(parameters['Measurement heights']))
            output_dataset.createDimension('time', None)
    
            # create the coordinate variables
            range1 = output_dataset.createVariable('range', 'f4', ('range',))
            range1.units = 'm'
            range1.long_name = 'range_gate_distance_from_lidar'
            range1[:] = np.array(parameters['Measurement heights'])
    
            time = output_dataset.createVariable('time', str, ('time',))
            time.units = 's'
            time.long_name = 'timestamp ISO 8601'
    
            # create the data variables
            scan_type = output_dataset.createVariable('scan_type', 'i')
            scan_type.units = 'none'
            scan_type.long_name = 'scan_type_of_the_measurement'
            scan_type[:] = 1
    
            accumulation_time = output_dataset.createVariable('accumulation_time', 'f4')
            accumulation_time.units = 'seconds'
            accumulation_time.long_name = 'time_for_spectral_accumulation'
            accumulation_time[:] = 1.0
    
            # create the measurement variables
            
            # Beschreibung einfügen
            tilt = output_dataset.createVariable('tilt', 'f4', ('time',))
            tilt.units = 'degrees north'
            tilt.long_name = 'either pitch or roll depending on higher value'
    
            T_external = output_dataset.createVariable('T_external', 'f4', ('time',))
            T_external.units = 'degrees C'
            T_external.long_name = 'temperature'
    
            yaw = output_dataset.createVariable('yaw', 'f4', ('time',))
            yaw.units = 'degrees'
            yaw.long_name = 'lidar_yaw_angle'
    
            rh = output_dataset.createVariable('rh', 'f4', ('time',))
            rh.units = 'degrees'
            rh.long_name = 'lidar_yaw_angle'
            
            p = output_dataset.createVariable('p', 'f4', ('time',))
            p.units = 'degrees'
            p.long_name = 'lidar_yaw_angle'
            
            if ten_min_file:
                n_valid = output_dataset.createVariable('n_valid', 'f4', ('time', 'range'))
                n_valid.units = '-'
                n_valid.long_name = 'number of valid scans in averaging period'
    
                if 'Proportion Of Packets With Rain (%)' in df.columns:
                    proportion_of_rain = output_dataset.createVariable('proportion_of_rain', 'f4', ('time',))
                    proportion_of_rain.units = 'percent'
                    proportion_of_rain.long_name = 'Proportion Of Packets With Rain'
                elif 'Raining' in df.columns:
                    proportion_of_rain = output_dataset.createVariable('rain', 'f4', ('time',))
                    proportion_of_rain.units = 'boolean'
                    proportion_of_rain.long_name = 'indictor for rain; 1 is rain 0 no rain'
                

            WS = output_dataset.createVariable('WS', 'f4', ('time', 'range'))
            WS.units = 'm.s-1'
            WS.long_name = 'mean of scalar wind speed'
            
            DIR = output_dataset.createVariable('DIR', 'f4', ('time', 'range'))
            DIR.units = 'degrees north'
            DIR.long_name = 'wind direction from north'
    
    
    
    
    
            # fill values from dataset        
            df['timestamp_iso8601'] = df['Time and Date'].apply(ZephIR300.parse_time)
        
    
            output_dataset.variables['time'][:] = df['timestamp_iso8601'].values        
            output_dataset.variables['T_external'][:] = df['Air Temp. (C)'].values        
            output_dataset.variables['tilt'][:] = df['Tilt (deg)'].values
            output_dataset.variables['yaw'][:] = df['ZephIR Bearing (deg)'].values
            output_dataset.variables['rh'][:] = df['Humidity (%)'].values
            output_dataset.variables['p'][:] = df['Pressure (mbar)'].values
            
            if ten_min_file:
                if 'Proportion Of Packets With Rain (%)' in df.columns:
                    output_dataset.variables['proportion_of_rain'][:] = df['Proportion Of Packets With Rain (%)'].values
                elif 'Raining' in df.columns:
                    output_dataset.variables['rain'][:] = df['Raining'].values
            
            met_ws_list = df.iloc[:,16]
            met_dir_list = df.iloc[:,17]
    
            if ten_min_file:
                ws_list = df.iloc[:,21:-2:8]
                dir_list = df.iloc[:,20:-2:8]
                n_valid_list = df.iloc[:,19:-2:8]
                n_valid_complete = pd.concat([n_valid_list,pd.Series(np.full_like(met_ws_list, np.nan),name='Packets in Average at MET')],join='inner',axis=1)
                output_dataset.variables['n_valid'][:, :] = n_valid_complete.values
    
            else:
                ws_list = df.iloc[:,20:-2:3]
                dir_list = df.iloc[:,19:-2:3]  
            
            ws_list_complete = pd.concat([ws_list, met_ws_list],join='inner',axis=1)
            dir_list_complete = pd.concat([dir_list, met_dir_list],join='inner',axis=1)
    
            output_dataset.variables['WS'][:, :] = ws_list_complete.values
            output_dataset.variables['DIR'][:, :] = dir_list_complete.values

        except Exception as err:
                print('Error ocurred while converting %s. See error.log for details.' % input_filepath)
                print(err)
           
                with open(Path(output_dataset.filepath()).parent / 'error.log','a') as logfile:
                    logfile.write( '%s'%output_dataset.filepath() +'\n')

