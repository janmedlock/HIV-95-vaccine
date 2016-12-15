'''
A :mod:`pickle` interface using files instead of descriptors.
'''

import pickle


def load(filename):
    with open(filename, 'rb') as fd:
        return pickle.load(fd)


def dump(obj, filename):
    with open(filename, 'wb') as fd:
        return pickle.dump(obj, fd)
