'''
Silence warnings from matplotlib that are triggered by seaborn.
'''

import warnings
warnings.filterwarnings('ignore',
                        module = 'matplotlib',
                        message = ('axes.color_cycle is deprecated '
                                   'and replaced with axes.prop_cycle; '
                                   'please use the latter.'))
from seaborn import *
