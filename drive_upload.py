#!/usr/bin/python3
'''
Upload figures etc to Google Drive.
'''

import os
import sys
import time

sys.path.append('Codes')
import drive


# 'Effectiveness of HIV vaccine files' folder
folderId = '0B_53qFSHU3XKNjc0d3lTV2s4cWM'


if __name__ == '__main__':
    first = True
    with drive.Driver(parent = folderId) as d:
        if not first:
            time.sleep(1)
        else:
            first = False
        for (dirpath, dirnames, filenames) in os.walk('upload',
                                                      followlinks = True):
            for f in filenames:
                d.upload_if_newer(os.path.join(dirpath, f))
