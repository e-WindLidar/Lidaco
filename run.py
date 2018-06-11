# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 12:58:05 2018

@author: skulla
"""

from lidaco.core.Builder import Builder

# user must set the configuration file for the specific data set
file1 = r'C:\Users\tklaas\Desktop\Kassel_Experiment_yaml_configs\NEWA_Kassel_WP6.yaml'

builder = Builder(config_file = file1)
builder.build()