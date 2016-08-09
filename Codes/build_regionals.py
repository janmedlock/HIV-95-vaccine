#!/usr/bin/python3
'''
Update the global and regional results.
'''

import model


def _main():
    regions = ['Global'] + model.regions.all_

    for region in regions:
        for target in model.targets.all_:
            if not model.results.samples.exists(region, target):
                results = model.results.samples.open_(region, target)
                results._load_data()
                model.results.samples.dump(region, target, results)


if __name__ == '__main__':
    _main()
