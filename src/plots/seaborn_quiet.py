'''
Silence warnings from :mod:`matplotlib` that are triggered by :mod:`seaborn`.
'''

import warnings
warnings.filterwarnings('ignore',
                        module = 'matplotlib',
                        message = ('axes.color_cycle is deprecated '
                                   'and replaced with axes.prop_cycle; '
                                   'please use the latter.'))
warnings.filterwarnings('ignore',
                        module = 'IPython.html',
                        message = ('The `IPython.html` package has '
                                   'been deprecated. You should import '
                                   'from `notebook` instead. '
                                   '`IPython.html.widgets` has moved '
                                   'to `ipywidgets`.'))
from seaborn import *
