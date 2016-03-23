#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import drive


files = ('Global.pdf',
         'Haiti.pdf',
         'India.pdf',
         'Rwanda.pdf',
         'South_Africa.pdf',
         'Uganda.pdf',
         'United_States_of_America.pdf',
         'map909090_ICER.pdf',
         'map909090_cost.pdf',
         'map909090_effectiveness.pdf',
         'map_infections_averted.mp4',
         'map_infections_averted.pdf',
         'map_infections_averted_proportion.mp4',
         'map_infections_averted_proportion.pdf',
         'map_initial_proportions.pdf',
         'map_prevalence.mp4',
         'map_prevalence.pdf',
         'table909090.csv'
)
       

# 90-90-90 folder
folderId = '0B_53qFSHU3XKUXVSMld5VjdqRk0'


if __name__ == '__main__':
    with drive.Driver(parent = folderId) as d:
        for f in files:
            d.upload(f)
