#!/usr/bin/python3
'''
Plot the effectiveness of interventions in all countries.
'''

import os.path
import sys

sys.path.append(os.path.dirname(__file__))  # For Sphinx.
import effectiveness


if __name__ == '__main__':
    effectiveness.plot_all()
