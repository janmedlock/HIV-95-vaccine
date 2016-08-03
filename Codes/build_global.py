#!/usr/bin/python3
'''
Update the Global results.
'''

import model


def _main():
    for target in model.targets.all_:
        if not model.results.samples.exists('Global', target):
            results = model.results.samples.Results('Global', target)
            results._load_data()
            model.results.samples.dump('Global', target, results)


if __name__ == '__main__':
    _main()
