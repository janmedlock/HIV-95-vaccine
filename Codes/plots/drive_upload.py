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
    'effectiveness.pdf',
    'effectiveness.png',
    'effectiveness_all.pdf',
    'effectiveness_regions.pdf',
    'effectiveness_regions.png',
    'infections_averted_map.pdf',
    'infections_averted_map.png',
    'infections_per_capita_averted_map.pdf',
    'infections_per_capita_averted_map.png',
    'initial_prevalence_map.pdf',
    'initial_prevalence_map.png',
    'prcc.pdf',
    'prcc.png',
    'transmission_rate.pdf',
    'transmission_rate.png',
    'vaccine_scenarios_Status_Quo.pdf',
    'vaccine_scenarios_Status_Quo.png',
    'vaccine_scenarios_95–95–95.pdf',
    'vaccine_scenarios_95–95–95.png'
)
       
# 'Effectiveness of HIV vaccine files' folder
folderId = '0B_53qFSHU3XKNjc0d3lTV2s4cWM'


if __name__ == '__main__':
    with drive.Driver(parent = folderId) as d:
        for f in files:
            try:
                d.upload_if_newer(f)
            except FileNotFoundError:
                print('{}: file not found locally.'.format(f))
