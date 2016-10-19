#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import os.path
import sys
import time

sys.path.append('..')
import drive


files = (
    '../../Documents/supplementary_information.pdf',
    '../../Documents/diagram_standalone.pdf',
    '../../Documents/diagram_standalone.png',
    'effectiveness.pdf',
    'effectiveness.png',
    'effectiveness_regions.pdf',
    'effectiveness_regions.png',
    'infections_averted_map.pdf',
    'infections_averted_map.png',
    'initial_prevalence_map.pdf',
    'initial_prevalence_map.png',
    'vaccine_scenarios.pdf',
    'vaccine_scenarios.png',
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
