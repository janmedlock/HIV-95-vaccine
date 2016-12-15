#!/usr/bin/python3
'''
Generate parameter samples to use for simulations.
'''

import model


nsamples = 1000


if __name__ == '__main__':
    model.samples.generate(nsamples)
