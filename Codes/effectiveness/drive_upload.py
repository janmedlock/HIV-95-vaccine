#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import sys

sys.path.append('..')
import drive


files = (
    'effectiveness_Global.pdf',
    'effectiveness_Global.png',
    'effectiveness_Haiti.pdf',
    'effectiveness_Haiti.png',
    'effectiveness_India.pdf',
    'effectiveness_India.png',
    'effectiveness_Rwanda.pdf',
    'effectiveness_Rwanda.png',
    'effectiveness_South_Africa.pdf',
    'effectiveness_South_Africa.png',
    'effectiveness_Uganda.pdf',
    'effectiveness_Uganda.png',
    'effectiveness_United_States.pdf',
    'effectiveness_United_States.png',
    'map_effectiveness.pdf',
    'map_effectiveness.png',
    'map_infections_averted.mp4',
    'map_infections_averted.pdf',
    'map_infections_averted.png',
    'map_prevalence.mp4',
    'map_prevalence.pdf',
    'map_prevalence.png',
    'prevalence.pdf',
    'prevalence.png',
    'table.csv'
)
       

# 'Effectiveness of 90-90-90 targets files' folder
folderId = '0B_53qFSHU3XKLS1TQjFWVl9HZGs'


if __name__ == '__main__':
    with drive.Driver(parent = folderId) as d:
        for f in files:
            d.upload(f)
