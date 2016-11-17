#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import os.path
import sys
import time

sys.path.append('Codes')
import drive


files = (
    'Documents/supplementary_information.pdf',
    'Documents/diagram_standalone.pdf',
    'Documents/diagram_standalone.png',
    'Codes/plots/effectiveness.pdf',
    'Codes/plots/effectiveness.png',
    'Codes/plots/effectiveness_regions.pdf',
    'Codes/plots/effectiveness_regions.png',
    'Codes/plots/infections_averted_map.pdf',
    'Codes/plots/infections_averted_map.png',
    'Codes/plots/initial_prevalence_map.pdf',
    'Codes/plots/initial_prevalence_map.png',
    'Codes/plots/vaccine_scenarios.pdf',
    'Codes/plots/vaccine_scenarios.png',
)
       
# 'Effectiveness of HIV vaccine files' folder
folderId = '0B_53qFSHU3XKNjc0d3lTV2s4cWM'


if __name__ == '__main__':
    first = True
    with drive.Driver(parent = folderId) as d:
        if not first:
            time.sleep(1)
        else:
            first = False
        for f in files:
            try:
                d.upload_if_newer(f)
            except FileNotFoundError:
                print('{}: file not found locally.'.format(f))
