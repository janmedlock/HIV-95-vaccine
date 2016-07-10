'''
Pickle with xz compression.
'''

import lzma
import pickle


def load(filename):
    with lzma.open(filename, 'rb') as fd:
        return pickle.load(fd)


def dump(obj, filename):
    with lzma.open(filename, 'wb') as fd:
        return pickle.dump(obj, fd)
