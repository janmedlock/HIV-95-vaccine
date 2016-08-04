#!/usr/bin/python3
'''
Update the global and regional results.
'''

import model


def _main():
    regions = ['Global'] + model.regions.all_

    # 90-90-90 isn't done yet.
    targets_baselines = [model.targets.StatusQuo(), model.targets.UNAIDS95()]
    targets = []
    for target in targets_baselines:
        targets.extend([target,
                        model.targets.Vaccine(treatment_targets = target)])

    for region in regions:
        # for target in model.targets.all_:
        for target in targets:
            if not model.results.samples.exists(region, target):
                results = model.results.samples.load(region, target)
                results._load_data()
                model.results.samples.dump(region, target, results)


if __name__ == '__main__':
    _main()
