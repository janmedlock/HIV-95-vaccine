#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import os.path
import sys

sys.path.append('..')
import drive


files = (
    '../../Documents/Latex/diagram_standalone.pdf',
    '../../Documents/Latex/diagram_standalone.png',
    'effectiveness_all.pdf',
    'effectiveness.pdf',
    'effectiveness.png',
    'infections_averted_map.pdf',
    'infections_averted_map.png',
    'initial_prevalence_map.pdf',
    'initial_prevalence_map.png',
    'transmission_rate.pdf',
    'transmission_rate.png',
    'vaccine_sensitivity_Status_Quo.pdf',
    'vaccine_sensitivity_Status_Quo.png',
    'vaccine_sensitivity_95–95–95.pdf',
    'vaccine_sensitivity_95–95–95.png'
)
       
# 'Effectiveness of HIV vaccine files' folder
folderId = '0B_53qFSHU3XKNjc0d3lTV2s4cWM'


if __name__ == '__main__':
    with drive.Driver(parent = folderId) as d:
        for f in files:
            d.upload(f)
