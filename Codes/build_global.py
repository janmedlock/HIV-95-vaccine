#!/usr/bin/python3
'''
Update the Global results.
'''

import model


# 90-90-90 isn't finished yet.
# targets = model.targets.all_
targets_baselines = [model.targets.StatusQuo(),
                     model.targets.UNAIDS95()]
targets = []
for t in targets_baselines:
    targets.extend([t, model.targets.Vaccine(treatment_targets = t)])


if __name__ == '__main__':
    for target in targets:
        if not model.results.samples.exists('Global', target):
            results = model.results.samples.Results('Global', target)
            results._load_data()
            model.results.samples.dump('Global', target, results)
