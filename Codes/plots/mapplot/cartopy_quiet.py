'''
Silence warnings from matplotlib that are triggered by cartopy.
'''

import warnings
warnings.filterwarnings('ignore',
                        module = 'matplotlib',
                        message = ('get_axes has been deprecated in mpl 1.5, '
                                   'please use the\naxes property.  '
                                   'A removal date has not been set.'))
from cartopy import *
