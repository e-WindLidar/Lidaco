from lidaco.core.Builder import Builder
import os

meas_ID = '95'


errLog = r'.\Lidar data\converted\0'+meas_ID+'\error.log'
if os.path.isfile(errLog):
    os.remove(errLog)

# user must set the configuration file for the specific data set
file1 = r'C:\Users\lpauscher\Documents\python_scripts\git\Lidaco\yamls\meas_IDs\Meas_ID_'+meas_ID+'.yaml'

builder = Builder(config_file = file1)
builder.build()


errLog = r'.\Lidar data\converted\0'+meas_ID+'\error.log'

if os.path.isfile(errLog):
    file = open(errLog, 'r') 
    errFiles = file.readlines()
    
    for file in errFiles:   
        os.remove(file[:-1])