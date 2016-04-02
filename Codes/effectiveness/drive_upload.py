#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import sys

sys.path.append('..')
import drive


files = (
    'effectiveness.pdf',
)
       

# 'Effectiveness of 90-90-90 targets files' folder
folderId = '0B_53qFSHU3XKLS1TQjFWVl9HZGs'


if __name__ == '__main__':
    with drive.Driver(parent = folderId) as d:
        for f in files:
            d.upload(f)
