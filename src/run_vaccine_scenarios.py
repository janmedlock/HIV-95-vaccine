#!/usr/bin/python3
'''
Using the modes of the parameter distributions,
run simulations for the different vaccine sensitivity scenarios.
'''

import joblib

import model
import run_modes


def _main():
    run_modes._main(model.target.vaccine_scenarios)


if __name__ == '__main__':
    _main()
