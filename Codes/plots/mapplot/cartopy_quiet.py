'''
Silence warnings from :mod:`matplotlib` that are triggered by :mod:`cartopy`.
'''

import warnings
warnings.filterwarnings('ignore',
                        module = 'matplotlib',
                        message = ('get_axes has been deprecated in mpl 1.5, '
                                   'please use the\naxes property.  '
                                   'A removal date has not been set.'))
from cartopy import *
