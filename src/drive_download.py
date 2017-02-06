#!/usr/bin/python3
'''
Download files from Google Drive.
'''

import drive

xlsx_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
files = (
    {'filename': 'data_sheet',
     'mimeType': xlsx_mime},
)
       

# 90-90-90/Codes
folderId = '0B5E-ra0QvBe-bjlVWGVzREgwbTg'


if __name__ == '__main__':
    with drive.Driver(parent = folderId) as d:
        for f in files:
            d.export_if_newer(**f)
