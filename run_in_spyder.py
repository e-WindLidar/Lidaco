# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 12:58:05 2018

@author: skulla
"""

from lidaco.core.Builder import Builder

# user must set the configuration file for the specific data set
file1 = r'C:\Users\tklaas\Documents\GitHub\tobkla_Lidaco\samples\Kassel_Experiment\configs\NEWA_Kassel_WS1.yaml'

builder = Builder(config_file = file1)
builder.build()