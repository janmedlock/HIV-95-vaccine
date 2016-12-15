#!/usr/bin/python3
'''
Patch samples.h5.
'''

import warnings

import numpy
import tables


filters = tables.Filters(complevel = 4,
                         complib = 'zlib',
                         shuffle = True,
                         fletcher32 = True)

def _main():
    patch = tables.open_file('samples_patch.h5')
    h5file = tables.open_file('results/samples.h5', mode = 'a', filters = filters)

    def are_equal(x, y):
        # Handle NaNs.
        X = numpy.ma.masked_invalid(x)
        Y = numpy.ma.masked_invalid(x)
        return (X == Y).all()


    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',
                                category = tables.NaturalNameWarning)
        for leaf in patch.walk_nodes(classname = 'Leaf'):
            if leaf._v_pathname in h5file:
                arr = h5file.get_node(leaf._v_parent._v_pathname, leaf._v_name)
                if are_equal(leaf, arr):
                    print('Skipping {}: identical in both files.'.format(
                        leaf._v_pathname))
                else:
                    print('Updating {}.'.format(leaf._v_pathname))
                    # arr[:] = leaf[:]
            else:
                print('Adding {}.'.format(leaf._v_pathname))
                h5file.create_carray(leaf._v_parent._v_pathname, leaf._v_name,
                                     obj = leaf[:],
                                     createparents = True)


    patch.close()
    h5file.close()


if __name__ == '__main__':
    _main()
